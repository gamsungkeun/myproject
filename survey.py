"""설문 참여 메뉴: '설문응시' / '설문결과 시각화' 탭.

survey_table(q1~q10, 5점 리커트 척도)에 AI의 교육적 효과에 대한 인식을 저장하고,
문항별 기술통계와 시각화를 제공합니다.
"""
from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from db import SURVEY_COLUMNS, get_all_surveys, get_user_survey, save_survey

# -----------------------------
# 설문 문항 (AI의 교육적 효과에 대한 인식)
# (key, 하위 영역, 문항)
# -----------------------------
SURVEY_ITEMS: list[tuple[str, str, str]] = [
    ("q1", "이해도 향상", "AI는 수업 내용에 대한 나의 이해도를 높이는 데 도움이 된다."),
    ("q2", "학습 효율성", "AI를 활용하면 학습에 필요한 정보를 더 효율적으로 찾고 정리할 수 있다."),
    ("q3", "개별화 학습", "AI는 나의 수준과 필요에 맞는 개별화된 학습을 가능하게 한다."),
    ("q4", "피드백", "AI의 즉각적인 피드백은 과제의 완성도를 높이는 데 도움이 된다."),
    ("q5", "학습 동기", "AI를 활용한 학습은 학습에 대한 흥미와 참여 동기를 높인다."),
    ("q6", "창의성", "AI는 창의적인 아이디어를 발상하고 표현하는 데 도움이 된다."),
    ("q7", "비판적 사고", "AI가 제시한 결과를 검토하는 과정은 비판적 사고력 향상에 도움이 된다."),
    ("q8", "진로 역량", "AI 활용 능력은 향후 진로 및 직무 역량 강화에 도움이 될 것이다."),
    ("q9", "교육 필요성", "수업에서 AI를 올바르게 활용하는 방법을 체계적으로 교육받을 필요가 있다."),
    ("q10", "전반적 효과", "전반적으로 AI는 교육의 효과를 높이는 데 긍정적인 역할을 한다."),
]

LIKERT_LABELS = {1: "전혀 아니다", 2: "아니다", 3: "보통이다", 4: "그렇다", 5: "매우 그렇다"}
LIKERT_ORDER = [LIKERT_LABELS[i] for i in range(1, 6)]
# 부정(빨강) → 중립(회색) → 긍정(파랑) 발산형 팔레트
LIKERT_COLORS = ["#c0392b", "#ec9a86", "#cfd4da", "#7fb3e0", "#1f5fa8"]

ITEM_SHORT = {key: f"{key.upper()}. {short}" for key, short, _ in SURVEY_ITEMS}
ITEM_ORDER = [ITEM_SHORT[k] for k in SURVEY_COLUMNS]


# -----------------------------
# 통계 계산
# -----------------------------
def cronbach_alpha(items: pd.DataFrame) -> float | None:
    """Cronbach's α = k/(k-1) · (1 - Σσ²ᵢ / σ²ₜ). 응답자가 2명 미만이면 계산하지 않습니다."""
    items = items.dropna()
    k = items.shape[1]
    if items.shape[0] < 2 or k < 2:
        return None
    total_var = items.sum(axis=1).var(ddof=1)
    if total_var == 0:
        return None
    return k / (k - 1) * (1 - items.var(ddof=1).sum() / total_var)


def build_stats_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for key, short, text in SURVEY_ITEMS:
        s = df[key].dropna().astype(int)
        n = len(s)
        counts = s.value_counts().reindex(range(1, 6), fill_value=0)
        row = {
            "문항": key.upper(),
            "영역": short,
            "내용": text,
            "N": n,
            "평균": round(s.mean(), 2) if n else None,
            "표준편차": round(s.std(ddof=1), 2) if n > 1 else None,
            "중앙값": float(s.median()) if n else None,
            "최빈값": LIKERT_LABELS[int(counts.idxmax())] if n else None,
        }
        for score in range(1, 6):
            pct = counts[score] / n * 100 if n else 0
            row[f"{score}점 {LIKERT_LABELS[score]}"] = f"{counts[score]} ({pct:.1f}%)"
        row["긍정률(4+5점)"] = f"{(counts[4] + counts[5]) / n * 100:.1f}%" if n else "-"
        rows.append(row)
    return pd.DataFrame(rows)


def build_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """문항 × 응답 범주별 빈도와 비율(long format)."""
    records = []
    for key in SURVEY_COLUMNS:
        s = df[key].dropna().astype(int)
        n = len(s)
        counts = s.value_counts().reindex(range(1, 6), fill_value=0)
        for score in range(1, 6):
            records.append(
                {
                    "문항": ITEM_SHORT[key],
                    "점수": score,
                    "응답": LIKERT_LABELS[score],
                    "빈도": int(counts[score]),
                    "비율": counts[score] / n if n else 0,
                }
            )
    return pd.DataFrame(records)


# -----------------------------
# 탭 1: 설문응시
# -----------------------------
def render_survey_form(user: dict) -> None:
    st.markdown("#### AI의 교육적 효과에 대한 인식 설문")
    st.caption(
        "각 문항을 읽고 본인의 생각과 가장 가까운 응답을 선택해 주세요. "
        "(1점: 전혀 아니다 ~ 5점: 매우 그렇다)"
    )

    existing = get_user_survey(user["userid"])
    if existing:
        st.info(
            f"이미 {existing['created_at']}에 설문에 응답하셨습니다. "
            "아래에서 응답을 수정해 다시 제출하면 기존 응답이 갱신되고 응답 일시가 현재 시각으로 바뀝니다."
        )

    options = list(LIKERT_LABELS.keys())
    with st.form("survey_form"):
        answers: dict[str, int | None] = {}
        for idx, (key, short, text) in enumerate(SURVEY_ITEMS, start=1):
            st.markdown(f"**{idx}. {text}**  \n<span style='color:#64748b;font-size:.85rem'>{short}</span>",
                        unsafe_allow_html=True)
            prev = existing.get(key) if existing else None
            answers[key] = st.radio(
                f"{key} 응답",
                options,
                index=options.index(prev) if prev in options else None,
                format_func=lambda v: f"{v} {LIKERT_LABELS[v]}",
                horizontal=True,
                key=f"survey_{key}",
                label_visibility="collapsed",
            )
            if idx < len(SURVEY_ITEMS):
                st.markdown("<hr style='margin:.4rem 0 .9rem;border-color:#eef2f7'>", unsafe_allow_html=True)
        submitted = st.form_submit_button("응답 수정 제출" if existing else "설문 제출", use_container_width=True)

    if submitted:
        missing = [k.upper() for k, v in answers.items() if v is None]
        if missing:
            st.error(f"응답하지 않은 문항이 있습니다: {', '.join(missing)}")
        else:
            action = save_survey(user["userid"], [answers[k] for k in SURVEY_COLUMNS])
            if action == "insert":
                st.success("설문에 참여해 주셔서 감사합니다. '설문결과 시각화' 탭에서 결과를 확인할 수 있습니다.")
            else:
                st.success("응답이 수정되었습니다. '설문결과 시각화' 탭에서 결과를 확인할 수 있습니다.")
            st.balloons()


# -----------------------------
# 탭 2: 설문결과 시각화
# -----------------------------
def render_survey_results(user: dict) -> None:
    data = get_all_surveys()
    if not data:
        st.info("아직 수집된 설문 응답이 없습니다. '설문응시' 탭에서 먼저 응답해 주세요.")
        return

    df = pd.DataFrame(data)
    df[SURVEY_COLUMNS] = df[SURVEY_COLUMNS].apply(pd.to_numeric, errors="coerce")
    n = len(df)
    item_means = df[SURVEY_COLUMNS].mean()
    all_scores = df[SURVEY_COLUMNS].stack()
    positive_rate = (all_scores >= 4).mean() * 100
    alpha = cronbach_alpha(df[SURVEY_COLUMNS])

    # --- 요약 지표
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("응답자 수", f"{n}명")
    c2.metric("전체 평균", f"{all_scores.mean():.2f} / 5")
    c3.metric("긍정 응답률(4·5점)", f"{positive_rate:.1f}%")
    c4.metric("Cronbach's α", f"{alpha:.3f}" if alpha is not None else "-",
              help="10개 문항의 내적 일관성 신뢰도. 응답자가 2명 이상이고 총점 분산이 0이 아닐 때 계산됩니다.")
    if n < 30:
        st.caption(f"※ 현재 응답자가 {n}명으로 적어, 통계값은 참고용으로 해석하는 것이 바람직합니다.")

    # --- 문항별 평균
    st.markdown("##### 문항별 평균 점수")
    mean_df = pd.DataFrame(
        {
            "문항": [ITEM_SHORT[k] for k in SURVEY_COLUMNS],
            "평균": item_means.values,
            "표준편차": df[SURVEY_COLUMNS].std(ddof=1).values if n > 1 else [0.0] * len(SURVEY_COLUMNS),
        }
    )
    bars = (
        alt.Chart(mean_df)
        .mark_bar(cornerRadiusEnd=4, height=18, color="#4f46e5")
        .encode(
            x=alt.X("평균:Q", scale=alt.Scale(domain=[0, 5], nice=False), title="평균 (1~5점)"),
            y=alt.Y("문항:N", sort=ITEM_ORDER, title=None),
            tooltip=["문항", alt.Tooltip("평균:Q", format=".2f"), alt.Tooltip("표준편차:Q", format=".2f")],
        )
    )
    labels = bars.mark_text(align="left", dx=4, color="#334155").encode(text=alt.Text("평균:Q", format=".2f"))
    midline = alt.Chart(pd.DataFrame({"x": [3]})).mark_rule(strokeDash=[4, 4], color="#94a3b8").encode(x="x:Q")
    st.altair_chart((bars + labels + midline).properties(height=360), use_container_width=True)
    st.caption("점선은 척도 중간값(3점 '보통이다')입니다.")

    # --- 문항별 응답 분포 (100% 누적 막대)
    st.markdown("##### 문항별 응답 분포")
    dist = build_distribution(df)
    stacked = (
        alt.Chart(dist)
        .mark_bar()
        .encode(
            x=alt.X("비율:Q", stack="normalize", axis=alt.Axis(format="%"), title="응답 비율"),
            y=alt.Y("문항:N", sort=ITEM_ORDER, title=None),
            color=alt.Color(
                "응답:N",
                sort=LIKERT_ORDER,
                scale=alt.Scale(domain=LIKERT_ORDER, range=LIKERT_COLORS),
                legend=alt.Legend(orient="top", title=None),
            ),
            order=alt.Order("점수:Q", sort="ascending"),
            tooltip=["문항", "응답", "빈도", alt.Tooltip("비율:Q", format=".1%")],
        )
        .properties(height=380)
    )
    st.altair_chart(stacked, use_container_width=True)

    # --- 문항별 통계표
    st.markdown("##### 문항별 기술통계")
    stats = build_stats_table(df)
    st.dataframe(stats, use_container_width=True, hide_index=True)

    # --- 문항 상세
    st.markdown("##### 문항 상세 보기")
    selected = st.selectbox(
        "문항 선택",
        SURVEY_COLUMNS,
        format_func=lambda k: f"{k.upper()}. {dict((a, c) for a, _, c in SURVEY_ITEMS)[k]}",
    )
    detail = dist[dist["문항"] == ITEM_SHORT[selected]]
    col_chart, col_info = st.columns((3, 1))
    with col_chart:
        detail_chart = (
            alt.Chart(detail)
            .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
            .encode(
                x=alt.X("응답:N", sort=LIKERT_ORDER, title=None, axis=alt.Axis(labelAngle=0)),
                y=alt.Y("빈도:Q", title="응답 수", axis=alt.Axis(tickMinStep=1)),
                color=alt.Color("응답:N", scale=alt.Scale(domain=LIKERT_ORDER, range=LIKERT_COLORS), legend=None),
                tooltip=["응답", "빈도", alt.Tooltip("비율:Q", format=".1%")],
            )
        )
        detail_text = (
            alt.Chart(detail)
            .mark_text(dy=-8, color="#334155", fontWeight="bold")
            .encode(x=alt.X("응답:N", sort=LIKERT_ORDER), y="빈도:Q", text="빈도:Q")
        )
        st.altair_chart((detail_chart + detail_text).properties(height=280), use_container_width=True)
    with col_info:
        row = stats[stats["문항"] == selected.upper()].iloc[0]
        st.metric("평균", f"{row['평균']:.2f}")
        st.metric("표준편차", f"{row['표준편차']:.2f}" if pd.notna(row["표준편차"]) else "-")
        st.metric("긍정률", row["긍정률(4+5점)"])
        mine = get_user_survey(user["userid"])
        if mine:
            st.caption(f"내 응답: {mine[selected]}점 ({LIKERT_LABELS[mine[selected]]})")

    # --- 응답 일자별 추이
    with st.expander("응답 일자별 참여 추이"):
        dates = pd.to_datetime(df["created_at"], errors="coerce").dt.date.value_counts().sort_index()
        trend = pd.DataFrame({"일자": pd.to_datetime(dates.index), "응답 수": dates.values})
        st.altair_chart(
            alt.Chart(trend)
            .mark_line(point=True, color="#4f46e5")
            .encode(x=alt.X("일자:T", title=None), y=alt.Y("응답 수:Q", axis=alt.Axis(tickMinStep=1)))
            .properties(height=220),
            use_container_width=True,
        )

    # --- 원자료 다운로드 (분석용)
    raw = df[["id_num", "user_id", *SURVEY_COLUMNS, "created_at"]]
    c_a, c_b = st.columns(2)
    c_a.download_button(
        "원자료 CSV 다운로드",
        raw.to_csv(index=False).encode("utf-8-sig"),
        file_name="survey_raw.csv",
        mime="text/csv",
        use_container_width=True,
    )
    c_b.download_button(
        "기술통계표 CSV 다운로드",
        stats.to_csv(index=False).encode("utf-8-sig"),
        file_name="survey_stats.csv",
        mime="text/csv",
        use_container_width=True,
    )


def render_survey_page(user: dict) -> None:
    st.subheader("설문 참여")
    tab_take, tab_result = st.tabs(["📝 설문응시", "📊 설문결과 시각화"])
    with tab_take:
        render_survey_form(user)
    with tab_result:
        render_survey_results(user)
