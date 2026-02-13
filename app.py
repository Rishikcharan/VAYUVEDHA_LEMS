import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
from datetime import datetime
import time

# ---------------- FIRESTORE INIT ----------------
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

st.set_page_config(layout="wide")
st.title("🌍 LEMS Smart Monitoring Dashboard")

# ---------------- Helper Function ----------------
def fetch_data_for_date(date_str):
    readings = db.collection("sensor_data") \
                 .document(date_str) \
                 .collection("readings") \
                 .stream()

    data = [doc.to_dict() for doc in readings]
    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")
    df = df.set_index("timestamp")
    return df

# ---------------- Tabs ----------------
tab1, tab2 = st.tabs(["📅 Today", "📁 Past Days"])

# ====================================================
# =================== TODAY TAB ======================
# ====================================================
with tab1:
    st.subheader("Live Data (Updates every 5 seconds)")

    placeholder = st.empty()

    while True:
        today_str = datetime.now().strftime("%Y-%m-%d")
        df_today = fetch_data_for_date(today_str)

        with placeholder.container():
            if df_today.empty:
                st.write("No data yet for today.")
            else:
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("🌡 Temperature")
                    st.line_chart(df_today["temperature"])

                with col2:
                    st.subheader("🌫 AQI")
                    st.line_chart(df_today["aqi"])

        time.sleep(5)
        st.rerun()

# ====================================================
# ================= PAST DAYS TAB ====================
# ====================================================
with tab2:
    st.subheader("View Previous Days Data")

    # Get available dates only once
    @st.cache_data
    def get_available_dates():
        docs = db.collection("sensor_data").stream()
        return sorted([doc.id for doc in docs], reverse=True)

    dates = get_available_dates()

    if not dates:
        st.write("No stored data available.")
    else:
        selected_date = st.selectbox("Select Date", dates)

        # Cache each date data separately
        @st.cache_data
        def load_past_data(date_str):
            return fetch_data_for_date(date_str)

        df_past = load_past_data(selected_date)

        if df_past.empty:
            st.write("No data for selected date.")
        else:
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("🌡 Temperature")
                st.line_chart(df_past["temperature"])

            with col2:
                st.subheader("🌫 AQI")
                st.line_chart(df_past["aqi"])
