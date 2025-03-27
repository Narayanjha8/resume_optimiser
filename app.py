import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Configure Google Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_gemini_response(input_text):
    try:
        model = genai.GenerativeModel("gemini-1.5-pro-latest")
        response = model.generate_content(input_text)

        # Debug: Print raw response for troubleshooting
        print("RAW RESPONSE:", response.text)

        # Ensure response is valid
        if hasattr(response, "text"):
            return response.text.strip()
        elif hasattr(response, "candidates") and response.candidates:
            return response.candidates[0].text.strip()

        return '{"error": "Invalid response format"}'
    except Exception as e:
        print(f"Error calling Gemini API: {str(e)}")
        return '{"error": "API call failed"}'

def input_pdf_text(uploaded_file):
    """Extracts text from a PDF file."""
    reader = pdf.PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += str(page.extract_text()) if page.extract_text() else ""
    return text

# Streamlit UI
st.title("🔍 Smart ATS - Resume Evaluator")
st.text("Enhance Your Resume's ATS Compatibility")

jd = st.text_area("📌 Paste the Job Description")
uploaded_file = st.file_uploader("📂 Upload Your Resume", type="pdf", help="Please upload a PDF file")

if st.button("🔎 Submit"):
    if uploaded_file and jd:
        resume_text = input_pdf_text(uploaded_file)

        input_prompt = f"""
        Act as an advanced ATS (Application Tracking System) specializing in:
        - Software Engineering
        - Data Science
        - Data Analytics
        - Big Data Engineering

        Analyze the resume against the provided job description and:
        - Assign a **percentage match**.
        - Identify **missing keywords**.
        - Provide a **brief profile summary**.

        **STRICTLY return only a JSON object** in the format below and nothing else:

        ```json
        {{
          "JD Match": "XX%",
          "MissingKeywords": ["keyword1", "keyword2"],
          "Profile Summary": "Short evaluation"
        }}
        ```

        Resume: {resume_text}
        Job Description: {jd}
        """

        response = get_gemini_response(input_prompt)

        try:
            # Extract JSON response
            response_cleaned = response.split("```json")[-1].split("```")[0].strip()
            parsed_response = json.loads(response_cleaned)

            if "JD Match" in parsed_response and "MissingKeywords" in parsed_response and "Profile Summary" in parsed_response:
                st.subheader(f"✅ JD Match: {parsed_response.get('JD Match', 'N/A')}")
                st.write(f"🔹 **Missing Keywords:** {', '.join(parsed_response.get('MissingKeywords', []))}")
                st.write(f"📄 **Profile Summary:** {parsed_response.get('Profile Summary', 'No summary available.')}")
            else:
                st.error("❌ AI response was not in the expected format. Please try again.")

        except json.JSONDecodeError as e:
            st.error(f"⚠️ JSON decoding error: {str(e)}")
            st.text("🔍 Raw AI Response:")
            st.code(response)  # Show the response for debugging

    else:
        st.warning("⚠️ Please upload a resume and enter a job description.")

