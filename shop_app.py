import streamlit as st
import pandas as pd
import os
from streamlit_calendar import calendar

APP_ROOT = os.path.dirname(__file__)
BOOKING_FILE = os.path.join(APP_ROOT, "bookings.csv")
FEEDBACK_FILE = os.path.join(APP_ROOT, "repair_feedback.csv")

@st.cache_data
def load_bookings():
    try:
        return pd.read_csv(BOOKING_FILE)
    except FileNotFoundError:
        return pd.DataFrame(columns=[
            "Name", "Date", "Time Slot", "Status", "Labor Rate ($/hr)", "Estimated Hours"
        ])

@st.cache_data
def load_feedback():
    try:
        return pd.read_csv(FEEDBACK_FILE, names=["Name", "Email", "Date", "Time Slot", "Resolved", "Comments"])
    except FileNotFoundError:
        return pd.DataFrame(columns=["Name", "Email", "Date", "Time Slot", "Resolved", "Comments"])

def save_bookings(df):
    df.to_csv(BOOKING_FILE, index=False)

st.title("🔧 Shop Booking Manager")

tab1, tab2 = st.tabs(["📅 Booking Calendar", "📝 Customer Feedback"])

with tab1:
    df = load_bookings()

    st.subheader("📋 All Bookings")
    st.dataframe(df)

    st.subheader("📅 Calendar View")

    def to_event(row, idx):
        try:
            start_hour, start_min = row["Time Slot"].split(" - ")[0].split(":")
            end_hour, end_min = row["Time Slot"].split(" - ")[1].split(":")
            date = pd.to_datetime(row["Date"]).strftime("%Y-%m-%d")
            return {
                "id": idx,
                "title": f"{row['Name']} (${row['Estimated Hours']}h)",
                "start": f"{date}T{start_hour.zfill(2)}:{start_min.zfill(2)}:00",
                "end": f"{date}T{end_hour.zfill(2)}:{end_min.zfill(2)}:00",
                "color": "green" if row["Status"].lower() == "accepted" else "orange",
                "extendedProps": {
                    "Quote": row["Estimated Hours"] * row["Labor Rate ($/hr)"],
                    "Status": row["Status"]
                }
            }
        except:
            return None

    events = [to_event(row, idx) for idx, row in df.iterrows() if to_event(row, idx)]
    event_data = calendar(events=events, options={"initialView": "timeGridWeek"})

    if event_data and "event" in event_data and event_data["event"]:
        e = event_data["event"]
        selected_idx = int(e["id"])
        selected = df.iloc[selected_idx]
        st.markdown("### 📝 Booking Details")
        st.write(f"**Customer**: {selected['Name']}")
        st.write(f"**Date**: {selected['Date']}")
        st.write(f"**Time**: {selected['Time Slot']}")
        st.write(f"**Status**: {selected['Status']}")
        st.write(f"**Quote**: ${selected['Estimated Hours'] * selected['Labor Rate ($/hr)']:.2f}")

        if selected["Status"].lower() == "pending":
            col1, col2 = st.columns(2)
            if col1.button("✅ Accept"):
                df.at[selected_idx, "Status"] = "Accepted"
                save_bookings(df)
                st.success("Booking accepted.")
                st.rerun()
            if col2.button("❌ Deny"):
                df.at[selected_idx, "Status"] = "Denied"
                save_bookings(df)
                st.error("Booking denied.")
                st.rerun()

with tab2:
    st.subheader("📝 Feedback from Customers")
    feedback = load_feedback()
    if feedback.empty:
        st.info("No feedback submitted yet.")
    else:
        st.dataframe(feedback)
