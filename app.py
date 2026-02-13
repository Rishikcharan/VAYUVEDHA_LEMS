import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
from datetime import datetime
import json
import time
import pytz

# =========================================================
# ---------------- PAGE CONFIG -----------------------------
# =========================================================
st.set_page_config(layout="wide")
st.title("🌍 LEMS Smart Monitoring Dashboard")
# Auto refresh every 5 seconds
st.autorefresh(interval=5000, key="auto_refresh")

# =========================================================
# ---------------- FIREBASE INIT --------------------------
# =========================================================
if not firebase_admin._apps:
    cred = credentials.Certificate(
        json.loads(st.secrets["firebase_key"])
    )
    firebase_admin.initialize_app(cred)

db = firestore.client()

# =========================================================
# ---------------- DATA FETCH FUNCTION --------------------
# =========================================================
def fetch_data_for_date(date_str):

    readings = db.collection("sensor_data") \
                 .document(date_str) \
                 .collection("readings") \
                 .order_by("timestamp") \
                 .stream()

    data = [doc.to_dict() for doc in readings]

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")

    df["time_only"] = df["timestamp"].dt.strftime("%H:%M:%S")
    df = df.set_index("time_only")

    return df




# =========================================================
# ---------------- TABS -----------------------------------
# =========================================================
tab1, tab2 = st.tabs(["📅 Today", "📁 Past Days"])

# =========================================================
# ===================== TODAY TAB =========================
# =========================================================
with tab1:

    st.subheader("Live Data (Auto Updates Every 5 Seconds)")

    ist = pytz.timezone("Asia/Kolkata")
    today_str = datetime.now(ist).strftime("%Y-%m-%d")

    df_today = fetch_data_for_date(today_str)

    if df_today.empty:
        st.warning("No data found for this date.")
    else:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🌡 Temperature")
            st.line_chart(df_today["temperature"])

        with col2:
            st.markdown("### 🌫 AQI")
            st.line_chart(df_today["aqi"])



# =========================================================
# ===================== PAST DAYS TAB =====================
# =========================================================
with tab2:

    st.subheader("View Previous Days Data")

    @st.cache_data
    def get_available_dates():
        docs = db.collection("sensor_data").stream()
        return sorted([doc.id for doc in docs], reverse=True)

    dates = get_available_dates()

    if not dates:
        st.warning("No stored data available.")
    else:
        selected_date = st.selectbox("Select Date", dates)

        df_past = fetch_data_for_date(selected_date)

        if df_past.empty:
            st.info("No data for selected date.")
        else:
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("🌡 Temperature")
                st.line_chart(df_past["temperature"])

            with col2:
                st.subheader("🌫 AQI")
                st.line_chart(df_past["aqi"])
