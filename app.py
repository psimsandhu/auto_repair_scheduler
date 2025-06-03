import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from openai import OpenAI
import os

# OpenAI setup using modern SDK
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load schedule from Excel
@st.cache_data
def load_schedule(file):
    return pd.read_excel(file)

# Lookup fault code in PDF
def lookup_pcode_description(pcode, pdf_path):
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text = page.get_text()
            if pcode in text:
                start = text.find(pcode)
                end = text.find('\n', start)
                return text[start:end].strip()
    return "No description found for this P-code."

# Chatbot response
def ask_auto_buddy(prompt):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are Auto Buddy, a friendly and helpful auto repair assistant. You help users understand car problems, diagnose SAE P-codes if mentioned, suggest DIY or shop repairs, and schedule service if needed."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

# UI layout
st.title("🚘 Auto Buddy: Your Car's Best Friend")
st.markdown("Describe your car issue, mention a fault code, or ask anything car-repair related:")

user_query = st.text_area("🔍 What's going on with your car?", placeholder="e.g. My 2012 Honda Civic shows code P0171 and the engine stutters.")

if st.button("Ask Auto Buddy"):
    if not user_query.strip():
        st.warning("Please describe your issue.")
    else:
        with st.spinner("Auto Buddy is thinking..."):
            response = ask_auto_buddy(user_query)
        st.text_area("Auto Buddy's Response", value=response, height=250)

        st.subheader("🗓️ Need a Repair?")
        if st.button("Check Repair Availability"):
            schedule = load_schedule("Weekly Shop Schedule.xlsx")
            st.dataframe(schedule)
            if st.button("Confirm Appointment"):
                st.success("✅ Appointment scheduled! We’ll see you soon.")
