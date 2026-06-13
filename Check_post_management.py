import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="SecureCheck Police Dashboard",
    page_icon="🚔",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0f1117; }
    .block-container { padding-top: 1rem; }
    .metric-card {
        background: linear-gradient(135deg, #1e2130, #2a2f45);
        border-radius: 12px;
        padding: 20px;
        border-left: 4px solid #4f8ef7;
        margin-bottom: 10px;
    }
    .section-header {
        font-size: 1.3rem;
        font-weight: 700;
        color: #4f8ef7;
        border-bottom: 2px solid #4f8ef7;
        padding-bottom: 6px;
        margin-bottom: 14px;
        margin-top: 20px;
    }
    .insight-box {
        background: #1a1f2e;
        border-left: 4px solid #f7c94f;
        border-radius: 8px;
        padding: 12px 16px;
        color: #e0e0e0;
        margin-top: 8px;
        font-size: 0.93rem;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DB CONNECTION
# ─────────────────────────────────────────────
@st.cache_resource
def get_engine():
    db_url = "mysql+mysqlconnector://root:Subash%4028@localhost:3306/securecheck"
    return create_engine(db_url)

@st.cache_data(ttl=300)
def run_query(query: str) -> pd.DataFrame:
    engine = get_engine()
    return pd.read_sql(query, engine)

# ─────────────────────────────────────────────
# SIDEBAR FILTERS
# ─────────────────────────────────────────────
st.sidebar.image("https://img.icons8.com/fluency/96/police-car.png", width=80)
st.sidebar.title("🚔 SecureCheck")
st.sidebar.markdown("### Filters")

# Load filter options
countries_df = run_query("SELECT DISTINCT country_name FROM police_data ORDER BY country_name")
races_df     = run_query("SELECT DISTINCT driver_race FROM police_data ORDER BY driver_race")
genders_df   = run_query("SELECT DISTINCT driver_gender FROM police_data ORDER BY driver_gender")
violations_df= run_query("SELECT DISTINCT violation FROM police_data ORDER BY violation")

country_options   = ["All"] + countries_df["country_name"].tolist()
race_options      = ["All"] + races_df["driver_race"].tolist()
gender_options    = ["All"] + genders_df["driver_gender"].tolist()
violation_options = ["All"] + violations_df["violation"].tolist()

sel_country   = st.sidebar.selectbox("🌍 Country",   country_options)
sel_gender    = st.sidebar.selectbox("👤 Gender",    gender_options)
sel_race      = st.sidebar.selectbox("🧬 Race",      race_options)
sel_violation = st.sidebar.selectbox("⚖️ Violation", violation_options)

age_range = st.sidebar.slider("🎂 Driver Age Range", 16, 90, (16, 90))

# Build WHERE clause from filters
def build_where(extra: str = "") -> str:
    clauses = [f"driver_age BETWEEN {age_range[0]} AND {age_range[1]}"]
    if sel_country   != "All": clauses.append(f"country_name = '{sel_country}'")
    if sel_gender    != "All": clauses.append(f"driver_gender = '{sel_gender}'")
    if sel_race      != "All": clauses.append(f"driver_race = '{sel_race}'")
    if sel_violation != "All": clauses.append(f"violation = '{sel_violation}'")
    if extra: clauses.append(extra)
    return "WHERE " + " AND ".join(clauses)

WHERE = build_where()

# ─────────────────────────────────────────────
# TITLE
# ─────────────────────────────────────────────
st.title("🚔 SecureCheck — Police Traffic Stop Dashboard")
st.caption("Interactive analytics on police stops • Powered by MySQL + Streamlit + Plotly")

# ─────────────────────────────────────────────
# KPI METRICS
# ─────────────────────────────────────────────
kpi_q = f"""
SELECT
    COUNT(*) AS total_stops,
    ROUND(100.0 * SUM(is_arrested) / COUNT(*), 2) AS arrest_rate,
    ROUND(100.0 * SUM(search_conducted) / COUNT(*), 2) AS search_rate,
    ROUND(100.0 * SUM(drugs_related_stop) / COUNT(*), 2) AS drug_rate
FROM police_data {WHERE}
"""
kpi = run_query(kpi_q).iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("🚦 Total Stops",    f"{int(kpi['total_stops']):,}")
c2.metric("🔒 Arrest Rate",    f"{kpi['arrest_rate']}%")
c3.metric("🔍 Search Rate",    f"{kpi['search_rate']}%")
c4.metric("💊 Drug Stop Rate", f"{kpi['drug_rate']}%")

st.markdown("---")

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tabs = st.tabs([
    "🚗 Vehicle",
    "🧍 Demographics",
    "🕒 Time & Duration",
    "⚖️ Violations",
    "🌍 Location",
    "📊 Advanced",
])

# ══════════════════════════════════════════════
# TAB 1 — VEHICLE
# ══════════════════════════════════════════════
with tabs[0]:
    st.markdown('<div class="section-header">Top 10 Vehicles in Drug-Related Stops</div>', unsafe_allow_html=True)

    drug_veh_q = f"""
        SELECT vehicle_number, COUNT(*) AS drug_stop_count
        FROM police_data {build_where('drugs_related_stop = 1')}
        GROUP BY vehicle_number ORDER BY drug_stop_count DESC LIMIT 10
    """
    drug_veh = run_query(drug_veh_q)
    fig = px.bar(drug_veh, x="vehicle_number", y="drug_stop_count",
                 color="drug_stop_count", color_continuous_scale="Blues",
                 labels={"vehicle_number": "Vehicle Number", "drug_stop_count": "Drug Stop Count"})
    fig.update_layout(template="plotly_dark", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('<div class="insight-box">💡 Drug-related stops are evenly distributed across vehicles — enforcement is case-based, not vehicle-targeted.</div>', unsafe_allow_html=True)

    with st.expander("📋 View Data Table"):
        st.dataframe(drug_veh, use_container_width=True)

    st.markdown('<div class="section-header">Most Frequently Searched Vehicles</div>', unsafe_allow_html=True)

    srch_veh_q = f"""
        SELECT vehicle_number, COUNT(*) AS search_count
        FROM police_data {build_where('search_conducted = 1')}
        GROUP BY vehicle_number ORDER BY search_count DESC LIMIT 10
    """
    srch_veh = run_query(srch_veh_q)
    fig2 = px.bar(srch_veh, x="vehicle_number", y="search_count",
                  color="search_count", color_continuous_scale="Oranges")
    fig2.update_layout(template="plotly_dark", showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)
    st.markdown('<div class="insight-box">💡 All searched vehicles appear only once — no single vehicle was repeatedly searched in the recorded period.</div>', unsafe_allow_html=True)

    with st.expander("📋 View Data Table"):
        st.dataframe(srch_veh, use_container_width=True)

# ══════════════════════════════════════════════
# TAB 2 — DEMOGRAPHICS
# ══════════════════════════════════════════════
with tabs[1]:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-header">Arrest Rate by Age Group</div>', unsafe_allow_html=True)
        age_q = f"""
            SELECT
                CASE
                    WHEN driver_age BETWEEN 18 AND 25 THEN '18-25'
                    WHEN driver_age BETWEEN 26 AND 35 THEN '26-35'
                    WHEN driver_age BETWEEN 36 AND 45 THEN '36-45'
                    WHEN driver_age BETWEEN 46 AND 55 THEN '46-55'
                    WHEN driver_age BETWEEN 56 AND 65 THEN '56-65'
                    WHEN driver_age BETWEEN 66 AND 75 THEN '66-75'
                    ELSE '76+'
                END AS age_group,
                ROUND(100.0 * SUM(CASE WHEN is_arrested=1 THEN 1 ELSE 0 END)/COUNT(*),2) AS arrest_rate
            FROM police_data {WHERE}
            GROUP BY age_group ORDER BY arrest_rate DESC
        """
        age_df = run_query(age_q)
        fig = px.bar(age_df, x="age_group", y="arrest_rate",
                     color="arrest_rate", color_continuous_scale="Reds",
                     labels={"age_group": "Age Group", "arrest_rate": "Arrest Rate (%)"})
        fig.update_layout(template="plotly_dark", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('<div class="insight-box">💡 The 18–25 age group has the highest arrest rate during traffic stops.</div>', unsafe_allow_html=True)
        with st.expander("📋 Data"): st.dataframe(age_df, use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">Search Rate by Race & Gender</div>', unsafe_allow_html=True)
        race_q = f"""
            SELECT driver_race, driver_gender,
                ROUND(100.0 * SUM(CASE WHEN search_conducted=1 THEN 1 ELSE 0 END)/COUNT(*),2) AS search_rate
            FROM police_data {WHERE}
            GROUP BY driver_race, driver_gender ORDER BY search_rate DESC
        """
        race_df = run_query(race_q)
        fig2 = px.bar(race_df, x="driver_race", y="search_rate",
                      color="driver_gender", barmode="group",
                      labels={"driver_race": "Race", "search_rate": "Search Rate (%)", "driver_gender": "Gender"},
                      color_discrete_sequence=px.colors.qualitative.Pastel)
        fig2.update_layout(template="plotly_dark")
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown('<div class="insight-box">💡 Asian female drivers show the highest vehicle search rate during traffic stops.</div>', unsafe_allow_html=True)
        with st.expander("📋 Data"): st.dataframe(race_df, use_container_width=True)

    st.markdown('<div class="section-header">Drug-Related Stops by Country & Gender</div>', unsafe_allow_html=True)
    gender_q = f"""
        SELECT country_name, driver_gender, COUNT(*) as gender_count
        FROM police_data {build_where('drugs_related_stop = 1')}
        GROUP BY country_name, driver_gender ORDER BY country_name
    """
    gender_df = run_query(gender_q)
    fig3 = px.bar(gender_df, x="country_name", y="gender_count",
                  color="driver_gender", barmode="group",
                  labels={"country_name": "Country", "gender_count": "Stops", "driver_gender": "Gender"},
                  color_discrete_sequence=px.colors.qualitative.Set2)
    fig3.update_layout(template="plotly_dark")
    st.plotly_chart(fig3, use_container_width=True)
    st.markdown('<div class="insight-box">💡 USA shows the highest drug-related stops, with Female drivers leading in that country.</div>', unsafe_allow_html=True)
    with st.expander("📋 Data"): st.dataframe(gender_df, use_container_width=True)

# ══════════════════════════════════════════════
# TAB 3 — TIME & DURATION
# ══════════════════════════════════════════════
with tabs[2]:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-header">Traffic Stops by Hour of Day</div>', unsafe_allow_html=True)
        hour_q = f"""
            SELECT HOUR(stop_datetime) AS stop_hour, COUNT(*) AS total_stops
            FROM police_data {WHERE}
            GROUP BY stop_hour ORDER BY stop_hour
        """
        hour_df = run_query(hour_q)
        fig = px.bar(hour_df, x="stop_hour", y="total_stops",
                     color="total_stops", color_continuous_scale="Viridis",
                     labels={"stop_hour": "Hour (0-23)", "total_stops": "Total Stops"})
        fig.update_layout(template="plotly_dark", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('<div class="insight-box">💡 Peak traffic stops occur during the morning hours (0–12), indicating higher early enforcement activity.</div>', unsafe_allow_html=True)
        with st.expander("📋 Data"): st.dataframe(hour_df, use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">Day vs Night Arrest Rate</div>', unsafe_allow_html=True)
        night_q = f"""
            SELECT
                CASE WHEN HOUR(stop_datetime) BETWEEN 6 AND 17 THEN 'Day' ELSE 'Night' END AS time_period,
                COUNT(*) AS total_stops,
                SUM(CASE WHEN is_arrested=1 THEN 1 ELSE 0 END) AS total_arrests,
                ROUND(100.0*SUM(CASE WHEN is_arrested=1 THEN 1 ELSE 0 END)/COUNT(*),2) AS arrest_rate
            FROM police_data {WHERE}
            GROUP BY time_period
        """
        night_df = run_query(night_q)
        fig2 = px.pie(night_df, names="time_period", values="arrest_rate",
                      color_discrete_sequence=["#4f8ef7", "#f7c94f"],
                      hole=0.45)
        fig2.update_layout(template="plotly_dark")
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown('<div class="insight-box">💡 Daytime stops have a higher arrest rate compared to nighttime stops.</div>', unsafe_allow_html=True)
        with st.expander("📋 Data"): st.dataframe(night_df, use_container_width=True)

    st.markdown('<div class="section-header">Stop Duration by Violation Type</div>', unsafe_allow_html=True)
    dur_q = f"""
        SELECT violation, stop_duration, COUNT(*) AS total_stop
        FROM police_data {WHERE}
        GROUP BY violation, stop_duration ORDER BY violation
    """
    dur_df = run_query(dur_q)
    fig3 = px.bar(dur_df, x="violation", y="total_stop",
                  color="stop_duration", barmode="group",
                  labels={"violation": "Violation", "total_stop": "Number of Stops", "stop_duration": "Duration"},
                  color_discrete_sequence=px.colors.qualitative.Bold)
    fig3.update_layout(template="plotly_dark")
    st.plotly_chart(fig3, use_container_width=True)
    st.markdown('<div class="insight-box">💡 DUI violations have the longest average stop duration, reflecting more thorough checks.</div>', unsafe_allow_html=True)
    with st.expander("📋 Data"): st.dataframe(dur_df, use_container_width=True)

# ══════════════════════════════════════════════
# TAB 4 — VIOLATIONS
# ══════════════════════════════════════════════
with tabs[3]:
    st.markdown('<div class="section-header">Search & Arrest Rate by Violation</div>', unsafe_allow_html=True)

    viol_q = f"""
        SELECT violation,
            ROUND(100.0*SUM(CASE WHEN search_conducted=1 THEN 1 ELSE 0 END)/COUNT(*),2) AS search_rate,
            ROUND(100.0*SUM(CASE WHEN is_arrested=1 THEN 1 ELSE 0 END)/COUNT(*),2) AS arrest_rate
        FROM police_data {WHERE}
        GROUP BY violation ORDER BY arrest_rate DESC
    """
    viol_df = run_query(viol_q)
    fig = px.bar(viol_df, x="violation", y=["search_rate", "arrest_rate"],
                 barmode="group",
                 labels={"violation": "Violation", "value": "Rate (%)", "variable": "Metric"},
                 color_discrete_map={"search_rate": "#4f8ef7", "arrest_rate": "#f75e4f"})
    fig.update_layout(template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('<div class="insight-box">💡 Seatbelt and DUI violations are most strongly linked to searches and arrests.</div>', unsafe_allow_html=True)
    with st.expander("📋 Data"): st.dataframe(viol_df, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-header">Violations Among Drivers Under 25</div>', unsafe_allow_html=True)
        young_q = f"""
            SELECT violation, COUNT(*) AS violation_count
            FROM police_data {build_where('driver_age < 25')}
            GROUP BY violation ORDER BY violation_count DESC
        """
        young_df = run_query(young_q)
        fig2 = px.pie(young_df, names="violation", values="violation_count",
                      color_discrete_sequence=px.colors.qualitative.Set3, hole=0.3)
        fig2.update_layout(template="plotly_dark")
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown('<div class="insight-box">💡 Speeding is the most common violation among drivers under 25.</div>', unsafe_allow_html=True)
        with st.expander("📋 Data"): st.dataframe(young_df, use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">Violation Ranking (Window Function)</div>', unsafe_allow_html=True)
        rank_q = f"""
            SELECT violation, search_rate, arrest_rate,
                RANK() OVER(ORDER BY search_rate DESC) AS search_rank,
                RANK() OVER(ORDER BY arrest_rate DESC) AS arrest_rank
            FROM (
                SELECT violation,
                    ROUND(100.0*SUM(CASE WHEN search_conducted=1 THEN 1 ELSE 0 END)/COUNT(*),2) AS search_rate,
                    ROUND(100.0*SUM(CASE WHEN is_arrested=1 THEN 1 ELSE 0 END)/COUNT(*),2) AS arrest_rate
                FROM police_data {WHERE}
                GROUP BY violation
            ) vr
        """
        rank_df = run_query(rank_q)
        fig3 = px.scatter(rank_df, x="search_rank", y="arrest_rank",
                          text="violation", size="search_rate",
                          color="arrest_rate", color_continuous_scale="RdYlGn_r",
                          labels={"search_rank": "Search Rank", "arrest_rank": "Arrest Rank"})
        fig3.update_traces(textposition="top center")
        fig3.update_layout(template="plotly_dark")
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown('<div class="insight-box">💡 Violations ranked by enforcement intensity — DUI and Seatbelt consistently rank highest.</div>', unsafe_allow_html=True)
        with st.expander("📋 Data"): st.dataframe(rank_df, use_container_width=True)

# ══════════════════════════════════════════════
# TAB 5 — LOCATION
# ══════════════════════════════════════════════
with tabs[4]:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-header">Drug-Related Stop Rate by Country</div>', unsafe_allow_html=True)
        drug_cntry_q = f"""
            SELECT country_name,
                ROUND(100.0*SUM(CASE WHEN drugs_related_stop=1 THEN 1 ELSE 0 END)/COUNT(*),2) AS drug_stop_rate
            FROM police_data {WHERE}
            GROUP BY country_name ORDER BY drug_stop_rate DESC
        """
        drug_cntry = run_query(drug_cntry_q)
        fig = px.bar(drug_cntry, x="country_name", y="drug_stop_rate",
                     color="drug_stop_rate", color_continuous_scale="Reds",
                     labels={"country_name": "Country", "drug_stop_rate": "Drug Stop Rate (%)"})
        fig.update_layout(template="plotly_dark", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('<div class="insight-box">💡 USA has the highest rate of drug-related traffic stops among all countries.</div>', unsafe_allow_html=True)
        with st.expander("📋 Data"): st.dataframe(drug_cntry, use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">Searches Conducted by Country</div>', unsafe_allow_html=True)
        srch_cntry_q = f"""
            SELECT country_name, COUNT(*) AS search_count
            FROM police_data {build_where('search_conducted = 1')}
            GROUP BY country_name ORDER BY search_count DESC
        """
        srch_cntry = run_query(srch_cntry_q)
        fig2 = px.pie(srch_cntry, names="country_name", values="search_count",
                      color_discrete_sequence=px.colors.qualitative.Pastel, hole=0.4)
        fig2.update_layout(template="plotly_dark")
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown('<div class="insight-box">💡 Canada leads in the number of stops where a search was conducted.</div>', unsafe_allow_html=True)
        with st.expander("📋 Data"): st.dataframe(srch_cntry, use_container_width=True)

    st.markdown('<div class="section-header">Top 10 Arrest Rates by Country & Violation</div>', unsafe_allow_html=True)
    arr_cntry_q = f"""
        SELECT country_name, violation,
            ROUND(100.0*SUM(CASE WHEN is_arrested=1 THEN 1 ELSE 0 END)/COUNT(*),2) AS arrest_rate
        FROM police_data {WHERE}
        GROUP BY country_name, violation ORDER BY arrest_rate DESC LIMIT 10
    """
    arr_cntry = run_query(arr_cntry_q)
    arr_cntry["label"] = arr_cntry["country_name"] + " - " + arr_cntry["violation"]
    fig3 = px.bar(arr_cntry, x="label", y="arrest_rate",
                  color="country_name",
                  labels={"label": "Country - Violation", "arrest_rate": "Arrest Rate (%)"},
                  color_discrete_sequence=px.colors.qualitative.Bold)
    fig3.update_layout(template="plotly_dark", xaxis_tickangle=-45)
    st.plotly_chart(fig3, use_container_width=True)
    st.markdown('<div class="insight-box">💡 Canada – DUI combination records the highest arrest rate across all country-violation pairs.</div>', unsafe_allow_html=True)
    with st.expander("📋 Data"): st.dataframe(arr_cntry, use_container_width=True)

# ══════════════════════════════════════════════
# TAB 6 — ADVANCED / COMPLEX QUERIES
# ══════════════════════════════════════════════
with tabs[5]:
    st.markdown('<div class="section-header">Yearly Stops & Arrests by Country (Cumulative)</div>', unsafe_allow_html=True)

    yearly_q = """
        SELECT country_name, year, total_stops, total_arrests,
            SUM(total_stops) OVER(PARTITION BY country_name ORDER BY year) AS cumulative_stops,
            SUM(total_arrests) OVER(PARTITION BY country_name ORDER BY year) AS cumulative_arrests,
            RANK() OVER(PARTITION BY country_name ORDER BY total_arrests DESC) AS arrest_rank
        FROM (
            SELECT country_name, YEAR(stop_datetime) AS year,
                COUNT(*) AS total_stops, SUM(is_arrested) AS total_arrests
            FROM police_data
            GROUP BY country_name, YEAR(stop_datetime)
        ) yearly_data
    """
    yearly_df = run_query(yearly_q)

    view_mode = st.radio("View Mode", ["Yearly", "Cumulative"], horizontal=True)
    y_col = "total_stops" if view_mode == "Yearly" else "cumulative_stops"
    y_arr = "total_arrests" if view_mode == "Yearly" else "cumulative_arrests"

    fig = go.Figure()
    for country in yearly_df["country_name"].unique():
        temp = yearly_df[yearly_df["country_name"] == country]
        fig.add_trace(go.Scatter(x=temp["year"], y=temp[y_col], mode="lines+markers", name=f"{country} Stops"))
        fig.add_trace(go.Scatter(x=temp["year"], y=temp[y_arr], mode="lines+markers", line=dict(dash="dash"), name=f"{country} Arrests"))
    fig.update_layout(template="plotly_dark", xaxis_title="Year", yaxis_title="Count")
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('<div class="insight-box">💡 Traffic stops and arrests both show an upward trend over the years, indicating increasing enforcement activity.</div>', unsafe_allow_html=True)
    with st.expander("📋 Data"): st.dataframe(yearly_df, use_container_width=True)

    st.markdown('<div class="section-header">Violation Trends by Age Group & Race (Top 10)</div>', unsafe_allow_html=True)
    trend_q = """
        SELECT a.age_group, p.driver_race, p.violation, COUNT(*) AS violation_count
        FROM police_data p
        JOIN (
            SELECT vehicle_number,
                CASE
                    WHEN driver_age BETWEEN 18 AND 25 THEN '18-25'
                    WHEN driver_age BETWEEN 26 AND 35 THEN '26-35'
                    WHEN driver_age BETWEEN 36 AND 45 THEN '36-45'
                    WHEN driver_age BETWEEN 46 AND 55 THEN '46-55'
                    ELSE '56+'
                END AS age_group
            FROM police_data
        ) a ON p.vehicle_number = a.vehicle_number
        GROUP BY a.age_group, p.driver_race, p.violation
        ORDER BY violation_count DESC LIMIT 10
    """
    trend_df = run_query(trend_q)
    trend_df["label"] = trend_df["age_group"] + " | " + trend_df["driver_race"] + " | " + trend_df["violation"]
    fig2 = px.bar(trend_df, x="label", y="violation_count",
                  color="driver_race",
                  labels={"label": "Age | Race | Violation", "violation_count": "Count"},
                  color_discrete_sequence=px.colors.qualitative.Set2)
    fig2.update_layout(template="plotly_dark", xaxis_tickangle=-50)
    st.plotly_chart(fig2, use_container_width=True)
    st.markdown('<div class="insight-box">💡 White drivers aged 56+ show the highest number of DUI violations in the dataset.</div>', unsafe_allow_html=True)
    with st.expander("📋 Data"): st.dataframe(trend_df, use_container_width=True)

    st.markdown('<div class="section-header">Driver Demographics by Country (Age, Gender, Race)</div>', unsafe_allow_html=True)
    demo_q = f"""
        SELECT country_name, driver_gender, driver_race,
            ROUND(AVG(driver_age),2) AS avg_age, COUNT(*) AS total_drivers
        FROM police_data {WHERE}
        GROUP BY country_name, driver_gender, driver_race
        ORDER BY total_drivers DESC
    """
    demo_df = run_query(demo_q)
    fig3 = px.treemap(demo_df,
                      path=["country_name", "driver_gender", "driver_race"],
                      values="total_drivers", color="avg_age",
                      color_continuous_scale="RdBu",
                      labels={"avg_age": "Avg Age", "total_drivers": "Total Drivers"})
    fig3.update_layout(template="plotly_dark")
    st.plotly_chart(fig3, use_container_width=True)
    st.markdown('<div class="insight-box">💡 India records the highest driver count; Asian female drivers are the dominant demographic group.</div>', unsafe_allow_html=True)
    with st.expander("📋 Data"): st.dataframe(demo_df, use_container_width=True)

