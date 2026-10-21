# Streamlit MyProject

첨부된 `app.py`의 주석 요구사항을 기준으로 구성한 Streamlit + SQLite 로그인 웹앱입니다.

## 주요 기능

- SQLite DB: `myproject.db`
- 사용자 테이블: `user_table`
- 사용자 등록 / 로그인 / 로그아웃
- `st.session_state` 기반 로그인 세션 관리
- 로그인 전/후 서로 다른 랜딩 페이지
- Streamlit 기본 햄버거/사이드바를 활용한 접이식 왼쪽 메뉴
- 비밀번호 PBKDF2-SHA256 해시 저장
- 기존 app.py의 동영상, name/age/address/phone 입력 및 DB 조회 흐름 유지
- 기존 개인정보 입력은 SQLite `profile_table`에 저장
- Tailwind CSS + Alpine.js를 Streamlit HTML 컴포넌트 영역에 적용
- 기존 `data.csv`는 참고용으로 포함
- **설문 참여** 메뉴: AI의 교육적 효과 인식 설문(10문항, 5점 척도) 응시 및 결과 시각화

## 디렉토리 구조

```text
streamlit_myproject/
├─ app.py            # Streamlit 실행 파일 / 화면 / 세션 / 메뉴
├─ db.py             # SQLite 연결, 테이블 생성, 인증 및 CRUD (survey_table 포함)
├─ survey.py         # 설문 참여 메뉴: 설문응시 / 설문결과 시각화 탭
├─ mycom.sql         # user_table, survey_table 생성 SQL
├─ myproject.db      # SQLite DB (초기 실행 또는 init 스크립트로 생성)
├─ data.csv          # 기존 CSV 데이터(참고용)
├─ requirements.txt  # Python 패키지 목록
├─ README.md         # 실행법 및 구조 설명
└─ .gitignore        # 캐시/로컬 환경 제외
```

## 실행 방법

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

macOS / Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

브라우저에서 보통 `http://localhost:8501`이 열립니다.

## DB 스키마

### user_table

- `id_num`: INTEGER PRIMARY KEY AUTOINCREMENT
- `userid`: TEXT UNIQUE
- `username`: TEXT
- `password`: TEXT (PBKDF2 해시)
- `email`: TEXT UNIQUE
- `created_at`: TEXT

### profile_table

기존 app.py의 `name`, `age`, `address`, `phone` 데이터를 사용자별로 저장하기 위해 추가했습니다.

- `id_num`: INTEGER PRIMARY KEY AUTOINCREMENT
- `user_id_num`: user_table FK
- `name`
- `age`
- `address`
- `phone`
- `created_at`

### survey_table

`mycom.sql`의 스키마를 그대로 사용하며, 앱 실행 시 없으면 자동 생성됩니다.

- `id_num`: INTEGER PRIMARY KEY AUTOINCREMENT
- `user_id`: TEXT (로그인 아이디 `userid`)
- `q1` ~ `q10`: INTEGER (1=전혀 아니다, 2=아니다, 3=보통이다, 4=그렇다, 5=매우 그렇다)
- `created_at`: TEXT (응답 제출 시점의 현재 날짜·시간, `YYYY-MM-DD HH:MM:SS`)

사용자당 1건의 응답을 유지하며, 다시 제출하면 기존 응답과 `created_at`이 갱신됩니다.

## 설문 참여 메뉴

로그인 후 왼쪽 메뉴의 **설문 참여**를 선택하면 두 개의 탭이 표시됩니다.

1. **설문응시**: AI의 교육적 효과에 대한 인식 10문항(이해도 향상, 학습 효율성, 개별화 학습, 피드백, 학습 동기, 창의성, 비판적 사고, 진로 역량, 교육 필요성, 전반적 효과)에 5점 척도로 응답
2. **설문결과 시각화**
   - 요약 지표: 응답자 수, 전체 평균, 긍정 응답률(4·5점), Cronbach's α
   - 문항별 평균 막대그래프(중간값 3점 기준선)
   - 문항별 응답 분포 100% 누적 막대그래프
   - 문항별 기술통계표(N, 평균, 표준편차, 중앙값, 최빈값, 점수별 빈도·비율, 긍정률)
   - 문항 상세 보기(선택 문항의 응답 분포 및 내 응답)
   - 응답 일자별 참여 추이, 원자료·통계표 CSV 다운로드

## 참고

Streamlit은 React 기반 앱이므로 Tailwind/Alpine.js를 메인 DOM 전체에 직접 적용하는 방식보다 `components.html()` 내부에 격리된 UI island로 적용하는 편이 안정적입니다. 실제 페이지 레이아웃과 사이드바는 Streamlit 컴포넌트 + CSS로 구성했습니다.
