import streamlit as st
import pandas as pd
import os
import csv
import random
import yagmail
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

APP_ROOT = os.path.dirname(__file__)
BOOKING_FILE = os.path.join(APP_ROOT, "bookings.csv")
SCHEDULE_FILE = os.path.join(APP_ROOT, "Weekly Shop Schedule.xlsx")
FEEDBACK_FILE = os.path.join(APP_ROOT, "repair_feedback.csv")

def send_confirmation_email(to, date, slot, quote):
    user = os.getenv("EMAIL_USER")
    try:
        yag = yagmail.SMTP(user)
        subject = "Auto Buddy Booking Confirmation"
        body = f"""
        Hello!

        Your repair appointment is confirmed for {date} at {slot}.
        Estimated quote: ${quote:.2f}

        Thank you for using Auto Buddy!
        """
        yag.send(to=to, subject=subject, contents=body)
        return True
    except Exception as e:
        st.error(f"Email failed: {e}")
        return False

def get_available_slots():
    try:
        df = pd.read_excel(SCHEDULE_FILE)
        df["slot_label"] = df["Date"].astype(str) + " - " + df["Day"] + " - " + df["Time Slot"]
        return df[df["Status"].str.lower() == "available"]
    except Exception as e:
        st.error(f"Schedule file error: {e}")
        return pd.DataFrame()

def ask_auto_buddy(prompt):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=st.session_state.messages + [{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def save_feedback(user, date, slot, resolved, comments):
    with open(FEEDBACK_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([user["name"], user["email"], date, slot, resolved, comments])

# Session state init
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": (
        "You are Auto Buddy, a friendly and helpful auto repair assistant. "
        "You diagnose SAE P-codes and car issues based on the user's vehicle details. "
        "You recommend DIY or shop repair, and offer to schedule shop service."
    )}]
if "booking_mode" not in st.session_state:
    st.session_state.booking_mode = False
if "user_info" not in st.session_state:
    st.session_state.user_info = {}
if "vehicle_info" not in st.session_state:
    st.session_state.vehicle_info = {}

st.title("🚘 Auto Buddy")
st.markdown("Your friendly car diagnosis + repair scheduling assistant.")

# Step 1: user info
if not st.session_state.user_info:
    with st.form("user_info_form"):
        name = st.text_input("Your Name")
        email = st.text_input("Your Email")
        if st.form_submit_button("Start"):
            if name and email:
                st.session_state.user_info = {"name": name, "email": email}
                st.rerun()

# Step 2: feedback
if st.session_state.user_info:
    st.subheader("🛠️ Was your vehicle issue resolved?")
    try:
        df_bookings = pd.read_csv(BOOKING_FILE)
        matches = df_bookings[
            (df_bookings["Name"] == st.session_state.user_info["name"])
        ]
        if matches.empty:
            st.info("No prior bookings found.")
        else:
            options = matches.apply(lambda r: f"{r['Date']} at {r['Time Slot']}", axis=1)
            selected = st.selectbox("Choose appointment", options)
            row = matches.iloc[options.index(selected)]
            resolved = st.radio("Was the issue fixed?", ["Yes", "No"])
            comment = st.text_area("Any feedback?")
            if st.button("Submit Feedback"):
                save_feedback(
                    st.session_state.user_info,
                    row["Date"],
                    row["Time Slot"],
                    resolved,
                    comment
                )
                st.success("Thanks for your feedback!")
    except:
        st.warning("No booking data available yet.")

# Step 3: vehicle info
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
                prompt = f"My {year} {make} {model} is having this issue: {issue}"
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.spinner("Auto Buddy is analyzing your issue..."):
                    reply = ask_auto_buddy(prompt)
                st.session_state.messages.append({"role": "assistant", "content": reply})
                st.rerun()

# Step 4: chatbot
if st.session_state.vehicle_info:
    for msg in st.session_state.messages[1:]:
        st.chat_message(msg["role"]).write(msg["content"])

    user_input = st.chat_input("Ask a follow-up or request a repair...")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.spinner("Auto Buddy is thinking..."):
            reply = ask_auto_buddy(user_input)
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()

    if not st.session_state.booking_mode:
        st.subheader("🔧 Would you like help scheduling a repair?")
        if st.button("Schedule an Appointment"):
            st.session_state.booking_mode = True
            st.rerun()

# Step 5: booking mode
if st.session_state.booking_mode:
    st.subheader("📅 Book Your Appointment")
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
            st.success("✅ Booking submitted!")
            st.info(f"Quote: {hours} hrs × ${rate} = ${hours * rate:.2f}")
            send_confirmation_email(
                st.session_state.user_info["email"],
                row["Date"],
                row["Time Slot"],
                hours * rate
            )
            st.session_state.booking_mode = False
