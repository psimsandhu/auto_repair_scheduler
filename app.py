import streamlit as st
import pandas as pd
import fitz  # PyMuPDF

# Load Excel schedule
@st.cache_data
def load_schedule(file):
    return pd.read_excel(file)

# Extract fault description from the PDF
def lookup_pcode_description(pcode, pdf_path):
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text = page.get_text()
            if pcode in text:
                start = text.find(pcode)
                end = text.find('\n', start)
                return text[start:end].strip()
    return "No description found for this P-code."

# UI
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

        st.write("Do you want to attempt this repair yourself?")
        if st.button("Yes, show me how"):
            st.write("🔧 DIY instructions and parts search coming soon!")
        elif st.button("No, schedule repair"):
            schedule = load_schedule("Weekly Shop Schedule.xlsx")
            st.subheader("Available Repair Slots")
            st.dataframe(schedule)

            if st.button("Confirm appointment"):
                st.success("Your repair has been scheduled. Thank you!")

