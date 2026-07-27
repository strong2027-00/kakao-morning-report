# 매일 아침 카카오톡 자산·뉴스 브리핑

매일 아침 7시(한국시간)에 자동으로 카카오톡 "나에게 보내기"로
- 보유자산 변화
- 관심종목(JEPQ, TSLA, AAPL, GOOGL, NVDA) 시세와 애널리스트 컨센서스
- 크립토 뉴스 / 트럼프 소식 / 주요 증시 이벤트

를 보내주는 시스템이에요. 서버나 본인 컴퓨터를 켜둘 필요 없이,
GitHub Actions(무료)가 대신 매일 실행해줘요.

---

## 준비물

- GitHub 계정 (무료)
- 카카오 계정
- 파이썬이 설치된 본인 컴퓨터 (최초 설정 1회만 필요)

---

## 1단계. 카카오 앱 만들기

1. https://developers.kakao.com 접속 → 로그인
2. [내 애플리케이션] → [애플리케이션 추가하기]
3. 앱 이름은 자유롭게 (예: "아침브리핑")
4. 생성된 앱 클릭 → 좌측 [앱 설정 > 앱 키] 에서 **REST API 키** 복사해두기
5. 좌측 [앱 설정 > 카카오 로그인] → **활성화 설정 ON**
6. [카카오 로그인 > Redirect URI] → `https://example.com/oauth` 등록
   (실제로 열리는 사이트가 아니어도 괜찮아요, 형식상 등록하는 값)
7. [카카오 로그인 > 동의항목] → **"카카오톡 메시지 전송"(talk_message)** 을
   찾아서 **필수 동의**로 설정

---

## 2단계. 최초 1회, 내 컴퓨터에서 토큰 발급받기

터미널(명령 프롬프트)에서:

```bash
pip install requests
python get_kakao_token.py
```

안내에 따라 REST API 키를 입력하고, 뜨는 주소를 브라우저에서 열어서
로그인 → 동의하면 `https://example.com/oauth?code=...` 형태로 리다이렉트돼요.
(페이지는 안 열려도 괜찮아요, **주소창의 URL만** 복사하면 돼요)

그 URL을 스크립트에 붙여넣으면 최종적으로 이런 값이 출력돼요:

```
KAKAO_REST_API_KEY = (본인 키)
KAKAO_REFRESH_TOKEN = (발급된 토큰)
```

이 두 값을 잘 복사해두세요. **이 스크립트는 이제 다시 실행할 필요 없어요.**

---

## 3단계. GitHub 저장소 만들기

1. GitHub에서 새 저장소 생성 (Public도 괜찮아요 — 보유자산 내용은
   저장소가 아니라 GitHub Secrets에만 저장되니까요. 다만 더 안심되면
   Private로 만들어도 좋아요)
2. 이 폴더(`kakao-morning-report`)의 파일들을 저장소에 업로드
   - `config.py`는 업로드하지 마세요 (`.gitignore`에 이미 등록되어 있어요)
     — 대신 4단계에서 Secrets로 등록해요.

---

## 4단계. GitHub Secrets 등록

저장소 → **Settings → Secrets and variables → Actions → New repository secret**
에서 아래 5개를 하나씩 등록하세요:

| Secret 이름 | 값 |
|---|---|
| `KAKAO_REST_API_KEY` | 1단계에서 복사한 REST API 키 |
| `KAKAO_REFRESH_TOKEN` | 2단계에서 발급받은 refresh_token |
| `HOLDINGS_JSON` | `{"BTC-USD": 0.368, "MSTR": 96, "SPCX": 24, "SPAX": 112}` |
| `WATCHLIST_JSON` | `["JEPQ", "TSLA", "AAPL", "GOOGL", "NVDA"]` |

`HOLDINGS_JSON`/`WATCHLIST_JSON`은 본인 실제 수량으로 자유롡게 수정해서 등록하세요.
이 값들은 Secrets에만 저장되고 저장소 코드에는 절대 남지 않아요.

---

## 5단계. 실행 확인

- 저장소의 **Actions** 탭 → `Morning KakaoTalk Report` 워크플로 선택
- **Run workflow** 버튼으로 수동 실행 → 카카오톡이 오는지 확인
- 문제없으면 이후로는 매일 아침 7시(KST)에 자동으로 실행돼요

---

## 동작 원리 요약

- **시세**: 야후 파이낸스(yfinance) — 무료, API 키 불필요
- **크립토 뉴스**: CoinDesk 공식 RSS
- **트럼프/증시 뉴스**: 구글 뉴스 검색 RSS (키워드 기반, 한국어)
- **X(트위터)**: 2023년 이후 무료 API/RSS가 막혀서 직접 수집하지 않아요.
  대신 트럼프 관련 X 발언은 언론이 기사화되면 구글 뉴스에 자연히 잡혀요.
- **전일 대비 자산 변화 / 카카오 refresh_token**: GitHub Actions 캐시에
  저장해서 다음 날 실행 때 이어서 사용해요. 별도 서버나 DB가 필요 없어요.

## 참고

- "애널리스트 컨센서스"는 야후 파이낸스에 집계된 증권사 의견을 그대로
  가져온 것으로, 매수/매도를 지시하는 조언이 아니에요. 참고 지표로만 봐주세요.
- 카카오 access_token은 6시간, refresh_token은 최대 60일까지 유효해요.
  이 시스템은 매일 자동으로 refresh_token을 갱신하기 때문에 별도 관리가
  필요 없지만, **60일 넘게 워크플로가 한 번도 실행되지 않으면** 토큰이
  만료돼서 2단계를 다시 해야 할 수 있어요 (매일 실행되니 걱정 없어요).
