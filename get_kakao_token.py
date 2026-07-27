# -*- coding: utf-8 -*-
"""
카카오 access_token / refresh_token을 최초 1회 발급받기 위한 도우미 스크립트.

** 이 스크립트는 딱 한 번, 본인 컴퓨터에서 직접 실행하세요. **
발급받은 refresh_token은 GitHub Secrets(KAKAO_REFRESH_TOKEN)에 등록하고,
이 스크립트는 그 이후로는 다시 실행할 필요 없어요.

사전 준비 (Kakao Developers, developers.kakao.com):
1. 내 애플리케이션 > 애플리케이션 추가
2. [앱 설정 > 카카오 로그인] 활성화
3. [카카오 로그인 > Redirect URI] 에 아래 값을 등록:
     https://example.com/oauth
   (실제로 이 주소가 열릴 필요는 없어요. 그냥 형식상 등록하는 값이에요)
4. [카카오 로그인 > 동의항목] 에서
   "카카오톡 메시지 전송" (talk_message) 을 '필수 동의'로 설정
5. [앱 설정 > 앱 키] 에서 REST API 키를 복사
"""

import urllib.parse
import requests

REST_API_KEY = input("REST API 키를 입력하세요: ").strip()
REDIRECT_URI = "https://example.com/oauth"

auth_url = (
    "https://kauth.kakao.com/oauth/authorize?"
    + urllib.parse.urlencode(
        {
            "client_id": REST_API_KEY,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "scope": "talk_message",
        }
    )
)

print("\n1) 아래 주소를 브라우저(카카오 로그인된 상태)에서 열어주세요:\n")
print(auth_url)
print(
    "\n2) 로그인/동의 후 리다이렉트되는 주소창의 URL 전체를 복사해서 아래에 붙여넣으세요."
    "\n   (예: https://example.com/oauth?code=AbCdEfG...)\n"
)

redirected_url = input("리다이렉트된 URL 전체를 붙여넣으세요: ").strip()
parsed = urllib.parse.urlparse(redirected_url)
code = urllib.parse.parse_qs(parsed.query).get("code", [None])[0]

if not code:
    raise SystemExit("code 파라미터를 찾지 못했어요. URL을 다시 확인해주세요.")

resp = requests.post(
    "https://kauth.kakao.com/oauth/token",
    data={
        "grant_type": "authorization_code",
        "client_id": REST_API_KEY,
        "redirect_uri": REDIRECT_URI,
        "code": code,
    },
    timeout=10,
)
resp.raise_for_status()
tokens = resp.json()

print("\n토큰 발급 완료! 아래 두 값을 GitHub Secrets에 등록하세요:\n")
print(f"KAKAO_REST_API_KEY = {REST_API_KEY}")
print(f"KAKAO_REFRESH_TOKEN = {tokens['refresh_token']}")
print(
    "\n(access_token은 6시간짜리라 따로 저장할 필요 없어요."
    " 매 실행마다 refresh_token으로 새로 발급받아요.)"
)
