# -------------------------------
# 📘 Advanced PDF Text & Table Extractor (with OCR)
# Description: 
# Streamlit web app that extracts text and tables from PDFs.
# It supports both native (digital) PDFs and scanned PDFs (via OCR).
# Author: [Your Name]
# Version: 1.0
# -------------------------------

# --- Import necessary libraries ---
import streamlit as st
import pdfplumber          # For text extraction from PDFs
import fitz                # PyMuPDF for rendering PDF pages as images
import camelot             # For extracting tables from PDFs
import pandas as pd
import pytesseract         # For OCR (Optical Character Recognition)
from PIL import Image       # Image processing for OCR
import io
import tempfile
import os

# --- Streamlit page setup ---
st.set_page_config(page_title="Advanced PDF Extractor", layout="wide")
st.title("📘 Advanced PDF Text & Table Extractor (with OCR)")

# --- File uploader widget ---
uploaded_file = st.file_uploader("📤 Upload your PDF file", type=["pdf"])

# Proceed only if user uploads a file
if uploaded_file:
    st.success("✅ File uploaded successfully!")

    # --- Save uploaded file temporarily ---
    # Using NamedTemporaryFile ensures a unique file name
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_path = tmp_file.name

    # Initialize containers for extracted content
    text_content = ""          # For native text
    ocr_text_content = ""      # For OCR text (if scanned PDF)
    extracted_tables = []      # For storing table data

    # --- Main extraction block ---
    with st.spinner("🔍 Extracting data from PDF..."):

        # STEP 1️⃣: Extract native text using pdfplumber
        try:
            with pdfplumber.open(tmp_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text + "\n"
        except Exception as e:
            st.error(f"❌ Text extraction error: {e}")

        # STEP 2️⃣: If minimal text found, run OCR for scanned PDFs
        if len(text_content.strip()) < 100:
            st.info("📸 Running OCR for scanned PDF...")
            try:
                doc = fitz.open(tmp_path)
                for page_num, page in enumerate(doc, start=1):
                    # Convert each page to an image
                    pix = page.get_pixmap(dpi=200)
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    # Perform OCR on the image
                    ocr_text = pytesseract.image_to_string(img)
                    ocr_text_content += f"\n--- Page {page_num} ---\n{ocr_text}"
            except Exception as e:
                st.warning(f"OCR extraction failed: {e}")

        # STEP 3️⃣: Extract tables using Camelot
        try:
            # Try lattice mode (good for bordered tables)
            tables = camelot.read_pdf(tmp_path, pages="all", flavor="lattice")
            # If no tables found, fall back to stream mode
            if len(tables) == 0:
                tables = camelot.read_pdf(tmp_path, pages="all", flavor="stream")
            extracted_tables = [t.df for t in tables]
        except Exception as e:
            st.warning(f"⚠️ Table extraction failed: {e}")

    # --- STEP 4️⃣: Display extracted results in tabs ---
    tab1, tab2, tab3 = st.tabs(["📝 Text", "📊 Tables", "⬇️ Download"])

    # --- Tab 1: Display extracted text ---
    with tab1:
        st.subheader("Extracted Text")
        # Use OCR text if native text is empty
        final_text = text_content if text_content.strip() else ocr_text_content
        if final_text:
            st.text_area("Full Extracted Text", final_text, height=400)
        else:
            st.warning("No text found. Try OCR-enabled extraction.")

    # --- Tab 2: Display extracted tables ---
    with tab2:
        st.subheader("Extracted Tables")
        if extracted_tables:
            for i, df in enumerate(extracted_tables):
                st.write(f"**Table {i+1}**")
                st.dataframe(df)
        else:
            st.info("No tables found in the PDF.")

    # --- Tab 3: Download option for extracted data ---
    with tab3:
        st.subheader("Download Extracted Data")

        # Create in-memory Excel file
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            # Write extracted text
            text_data = text_content if text_content.strip() else ocr_text_content
            pd.DataFrame({"Extracted Text": [text_data]}).to_excel(
                writer, sheet_name="Text", index=False
            )
            # Write extracted tables
            for i, df in enumerate(extracted_tables):
                df.to_excel(writer, sheet_name=f"Table_{i+1}", index=False)
        output.seek(0)

        # Streamlit download button
        st.download_button(
            label="📥 Download Extracted Excel",
            data=output,
            file_name="pdf_extracted_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # --- STEP 5️⃣: Cleanup temporary file ---
    os.remove(tmp_path)
