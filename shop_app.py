import streamlit as st
import pandas as pd
from streamlit_calendar import calendar

BOOKING_FILE = "bookings.csv"

@st.cache_data
def load_bookings():
    try:
        return pd.read_csv(BOOKING_FILE)
    except FileNotFoundError:
        return pd.DataFrame(columns=["Name", "Date", "Time Slot", "Status", "Labor Rate ($/hr)", "Estimated Hours"])

def save_bookings(df):
    df.to_csv(BOOKING_FILE, index=False)

# Load bookings
df = load_bookings()

st.title("🔧 Shop Booking Manager")

# Raw data view
with st.expander("📋 Show All Bookings"):
    st.dataframe(df)

# Convert to calendar events
def to_event(row):
    start_time = row["Time Slot"].split(" - ")[0]
    end_time = row["Time Slot"].split(" - ")[1]
    start = f"{row['Date']}T{start_time}:00"
    end = f"{row['Date']}T{end_time}:00"
    return {
        "title": f"{row['Name']} (${row['Estimated Hours']}h)",
        "start": start,
        "end": end,
        "color": "green" if row["Status"].lower() == "accepted" else "orange"
    }

st.subheader("📅 Calendar View")
events = [to_event(r) for _, r in df.iterrows()]
calendar(events=events, options={"editable": False, "initialView": "timeGridWeek"})

# Manage pending bookings
pending_df = df[df["Status"].str.lower() == "pending"]

st.subheader("⚙️ Manage Pending Bookings")
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
