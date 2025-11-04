# file: embed_profiles_with_kure_jsonl.py
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Iterator

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
import faiss

# -------------------------
# 설정
# -------------------------
INPUT_JSONL_PATH = "records.jsonl"   # jsonl 입력 경로
OUTPUT_META_CSV = "embedding_meta.csv"
OUTPUT_EMBED_NPY = "embeddings.npy"
FAISS_INDEX_PATH = "faiss_index.bin"

EMBED_MODEL_NAME = "nlpai-lab/KURE-v1"
BATCH_SIZE = 64
# EMBED_DIM는 모델 로드 후 확인 가능하므로 하드코딩 불필요

# -------------------------
# 유틸(전처리/직렬화)
# -------------------------
def normalize_text(s: Any) -> str:
    if s is None:
        return "none"
    s = str(s).strip()
    if s == "":
        return "none"
    s = re.sub(r"[\t\n\r]+", " ", s)
    s = re.sub(r"\s{2,}", " ", s)
    s = re.sub(r"\([^)]*\)", "", s)
    return s.strip()

def join_list_items(items) -> str:
    if not items:
        return "none"
    cleaned = []
    for it in items:
        if it is None:
            continue
        t = normalize_text(it)
        if t and t.lower() != "none":
            cleaned.append(t)
    if not cleaned:
        return "none"
    return ",".join(cleaned[:2])

def make_profile_string(profile: Dict[str, Any]) -> str:
    age = profile.get("age_group") or "none"
    sex = profile.get("sex") or "none"
    region = None
    try:
        region = profile.get("region", {}).get("level1") or "none"
    except:
        region = profile.get("region") or "none"
    occupation = profile.get("occupation") or "none"
    products = profile.get("ownership_products") or profile.get("products") or []
    products_str = join_list_items(products) if isinstance(products, (list, tuple)) else normalize_text(products)
    has_car_raw = profile.get("has_car")
    if isinstance(has_car_raw, bool):
        has_car = "yes" if has_car_raw else "no"
    else:
        hc = str(has_car_raw).lower() if has_car_raw is not None else ""
        if hc in ("yes","y","true","있다"):
            has_car = "yes"
        elif hc in ("no","n","false","없다"):
            has_car = "no"
        else:
            has_car = "none"
    return f"age:{normalize_text(age)} | sex:{normalize_text(sex)} | region:{normalize_text(region)} | occupation:{normalize_text(occupation)} | products:{products_str} | car:{has_car}"

def make_response_string(response: Dict[str, Any]) -> str:
    keys_to_extract = ["Q1","Q2","Q3_1","Q8","Q11","Q13","Q16","Q17","Q31","Q32"]
    parts = []
    for k in keys_to_extract:
        val = response.get(k)
        if val is None:
            parts.append(f"{k}:none")
        else:
            if isinstance(val, list):
                parts.append(f"{k}:{join_list_items(val)}")
            else:
                parts.append(f"{k}:{normalize_text(val)}")
    return "; ".join(parts)

# -------------------------
# JSONL 스트리밍 로더
# -------------------------
def iter_records_jsonl(path: str) -> Iterator[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue

# -------------------------
# 임베딩 배치 생성
# -------------------------
def embed_texts(model: SentenceTransformer, texts: List[str], batch_size: int = 64) -> np.ndarray:
    return model.encode(texts, convert_to_numpy=True, show_progress_bar=False, batch_size=min(batch_size, len(texts)))

# -------------------------
# FAISS 색인 빌드
# -------------------------
def build_and_save_faiss_index(embeddings: np.ndarray, index_path: str) -> None:
    faiss.normalize_L2(embeddings)
    D = embeddings.shape[1]
    index = faiss.IndexFlatIP(D)
    index.add(embeddings)
    faiss.write_index(index, index_path)

# -------------------------
# 메인: 스트리밍 처리 + 배치 색인
# -------------------------
def main():
    model = SentenceTransformer(EMBED_MODEL_NAME)
    print("Loaded model:", EMBED_MODEL_NAME)

    meta_rows = []
    all_embeddings = []  # 메모리 허용 범위에서 사용. 대용량이면 chunk별로 FAISS에 append/merge 필요
    faiss_id = 0
    ids = []

    batch_profile_texts = []
    batch_record_ids = []
    batch_response_texts = []

    for rec in iter_records_jsonl(INPUT_JSONL_PATH):
        rec_id = rec.get("id") or rec.get("record_id") or f"row_{faiss_id}"
        response = rec.get("response", {}) or {}
        profile = rec.get("profile", {}) or {}

        pstr = make_profile_string(profile)
        rstr = make_response_string(response)

        batch_profile_texts.append(pstr)
        batch_response_texts.append(rstr)
        batch_record_ids.append(rec_id)

        # 배치가 모이면 임베딩하고 저장 메타 생성
        if len(batch_profile_texts) >= BATCH_SIZE:
            emb = embed_texts(model, batch_profile_texts, batch_size=BATCH_SIZE)
            # 정규화는 FAISS 추가 전에 처리
            # 저장
            all_embeddings.append(emb)
            for i, rid in enumerate(batch_record_ids):
                meta_rows.append({
                    "record_id": rid,
                    "faiss_id": len(ids) + i,
                    "profile_string": batch_profile_texts[i],
                    "response_string": batch_response_texts[i],
                    "embed_model": EMBED_MODEL_NAME
                })
            ids.extend(batch_record_ids)
            faiss_id += len(batch_profile_texts)
            batch_profile_texts = []
            batch_record_ids = []
            batch_response_texts = []

    # 남은 배치 처리
    if batch_profile_texts:
        emb = embed_texts(model, batch_profile_texts, batch_size=BATCH_SIZE)
        all_embeddings.append(emb)
        for i, rid in enumerate(batch_record_ids):
            meta_rows.append({
                "record_id": rid,
                "faiss_id": len(ids) + i,
                "profile_string": batch_profile_texts[i],
                "response_string": batch_response_texts[i],
                "embed_model": EMBED_MODEL_NAME
            })
        ids.extend(batch_record_ids)

    if not all_embeddings:
        print("No embeddings generated.")
        return

    # 모든 임베딩 합치기
    embeddings = np.vstack(all_embeddings).astype('float32')
    print("Final embeddings shape:", embeddings.shape)

    # FAISS 인덱스 생성/저장
    build_and_save_faiss_index(embeddings, FAISS_INDEX_PATH)
    print("FAISS index written to", FAISS_INDEX_PATH)

    # 임베딩 배열 저장(정규화 전/후 상태에 따라 다름; 위에서 FAISS는 normalize_L2 했음)
    np.save(OUTPUT_EMBED_NPY, embeddings)
    print("Embeddings saved to", OUTPUT_EMBED_NPY)

    # 메타 CSV 저장
    meta_df = pd.DataFrame(meta_rows)
    meta_df.to_csv(OUTPUT_META_CSV, index=False, encoding="utf-8-sig")
    print("Meta CSV saved to", OUTPUT_META_CSV)

if __name__ == "__main__":
    main()