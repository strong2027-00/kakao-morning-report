# -*- coding: utf-8 -*-
"""
매일 아침 카카오톡으로 보낼 리포트를 만들고 전송하는 메인 스크립트.

실행 흐름:
1. GitHub Secrets(HOLDINGS_JSON/WATCHLIST_JSON, 없으면 config.py)에서 설정 로드
2. yfinance로 시세 조회
3. 캐시에 저장된 state.json과 비교해서 포트폴리오 변화 계산
4. CoinDesk RSS / 구글 뉴스 RSS로 뉴스 헤드라인 수집
5. 위 내용을 한국어 메시지로 조합
6. 캐시된 refresh_token(없으면 Secrets 초기값)으로 access_token 갱신 후 "나에게 보내기" 전송
7. 오늘의 포트폴리오 총액과 새 refresh_token을 로컬 파일에 저장
   (GitHub Actions 워크플로가 이 파일들을 캐시에 저장해서 다음 실행에 넘겨줌)
"""

import json
import os
from datetime import datetime

import config
import market_data
import news_feed
import kakao_client

STATE_FILE = "state.json"
REFRESH_TOKEN_FILE = "kakao_refresh_token.txt"


def load_previous_state():
    if not os.path.exists(STATE_FILE):
        return None
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(portfolio_value_usd):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                "portfolio_value_usd": portfolio_value_usd,
                "saved_at": datetime.utcnow().isoformat(),
            },
            f,
            ensure_ascii=False,
            indent=2,
        )


def format_money_krw(usd_amount):
    krw = usd_amount * config.KRW_PER_USD
    if abs(krw) >= 1_0000_0000:
        return f"{krw / 1_0000_0000:.2f}억원"
    return f"{krw / 10000:,.0f}만원"


def build_portfolio_section(holdings, quotes, prev_state):
    total_usd = market_data.get_portfolio_value_usd(holdings, quotes)
    lines = ["[자산 현황]"]
    lines.append(f"총 평가금액: {format_money_krw(total_usd)}")

    if prev_state and prev_state.get("portfolio_value_usd"):
        prev_usd = prev_state["portfolio_value_usd"]
        diff_usd = total_usd - prev_usd
        diff_pct = (diff_usd / prev_usd * 100) if prev_usd else 0
        arrow = "▲" if diff_usd >= 0 else "▼"
        lines.append(f"전일 대비: {arrow} {format_money_krw(abs(diff_usd))} ({diff_pct:+.2f}%)")
    else:
        lines.append("전일 대비: (첫 실행이라 비교 데이터 없음)")

    for ticker in holdings:
        q = quotes.get(ticker)
        if q:
            lines.append(
                f"  · {ticker}: {q['price']:,.2f} ({q['change_pct']:+.2f}%) "
                f"— {q['relative_position_phrase']}"
            )
        else:
            lines.append(f"  · {ticker}: 시세 조회 실패")

    return "\n".join(lines), total_usd


def build_watchlist_section(watchlist, quotes):
    lines = ["[관심 종목 시세 · 애널리스트 컨센서스]"]
    for ticker in watchlist:
        q = quotes.get(ticker)
        if not q:
            lines.append(f"  · {ticker}: 시세 조회 실패")
            continue
        ma_note = ""
        if q["ma50"] and q["price"]:
            vs_ma50 = (q["price"] - q["ma50"]) / q["ma50"] * 100
            ma_note = f", 50일선 대비 {vs_ma50:+.1f}%"
        lines.append(
            f"  · {ticker}: ${q['price']:,.2f} ({q['change_pct']:+.2f}%{ma_note}) "
            f"- 컨센서스: {q['recommendation']} / {q['relative_position_phrase']}"
        )
    lines.append("(컨센서스는 야후 파이낸스 집계 애널리스트 의견이며 투자 조언이 아니에요)")
    return "\n".join(lines)


def build_news_section(news_by_topic):
    lines = []
    for topic, items in news_by_topic.items():
        lines.append(f"[{topic}]")
        for title, _link in items:
            lines.append(f"  · {title}")
    return "\n".join(lines)


def build_perspective_note(quotes, holdings):
    """단순 사실 기반 관전 포인트 (투자 조언이 아닌 참고용 관찰)"""
    btc = quotes.get("BTC-USD")
    if not btc:
        return ""
    lines = ["[BTC 추가매수 관련 참고 지표]"]
    lines.append(f"  · 현재가: ${btc['price']:,.0f} ({btc['change_pct']:+.2f}%)")
    lines.append(f"  · 상대적 위치: {btc['relative_position_phrase']}")
    if btc.get("ma200"):
        vs_ma200 = (btc["price"] - btc["ma200"]) / btc["ma200"] * 100
        lines.append(f"  · 200일 이동평균 대비: {vs_ma200:+.1f}%")
    if btc.get("high_52w"):
        vs_high = (btc["price"] - btc["high_52w"]) / btc["high_52w"] * 100
        lines.append(f"  · 52주 최고가 대비: {vs_high:+.1f}%")
    lines.append("(참고용 지표일 뿐, 매수/매도 판단은 본인이 직접 하는 것을 추천해요)")
    return "\n".join(lines)


def build_ticker_news_section(ticker_news_by_ticker):
    lines = ["[보유·관심 종목별 뉴스]"]
    for ticker, items in ticker_news_by_ticker.items():
        lines.append(f"  {ticker}")
        for title, _link in items:
            lines.append(f"    · {title}")
    return "\n".join(lines)


def build_message(holdings, watchlist, quotes, news_by_topic, ticker_news_by_ticker, prev_state):
    today = datetime.now().strftime("%Y-%m-%d")
    header = f"🌅 {today} 아침 브리핑"

    portfolio_section, total_usd = build_portfolio_section(holdings, quotes, prev_state)
    watchlist_section = build_watchlist_section(watchlist, quotes)
    ticker_news_section = build_ticker_news_section(ticker_news_by_ticker)
    news_section = build_news_section(news_by_topic)
    perspective_section = build_perspective_note(quotes, holdings)

    full_message = "\n\n".join(
        [
            header,
            portfolio_section,
            perspective_section,
            watchlist_section,
            ticker_news_section,
            news_section,
        ]
    )
    return full_message, total_usd


def load_holdings_and_watchlist():
    """HOLDINGS_JSON / WATCHLIST_JSON 환경변수(GitHub Secrets)가 있으면 그걸 쓰고,
    없으면 로컬 테스트용으로 config.py의 값을 사용. 이렇게 하면 보유자산 내용이
    git 저장소에는 전혀 남지 않아요 (저장소를 굳이 비공개로 안 해도 됨)."""
    holdings_json = os.environ.get("HOLDINGS_JSON")
    watchlist_json = os.environ.get("WATCHLIST_JSON")

    holdings = json.loads(holdings_json) if holdings_json else config.HOLDINGS
    watchlist = json.loads(watchlist_json) if watchlist_json else config.WATCHLIST
    return holdings, watchlist


def load_refresh_token():
    """캐시된 refresh_token 파일(직전 실행이 남긴 것)이 있으면 우선 사용하고,
    없으면(최초 실행) Secrets에 등록해둔 초기값을 사용"""
    if os.path.exists(REFRESH_TOKEN_FILE):
        with open(REFRESH_TOKEN_FILE, "r", encoding="utf-8") as f:
            token = f.read().strip()
            if token:
                return token
    return os.environ["KAKAO_REFRESH_TOKEN"]


def main():
    rest_api_key = os.environ["KAKAO_REST_API_KEY"]
    refresh_token = load_refresh_token()
    holdings, watchlist = load_holdings_and_watchlist()

    # 1. 카카오 토큰 갱신
    tokens = kakao_client.refresh_access_token(rest_api_key, refresh_token)
    access_token = tokens["access_token"]
    new_refresh_token = tokens["refresh_token"]

    # 2. 시세 조회
    all_tickers = list(holdings.keys()) + watchlist
    quotes = market_data.get_multiple_quotes(all_tickers)

    # 3. 이전 상태 로드
    prev_state = load_previous_state()

    # 4. 뉴스 수집 (일반 주제 + 보유/관심 종목별)
    news_by_topic = news_feed.fetch_all_news(config)
    ticker_news_by_ticker = news_feed.fetch_all_ticker_news(
        all_tickers, getattr(config, "NEWS_ITEMS_PER_TICKER", 2)
    )

    # 5. 메시지 조합
    message, total_usd = build_message(
        holdings, watchlist, quotes, news_by_topic, ticker_news_by_ticker, prev_state
    )

    print("---- 전송할 메시지 ----")
    print(message)
    print("-----------------------")

    # 6. 카카오톡 전송
    results = kakao_client.send_memo(access_token, message)
    for status, body in results:
        print(f"카카오 전송 결과: {status} / {body}")

    # 7. 상태 저장 (다음 실행에서 전일 대비 계산용, GitHub Actions 캐시로 보존됨)
    save_state(total_usd)

    # 8. 갱신된 refresh_token도 캐시 파일에 남김 (다음 실행이 이 값을 우선 사용)
    with open(REFRESH_TOKEN_FILE, "w", encoding="utf-8") as f:
        f.write(new_refresh_token)


if __name__ == "__main__":
    main()
