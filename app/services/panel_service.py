from typing import List, Dict, Any, Optional

def search(
    query: str,
    *,
    db_session = None,
    mode: str = "field",          # "field" | "semantic" | "hybrid"
    limit: int = 10,
    offset: int = 0,
    min_score: float = 0.0,
) -> List[Dict[str, Any]]:
    """
    자연어 쿼리를 받아 DB 조회 또는 의미검색을 통해 패널 목록을 반환합니다.
    - db_session: 데이터베이스 세션(ORM 세션 또는 커넥션). 라우터에서 주입됨.
    - mode: 검색 전략 결정. "field"는 필드 매핑 기반 검색, "semantic"은 임베딩+벡터검색.
    """

    # 기본 동작(개발/테스트용 샘플 데이터)
    SAMPLE_DATA = [
        {"nickname": "홍길동", "age": 25, "interests": ["러닝", "운동"], "match_score": 0.91},
        {"nickname": "김영희", "age": 28, "interests": ["요가", "명상"], "match_score": 0.87},
    ]

    # 1) 입력 전처리
    q = (query or "").strip().lower()

    # 2) 검색 전략 분기 포인트
    if mode == "field":
        # TODO: 필드 매핑 기반 검색 구현
        # - FieldMapper 인터페이스를 호출해서 q -> 필터(예: {"age_min":20, "interests":["러닝"]}) 변환
        # - db_session을 사용해 ORM/SQL로 필터 적용 쿼리 실행
        # - 아래 코드는 샘플 데이터에 대한 간단한 ILIKE 유사 필터 예시
        def matches(item):
            if q == "":
                return True
            if q in item["nickname"].lower():
                return True
            for intr in item["interests"]:
                if q in intr.lower():
                    return True
            return False

        filtered = [d for d in SAMPLE_DATA if matches(d) and d["match_score"] >= min_score]

    elif mode == "semantic":
        # TODO: 의미 검색(임베딩 + 벡터 색인) 구현
        # - Embedder 인터페이스 호출: q -> 벡터
        # - SemanticSearchEngine 호출: 벡터 -> 후보 id + score 리스트
        # - 후보 id를 사용해 db_session에서 레코드 조회
        # - 반환 레코드에 벡터 검색 점수(정규화) 포함
        # 현재는 샘플 데이터 필터로 대체
        filtered = [d for d in SAMPLE_DATA if d["match_score"] >= min_score]

    elif mode == "hybrid":
        # TODO: 하이브리드 전략 구현
        # - LLM을 사용해 필드 필터를 추출하고(선택적), 동시에 의미검색으로 후보를 얻음
        # - 후보 집합을 병합(예: 가중치 결합)해서 최종 정렬
        filtered = [d for d in SAMPLE_DATA if d["match_score"] >= min_score]

    else:
        raise ValueError("지원하지 않는 검색 모드입니다")

    # 3) 정렬 및 페이징
    filtered.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    paged = filtered[offset: offset + limit]

    # 4) DB 결과를 API 응답 스키마에 맞게 매핑
    # TODO: 실제 ORM 모델의 필드명에 맞춰 매핑 코드로 교체
    results = []
    for rec in paged:
        results.append({
            "nickname": rec.get("nickname"),
            "age": rec.get("age"),
            "interests": rec.get("interests"),
            "match_score": rec.get("match_score"),
            # 추가 메타(예: similarity_score, source: "db"|"vector")를 여기에 넣을 수 있음
        })

    return results
