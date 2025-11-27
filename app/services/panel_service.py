import time
import json
import ast
import random
from typing import List, Optional
import numpy as np
import logging

from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough

from app.config.llm_config import get_embedding_model, get_chroma_db, get_llm_client
from app.schemas.panel_schema import QueryOutputSchema
from app.config.firebase_config import db  # Firestore 사용


# 🔥 카테고리 → 라이프스타일 매핑표
CATEGORY_TO_LIFESTYLE = {
    "생활습관·건강": ["자기관리형 웰니스족"],
    "기술": ["디지털 트렌드세터"],
    "소비·경제": ["알뜰살뜰 실속파"],
    "여가·문화": ["감성 충만 아티스트", "소박한 힐링주의자"],
}


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

    # 🔥 verbalized confidence 출력 지시
    chain = (
        {
            "context": chroma.as_retriever() | (lambda docs: "\n\n".join([doc.page_content for doc in docs])),
            "question": RunnablePassthrough(),
        }
        | PromptTemplate(
            input_variables=["question", "context"],
            template="""
                아래 참고 문서를 기반으로 질문에 대해
                1. panel_demographic 테이블에서 검색 가능한 조건은 SQL로 생성하고,
                2. panel_demographic에서 검색할 수 없는 조건(비정형/자유응답 등)은 임베딩 기반 의미검색용 문장으로 생성하세요.
                3. 각 항목별로 verbalized confidence(모델이 해당 답변에 대해 얼마나 확신하는지 0~1 사이의 수치와 간단한 설명)를 함께 출력하세요.

                질문:
                {question}

                참고 문서:
                {context}

                [출력은 반드시 JSON 스키마에 맞추세요.]
            """
        )
        | LLM.with_structured_output(QueryOutputSchema)
    )

    return chain.invoke(prompt)


# --------------------------------------------------------
# 🔥 Firestore에서 category 기반 유저 1명 추천
# --------------------------------------------------------
def pick_user_by_category(category: Optional[str]) -> Optional[dict]:
    """
    category -> lifestyle -> 해당 lifestyle 유저 랜덤 1명
    없으면 전체 users에서 랜덤 1명
    """
    # 1) lifestyle 매핑이 가능한 경우
    if category and category in CATEGORY_TO_LIFESTYLE:
        lifestyle_candidates = CATEGORY_TO_LIFESTYLE[category]
        chosen_life = random.choice(lifestyle_candidates)

        matched_users = list(
            db.collection("users")
            .where("user_lifestyle_type", "==", chosen_life)
            .stream()
        )

        if matched_users:
            user_doc = random.choice(matched_users)
            return {"id": user_doc.id, **user_doc.to_dict()}

    # 2) fallback: 전체 유저
    all_users = list(db.collection("users").stream())
    if not all_users:
        return None

    user_doc = random.choice(all_users)
    return {"id": user_doc.id, **user_doc.to_dict()}


# --------------------------------------------------------
# 🔥 임베딩 검색
# --------------------------------------------------------
def embedding_search(queries_to_embedding: List[str], conn) -> List[dict]:
    emb_model = get_embedding_model()
    results = []

    for query in queries_to_embedding:
        query_emb = emb_model.embed_query(query)
        vector_str = "[" + ",".join(str(x) for x in query_emb) + "]"

        # 1) question_embeddings에서 유사도 검색
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

        # 2) summary_embedding 가져오기
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
        sim_scores = [] # 🔥 retrieval sim_score
        for qid, _, choice_text, summary_emb in summary_rows:
            if isinstance(summary_emb, str):
                try:
                    summary_emb = ast.literal_eval(summary_emb)
                except:
                    continue
            if summary_emb is None:
                continue

            score = cosine_similarity(query_emb, summary_emb)
            sim_scores.append(score)
            scored.append({
                "query": query,
                "question_id": qid,
                "choice_text": choice_text,
                "score": score
            })

        if scored:
            best = max(scored, key=lambda x: x["score"])
            # 🔥 retrieval sim_score: top K(여기선 summary_rows) 평균/최댓값
            best["retrieval_sim_score_avg"] = float(np.mean(sim_scores)) if sim_scores else None
            best["retrieval_sim_score_max"] = float(np.max(sim_scores)) if sim_scores else None
            results.append(best)

    return results


# --------------------------------------------------------
# 🔥 panel_response에서 임베딩 결과에 해당하는 패널 찾기
# --------------------------------------------------------
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

# --------------------------------------------------------
# 🔥 confidence 결합·정규화·캘리브레이션 함수
# --------------------------------------------------------
def normalize_confidence(val, min_val=0.0, max_val=1.0):
    # min-max 정규화 (값이 None이면 0 반환)
    if val is None:
        return 0.0
    return max(min((val - min_val) / (max_val - min_val), 1.0), 0.0)

def calibrate_confidence(conf, method="identity"):
    # 캘리브레이션 함수 (identity: 그대로 반환, 향후 모델 기반 보정 가능)
    if method == "identity":
        return conf
    # 예: sigmoid 보정 등 추가 가능
    return conf

def combine_confidences(verbalized_conf, retrieval_conf, weights=(0.6, 0.4)):
    # verbalized_conf와 retrieval_conf만 결합
    confs = [verbalized_conf, retrieval_conf]
    norm_confs = [normalize_confidence(c) for c in confs]
    combined = sum(w * c for w, c in zip(weights, norm_confs))
    return calibrate_confidence(combined)

# --------------------------------------------------------
# 🔥 신뢰도 결합·출력 비동기 함수
# --------------------------------------------------------
import threading
def calc_and_log_confidence(llm_out, sql_query, embedding_results):
    try:
        # LLM verbalized confidence (SQL 기준)
        verbalized_conf = float(getattr(llm_out, "sql_confidence", 0.0))
    except Exception:
        verbalized_conf = 0.0

    if embedding_results and "retrieval_sim_score_avg" in embedding_results[0]:
        retrieval_conf = float(embedding_results[0]["retrieval_sim_score_avg"])
    else:
        retrieval_conf = 0.0
    final_confidence = combine_confidences(verbalized_conf, retrieval_conf)
    logging.info(f"[panel] confidence: verbalized={verbalized_conf:.3f}, retrieval={retrieval_conf:.3f}, final={final_confidence:.3f}")

# --------------------------------------------------------
# 🔥 메인 로직: category 포함 패널 검색
# --------------------------------------------------------
def decompose_and_search(query: str, category: Optional[str], conn):
    start = time.time()

    # 1) LLM으로 쿼리 분해
    llm_out = LLM_Decomposer(query)
    sql_query = llm_out.sql
    queries_to_embedding = llm_out.queries_to_embedding

    # 2) Firestore에서 category 기반 user 추천
    matched_user = pick_user_by_category(category)
    recommended_user_id = None
    if matched_user:
        recommended_user_id = matched_user.get("user_id") or matched_user["id"]
        #userid넣을때 "user" : {"id" : recommended_user_id, "lifestryle" : recommended_user_lifestyle} 형태로 넣기
        recommended_user_lifestyle = matched_user.get("user_lifestyle_type")
        recommended_user = {"id": recommended_user_id, "lifestyle": recommended_user_lifestyle}
        logging.info(f"[panel] selected user = {recommended_user}")

    # 3) SQL 실행
    with conn.cursor() as cur:
        try:
            cur.execute(sql_query)
            demographic_ids = [r[0] for r in cur.fetchall()]
        except Exception as e:
            conn.rollback()
            raise e

    # 4) 임베딩 검색
    embedding_results = embedding_search(queries_to_embedding, conn)

    # 5) panel_response 샘플
    panel_response_sample = {}
    with conn.cursor() as cur:
        try:
            cur.execute("SELECT * FROM panel_response LIMIT 1")
            row = cur.fetchone()
            if row:
                colnames = [desc[0] for desc in cur.description]
                panel_response_sample = dict(zip(colnames, row))
        except Exception:
            pass

    # 6) panel_response 매칭
    embedding_matched_ids = find_matching_panel_ids(
        embedding_results, conn, panel_response_sample
    )

    # 7) 두 조건 교집합
    final_ids = list(set(demographic_ids) & set(embedding_matched_ids))

    logging.info(f"[panel] final_result: {final_ids}")
    logging.info(f"elapsed: {time.time() - start}s")
    
    # 9) 신뢰도 결합·출력 비동기 실행 (응답속도 개선)
    threading.Thread(target=calc_and_log_confidence, args=(llm_out, sql_query, embedding_results)).start()


    return {
        "user" : recommended_user,
        "panel" : final_ids,
        "length": len(final_ids)
    }