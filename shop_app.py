import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime
import json

BOOKING_FILE = "bookings.csv"

@st.cache_data
def load_bookings():
    try:
        df = pd.read_csv(BOOKING_FILE)
        return df
    except FileNotFoundError:
        return pd.DataFrame(columns=[
            "Name", "Date", "Time Slot", "Status", "Labor Rate ($/hr)", "Estimated Hours"
        ])

def save_bookings(df):
    df.to_csv(BOOKING_FILE, index=False)

st.title("🔧 Shop Booking Manager")

df = load_bookings()

st.subheader("📅 Booking Calendar")

# Convert to calendar events
def to_event(row, idx):
    start_time, end_time = row["Time Slot"].split(" - ")
    return {
        "id": idx,
        "title": f"{row['Name']} (${row['Estimated Hours']}h)",
        "start": f"{row['Date']}T{start_time}:00",
        "end": f"{row['Date']}T{end_time}:00",
        "color": "green" if row["Status"].lower() == "accepted" else "orange",
        "extendedProps": {
            "Name": row["Name"],
            "Date": row["Date"],
            "Slot": row["Time Slot"],
            "Status": row["Status"],
            "Quote": row["Estimated Hours"] * row["Labor Rate ($/hr)"]
        }
    }

events = [to_event(r, idx) for idx, r in df.iterrows()]
event_data = calendar(events=events, options={"initialView": "timeGridWeek"})

# Post-interaction
if event_data and "event" in event_data and event_data["event"]:
    e = event_data["event"]
    selected_idx = int(e["id"])
    selected = df.iloc[selected_idx]
    st.markdown(f"### 📋 Booking Details")
    st.write(f"**Customer**: {selected['Name']}")
    st.write(f"**Date**: {selected['Date']} | **Time**: {selected['Time Slot']}")
    st.write(f"**Quote**: {selected['Estimated Hours']} hrs × ${selected['Labor Rate ($/hr)']} = ${selected['Estimated Hours'] * selected['Labor Rate ($/hr)']:.2f}")
    st.write(f"**Status**: {selected['Status']}")

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
