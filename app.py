import streamlit as st
import pandas as pd
import os
import csv
from datetime import date
import random
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

BOOKING_FILE = "bookings.csv"
SCHEDULE_FILE = "Weekly Shop Schedule.xlsx"

# Initialize session
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are Auto Buddy, a friendly and helpful auto repair assistant. You help users understand car problems, diagnose SAE P-codes if mentioned, suggest DIY or shop repairs, and schedule service if needed."}
    ]
if "booking_mode" not in st.session_state:
    st.session_state.booking_mode = False
if "user_info" not in st.session_state:
    st.session_state.user_info = {}

# Helper to get available slots
def get_available_slots():
    try:
        df = pd.read_excel(SCHEDULE_FILE)
        return df[df["Status"].str.lower() == "available"]
    except:
        return pd.DataFrame()

# OpenAI call
def ask_auto_buddy(prompt):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=st.session_state.messages + [{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# UI
st.title("🚘 Auto Buddy")
st.markdown("Your friendly car assistant. Chat to diagnose issues and book repairs!")

# First-time user form
if not st.session_state.user_info:
    with st.form("user_info_form"):
        name = st.text_input("Your Name")
        email = st.text_input("Your Email")
        submit = st.form_submit_button("Start Chat")
        if submit and name and email:
            st.session_state.user_info = {"name": name, "email": email}
            st.rerun()

# Chatbot UI
if st.session_state.user_info:
    st.success(f"Hi {st.session_state.user_info['name']} 👋")
    user_input = st.chat_input("What's going on with your car?")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.spinner("Auto Buddy is thinking..."):
            reply = ask_auto_buddy(user_input)
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.session_state.last_reply = reply = reply.lower()

    for msg in st.session_state.messages[1:]:
        st.chat_message(msg["role"]).write(msg["content"])

    # Detect shop repair suggestion
    if "repair at a shop" in st.session_state.get("last_reply", "") or "schedule a repair" in st.session_state.get("last_reply", ""):
        st.subheader("🔧 Auto Buddy recommends a shop repair.")
        if st.button("Yes, show available slots"):
            st.session_state.booking_mode = True

    # Booking interface
    if st.session_state.booking_mode:
        st.subheader("📅 Book a Repair Slot")
        available = get_available_slots()
        if available.empty:
            st.warning("No slots available.")
        else:
            selected = st.selectbox("Choose a time slot", available["Day"] + " - " + available["Time Slot"])
            confirm = st.button("Confirm Booking")

            if confirm:
                hours = round(random.uniform(1.0, 3.0), 1)
                rate = 100
                row = available.iloc[available.index[available["Day"] + " - " + available["Time Slot"] == selected][0]]
                date_str = f"2025-{['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'].index(row['Day']) + 6:02d}"  # simulated date
                with open(BOOKING_FILE, "a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        st.session_state.user_info["name"],
                        date_str,
                        row["Time Slot"],
                        "Pending",
                        rate,
                        hours
                    ])
                st.success("✅ Your repair request was submitted!")
                st.info(f"Quote: {hours} hrs × ${rate} = ${hours * rate:.2f}")
                st.session_state.booking_mode = False
