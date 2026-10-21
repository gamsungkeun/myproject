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

## 디렉토리 구조

```text
streamlit_myproject/
├─ app.py            # Streamlit 실행 파일 / 화면 / 세션 / 메뉴
├─ db.py             # SQLite 연결, 테이블 생성, 인증 및 CRUD
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

## 참고

Streamlit은 React 기반 앱이므로 Tailwind/Alpine.js를 메인 DOM 전체에 직접 적용하는 방식보다 `components.html()` 내부에 격리된 UI island로 적용하는 편이 안정적입니다. 실제 페이지 레이아웃과 사이드바는 Streamlit 컴포넌트 + CSS로 구성했습니다.
