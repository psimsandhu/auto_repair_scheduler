import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from openai import OpenAI
import os

# OpenAI setup
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load schedule from Excel
@st.cache_data
def load_schedule(file):
    return pd.read_excel(file)

# Look up P-code description from PDF
def lookup_pcode_description(pcode, pdf_path):
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text = page.get_text()
            if pcode in text:
                start = text.find(pcode)
                end = text.find('\n', start)
                return text[start:end].strip()
    return "No description found for this P-code."
    import csv
from datetime import date

# Booking input UI
st.divider()
st.subheader("🗓️ Schedule a Repair")

with st.form("booking_form"):
    cust_name = st.text_input("Your Name")
    appt_date = st.date_input("Preferred Date", min_value=date.today())
    appt_time = st.selectbox("Preferred Time", ["9:00 - 10:00", "10:00 - 11:00", "1:00 - 2:00", "2:00 - 3:00", "3:00 - 4:00"])
    submit = st.form_submit_button("Submit Request")

    if submit:
        hours = round(random.uniform(1.0, 3.0), 1)
        rate = 100
        with open("bookings.csv", "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([cust_name, appt_date, appt_time, "Pending", rate, hours])
        st.success("✅ Your request has been submitted.")
        st.info(f"Estimated Quote: {hours} hrs × ${rate}/hr = ${hours * rate}")


# Initialize session for chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are Auto Buddy, a friendly and helpful auto repair assistant. You help users understand car problems, diagnose SAE P-codes if mentioned, suggest DIY or shop repairs, and schedule service if needed."}
    ]

# UI Header
st.title("🚘 Auto Buddy: Your Car's Best Friend")
st.markdown("Describe your car issue, ask about a fault code, or get repair help:")

# Chat input
user_input = st.chat_input("What's going on with your car?")

if user_input:
    # Append user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.spinner("Auto Buddy is thinking..."):
        response = client.chat.completions.create(
            model="gpt-4",
            messages=st.session_state.messages
        )
        reply = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": reply})

# Display chat history
for msg in st.session_state.messages[1:]:
    st.chat_message(msg["role"]).write(msg["content"])

# Offer scheduling section
st.divider()
st.subheader("🗓️ Need a Repair?")

if st.button("Check Available Slots"):
    schedule = load_schedule("Weekly Shop Schedule.xlsx")
    st.dataframe(schedule)
    if st.button("Confirm Appointment"):
        st.success("✅ Appointment scheduled! We’ll see you soon.")
