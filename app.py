import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import pytz

# -------------------------
# PAGE CONFIG
# -------------------------
st.set_page_config(layout="wide")
st.title("🌍 LEMS Smart Monitoring Dashboard")

# Auto refresh every 5 seconds
st.autorefresh(interval=5000, key="auto_refresh")

# -------------------------
# FIREBASE INITIALIZATION
# -------------------------
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_key.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

# -------------------------
# DATA FETCH FUNCTION
# -------------------------
def fetch_data_for_date(date_str):

    readings = (
        db.collection("sensor_data")
        .document(date_str)
        .collection("readings")
        .order_by("timestamp")
        .stream()
    )

    data = [doc.to_dict() for doc in readings]

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    # Convert timestamp
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")

    # Create readable time column
    df["time_only"] = df["timestamp"].dt.strftime("%H:%M:%S")

    # Set as index for graph x-axis
    df = df.set_index("time_only")

    return df

# -------------------------
# TABS
# -------------------------
tab1, tab2 = st.tabs(["📡 Today", "📅 Select Date"])

# =========================
# TAB 1 — TODAY LIVE
# =========================
with tab1:

    st.subheader("Live Data (Updates Every 5 Seconds)")

    ist = pytz.timezone("Asia/Kolkata")
    today_str = datetime.now(ist).strftime("%Y-%m-%d")

    df_today = fetch_data_for_date(today_str)

    if df_today.empty:
        st.warning("No data found for today.")
    else:

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🌡 Temperature (°C)")
            st.line_chart(df_today["temperature"])

        with col2:
            st.markdown("### 🌫 AQI")
            st.line_chart(df_today["aqi"])

# =========================
# TAB 2 — SELECT DATE
# =========================
with tab2:

    st.subheader("View Historical Data")

    selected_date = st.date_input("Choose Date")

    if selected_date:

        selected_str = selected_date.strftime("%Y-%m-%d")

        df_selected = fetch_data_for_date(selected_str)

        if df_selected.empty:
            st.warning("No data found for this date.")
        else:

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### 🌡 Temperature (°C)")
                st.line_chart(df_selected["temperature"])

            with col2:
                st.markdown("### 🌫 AQI")
                st.line_chart(df_selected["aqi"])
