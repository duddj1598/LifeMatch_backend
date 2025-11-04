#!/usr/bin/env python3
# save_embeddings_to_postgres.py
import os
import sys
import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from pgvector.psycopg2 import register_vector

# -------------------------
# 설정 (커맨드라인 인자 또는 환경변수로 설정 가능)
# -------------------------
DEFAULT_META_CSV = "embedding_meta.csv"
DEFAULT_EMBED_NPY = "embeddings.npy"

# 예: export DATABASE_URL="postgresql://user:password@host:5432/dbname"
DATABASE_URL_ENV = "DATABASE_URL"

TABLE_NAME = "embeddings_meta"  # 저장할 테이블명

BATCH_SIZE = 500  # 한 번에 INSERT할 레코드 수 (성능/메모리 조절)

# -------------------------
# 유틸: DB 연결 및 테이블 생성
# -------------------------
def get_conn_from_env():
    db_url = os.environ.get(DATABASE_URL_ENV)
    if not db_url:
        raise RuntimeError(f"환경변수 {DATABASE_URL_ENV}가 설정되어 있지 않습니다.")
    conn = psycopg2.connect(db_url)
    # pgvector를 psycopg2에 등록 (vector 타입 사용 가능하게 함)
    register_vector(conn)
    return conn

def create_table_if_not_exists(conn, dim: int, table_name: str = TABLE_NAME):
    ddl = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        id bigserial PRIMARY KEY,
        record_id text UNIQUE,
        faiss_id integer,
        profile_string text,
        response_string text,
        embed_model text,
        embedding vector({dim}),
        created_at timestamptz DEFAULT now()
    );
    """
    with conn.cursor() as cur:
        # ensure pgvector extension exists (requires superuser on some hosts)
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute(ddl)
        conn.commit()

# -------------------------
# 데이터 로드
# -------------------------
def load_meta_and_embeddings(meta_csv_path: str, embed_npy_path: str):
    meta_df = pd.read_csv(meta_csv_path, dtype=str)  # faiss_id,record_id,... 텍스트로 로드 후 변환
    embeddings = np.load(embed_npy_path)
    if embeddings.ndim != 2:
        raise ValueError("임베딩 배열은 2차원이어야 합니다. shape:", embeddings.shape)
    if len(meta_df) != embeddings.shape[0]:
        raise ValueError(f"meta 행수({len(meta_df)})와 embeddings 행수({embeddings.shape[0]})가 다릅니다.")
    return meta_df, embeddings

# -------------------------
# 배치 INSERT
# -------------------------
def upsert_rows(conn, table_name: str, rows: list, dim: int):
    """
    rows: list of tuples (record_id, faiss_id, profile_string, response_string, embed_model, embedding_numpy_array)
    embedding_numpy_array: 1D numpy array of length dim
    """
    # prepare SQL. ON CONFLICT(record_id) DO UPDATE 로 upsert 처리
    sql = f"""
    INSERT INTO {table_name} (record_id, faiss_id, profile_string, response_string, embed_model, embedding)
    VALUES %s
    ON CONFLICT (record_id) DO UPDATE
      SET faiss_id = EXCLUDED.faiss_id,
          profile_string = EXCLUDED.profile_string,
          response_string = EXCLUDED.response_string,
          embed_model = EXCLUDED.embed_model,
          embedding = EXCLUDED.embedding,
          created_at = now()
    ;
    """
    # execute_values requires the sequence elements to be Python scalars. pgvector supports list->vector conversion.
    # Convert numpy arrays to Python list (float) for insertion
    values = []
    for rec_id, faiss_id, pstr, rstr, model_name, emb in rows:
        values.append((rec_id, int(faiss_id) if faiss_id is not None else None, pstr, rstr, model_name, emb.tolist()))
    with conn.cursor() as cur:
        execute_values(cur, sql, values, page_size=BATCH_SIZE)
    conn.commit()

# -------------------------
# 메인 처리
# -------------------------
def main(meta_csv_path: str, embed_npy_path: str, table_name: str):
    meta_csv_path = Path(meta_csv_path)
    embed_npy_path = Path(embed_npy_path)
    if not meta_csv_path.exists():
        print("메타 CSV 파일이 존재하지 않습니다:", meta_csv_path)
        sys.exit(1)
    if not embed_npy_path.exists():
        print("임베딩 NPY 파일이 존재하지 않습니다:", embed_npy_path)
        sys.exit(1)

    print("메타 및 임베딩 로드 중...")
    meta_df, embeddings = load_meta_and_embeddings(str(meta_csv_path), str(embed_npy_path))
    N, D = embeddings.shape
    print(f"로드 완료: 레코드 수={N}, 임베딩 차원={D}")

    print("Postgres 연결...")
    conn = get_conn_from_env()

    print("테이블 생성(존재하지 않으면) 또는 스키마 준비...")
    create_table_if_not_exists(conn, dim=D, table_name=table_name)

    # prepare rows for batch insert
    rows = []
    for i, row in meta_df.iterrows():
        record_id = str(row.get("record_id"))
        faiss_id = row.get("faiss_id")
        profile_string = row.get("profile_string") if "profile_string" in row else None
        response_string = row.get("response_string") if "response_string" in row else None
        embed_model = row.get("embed_model") if "embed_model" in row else None
        emb = embeddings[int(i)].astype(float)
        rows.append((record_id, faiss_id, profile_string, response_string, embed_model, emb))

    print("DB에 배치 업서트 중...")
    start = time.time()
    # 배치로 분할해서 insert
    for i in range(0, len(rows), BATCH_SIZE):
        chunk = rows[i : i + BATCH_SIZE]
        upsert_rows(conn, table_name, chunk, dim=D)
        print(f"Inserted chunk {i} ~ {i + len(chunk) - 1}")
    elapsed = time.time() - start
    print(f"완료: 총 {len(rows)} 레코드 삽입/갱신 (소요 {elapsed:.1f}s)")

    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Save embeddings + meta CSV into Postgres (pgvector)")
    parser.add_argument("--meta", default=DEFAULT_META_CSV, help="meta CSV path")
    parser.add_argument("--emb", default=DEFAULT_EMBED_NPY, help="embeddings .npy path")
    parser.add_argument("--table", default=TABLE_NAME, help="postgres table name")
    args = parser.parse_args()
    main(args.meta, args.emb, args.table)