import streamlit as st
import pandas as pd

BOOKING_FILE = "bookings.csv"

@st.cache_data
def load_bookings():
    try:
        return pd.read_csv(BOOKING_FILE)
    except FileNotFoundError:
        return pd.DataFrame(columns=["Name", "Date", "Time Slot", "Status", "Labor Rate ($/hr)", "Estimated Hours"])

def save_bookings(df):
    df.to_csv(BOOKING_FILE, index=False)

st.title("🔧 Shop Booking Manager")
df = load_bookings()

st.write("📋 All Bookings:", df)  # Debug print

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
            st.success(f"Accepted booking for {row['Name']}")
        if col2.button(f"❌ Deny", key=f"deny_{idx}"):
            df.at[idx, "Status"] = "Denied"
            save_bookings(df)
            st.error(f"Denied booking for {row['Name']}")

