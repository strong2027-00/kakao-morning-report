# -*- coding: utf-8 -*-
"""
뉴스 수집 모듈.

- 크립토 뉴스: CoinDesk 공식 RSS
- 트럼프 소식 / 주요 이벤트: 구글 뉴스 검색 RSS (한국어)

두 방식 모두 API 키가 필요 없어요.
"""

import urllib.parse
import feedparser
import yfinance as yf

# 종목별 뉴스가 부족할 때 구글 뉴스 검색으로 대체하기 위한 검색어 매핑
TICKER_SEARCH_NAMES = {
    "BTC-USD": "비트코인",
    "MSTR": "MicroStrategy Strategy Inc",
    "SPCX": "SpaceX 스페이스X",
    "SPAX": "SpaceX 레버리지 ETF",
    "JEPQ": "JEPQ ETF",
    "TSLA": "테슬라 Tesla",
    "AAPL": "애플 Apple",
    "GOOGL": "구글 Google Alphabet",
    "NVDA": "엔비디아 Nvidia",
}


def _parse_feed(url, limit):
    """RSS/Atom 피드 URL을 받아 (제목, 링크) 리스트로 반환"""
    try:
        feed = feedparser.parse(url)
    except Exception as e:
        return [(f"[뉴스를 불러오지 못했어요: {e}]", "")]

    items = []
    for entry in feed.entries[:limit]:
        title = entry.get("title", "제목 없음").strip()
        link = entry.get("link", "")
        items.append((title, link))
    if not items:
        items = [("[해당 주제의 새 기사를 찾지 못했어요]", "")]
    return items


def fetch_crypto_news(rss_url, limit=3):
    """CoinDesk 등 크립토 전문 매체 RSS에서 최신 헤드라인 가져오기"""
    return _parse_feed(rss_url, limit)


def fetch_google_news(query, limit=3, lang="ko", country="KR"):
    """구글 뉴스 검색 RSS에서 키워드 기반 헤드라인 가져오기"""
    encoded_query = urllib.parse.quote(query)
    url = (
        f"https://news.google.com/rss/search?q={encoded_query}"
        f"&hl={lang}&gl={country}&ceid={country}:{lang}"
    )
    return _parse_feed(url, limit)


def fetch_ticker_news_via_yfinance(ticker, limit):
    """야후 파이낸스가 제공하는 종목별 뉴스(무료, 키 불필요).
    일부 티커(특히 SPAX 같은 소형 레버리지 ETF)는 결과가 거의 없을 수 있어요."""
    try:
        items = yf.Ticker(ticker).news or []
    except Exception:
        return []

    results = []
    for item in items[:limit]:
        # yfinance 버전에 따라 필드 위치가 다를 수 있어 두 형태 모두 처리
        content = item.get("content", item)
        title = content.get("title") or item.get("title")
        link = (
            (content.get("clickThroughUrl") or {}).get("url")
            or (content.get("canonicalUrl") or {}).get("url")
            or item.get("link")
            or ""
        )
        if title:
            results.append((title.strip(), link))
    return results


def fetch_ticker_news(ticker, limit=2):
    """종목별 뉴스. 야후 파이낸스에서 먼저 찾아보고, 부족하면 구글 뉴스
    검색으로 채움."""
    results = fetch_ticker_news_via_yfinance(ticker, limit)
    if len(results) >= limit:
        return results[:limit]

    query = TICKER_SEARCH_NAMES.get(ticker, ticker)
    fallback = fetch_google_news(query, limit - len(results))
    return results + fallback


def fetch_all_ticker_news(tickers, limit=2):
    """여러 티커의 종목별 뉴스를 { 티커: [(제목, 링크), ...] } 형태로 반환"""
    return {ticker: fetch_ticker_news(ticker, limit) for ticker in tickers}


def fetch_all_news(config):
    """config.py의 설정을 바탕으로 모든 뉴스 주제를 수집해서
    { 주제명: [(제목, 링크), ...] } 형태의 딕셔너리로 반환"""
    result = {}

    result["크립토 뉴스"] = fetch_crypto_news(
        config.CRYPTO_RSS_URL, config.NEWS_ITEMS_PER_TOPIC
    )

    for topic_name, query in config.NEWS_SEARCH_TOPICS.items():
        result[topic_name] = fetch_google_news(
            query, config.NEWS_ITEMS_PER_TOPIC
        )

    return result
