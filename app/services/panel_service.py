import time
import json
import ast
import re
from typing import List, Optional
import numpy as np
import logging
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough

from app.config.llm_config import get_embedding_model, get_chroma_db, get_llm_client
from app.schemas.panel_schema import QueryOutputSchema

def cosine_similarity(vec1, vec2):
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    denom = (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    if denom == 0:
        return 0.0
    return float(np.dot(vec1, vec2) / denom)

def LLM_Decomposer(prompt: str) -> QueryOutputSchema:
    chroma = get_chroma_db()
    LLM = get_llm_client()

    chain = (
        {
            "context": chroma.as_retriever() | (lambda docs: "\n\n".join([doc.page_content for doc in docs])),
            "question": RunnablePassthrough()
        }
        | PromptTemplate(
                input_variables = ["question", "context"],
                template = """
                    아래 참고 문서를 기반으로 질문에 대해
                    1. panel_demographic 테이블에서 검색 가능한 조건은 SQL로 생성하고,
                    2. panel_demographic에서 검색할 수 없는 조건(비정형/자유응답 등)은 임베딩 기반 의미검색용 문장으로, 조건별로 각각 생성하세요.

                    질문:
                    {question}

                    참고 문서:
                    {context}

                    [출력은 반드시 아래 JSON 스키마에 맞춰주세요.]
                """
            )
        | LLM.with_structured_output(QueryOutputSchema)
    )

    response = chain.invoke(prompt)
    return response

def embedding_search(queries_to_embedding: List[str], conn) -> List[dict]:
    emb_model = get_embedding_model()
    results = []
    for query in queries_to_embedding:
        query_emb = emb_model.embed_query(query)
        vector_str = "[" + ",".join(str(x) for x in query_emb) + "]"
        with conn.cursor() as cur:
            try:
                cur.execute("""
                    SELECT DISTINCT ON (question_id) question_id, choice_text, question_embedding
                    FROM question_embeddings
                    ORDER BY question_id, question_embedding <-> %s::vector
                    LIMIT 3
                """, (vector_str,))
                first_results = cur.fetchall()
            except Exception:
                conn.rollback()
                first_results = []

        if not first_results:
            continue

        question_ids = [row[0] for row in first_results]
        with conn.cursor() as cur:
            try:
                cur.execute("""
                    SELECT question_id, question_text, choice_text, summary_embedding
                    FROM question_embeddings
                    WHERE question_id = ANY(%s)
                """, (question_ids,))
                summary_rows = cur.fetchall()
            except Exception:
                conn.rollback()
                continue

        scored = []
        for qid, question_text, choice_text, summary_emb in summary_rows:
            if isinstance(summary_emb, str):
                try:
                    summary_emb = ast.literal_eval(summary_emb)
                except Exception:
                    continue
            if summary_emb is None:
                continue
            score = cosine_similarity(query_emb, summary_emb)
            scored.append({
                "query": query,
                "question_id": qid,
                "question_text": question_text,
                "choice_text": choice_text,
                "score": float(score)
            })
        if scored:
            best = max(scored, key=lambda x: x["score"])
            results.append(best)
    return results

def find_matching_panel_ids(embedding_results_json: List[dict], conn, panel_response_sample: Optional[dict] = None):
    matched_ids = set()
    for result in embedding_results_json:
        question_id = result["question_id"]
        choice_text = result["choice_text"]
        with conn.cursor() as cur:
            try:
                cur.execute(f"""
                    SELECT id FROM panel_response
                    WHERE "{question_id}" IS NOT NULL
                    AND "{question_id}"::jsonb @> %s::jsonb
                """, (json.dumps([choice_text]),))
            except Exception:
                conn.rollback()
                try:
                    cur.execute(f"""
                        SELECT id FROM panel_response
                        WHERE "{question_id}" = %s
                    """, (choice_text,))
                except Exception:
                    conn.rollback()
                    continue
            rows = cur.fetchall()
            for row in rows:
                matched_ids.add(row[0])
    return list(matched_ids)

def decompose_and_search(query: str, conn):
    start = time.time()
    logging.info(f"input query: {query}")
    llm_out = LLM_Decomposer(query)
    sql_query = llm_out.sql
    queries_to_embedding = llm_out.queries_to_embedding

    with conn.cursor() as cur:
        try:
            cur.execute(sql_query)
            panel_demographic_ids = [r[0] for r in cur.fetchall()]
        except Exception as e:
            conn.rollback()
            raise e

    embedding_results = embedding_search(queries_to_embedding, conn)

    panel_response_sample = {}
    with conn.cursor() as cur:
        try:
            cur.execute("SELECT * FROM panel_response LIMIT 1")
            sample_row = cur.fetchone()
            if sample_row:
                colnames = [desc[0] for desc in cur.description]
                panel_response_sample = dict(zip(colnames, sample_row))
        except Exception:
            panel_response_sample = {}

    embedding_matched_ids = find_matching_panel_ids(embedding_results, conn, panel_response_sample)
    logging.info(f"embedding_matched_ids: {embedding_matched_ids}")

    final_ids = list(set(panel_demographic_ids) & set(embedding_matched_ids))
    logging.info(f"final_ids: {final_ids}")
    elapsed = time.time() - start
    return {
        "final_ids": final_ids,
        "panel_demographic_count": len(panel_demographic_ids),
        "embedding_matched_count": len(embedding_matched_ids),
        "elapsed_seconds": round(elapsed, 3)
    }
