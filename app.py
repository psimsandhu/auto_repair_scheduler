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

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": (
            "You are Auto Buddy, a friendly and helpful auto repair assistant. "
            "You diagnose SAE P-codes and car issues based on the user's vehicle details. "
            "You recommend DIY or shop repair, and if shop repair is needed, prompt to schedule it."
        )}
    ]
if "booking_mode" not in st.session_state:
    st.session_state.booking_mode = False
if "user_info" not in st.session_state:
    st.session_state.user_info = {}
if "vehicle_info" not in st.session_state:
    st.session_state.vehicle_info = {}

# Load shop availability
def get_available_slots():
    try:
        df = pd.read_excel(SCHEDULE_FILE)
        return df[df["Status"].str.lower() == "available"]
    except:
        return pd.DataFrame()

# Ask OpenAI
def ask_auto_buddy(prompt):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=st.session_state.messages + [{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# App UI
st.title("🚘 Auto Buddy")
st.markdown("Friendly car diagnosis + repair scheduling assistant.")

# Get user info
if not st.session_state.user_info:
    with st.form("user_info_form"):
        name = st.text_input("Your Name")
        email = st.text_input("Your Email")
        submit = st.form_submit_button("Start")
        if submit and name and email:
            st.session_state.user_info = {"name": name, "email": email}
            st.rerun()

# Get vehicle info
if st.session_state.user_info and not st.session_state.vehicle_info:
    with st.form("vehicle_form"):
        year = st.text_input("Vehicle Year")
        make = st.text_input("Make")
        model = st.text_input("Model")
        issue = st.text_area("Describe your issue or fault code")
        submit = st.form_submit_button("Submit")
        if submit and year and make and model and issue:
            st.session_state.vehicle_info = {
                "year": year, "make": make, "model": model, "issue": issue
            }
            prompt = f"My {year} {make} {model} is having this issue: {issue}"
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.spinner("Auto Buddy is analyzing your issue..."):
                reply = ask_auto_buddy(prompt)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.session_state.last_reply = reply.lower()
            st.rerun()

# Chat + results
if st.session_state.vehicle_info:
    for msg in st.session_state.messages[1:]:
        st.chat_message(msg["role"]).write(msg["content"])

    # Check if shop repair is advised
    if "repair at a shop" in st.session_state.get("last_reply", "") or "schedule a repair" in st.session_state.get("last_reply", ""):
        st.subheader("🔧 Auto Buddy recommends a shop repair.")
        if st.button("See Available Appointments"):
            st.session_state.booking_mode = True

# Booking form
if st.button("Confirm Booking"):
    row = available.iloc[available.index[available["Day"] + " - " + available["Time Slot"] == selected][0]]
    hours = round(random.uniform(1.0, 3.0), 1)
    rate = 100
    date_str = f"2025-{['Monday','Tuesday','Wednesday','Thursday','Friday'].index(row['Day'])+9:02d}"
    with open("bookings.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            st.session_state.user_info["name"],
            date_str,
            row["Time Slot"],
            "Pending",
            rate,
            hours
        ])
    st.success("✅ Booking submitted!")
    st.info(f"Quote: {hours} hrs × ${rate} = ${hours * rate:.2f}")
    st.session_state.booking_mode = False
