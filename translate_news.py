# -*- coding: utf-8 -*-
"""
영어로 된 뉴스 제목을 한국어로 번역하는 모듈.

deep-translator 라이브러리(무료, API 키 불필요)를 사용해요.
번역이 실패하면 조용히 원문을 그대로 반환해서, 번역 서버 문제로
전체 리포트가 중단되지 않도록 해요.
"""

from deep_translator import GoogleTranslator

_translator = GoogleTranslator(source="auto", target="ko")


def looks_english(text):
    """제목이 영어(비한국어)인지 대략적으로 판단.
    한글이 하나도 없고 알파벳이 있으면 영어로 간주해요."""
    has_hangul = any("\uac00" <= ch <= "\ud7a3" for ch in text)
    has_alpha = any(ch.isalpha() for ch in text)
    return has_alpha and not has_hangul


def translate_to_korean(text):
    """영어로 보이는 텍스트만 한국어로 번역. 이미 한국어면 그대로 반환.
    번역 API 호출이 실패해도 예외를 던지지 않고 원문을 반환해요."""
    if not text or not looks_english(text):
        return text
    try:
        return _translator.translate(text)
    except Exception:
        return text


def translate_items(items):
    """[(제목, 링크), ...] 리스트를 받아 제목만 번역해서 반환"""
    return [(translate_to_korean(title), link) for title, link in items]
