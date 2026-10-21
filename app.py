from __future__ import annotations

import html
import re

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from db import add_profile, authenticate_user, create_user, get_profiles, init_db
from survey import render_survey_page

st.set_page_config(
    page_title="MyProject",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed",
)

init_db()

# -----------------------------
# Session state
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "로그인"

# -----------------------------
# Modern UI CSS
# Streamlit's native sidebar provides the hamburger open/close behavior.
# -----------------------------
st.markdown(
    """
    <style>
      .stApp {background: linear-gradient(135deg, #f8fafc 0%, #eef2ff 50%, #f8fafc 100%);}
      .block-container {max-width: 1180px; padding-top: 2.2rem; padding-bottom: 4rem;}
      [data-testid="stSidebar"] {border-right: 1px solid rgba(148,163,184,.25);}
      [data-testid="stSidebar"] > div:first-child {background: rgba(255,255,255,.96);}
      .hero-card {
        padding: 2.2rem; border-radius: 24px; background: rgba(255,255,255,.82);
        border: 1px solid rgba(148,163,184,.20); box-shadow: 0 20px 45px rgba(15,23,42,.08);
        backdrop-filter: blur(14px); margin-bottom: 1.3rem;
      }
      .eyebrow {font-size:.82rem; font-weight:800; letter-spacing:.12em; color:#4f46e5; text-transform:uppercase;}
      .hero-title {font-size:clamp(2rem,4vw,3.5rem); line-height:1.05; font-weight:900; color:#0f172a; margin:.55rem 0 .8rem;}
      .hero-desc {font-size:1.05rem; color:#475569; max-width:760px;}
      .metric-card {padding:1.25rem; border-radius:18px; background:white; border:1px solid #e2e8f0;}
      div[data-testid="stForm"] {background:white; border:1px solid #e2e8f0; border-radius:20px; padding:1.2rem; box-shadow:0 12px 30px rgba(15,23,42,.05);}
      div[data-testid="stExpander"] {background:rgba(255,255,255,.88); border-radius:16px; overflow:hidden;}
      .stButton > button, .stFormSubmitButton > button {border-radius:12px; font-weight:700; min-height:42px;}
      .footer {text-align:center; color:#94a3b8; font-size:.86rem; margin-top:3rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


def render_tailwind_alpine_banner(title: str, subtitle: str) -> None:
    """Render a small Tailwind + Alpine.js island inside Streamlit."""
    safe_title = html.escape(title)
    safe_subtitle = html.escape(subtitle)
    components.html(
        f"""
        <script src="https://cdn.tailwindcss.com"></script>
        <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
        <div x-data="{{ open: true }}" class="font-sans">
          <div class="flex items-center justify-between rounded-2xl border border-indigo-100 bg-white/90 px-5 py-4 shadow-sm">
            <div>
              <div class="text-xs font-extrabold uppercase tracking-[.18em] text-indigo-600">Streamlit · SQLite</div>
              <div class="mt-1 text-lg font-extrabold text-slate-900">{safe_title}</div>
              <div x-show="open" x-transition class="mt-1 text-sm text-slate-500">{safe_subtitle}</div>
            </div>
            <button @click="open = !open" class="rounded-xl bg-slate-900 px-3 py-2 text-sm font-bold text-white hover:bg-indigo-600">
              <span x-text="open ? '접기' : '펼치기'"></span>
            </button>
          </div>
        </div>
        """,
        height=105,
    )


def logout() -> None:
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.page = "로그인"
    st.rerun()


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("## 🚀 MyProject")
        st.caption("왼쪽 상단의 햄버거 버튼으로 메뉴를 열고 닫을 수 있습니다.")
        st.divider()

        if not st.session_state.logged_in:
            options = ["로그인", "사용자 등록"]
            default_index = options.index(st.session_state.page) if st.session_state.page in options else 0
            st.session_state.page = st.radio("메뉴", options, index=default_index)
        else:
            user = st.session_state.user
            st.success(f"{user['username']}님 로그인 중")
            st.caption(user["email"])
            st.session_state.page = st.radio("메뉴", ["대시보드", "내 정보 입력", "내 DB 조회", "설문 참여"])
            st.divider()
            if st.button("로그아웃", use_container_width=True):
                logout()


render_sidebar()

# -----------------------------
# Logged-out landing pages
# -----------------------------
if not st.session_state.logged_in:
    st.markdown(
        """
        <section class="hero-card">
          <div class="eyebrow">Welcome</div>
          <div class="hero-title">This is my first webapp</div>
          <p class="hero-desc">SQLite 기반 사용자 등록과 로그인, 세션 관리가 적용된 Streamlit 웹앱입니다. 햄버거 메뉴를 열어 로그인하거나 새 사용자를 등록하세요.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )
    render_tailwind_alpine_banner("Modern UI/UX", "Tailwind CSS와 Alpine.js를 Streamlit 컴포넌트 영역에 적용했습니다.")

    if st.session_state.page == "사용자 등록":
        st.subheader("사용자 등록")
        with st.form("register_form", clear_on_submit=False):
            userid = st.text_input("아이디", placeholder="예: cneway")
            username = st.text_input("사용자 이름", placeholder="이름을 입력하세요")
            email = st.text_input("이메일", placeholder="name@example.com")
            password = st.text_input("비밀번호", type="password", help="8자 이상을 권장합니다.")
            password2 = st.text_input("비밀번호 확인", type="password")
            submitted = st.form_submit_button("사용자 등록", use_container_width=True)

        if submitted:
            if not all([userid.strip(), username.strip(), email.strip(), password, password2]):
                st.error("모든 항목을 입력해 주세요.")
            elif not re.fullmatch(r"[A-Za-z0-9_.-]{4,30}", userid.strip()):
                st.error("아이디는 영문/숫자/._- 조합 4~30자로 입력해 주세요.")
            elif "@" not in email or "." not in email.split("@")[-1]:
                st.error("올바른 이메일 형식을 입력해 주세요.")
            elif len(password) < 8:
                st.error("비밀번호는 8자 이상으로 입력해 주세요.")
            elif password != password2:
                st.error("비밀번호가 서로 일치하지 않습니다.")
            else:
                ok, message = create_user(userid, username, password, email)
                if ok:
                    st.success(message)
                    st.info("왼쪽 메뉴에서 '로그인'을 선택해 주세요.")
                else:
                    st.error(message)

    else:
        st.subheader("로그인")
        with st.form("login_form"):
            userid = st.text_input("아이디")
            password = st.text_input("비밀번호", type="password")
            submitted = st.form_submit_button("로그인", use_container_width=True)

        if submitted:
            user = authenticate_user(userid, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user = user
                st.session_state.page = "대시보드"
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호가 올바르지 않습니다.")

# -----------------------------
# Logged-in landing pages
# -----------------------------
else:
    user = st.session_state.user
    st.markdown(
        f"""
        <section class="hero-card">
          <div class="eyebrow">Dashboard</div>
          <div class="hero-title">반갑습니다, {html.escape(user['username'])}님 👋</div>
          <p class="hero-desc">로그인 세션이 활성화되었습니다. 기존 예제의 동영상, 개인정보 입력, DB 조회 기능을 SQLite 기반으로 사용할 수 있습니다.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.page == "대시보드":
        render_tailwind_alpine_banner("로그인 완료", f"현재 사용자: {user['userid']} · 가입일: {user['created_at']}")
        col1, col2 = st.columns((4, 1))
        with col1:
            with st.expander(f"{user['username']}님 여기는 content입니다", expanded=True):
                url = "https://www.youtube.com/watch?v=MHShfgqrUWs"
                st.write("content....")
                st.video(url)
        with col2:
            with st.expander("Tips...", expanded=True):
                st.write("왼쪽 메뉴에서 정보 입력, DB 조회, 설문 참여를 이용할 수 있습니다.")

    elif st.session_state.page == "내 정보 입력":
        st.subheader("내 정보 입력")
        st.caption("기존 app.py의 name / age / address / phone 입력 흐름을 SQLite 저장 방식으로 변경했습니다.")
        with st.form("profile_form", clear_on_submit=True):
            name = st.text_input("Name?", value=user["username"])
            age = st.number_input("Age?", min_value=1, max_value=120, step=1)
            address = st.text_input("Address?")
            phone = st.text_input("Phone?")
            submitted = st.form_submit_button("저장", use_container_width=True)

        if submitted:
            if not all([name.strip(), age, address.strip(), phone.strip()]):
                st.error("모든 항목을 입력해 주세요.")
            else:
                add_profile(user["id_num"], name, int(age), address, phone)
                st.success("Successful Add!!!")

    elif st.session_state.page == "내 DB 조회":
        st.subheader("Check my DB")
        profiles = get_profiles(user["id_num"])
        if profiles:
            df = pd.DataFrame(profiles)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("아직 저장된 정보가 없습니다. '내 정보 입력' 메뉴에서 먼저 등록해 주세요.")

        with st.expander("기존 data.csv 확인 (참고용)"):
            st.caption("SQLite 전환 전 CSV 파일은 마이그레이션 참고를 위해 프로젝트에 그대로 포함했습니다.")
            try:
                legacy = pd.read_csv("data.csv", header=None, names=["name", "age", "address", "phone"])
                st.dataframe(legacy, use_container_width=True, hide_index=True)
            except (FileNotFoundError, pd.errors.EmptyDataError):
                st.info("data.csv가 없거나 비어 있습니다.")

    elif st.session_state.page == "설문 참여":
        render_survey_page(user)

st.markdown('<div class="footer">MyProject · Streamlit + SQLite</div>', unsafe_allow_html=True)
import streamlit.components.v1 as components
