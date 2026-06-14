import streamlit as st
import pandas as pd
import plotly.express as px
import os

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
# DATA LOADING
# ─────────────────────────────────────────────
DATA_PATH = "police_data.csv"  


@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]

    # Build a single stop_datetime column for time-based analysis
    if "stop_datetime" in df.columns:
        df["stop_datetime"] = pd.to_datetime(df["stop_datetime"], errors="coerce")
    elif "stop_date" in df.columns and "stop_time" in df.columns:
        df["stop_datetime"] = pd.to_datetime(
            df["stop_date"].astype(str) + " " + df["stop_time"].astype(str),
            errors="coerce",
        )
    else:
        df["stop_datetime"] = pd.NaT

    df["stop_hour"] = df["stop_datetime"].dt.hour

    # Normalise boolean-like flag columns to 0/1 integers
    for col in ["is_arrested", "search_conducted", "drugs_related_stop"]:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.strip()
                .str.lower()
                .map({"true": 1, "false": 0, "1": 1, "0": 0, "yes": 1, "no": 0})
            )
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    if "driver_age" in df.columns:
        df["driver_age"] = pd.to_numeric(df["driver_age"], errors="coerce")

    return df


if not os.path.exists(DATA_PATH):
    st.error(
        f"❌ '{DATA_PATH}' file kaanom! Please keep 'police_data.csv' in the same "
        f"folder as this script, or update the DATA_PATH variable at the top of the code."
    )
    st.stop()

df = load_data(DATA_PATH)

# ─────────────────────────────────────────────
# SIDEBAR FILTERS
# ─────────────────────────────────────────────
st.sidebar.image("https://img.icons8.com/fluency/96/police-car.png", width=80)
st.sidebar.title("🚔 SecureCheck")
st.sidebar.markdown("### Filters")


def col_options(col: str):
    if col in df.columns:
        return ["All"] + sorted(df[col].dropna().unique().tolist())
    return ["All"]


sel_country = st.sidebar.selectbox("🌍 Country", col_options("country_name"))
sel_gender = st.sidebar.selectbox("👤 Gender", col_options("driver_gender"))
sel_race = st.sidebar.selectbox("🧬 Race", col_options("driver_race"))
sel_violation = st.sidebar.selectbox("⚖️ Violation", col_options("violation"))

if "driver_age" in df.columns and df["driver_age"].notna().any():
    min_age = int(df["driver_age"].min())
    max_age = int(df["driver_age"].max())
else:
    min_age, max_age = 16, 90

age_range = st.sidebar.slider("🎂 Driver Age Range", min_age, max_age, (min_age, max_age))

# Apply filters
filtered = df.copy()
if "driver_age" in filtered.columns:
    filtered = filtered[filtered["driver_age"].between(age_range[0], age_range[1])]
if sel_country != "All" and "country_name" in filtered.columns:
    filtered = filtered[filtered["country_name"] == sel_country]
if sel_gender != "All" and "driver_gender" in filtered.columns:
    filtered = filtered[filtered["driver_gender"] == sel_gender]
if sel_race != "All" and "driver_race" in filtered.columns:
    filtered = filtered[filtered["driver_race"] == sel_race]
if sel_violation != "All" and "violation" in filtered.columns:
    filtered = filtered[filtered["violation"] == sel_violation]

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Filtered Records:** {len(filtered):,} / {len(df):,}")

# ─────────────────────────────────────────────
# TITLE
# ─────────────────────────────────────────────
st.title("🚔 SecureCheck — Police Traffic Stop Dashboard")
st.caption("Interactive analytics on police stops • Powered by Pandas + Streamlit + Plotly")

if filtered.empty:
    st.warning("⚠️ Selected filters-ku match aana records illa. Filters-ah maathi try pannunga.")
    st.stop()

# ─────────────────────────────────────────────
# KPI METRICS
# ─────────────────────────────────────────────
total_stops = len(filtered)
arrest_rate = round(100 * filtered["is_arrested"].mean(), 2) if "is_arrested" in filtered.columns else 0
search_rate = round(100 * filtered["search_conducted"].mean(), 2) if "search_conducted" in filtered.columns else 0
drug_rate = round(100 * filtered["drugs_related_stop"].mean(), 2) if "drugs_related_stop" in filtered.columns else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("🚦 Total Stops", f"{total_stops:,}")
c2.metric("🔒 Arrest Rate", f"{arrest_rate}%")
c3.metric("🔍 Search Rate", f"{search_rate}%")
c4.metric("💊 Drug Stop Rate", f"{drug_rate}%")

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
    st.subheader("Top 10 Vehicles in Drug-Related Stops")

    drug_veh = (
        filtered[filtered["drugs_related_stop"] == 1]
        .groupby("vehicle_number")
        .size()
        .reset_index(name="drug_stop_count")
        .sort_values("drug_stop_count", ascending=False)
        .head(10)
    )

    if not drug_veh.empty:
        fig = px.bar(
            drug_veh, x="vehicle_number", y="drug_stop_count",
            color="drug_stop_count", color_continuous_scale="Blues",
            labels={"vehicle_number": "Vehicle Number", "drug_stop_count": "Drug Stop Count"},
        )
        fig.update_layout(template="plotly_dark", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        top = drug_veh.iloc[0]
        if drug_veh["drug_stop_count"].max() <= 1:
            st.info("💡 Drug-related stops are evenly distributed across vehicles — enforcement is case-based, not vehicle-targeted.")
        else:
            st.info(f"💡 Vehicle **{top['vehicle_number']}** had the highest number of drug-related stops ({int(top['drug_stop_count'])}).")
    else:
        st.info("💡 Selected filters-ku drug-related stop data illa.")

    with st.expander("📋 View Data Table"):
        st.dataframe(drug_veh, use_container_width=True)

    st.subheader("Most Frequently Searched Vehicles")

    srch_veh = (
        filtered[filtered["search_conducted"] == 1]
        .groupby("vehicle_number")
        .size()
        .reset_index(name="search_count")
        .sort_values("search_count", ascending=False)
        .head(10)
    )

    if not srch_veh.empty:
        fig2 = px.bar(
            srch_veh, x="vehicle_number", y="search_count",
            color="search_count", color_continuous_scale="Oranges",
            labels={"vehicle_number": "Vehicle Number", "search_count": "Search Count"},
        )
        fig2.update_layout(template="plotly_dark", showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

        if srch_veh["search_count"].max() <= 1:
            st.info("💡 All searched vehicles appear only once — no single vehicle was repeatedly searched in the selected data.")
        else:
            top = srch_veh.iloc[0]
            st.info(f"💡 Vehicle **{top['vehicle_number']}** was searched the most ({int(top['search_count'])} times).")
    else:
        st.info("💡 Selected filters-ku search data illa.")

    with st.expander("📋 View Data Table"):
        st.dataframe(srch_veh, use_container_width=True)

# ══════════════════════════════════════════════
# TAB 2 — DEMOGRAPHICS
# ══════════════════════════════════════════════
with tabs[1]:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Arrest Rate by Age Group")

        temp = filtered.dropna(subset=["driver_age"]).copy()
        bins = [0, 17, 25, 35, 45, 55, 65, 75, 150]
        labels = ["<18", "18-25", "26-35", "36-45", "46-55", "56-65", "66-75", "76+"]
        temp["age_group"] = pd.cut(temp["driver_age"], bins=bins, labels=labels, right=True)

        age_df = (
            temp.groupby("age_group", observed=True)["is_arrested"]
            .mean()
            .mul(100)
            .round(2)
            .reset_index(name="arrest_rate")
            .sort_values("arrest_rate", ascending=False)
        )

        if not age_df.empty:
            fig = px.bar(
                age_df, x="age_group", y="arrest_rate",
                color="arrest_rate", color_continuous_scale="Reds",
                labels={"age_group": "Age Group", "arrest_rate": "Arrest Rate (%)"},
            )
            fig.update_layout(template="plotly_dark", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            top = age_df.iloc[0]
            st.info(f"💡 The **{top['age_group']}** age group has the highest arrest rate ({top['arrest_rate']}%).")

        with st.expander("📋 Data"):
            st.dataframe(age_df, use_container_width=True)

    with col2:
        st.subheader("Search Rate by Race & Gender")

        race_df = (
            filtered.groupby(["driver_race", "driver_gender"])["search_conducted"]
            .mean()
            .mul(100)
            .round(2)
            .reset_index(name="search_rate")
            .sort_values("search_rate", ascending=False)
        )

        if not race_df.empty:
            fig2 = px.bar(
                race_df, x="driver_race", y="search_rate", color="driver_gender",
                barmode="group",
                labels={"driver_race": "Race", "search_rate": "Search Rate (%)", "driver_gender": "Gender"},
                color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            fig2.update_layout(template="plotly_dark")
            st.plotly_chart(fig2, use_container_width=True)
            top = race_df.iloc[0]
            st.info(f"💡 **{top['driver_race']} {top['driver_gender']}** drivers show the highest vehicle search rate ({top['search_rate']}%).")

        with st.expander("📋 Data"):
            st.dataframe(race_df, use_container_width=True)

    st.subheader("Drug-Related Stops by Country & Gender")

    gender_df = (
        filtered[filtered["drugs_related_stop"] == 1]
        .groupby(["country_name", "driver_gender"])
        .size()
        .reset_index(name="gender_count")
        .sort_values("country_name")
    )

    if not gender_df.empty:
        fig3 = px.bar(
            gender_df, x="country_name", y="gender_count", color="driver_gender",
            barmode="group",
            labels={"country_name": "Country", "gender_count": "Stops", "driver_gender": "Gender"},
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig3.update_layout(template="plotly_dark")
        st.plotly_chart(fig3, use_container_width=True)

        totals_by_country = gender_df.groupby("country_name")["gender_count"].sum()
        top_country = totals_by_country.idxmax()
        top_row = gender_df[gender_df["country_name"] == top_country].sort_values("gender_count", ascending=False).iloc[0]
        st.info(f"💡 **{top_country}** shows the highest drug-related stops, with **{top_row['driver_gender']}** drivers leading there.")
    else:
        st.info("💡 Selected filters-ku drug-related stop data illa.")

    with st.expander("📋 Data"):
        st.dataframe(gender_df, use_container_width=True)

# ══════════════════════════════════════════════
# TAB 3 — TIME & DURATION
# ══════════════════════════════════════════════
with tabs[2]:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Traffic Stops by Hour of Day")

        hour_df = (
            filtered.dropna(subset=["stop_hour"])
            .groupby("stop_hour")
            .size()
            .reset_index(name="total_stops")
            .sort_values("stop_hour")
        )
        hour_df["stop_hour"] = hour_df["stop_hour"].astype(int)

        if not hour_df.empty:
            fig = px.bar(
                hour_df, x="stop_hour", y="total_stops",
                color="total_stops", color_continuous_scale="Viridis",
                labels={"stop_hour": "Hour (0-23)", "total_stops": "Total Stops"},
            )
            fig.update_layout(template="plotly_dark", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            peak = hour_df.sort_values("total_stops", ascending=False).iloc[0]
            st.info(f"💡 Peak traffic stops occur around **{int(peak['stop_hour'])}:00** hrs.")
        else:
            st.info("💡 Datetime information illa, hourly analysis seiya mudiyala.")

        with st.expander("📋 Data"):
            st.dataframe(hour_df, use_container_width=True)

    with col2:
        st.subheader("Day vs Night Arrest Rate")

        temp = filtered.dropna(subset=["stop_hour"]).copy()
        temp["time_period"] = temp["stop_hour"].apply(lambda h: "Day" if 6 <= h <= 17 else "Night")

        night_df = (
            temp.groupby("time_period")
            .agg(
                total_stops=("is_arrested", "size"),
                total_arrests=("is_arrested", "sum"),
                arrest_rate=("is_arrested", lambda x: round(100 * x.mean(), 2)),
            )
            .reset_index()
        )

        if not night_df.empty:
            fig2 = px.pie(
                night_df, names="time_period", values="arrest_rate",
                color_discrete_sequence=["#4f8ef7", "#f7c94f"], hole=0.45,
            )
            fig2.update_layout(template="plotly_dark")
            st.plotly_chart(fig2, use_container_width=True)
            top = night_df.sort_values("arrest_rate", ascending=False).iloc[0]
            st.info(f"💡 **{top['time_period']}** stops have a higher arrest rate ({top['arrest_rate']}%).")
        else:
            st.info("💡 Datetime information illa, day/night analysis seiya mudiyala.")

        with st.expander("📋 Data"):
            st.dataframe(night_df, use_container_width=True)

    st.subheader("Stop Duration by Violation Type")

    if "stop_duration" in filtered.columns:
        dur_df = (
            filtered.groupby(["violation", "stop_duration"])
            .size()
            .reset_index(name="total_stop")
            .sort_values("violation")
        )

        if not dur_df.empty:
            fig3 = px.bar(
                dur_df, x="violation", y="total_stop", color="stop_duration",
                barmode="group",
                labels={"violation": "Violation", "total_stop": "Number of Stops", "stop_duration": "Duration"},
                color_discrete_sequence=px.colors.qualitative.Bold,
            )
            fig3.update_layout(template="plotly_dark")
            st.plotly_chart(fig3, use_container_width=True)

            longest = dur_df.sort_values("total_stop", ascending=False).iloc[0]
            st.info(f"💡 **{longest['violation']}** violations have the most stops recorded with **{longest['stop_duration']}** duration.")

        with st.expander("📋 Data"):
            st.dataframe(dur_df, use_container_width=True)
    else:
        st.info("💡 'stop_duration' column dataset-la illa.")

# ══════════════════════════════════════════════
# TAB 4 — VIOLATIONS
# ══════════════════════════════════════════════
with tabs[3]:
    st.subheader("Search & Arrest Rate by Violation")

    viol_df = (
        filtered.groupby("violation")
        .agg(
            search_rate=("search_conducted", lambda x: round(100 * x.mean(), 2)),
            arrest_rate=("is_arrested", lambda x: round(100 * x.mean(), 2)),
        )
        .reset_index()
        .sort_values("arrest_rate", ascending=False)
    )

    if not viol_df.empty:
        fig = px.bar(
            viol_df, x="violation", y=["search_rate", "arrest_rate"],
            barmode="group",
            labels={"violation": "Violation", "value": "Rate (%)", "variable": "Metric"},
            color_discrete_map={"search_rate": "#4f8ef7", "arrest_rate": "#f75e4f"},
        )
        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
        top = viol_df.iloc[0]
        st.info(f"💡 **{top['violation']}** violations show the highest arrest rate ({top['arrest_rate']}%).")

    with st.expander("📋 Data"):
        st.dataframe(viol_df, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Violations Among Drivers Under 25")

        young_df = (
            filtered[filtered["driver_age"] < 25]
            .groupby("violation")
            .size()
            .reset_index(name="violation_count")
            .sort_values("violation_count", ascending=False)
        )

        if not young_df.empty:
            fig2 = px.pie(
                young_df, names="violation", values="violation_count",
                color_discrete_sequence=px.colors.qualitative.Set3, hole=0.3,
            )
            fig2.update_layout(template="plotly_dark")
            st.plotly_chart(fig2, use_container_width=True)
            st.info(f"💡 **{young_df.iloc[0]['violation']}** is the most common violation among drivers under 25.")
        else:
            st.info("💡 Selected filters-ku 25 vayasukku keezha drivers data illa.")

        with st.expander("📋 Data"):
            st.dataframe(young_df, use_container_width=True)

    with col2:
        st.subheader("Violation Ranking — Search vs Arrest")

        rank_df = viol_df.copy()
        if not rank_df.empty:
            rank_df["search_rank"] = rank_df["search_rate"].rank(ascending=False, method="min").astype(int)
            rank_df["arrest_rank"] = rank_df["arrest_rate"].rank(ascending=False, method="min").astype(int)

            fig3 = px.scatter(
                rank_df, x="search_rank", y="arrest_rank",
                text="violation", size="search_rate",
                color="arrest_rate", color_continuous_scale="RdYlGn_r",
                labels={"search_rank": "Search Rank", "arrest_rank": "Arrest Rank"},
            )
            fig3.update_traces(textposition="top center")
            fig3.update_layout(template="plotly_dark")
            st.plotly_chart(fig3, use_container_width=True)
            st.info("💡 Violations closer to rank (1, 1) face both the highest search & arrest enforcement.")

        with st.expander("📋 Data"):
            st.dataframe(rank_df, use_container_width=True)

# ══════════════════════════════════════════════
# TAB 5 — LOCATION
# ══════════════════════════════════════════════
with tabs[4]:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Drug-Related Stop Rate by Country")

        drug_cntry = (
            filtered.groupby("country_name")["drugs_related_stop"]
            .mean()
            .mul(100)
            .round(2)
            .reset_index(name="drug_stop_rate")
            .sort_values("drug_stop_rate", ascending=False)
        )

        if not drug_cntry.empty:
            fig = px.bar(
                drug_cntry, x="country_name", y="drug_stop_rate",
                color="drug_stop_rate", color_continuous_scale="Reds",
                labels={"country_name": "Country", "drug_stop_rate": "Drug Stop Rate (%)"},
            )
            fig.update_layout(template="plotly_dark", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            top = drug_cntry.iloc[0]
            st.info(f"💡 **{top['country_name']}** has the highest rate of drug-related traffic stops ({top['drug_stop_rate']}%).")

        with st.expander("📋 Data"):
            st.dataframe(drug_cntry, use_container_width=True)

    with col2:
        st.subheader("Searches Conducted by Country")

        srch_cntry = (
            filtered[filtered["search_conducted"] == 1]
            .groupby("country_name")
            .size()
            .reset_index(name="search_count")
            .sort_values("search_count", ascending=False)
        )

        if not srch_cntry.empty:
            fig2 = px.pie(
                srch_cntry, names="country_name", values="search_count",
                color_discrete_sequence=px.colors.qualitative.Pastel, hole=0.4,
            )
            fig2.update_layout(template="plotly_dark")
            st.plotly_chart(fig2, use_container_width=True)
            st.info(f"💡 **{srch_cntry.iloc[0]['country_name']}** leads in the number of stops where a search was conducted.")
        else:
            st.info("💡 Selected filters-ku search data illa.")

        with st.expander("📋 Data"):
            st.dataframe(srch_cntry, use_container_width=True)

    st.subheader("Top 10 Arrest Rates by Country & Violation")

    arr_cntry = (
        filtered.groupby(["country_name", "violation"])
        .agg(
            total_stops=("is_arrested", "size"),
            arrest_rate=("is_arrested", lambda x: round(100 * x.mean(), 2)),
        )
        .reset_index()
        .sort_values("arrest_rate", ascending=False)
        .head(10)
    )

    if not arr_cntry.empty:
        fig3 = px.bar(
            arr_cntry, x="violation", y="arrest_rate", color="country_name",
            barmode="group",
            labels={"violation": "Violation", "arrest_rate": "Arrest Rate (%)", "country_name": "Country"},
            color_discrete_sequence=px.colors.qualitative.Vivid,
        )
        fig3.update_layout(template="plotly_dark")
        st.plotly_chart(fig3, use_container_width=True)
        top = arr_cntry.iloc[0]
        st.info(f"💡 **{top['country_name']} – {top['violation']}** has the highest arrest rate ({top['arrest_rate']}%).")

    with st.expander("📋 Data"):
        st.dataframe(arr_cntry, use_container_width=True)

# ══════════════════════════════════════════════
# TAB 6 — ADVANCED / CUSTOM QUERY
# ══════════════════════════════════════════════
with tabs[5]:
    st.subheader("Top 10 Vehicles by Total Stops")

    veh_total = (
        filtered.groupby("vehicle_number")
        .size()
        .reset_index(name="total_stops")
        .sort_values("total_stops", ascending=False)
        .head(10)
    )

    if not veh_total.empty:
        fig = px.bar(
            veh_total, x="vehicle_number", y="total_stops",
            color="total_stops", color_continuous_scale="Purples",
            labels={"vehicle_number": "Vehicle Number", "total_stops": "Total Stops"},
        )
        fig.update_layout(template="plotly_dark", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        top = veh_total.iloc[0]
        st.info(f"💡 Vehicle **{top['vehicle_number']}** had the most total stops ({int(top['total_stops'])}).")

    with st.expander("📋 Data"):
        st.dataframe(veh_total, use_container_width=True)

    st.markdown("---")
    st.subheader("🔧 Build Your Own Query")
    st.caption("Group-by column-um, metric-um select pannunga — chart matrum table automatic-aa update aagum.")

    categorical_cols = [
        c for c in ["country_name", "driver_gender", "driver_race", "violation", "stop_duration", "vehicle_number"]
        if c in filtered.columns
    ]

    metric_options = {
        "Total Stops": None,
        "Arrest Rate (%)": "is_arrested",
        "Search Rate (%)": "search_conducted",
        "Drug Stop Rate (%)": "drugs_related_stop",
    }

    qcol1, qcol2 = st.columns(2)
    with qcol1:
        group_col = st.selectbox("Group by", categorical_cols, key="group_col")
    with qcol2:
        metric_label = st.selectbox("Metric", list(metric_options.keys()), key="metric_label")

    metric_col = metric_options[metric_label]

    if metric_col is None:
        custom_df = (
            filtered.groupby(group_col)
            .size()
            .reset_index(name="Total Stops")
            .sort_values("Total Stops", ascending=False)
            .head(15)
        )
        y_col = "Total Stops"
    else:
        custom_df = (
            filtered.groupby(group_col)[metric_col]
            .mean()
            .mul(100)
            .round(2)
            .reset_index(name=metric_label)
            .sort_values(metric_label, ascending=False)
            .head(15)
        )
        y_col = metric_label

    if not custom_df.empty:
        fig_custom = px.bar(
            custom_df, x=group_col, y=y_col,
            color=y_col, color_continuous_scale="Greens",
            labels={group_col: group_col.replace("_", " ").title(), y_col: y_col},
        )
        fig_custom.update_layout(template="plotly_dark", showlegend=False)
        st.plotly_chart(fig_custom, use_container_width=True)
        top = custom_df.iloc[0]
        st.info(f"💡 **{top[group_col]}** ranks highest for **{y_col}** ({top[y_col]}).")
    else:
        st.info("💡 Selected combination-ku data illa.")

    with st.expander("📋 Data"):
        st.dataframe(custom_df, use_container_width=True)

    st.markdown("---")
    st.subheader("🔎 Search by Vehicle Number")

    if "vehicle_number" in filtered.columns:
        vehicle_input = st.text_input("Vehicle number (or part of it) potturunga, athukana stops kaattum")
        if vehicle_input:
            veh_records = filtered[
                filtered["vehicle_number"].astype(str).str.contains(vehicle_input, case=False, na=False)
            ]
            st.write(f"**{len(veh_records)}** matching record(s) found.")
            st.dataframe(veh_records, use_container_width=True)
    else:
        st.info("💡 'vehicle_number' column dataset-la illa.")
