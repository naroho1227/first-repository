"""
recommend.py - 뉴스 추천 알고리즘

[현재 상태]
백엔드 DB 연동 전 단계입니다.
DUMMY_USERS / DUMMY_NEWS / DUMMY_LOGS 는 임시 더미 데이터이며,
백엔드의 database.py 와 models.py 가 완성되면
각 함수 내부의 더미 데이터 조회 부분을 실제 DB 쿼리로 교체합니다.

[[DB 연동 시 교체 위치]]
- get_user_interest()      → users 테이블 쿼리로 교체
- filter_news_by_category() → news 테이블 쿼리로 교체
- get_category_scores()    → user_logs 테이블 쿼리로 교체

[News API 카테고리 7개]
business, entertainment, general, health, science, sports, technology

[추천 로직]
1. 유저의 클릭/뷰 로그를 기반으로 카테고리별 점수 계산
   - click: +2점 / view: +1점
2. 점수가 없는 경우 (첫 접속): 전체 뉴스에서 랜덤 추천
3. 점수가 있는 경우: 점수 높은 카테고리 뉴스 우선 추천
4. 상위 5개 반환
"""

import random


# ─────────────────────────────────────────
# 더미 데이터 (DB 연동 후 삭제될 부분)
# ─────────────────────────────────────────

DUMMY_USERS = [
    {"id": 1, "interest": "business"},
    {"id": 2, "interest": "technology"},
    {"id": 3, "interest": "sports"},      # 첫 접속 유저 (로그 없음)
]

DUMMY_NEWS = [
    {"id": 1,  "title": "KOSPI surges past 2600",             "category": "business",     "created_at": "2025-03-20"},
    {"id": 2,  "title": "AI chip demand hits record high",     "category": "technology",   "created_at": "2025-03-21"},
    {"id": 3,  "title": "Exchange rate jumps to 1380 KRW",    "category": "business",     "created_at": "2025-03-22"},
    {"id": 4,  "title": "Son Heung-min scores twice",         "category": "sports",       "created_at": "2025-03-21"},
    {"id": 5,  "title": "Central bank holds interest rate",   "category": "business",     "created_at": "2025-03-19"},
    {"id": 6,  "title": "Samsung Galaxy new model released",  "category": "technology",   "created_at": "2025-03-22"},
    {"id": 7,  "title": "K-League opening match results",     "category": "sports",       "created_at": "2025-03-20"},
    {"id": 8,  "title": "Real estate market stabilizes",      "category": "business",     "created_at": "2025-03-23"},
    {"id": 9,  "title": "OpenAI announces GPT-5",             "category": "technology",   "created_at": "2025-03-23"},
    {"id": 10, "title": "WBC Korea national team roster set", "category": "sports",       "created_at": "2025-03-22"},
    {"id": 11, "title": "New cancer vaccine shows promise",   "category": "health",       "created_at": "2025-03-23"},
    {"id": 12, "title": "NASA confirms new exoplanet",        "category": "science",      "created_at": "2025-03-22"},
    {"id": 13, "title": "Top 10 movies this week",            "category": "entertainment","created_at": "2025-03-21"},
    {"id": 14, "title": "WHO warns of new virus strain",      "category": "health",       "created_at": "2025-03-20"},
    {"id": 15, "title": "General election results overview",  "category": "general",      "created_at": "2025-03-23"},
]

# action: click(+2점) / view(+1점)
DUMMY_LOGS = [
    {"user_id": 1, "news_id": 1,  "action": "click"},
    {"user_id": 1, "news_id": 3,  "action": "click"},
    {"user_id": 1, "news_id": 5,  "action": "view"},
    {"user_id": 1, "news_id": 11, "action": "click"},
    {"user_id": 1, "news_id": 14, "action": "click"},
    {"user_id": 2, "news_id": 2,  "action": "click"},
    {"user_id": 2, "news_id": 6,  "action": "click"},
    {"user_id": 2, "news_id": 9,  "action": "view"},
    # user_id=3 로그 없음 → 첫 접속 유저
]


# ─────────────────────────────────────────
# TODO [1] 사용자 관심사 기반 로직
# users 테이블에서 관심 카테고리 조회
# ─────────────────────────────────────────

def get_user_interest(user_id: int) -> str | None:
    """
    user_id 로 유저의 기본 관심 카테고리를 반환합니다.

    [DB 연동 시 교체]
    return db.query(User).filter(User.id == user_id).first().interest

    Args:
        user_id: 조회할 유저의 ID

    Returns:
        관심 카테고리 문자열 (예: "business") 또는 None (유저 없을 시)
    """
    for user in DUMMY_USERS:
        if user["id"] == user_id:
            return user["interest"]
    return None


# ─────────────────────────────────────────
# TODO [2] 뉴스 필터링
# news 테이블에서 관심 카테고리 뉴스 추출 + 최신순 정렬
# ─────────────────────────────────────────

def filter_news_by_category(category: str) -> list:
    """
    특정 카테고리의 뉴스를 최신순으로 정렬하여 반환합니다.

    [DB 연동 시 교체]
    return db.query(News)\
             .filter(News.category == category)\
             .order_by(News.created_at.desc())\
             .all()

    Args:
        category: 필터링할 카테고리 (예: "business")

    Returns:
        최신순으로 정렬된 뉴스 리스트
    """
    filtered = [n for n in DUMMY_NEWS if n["category"] == category]
    return sorted(filtered, key=lambda x: x["created_at"], reverse=True)


# ─────────────────────────────────────────
# TODO [3] 점수 기반 추천
# user_logs 참조, 클릭 수 많은 카테고리 가중치 적용
# ─────────────────────────────────────────

def get_category_scores(user_id: int) -> dict:
    """
    유저의 행동 로그를 기반으로 카테고리별 점수를 계산합니다.
    click: +2점 / view: +1점

    [DB 연동 시 교체]
    logs = db.query(UserLog).filter(UserLog.user_id == user_id).all()

    Args:
        user_id: 점수를 계산할 유저의 ID

    Returns:
        카테고리별 점수 딕셔너리 (예: {"business": 5, "health": 4})
        로그가 없으면 빈 딕셔너리 반환
    """
    scores = {}

    user_logs = [log for log in DUMMY_LOGS if log["user_id"] == user_id]

    for log in user_logs:
        news = next((n for n in DUMMY_NEWS if n["id"] == log["news_id"]), None)
        if not news:
            continue

        category = news["category"]
        point = 2 if log["action"] == "click" else 1
        scores[category] = scores.get(category, 0) + point

    return scores


# ─────────────────────────────────────────
# TODO [4] 추천 반환
# 상위 5개 뉴스 추출 + recommend.py 함수 구현
# ─────────────────────────────────────────

def get_recommendations(user_id: int, limit: int = 5) -> list:
    """
    유저에게 뉴스를 추천하는 메인 함수입니다.
    백엔드 main.py 의 GET /recommend/{user_id} 엔드포인트에서 호출됩니다.

    [추천 로직]
    - 첫 접속 (로그 없음): 전체 뉴스에서 랜덤으로 limit 개 추천
    - 재방문 (로그 있음): 카테고리 점수 높은 순으로 최신 뉴스 추천

    Args:
        user_id: 추천을 요청한 유저의 ID
        limit: 반환할 뉴스 개수 (기본값 5)

    Returns:
        추천 뉴스 리스트 (각 항목은 title, category, created_at 포함)
    """
    scores = get_category_scores(user_id)

    # 첫 접속 → 랜덤 추천
    if not scores:
        return random.sample(DUMMY_NEWS, min(limit, len(DUMMY_NEWS)))

    # 점수 높은 순으로 카테고리 정렬
    ranked_categories = sorted(scores, key=scores.get, reverse=True)

    result = []
    seen_ids = set()

    # 점수 높은 카테고리부터 뉴스 채우기
    for category in ranked_categories:
        if len(result) >= limit:
            break
        news_list = filter_news_by_category(category)
        for news in news_list:
            if len(result) >= limit:
                break
            if news["id"] not in seen_ids:
                result.append(news)
                seen_ids.add(news["id"])

    return result

print("완료")
