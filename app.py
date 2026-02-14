import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import json
import pytz

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(layout="wide")
st.title("🌍 LEMS Smart Monitoring Dashboard")

# Inject meta refresh (reload every 5 seconds)
st.markdown("<meta http-equiv='refresh' content='5'>", unsafe_allow_html=True)

# =========================================================
# FIREBASE INITIALIZATION
# =========================================================
if not firebase_admin._apps:
    cred = credentials.Certificate(
        json.loads(st.secrets["firebase_key"])
    )
    firebase_admin.initialize_app(cred)

db = firestore.client()


# =========================================================
# DATA FETCH FUNCTION
# =========================================================
def fetch_data_for_date(date_str):
    readings = (
        db.collection("history")
        .document(date_str)
        .collection("readings")
        .order_by("time")
        .stream()
    )

    data = [doc.to_dict() for doc in readings]

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    # Convert Firestore timestamp field to IST
    if "time" in df.columns:
        ist = pytz.timezone("Asia/Kolkata")
        df["time"] = pd.to_datetime(df["time"]).dt.tz_convert(ist)
        df = df.sort_values("time")
        df["time_only"] = df["time"].dt.strftime("%H:%M:%S")
        df = df.set_index("time_only")

    return df

# =========================================================
# TABS
# =========================================================
tab1, tab2 = st.tabs(["📡 Today", "📅 Select Date"])

# =========================================================
# TODAY TAB
# =========================================================
with tab1:
    st.subheader("Today's Data")

    ist = pytz.timezone("Asia/Kolkata")
    today_str = datetime.now(ist).strftime("%Y-%m-%d")

    df_today = fetch_data_for_date(today_str)

    if df_today.empty:
        st.warning("No data found for today.")
    else:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🌡 Temperature (°C)")
            st.line_chart(df_today["temp"], use_container_width=True)

        with col2:
            st.markdown("### 🌫 AQI")
            st.line_chart(df_today["aqi"], use_container_width=True)

# =========================================================
# SELECT DATE TAB
# =========================================================
with tab2:
    selected_date = st.date_input("Choose Date")

    if selected_date:
        selected_str = selected_date.strftime("%Y-%m-%d")
        df_selected = fetch_data_for_date(selected_str)

        if df_selected.empty:
            st.warning("No data found.")
        else:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"### 🌡 Temperature (°C) — {selected_str}")
                st.line_chart(df_selected["temp"], use_container_width=True)

            with col2:
                st.markdown(f"### 🌫 AQI — {selected_str}")
                st.line_chart(df_selected["aqi"], use_container_width=True)

            # CSV download option
            csv = df_selected.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download this day's data as CSV",
                data=csv,
                file_name=f"{selected_str}_sensor_data.csv",
                mime="text/csv",
            )
