import streamlit as st
import pandas as pd
from streamlit_calendar import calendar

BOOKING_FILE = "bookings.csv"

@st.cache_data
def load_bookings():
    try:
        df = pd.read_csv(BOOKING_FILE)
        st.write("🔍 Bookings loaded:", df)  # Debug line
        return df
    except FileNotFoundError:
        return pd.DataFrame(columns=[
            "Name", "Date", "Time Slot", "Status", "Labor Rate ($/hr)", "Estimated Hours"
        ])

def save_bookings(df):
    df.to_csv(BOOKING_FILE, index=False)

df = load_bookings()
st.title("🔧 Shop Booking Manager")

st.subheader("📅 Calendar View")

def to_event(row):
    start_time, end_time = row["Time Slot"].split(" - ")
    return {
        "title": f"{row['Name']} (${row['Estimated Hours']}h)",
        "start": f"{row['Date']}T{start_time}:00",
        "end": f"{row['Date']}T{end_time}:00",
        "color": "green" if row["Status"].lower() == "accepted" else "orange"
    }

events = [to_event(r) for _, r in df.iterrows()]
calendar(events=events, options={"editable": False, "initialView": "timeGridWeek"})

st.subheader("⚙️ Manage Pending Bookings")
pending_df = df[df["Status"].str.lower() == "pending"]

if pending_df.empty:
    st.info("No pending bookings.")
else:
    for idx, row in pending_df.iterrows():
        st.markdown("---")
        st.write(f"**Customer**: {row['Name']}")
        st.write(f"**Date**: {row['Date']} | **Time**: {row['Time Slot']}")
        quote = row["Estimated Hours"] * row["Labor Rate ($/hr)"]
        st.write(f"**Quote**: {row['Estimated Hours']} hrs × ${row['Labor Rate ($/hr)']} = **${quote:.2f}**")

        col1, col2 = st.columns(2)
        if col1.button(f"✅ Accept", key=f"accept_{idx}"):
            df.at[idx, "Status"] = "Accepted"
            save_bookings(df)
            st.success(f"✅ Accepted booking for {row['Name']}")
            st.rerun()
        if col2.button(f"❌ Deny", key=f"deny_{idx}"):
            df.at[idx, "Status"] = "Denied"
            save_bookings(df)
            st.error(f"❌ Denied booking for {row['Name']}")
            st.rerun()
