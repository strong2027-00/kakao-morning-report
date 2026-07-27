# -*- coding: utf-8 -*-
"""
시세 조회 모듈. yfinance(야후 파이낸스)를 사용해요.

주의: 여기서 만드는 "애널리스트 컨센서스"는 Claude나 이 스크립트의 개인적인
투자 의견이 아니라, 야후 파이낸스에 집계된 증권사 애널리스트들의 평균 의견을
그대로 가져오는 것뿐이에요. 투자 조언이 아니라 참고 정보로만 봐주세요.
"""

import bisect

import yfinance as yf

REC_KEY_KO = {
    "strong_buy": "적극 매수",
    "buy": "매수",
    "hold": "보유",
    "sell": "매도",
    "strong_sell": "적극 매도",
    "none": "의견 없음",
}


def get_relative_position_pct(ticker, period="1y"):
    """최근 1년 종가 분포에서 현재가가 몇 번째 백분위(percentile)에
    있는지 계산. 이건 '싸다/비싸다'를 판단하는 게 아니라 순수하게
    '최근 1년 동안의 가격 분포 중 어디쯔음인지'를 나타내는 통계값이에요."""
    try:
        hist = yf.Ticker(ticker).history(period=period)
        closes = hist["Close"].dropna().tolist()
        if len(closes) < 30:
            return None
        current = closes[-1]
        sorted_vals = sorted(closes)
        idx = bisect.bisect_left(sorted_vals, current)
        percentile = idx / len(sorted_vals) * 100
        return percentile
    except Exception:
        return None


def relative_position_phrase(percentile):
    """백분위 숫자를 사람이 읽기 쉬운 한국어 문구로 변환.
    전부 '지금 위치가 통계적으로 어디인지'만 설명하는 사실 문구이고,
    매수/매도를 지시하는 표현은 쓰지 않아요."""
    if percentile is None:
        return "최근 1년 데이터 부족"
    if percentile >= 90:
        return f"최근 1년 중 최고 수준 구간 (상위 {100 - percentile:.0f}% 이내)"
    if percentile >= 70:
        return f"최근 1년 기준 높은 편 (상위 {100 - percentile:.0f}%대)"
    if percentile >= 30:
        return "최근 1년 기준 중간 구간"
    if percentile >= 10:
        return f"최근 1년 기준 낮은 편 (하위 {percentile:.0f}%대)"
    return f"최근 1년 중 최저 수준 구간 (하위 {percentile:.0f}% 이내)"


def get_quote(ticker):
    """단일 티커의 현재가, 전일 대비 변동률, 이동평균 대비 위치,
    최근 1년 상대적 위치, 애널리스트 컨센서스를 조회해서 dict로 반환.
    실패하면 None."""
    try:
        t = yf.Ticker(ticker)
        info = t.info or {}

        price = info.get("currentPrice") or info.get("regularMarketPrice")
        prev_close = info.get("previousClose")
        if price is None or prev_close is None:
            # 일부 티커(특히 암호화폐)는 fast_info로 재시도
            fi = t.fast_info
            price = price or fi.get("lastPrice")
            prev_close = prev_close or fi.get("previousClose")

        if price is None or prev_close is None:
            return None

        change_pct = (price - prev_close) / prev_close * 100

        ma50 = info.get("fiftyDayAverage")
        ma200 = info.get("twoHundredDayAverage")
        high_52w = info.get("fiftyTwoWeekHigh")

        rec_key = info.get("recommendationKey", "none")
        rec_ko = REC_KEY_KO.get(rec_key, "의견 없음")

        rel_pct = get_relative_position_pct(ticker)
        rel_phrase = relative_position_phrase(rel_pct)

        return {
            "ticker": ticker,
            "price": price,
            "change_pct": change_pct,
            "ma50": ma50,
            "ma200": ma200,
            "high_52w": high_52w,
            "recommendation": rec_ko,
            "relative_position_pct": rel_pct,
            "relative_position_phrase": rel_phrase,
        }
    except Exception:
        return None


def get_multiple_quotes(tickers):
    """여러 티커를 조회해서 { 티커: quote dict } 형태로 반환.
    조회 실패한 티커는 결과에서 제외됨."""
    result = {}
    for ticker in tickers:
        q = get_quote(ticker)
        if q:
            result[ticker] = q
    return result


def get_portfolio_value_usd(holdings, quotes):
    """holdings(티커:수량)와 quotes(티커:quote dict)를 받아
    전체 포트폴리오의 현재 총 평가금액(달러)을 계산"""
    total = 0.0
    for ticker, qty in holdings.items():
        q = quotes.get(ticker)
        if q:
            total += q["price"] * qty
    return total
