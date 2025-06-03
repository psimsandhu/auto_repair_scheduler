import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from openai import OpenAI
import os
import csv
from datetime import date
import random

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
BOOKING_FILE = "bookings.csv"

# Session state setup
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are Auto Buddy, a friendly and helpful auto repair assistant. You help users understand car problems, diagnose SAE P-codes if mentioned, suggest DIY or shop repairs, and schedule service if needed."}
    ]
if "last_reply" not in st.session_state:
    st.session_state.last_reply = ""
if "booking_mode" not in st.session_state:
    st.session_state.booking_mode = False

# Chatbot call
def ask_auto_buddy(prompt):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=st.session_state.messages + [{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# UI
st.title("🚘 Auto Buddy: Your Car's Best Friend")
st.markdown("Describe your car issue or ask for help. Auto Buddy will guide you through diagnosis and repair.")

# Chat input
user_input = st.chat_input("What's going on with your car?")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.spinner("Auto Buddy is thinking..."):
        reply = ask_auto_buddy(user_input)
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.session_state.last_reply = reply

# Display conversation
for msg in st.session_state.messages[1:]:
    st.chat_message(msg["role"]).write(msg["content"])

# Check if booking is recommended
if "repair at a shop" in st.session_state.last_reply.lower() or "schedule a repair" in st.session_state.last_reply.lower():
    st.subheader("🛠️ Auto Buddy recommends a shop repair.")
    if st.button("Yes, book a repair"):
        st.session_state.booking_mode = True

# Booking form
if st.session_state.booking_mode:
    st.subheader("📅 Book Your Repair Appointment")
    with st.form("booking_form"):
        cust_name = st.text_input("Your Name")
        appt_date = st.date_input("Preferred Date", min_value=date.today())
        appt_time = st.selectbox("Preferred Time", ["9:00 - 10:00", "10:00 - 11:00", "1:00 - 2:00", "2:00 - 3:00", "3:00 - 4:00"])
        submit = st.form_submit_button("Submit Request")

        if submit:
            hours = round(random.uniform(1.0, 3.0), 1)
            rate = 100
            with open(BOOKING_FILE, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([cust_name, appt_date, appt_time, "Pending", rate, hours])
            st.success("✅ Booking submitted!")
            st.info(f"Estimated Quote: {hours} hrs × ${rate}/hr = ${hours * rate:.2f}")
            st.session_state.booking_mode = False

# Check booking status
st.divider()
st.subheader("📋 Check Your Booking Status")

with st.form("status_form"):
    search_name = st.text_input("Enter your name to look up your appointment")
    check = st.form_submit_button("Check Status")

    if check:
        try:
            df = pd.read_csv(BOOKING_FILE)
            matches = df[df["Name"].str.lower() == search_name.strip().lower()]
            if matches.empty:
                st.warning("No booking found for that name.")
            else:
                for _, row in matches.iterrows():
                    st.markdown(f"""
                    **Date**: {row['Date']}  
                    **Time**: {row['Time Slot']}  
                    **Status**: {row['Status']}  
                    **Quote**: {row['Estimated Hours']} hrs × ${row['Labor Rate ($/hr)']} = ${row['Estimated Hours'] * row['Labor Rate ($/hr)']:.2f}
                    """)
        except FileNotFoundError:
            st.error("No bookings have been made yet.")
