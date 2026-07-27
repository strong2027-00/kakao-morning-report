# -*- coding: utf-8 -*-
"""
사용자 설정 파일 템플릿입니다.

사용법:
1) 이 파일을 복사해서 'config.py' 라는 이름으로 저장하세요.
   (config.py는 .gitignore에 등록되어 있어서 절대 GitHub에 올라가지 않아요)
2) 아래 값들을 본인 상황에 맞게 수정하세요.
"""

# 보유 중인 자산 (티커: 수량)
# BTC는 야후 파이낸스 표기법으로 "BTC-USD" 를 사용해요.
HOLDINGS = {
    "BTC-USD": 0.368,
    "MSTR": 96,
    "SPCX": 24,
    "SPAX": 112,
}

# 매일 시세/의견을 확인하고 싶은 관심 종목
WATCHLIST = ["JEPQ", "TSLA", "AAPL", "GOOGL", "NVDA"]

# 환율 (원/달러). 필요하면 나중에 실시간 환율 API로 바꿔도 돼요.
KRW_PER_USD = 1460

# ---- 뉴스 소스 설정 ----
# X(트위터)는 무료로 안정적인 자동 수집 API/RSS가 없어서(2023년 이후 대부분 유료화),
# 대신 공식 RSS와 구글 뉴스 검색 RSS를 사용해요. 트럼프의 X 발언 등도
# 언론이 기사화하면 구글 뉴스 검색에 자연히 포함돼요.

# 크립토 전문 매체의 공식 RSS (전 세계 크립토 업계 표준 소스)
CRYPTO_RSS_URL = "https://www.coindesk.com/arc/outboundfeeds/rss/"

# 구글 뉴스 검색 RSS로 가져올 주제들 (한국어 기사 기준)
NEWS_SEARCH_TOPICS = {
    "트럼프 소식": "트럼프",
    "주요 증시 이벤트": "증시 OR 연준 OR 금리",
}

# 각 주제/소스당 가져올 헤드라인 개수
NEWS_ITEMS_PER_TOPIC = 3

# 보유·관심 종목 하나당 가져올 뉴스 개수
NEWS_ITEMS_PER_TICKER = 2
