# -*- coding: utf-8 -*-
"""
카카오톡 "나에게 보내기" API 클라이언트.

카카오 액세스 토큰은 6시간만 유효해요. 그래서 매번 실행할 때
refresh_token으로 새 access_token을 발급받아 사용해요.
refresh_token 자체도 갱신될 수 있어서, 매번 새 refresh_token을
돌려주고 그걸 GitHub Secrets에 다시 저장해야 해요.
(이 부분은 GitHub Actions 워크플로에서 처리해요)
"""

import requests

TOKEN_URL = "https://kauth.kakao.com/oauth/token"
MEMO_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"

MAX_CHARS_PER_MESSAGE = 180  # 카카오 기본 텍스트 템플릿 안전 마진


def refresh_access_token(rest_api_key, refresh_token):
    """refresh_token으로 새 access_token(및 갱신된 refresh_token)을 발급받음.
    반환: {"access_token": ..., "refresh_token": ...} (refresh_token은
    카카오가 새로 내려주지 않으면 기존 값 그대로 유지)"""
    data = {
        "grant_type": "refresh_token",
        "client_id": rest_api_key,
        "refresh_token": refresh_token,
    }
    resp = requests.post(TOKEN_URL, data=data, timeout=10)
    resp.raise_for_status()
    payload = resp.json()

    new_access_token = payload["access_token"]
    # 카카오는 refresh_token이 만료 임박했을 때만 새 값을 내려줌
    new_refresh_token = payload.get("refresh_token", refresh_token)

    return {"access_token": new_access_token, "refresh_token": new_refresh_token}


def _split_message(text, max_len=MAX_CHARS_PER_MESSAGE):
    """긴 메시지를 줄바꿈 기준으로 max_len 이하 조각들로 나눔"""
    chunks = []
    current = ""
    for line in text.split("\n"):
        candidate = (current + "\n" + line) if current else line
        if len(candidate) > max_len:
            if current:
                chunks.append(current)
            current = line
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def send_memo(access_token, text):
    """카카오톡 나에게 보내기. 길면 여러 통으로 나눠서 순서대로 전송."""
    headers = {"Authorization": f"Bearer {access_token}"}
    chunks = _split_message(text)

    results = []
    for chunk in chunks:
        template_object = {
            "object_type": "text",
            "text": chunk,
            "link": {"web_url": "https://www.kakaocorp.com"},
        }
        resp = requests.post(
            MEMO_URL,
            headers=headers,
            data={"template_object": _to_json(template_object)},
            timeout=10,
        )
        results.append((resp.status_code, resp.text))
    return results


def _to_json(obj):
    import json

    return json.dumps(obj, ensure_ascii=False)
