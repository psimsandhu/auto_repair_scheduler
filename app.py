import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import openai
import os

# Configure your OpenAI API key (set this in your Streamlit secrets or env variables)
openai.api_key = os.getenv("OPENAI_API_KEY")

# Load Excel schedule
@st.cache_data
def load_schedule(file):
    return pd.read_excel(file)

# Extract fault description from PDF
def lookup_pcode_description(pcode, pdf_path):
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text = page.get_text()
            if pcode in text:
                start = text.find(pcode)
                end = text.find('\n', start)
                return text[start:end].strip()
    return "No description found for this P-code."

# Call ChatGPT API
from openai import OpenAI

client = OpenAI()

def call_chatbot(prompt):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an auto repair chatbot that helps users diagnose SAE P-codes, offer DIY repair advice, or schedule a shop visit."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content


# Streamlit UI
st.title("Auto Repair Scheduler")
st.markdown("Enter your vehicle details and fault code to get help.")

year = st.text_input("Car Year")
make = st.text_input("Make")
model = st.text_input("Model")
pcode = st.text_input("Fault Code (e.g., P0171)").upper()

if st.button("Diagnose"):
    if not all([year, make, model, pcode]):
        st.warning("Please fill in all fields.")
    else:
        desc = lookup_pcode_description(pcode, "B123214_SAE_P-Code_List.pdf")
        st.subheader(f"Code {pcode} Description:")
        st.info(desc)

        prompt = f"My car is a {year} {make} {model} and I got code {pcode} ({desc}). What does it mean and what should I do?"
        st.subheader("Ask Chatbot")
        with st.spinner("Chatbot is thinking..."):
            answer = call_chatbot(prompt)
            st.text_area("Chatbot Response", value=answer, height=250)

        if st.button("Show available repair slots"):
            schedule = load_schedule("Weekly Shop Schedule.xlsx")
            st.subheader("Available Repair Slots")
            st.dataframe(schedule)

            if st.button("Confirm appointment"):
                st.success("Your repair has been scheduled. Thank you!")
