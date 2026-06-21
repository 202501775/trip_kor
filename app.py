from datetime import date, timedelta

import pandas as pd
import pydeck as pdk
import streamlit as st

from planner import build_itinerary, lodging_links
from places import fetch_places


st.set_page_config(page_title="같이가자", layout="wide")

st.markdown(
    """
    <style>
    :root { --accent: #007a5a; }
    .block-container { max-width: 1180px; padding-top: 2rem; }
    h1, h2, h3 { letter-spacing: 0; }
    div[data-testid="stMetric"] { border: 1px solid #e5e7eb; padding: 14px; border-radius: 8px; }
    .place-line { padding: 12px 0; border-bottom: 1px solid #eceff1; }
    .muted { color: #687076; font-size: 0.9rem; }
    .stButton > button[kind="primary"] { background: var(--accent); border-color: var(--accent); }
    </style>
    """,
    unsafe_allow_html=True,
)


def secret(name, default=""):
    try:
        return st.secrets.get(name, default)
    except FileNotFoundError:
        return default


st.title("같이가자")
st.caption("인원, 예산, 취향을 넣으면 국내 여행 동선과 맛집을 한 번에 짜드려요.")

with st.sidebar:
    st.header("여행 조건")
    with st.form("trip_form"):
        region = st.text_input("여행 지역", placeholder="예: 강릉, 부산 해운대", value="강릉")
        start_date = st.date_input("출발일", value=date.today() + timedelta(days=14), min_value=date.today())
        days = st.number_input("여행 기간(일)", min_value=1, max_value=7, value=2, format="%d")
        people = st.number_input("인원(명)", min_value=1, max_value=12, value=6, format="%d")
        budget = st.number_input("1인 예산", min_value=50000, max_value=2000000, value=250000, step=10000)
        transport = st.radio("이동 수단", ["대중교통", "자가용", "렌터카"], index=1, horizontal=True)
        pace = st.select_slider("일정 밀도", ["여유롭게", "적당히", "빡빡하게"], value="적당히")
        spend_level = st.radio("소비 성향", ["가성비", "보통", "여유"], index=1, horizontal=True)
        interests = st.multiselect(
            "관심사",
            ["맛집", "카페", "자연·바다", "액티비티", "역사·문화", "사진"],
            default=["맛집", "자연·바다"],
        )
        generate = st.form_submit_button("여행 계획 만들기", type="primary", use_container_width=True)

if not region.strip():
    st.info("왼쪽에서 여행할 지역을 입력해 주세요.")
    st.stop()

if generate or "trip_result" not in st.session_state:
    with st.spinner("가까운 장소끼리 묶어 여행 동선을 만들고 있어요..."):
        place_data, warning = fetch_places(region.strip(), secret("KAKAO_REST_API_KEY"), interests)
        rows, budget_result = build_itinerary(
            start_date, int(days), int(people), int(budget), transport, pace, spend_level, place_data
        )
        request = {
            "region": region.strip(), "start_date": start_date, "days": int(days),
            "people": int(people), "budget": int(budget)
        }
        st.session_state.trip_result = (request, place_data, rows, budget_result, warning)

request, place_data, rows, budget_result, warning = st.session_state.trip_result
region = request["region"]
start_date = request["start_date"]
days = request["days"]
people = request["people"]
budget = request["budget"]
if warning:
    st.warning(warning)
elif place_data["attractions"][0]["source"] == "샘플":
    st.info("현재 데모 장소 데이터를 사용 중입니다. 카카오 REST API 키를 등록하면 입력한 지역을 실시간 검색합니다.")

title_col, action_col = st.columns([4, 1])
with title_col:
    st.subheader(f"{region} {int(days)}일 여행 · {int(people)}명")
with action_col:
    csv_df = pd.DataFrame(rows).drop(columns=["lat", "lon"])
    st.download_button(
        "계획표 CSV 저장",
        csv_df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{region}_여행계획.csv",
        mime="text/csv",
        use_container_width=True,
    )

metric_cols = st.columns(4)
metric_cols[0].metric("전체 예산", f"{budget_result['전체 예산']:,}원")
metric_cols[1].metric("예상 지출", f"{budget_result['예상 합계']:,}원")
metric_cols[2].metric("1인 예상", f"{budget_result['예상 합계'] // int(people):,}원")
remaining = budget_result["잔여 예산"]
metric_cols[3].metric("잔여 예산", f"{remaining:,}원", delta="예산 내" if remaining >= 0 else "예산 초과")

tab_schedule, tab_map, tab_food, tab_lodging, tab_budget = st.tabs(
    ["일정표", "지도", "맛집", "숙소", "예산"]
)

with tab_schedule:
    for day_label in dict.fromkeys(row["일차"] for row in rows):
        day_rows = [row for row in rows if row["일차"] == day_label]
        st.markdown(f"### {day_label} · {day_rows[0]['날짜']}")
        for row in day_rows:
            st.markdown(
                f"<div class='place-line'><b>{row['시간']} · {row['구분']}</b>　"
                f"<a href='{row['지도']}' target='_blank'>{row['장소']}</a>"
                f"<div class='muted'>{row['주소']}</div></div>",
                unsafe_allow_html=True,
            )

with tab_map:
    map_df = pd.DataFrame(rows).drop_duplicates(subset=["장소"])
    st.pydeck_chart(
        pdk.Deck(
            initial_view_state=pdk.ViewState(
                latitude=map_df["lat"].mean(), longitude=map_df["lon"].mean(), zoom=10.5, pitch=0
            ),
            layers=[
                pdk.Layer(
                    "ScatterplotLayer",
                    data=map_df,
                    get_position="[lon, lat]",
                    get_fill_color="[0, 122, 90, 190]",
                    get_radius=180,
                    pickable=True,
                )
            ],
            tooltip={"html": "<b>{장소}</b><br>{주소}"},
        ),
        use_container_width=True,
    )

with tab_food:
    st.caption("실제 방문 전 영업시간, 휴무일, 단체석과 예약 가능 여부를 확인해 주세요.")
    for place in place_data["restaurants"][:10]:
        phone = f" · {place['phone']}" if place["phone"] else ""
        st.markdown(
            f"<div class='place-line'><b><a href='{place['url']}' target='_blank'>{place['name']}</a></b>"
            f"<div class='muted'>{place['address']}{phone}</div></div>",
            unsafe_allow_html=True,
        )

with tab_lodging:
    if int(days) == 1:
        st.info("당일치기 일정이라 숙소가 필요하지 않습니다.")
    else:
        checkout = start_date + timedelta(days=int(days) - 1)
        st.write(f"체크인 `{start_date}` · 체크아웃 `{checkout}` · `{int(people)}명`")
        st.caption("숙박 가격과 잔여 객실은 자주 바뀌므로 예약 플랫폼에서 최종 확인합니다.")
        for label, url in lodging_links(region, int(people), start_date, checkout):
            st.link_button(label, url, use_container_width=True)

with tab_budget:
    chart_data = pd.DataFrame(
        {"항목": ["식비", "숙박", "교통", "입장·체험"], "금액": [budget_result[k] for k in ["식비", "숙박", "교통", "입장·체험"]]}
    ).set_index("항목")
    st.bar_chart(chart_data, color="#007a5a")
    st.dataframe(chart_data.style.format("{:,.0f}원"), use_container_width=True)
    if remaining < 0:
        st.error(f"현재 조건에서는 예산을 약 {abs(remaining):,}원 초과할 가능성이 있습니다.")
    else:
        st.success(f"예상 지출 후 약 {remaining:,}원의 여유가 있습니다.")

st.divider()
st.caption("추천 결과는 여행 계획을 돕기 위한 정보입니다. 방문 전 영업 여부와 예약 조건을 반드시 확인하세요.")
