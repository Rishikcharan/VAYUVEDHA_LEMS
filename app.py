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
@st.cache_data(ttl=5)
def fetch_data_for_date(date_str):

    st.write("Fetching date:", date_str)

    readings_ref = db.collection("sensor_data") \
                     .document(date_str) \
                     .collection("readings")

    docs = list(readings_ref.stream())

    st.write("Number of documents found:", len(docs))

    if not docs:
        return pd.DataFrame()

    data = [doc.to_dict() for doc in docs]

    df = pd.DataFrame(data)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")
    df = df.set_index("timestamp")

    return df


# =========================================================
# ---------------- TABS -----------------------------------
# =========================================================
tab1, tab2 = st.tabs(["📅 Today", "📁 Past Days"])

# =========================================================
# ===================== TODAY TAB =========================
# =========================================================
with tab1:

    st.subheader("Live Data")

    ist = pytz.timezone("Asia/Kolkata")
    today_str = datetime.now(ist).strftime("%Y-%m-%d")
    st.write("Checking date:", today_str)  # Debug

    df_today = fetch_data_for_date(today_str)

    if df_today.empty:
        st.warning("No data found for this date.")
    else:
        st.success(f"Found {len(df_today)} records")

        col1, col2 = st.columns(2)

        with col1:
            st.line_chart(df_today["temperature"])

        with col2:
            st.line_chart(df_today["aqi"])

    if st.button("Refresh"):
        st.rerun()

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
