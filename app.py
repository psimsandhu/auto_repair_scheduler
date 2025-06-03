import streamlit as st
import pandas as pd
import os
import csv
import random
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

APP_ROOT = os.path.dirname(__file__)
BOOKING_FILE = os.path.join(APP_ROOT, "bookings.csv")
SCHEDULE_FILE = os.path.join(APP_ROOT, "Weekly Shop Schedule.xlsx")

def get_available_slots():
    try:
        df = pd.read_excel(SCHEDULE_FILE)
        df["slot_label"] = df["Date"].astype(str) + " - " + df["Day"] + " - " + df["Time Slot"]
        return df[df["Status"].str.lower() == "available"]
    except:
        return pd.DataFrame()

def ask_auto_buddy(prompt):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=st.session_state.messages + [{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": (
        "You are Auto Buddy, a friendly and helpful auto repair assistant. "
        "You diagnose SAE P-codes and recommend repair paths."
    )}]
if "booking_mode" not in st.session_state:
    st.session_state.booking_mode = False
if "user_info" not in st.session_state:
    st.session_state.user_info = {}
if "vehicle_info" not in st.session_state:
    st.session_state.vehicle_info = {}

# UI starts
st.title("🚘 Auto Buddy")

if not st.session_state.user_info:
    with st.form("user_info_form"):
        name = st.text_input("Your Name")
        email = st.text_input("Your Email")
        if st.form_submit_button("Start"):
            if name and email:
                st.session_state.user_info = {"name": name, "email": email}
                st.rerun()

if st.session_state.user_info and not st.session_state.vehicle_info:
    with st.form("vehicle_form"):
        year = st.text_input("Vehicle Year")
        make = st.text_input("Make")
        model = st.text_input("Model")
        issue = st.text_area("Describe your issue or fault code")
        if st.form_submit_button("Submit"):
            if year and make and model and issue:
                st.session_state.vehicle_info = {
                    "year": year, "make": make, "model": model, "issue": issue
                }
                prompt = f"My {year} {make} {model} has this issue: {issue}"
                st.session_state.messages.append({"role": "user", "content": prompt})
                reply = ask_auto_buddy(prompt)
                st.session_state.messages.append({"role": "assistant", "content": reply})
                st.rerun()

if st.session_state.vehicle_info:
    for msg in st.session_state.messages[1:]:
        st.chat_message(msg["role"]).write(msg["content"])

    user_input = st.chat_input("Ask more or request a repair...")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        reply = ask_auto_buddy(user_input)
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()

    if not st.session_state.booking_mode:
        st.subheader("🔧 Schedule a repair?")
        if st.button("Schedule an Appointment"):
            st.session_state.booking_mode = True
            st.rerun()

if st.session_state.booking_mode:
    st.subheader("📅 Choose a Time Slot")
    available = get_available_slots()
    if available.empty:
        st.warning("No slots available.")
    else:
        selected = st.selectbox("Choose a slot", available["slot_label"])
        if st.button("Confirm Booking"):
            row = available[available["slot_label"] == selected].iloc[0]
            hours = round(random.uniform(1.0, 3.0), 1)
            rate = 100
            with open(BOOKING_FILE, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    st.session_state.user_info["name"],
                    row["Date"],
                    row["Time Slot"],
                    "Pending",
                    rate,
                    hours
                ])
            st.success("Booking submitted.")
            st.info(f"Quote: {hours} hrs × ${rate} = ${hours * rate:.2f}")
            st.session_state.booking_mode = False
