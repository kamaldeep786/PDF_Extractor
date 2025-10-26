import streamlit as st
import pdfplumber
import fitz  # PyMuPDF
import camelot
import pandas as pd
import pytesseract
from PIL import Image
import io
import tempfile
import os

st.set_page_config(page_title="Advanced PDF Extractor", layout="wide")

st.title("📘 Advanced PDF Text & Table Extractor (with OCR)")

uploaded_file = st.file_uploader("📤 Upload your PDF file", type=["pdf"])

if uploaded_file:
    st.success("✅ File uploaded successfully!")

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_path = tmp_file.name

    text_content = ""
    ocr_text_content = ""
    extracted_tables = []

    with st.spinner("🔍 Extracting data from PDF..."):
        # --- Step 1: Extract text (try native text first)
        try:
            with pdfplumber.open(tmp_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text + "\n"
        except Exception as e:
            st.error(f"❌ Text extraction error: {e}")

        # --- Step 2: Run OCR if text content is minimal ---
        if len(text_content.strip()) < 100:
            st.info("📸 Running OCR for scanned PDF...")
            try:
                doc = fitz.open(tmp_path)
                for page_num, page in enumerate(doc, start=1):
                    pix = page.get_pixmap(dpi=200)
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    ocr_text = pytesseract.image_to_string(img)
                    ocr_text_content += f"\n--- Page {page_num} ---\n{ocr_text}"
            except Exception as e:
                st.warning(f"OCR extraction failed: {e}")

        # --- Step 3: Extract tables using Camelot ---
        try:
            tables = camelot.read_pdf(tmp_path, pages="all", flavor="lattice")
            if len(tables) == 0:
                tables = camelot.read_pdf(tmp_path, pages="all", flavor="stream")
            extracted_tables = [t.df for t in tables]
        except Exception as e:
            st.warning(f"⚠️ Table extraction failed: {e}")

    # --- Step 4: Display results ---
    tab1, tab2, tab3 = st.tabs(["📝 Text", "📊 Tables", "⬇️ Download"])

    with tab1:
        st.subheader("Extracted Text")
        final_text = text_content if text_content.strip() else ocr_text_content
        if final_text:
            st.text_area("Full Extracted Text", final_text, height=400)
        else:
            st.warning("No text found. Try OCR-enabled extraction.")

    with tab2:
        st.subheader("Extracted Tables")
        if extracted_tables:
            for i, df in enumerate(extracted_tables):
                st.write(f"**Table {i+1}**")
                st.dataframe(df)
        else:
            st.info("No tables found in the PDF.")

    with tab3:
        st.subheader("Download Extracted Data")
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            # Write text sheet
            text_data = text_content if text_content.strip() else ocr_text_content
            pd.DataFrame({"Extracted Text": [text_data]}).to_excel(writer, sheet_name="Text", index=False)
            # Write tables
            for i, df in enumerate(extracted_tables):
                df.to_excel(writer, sheet_name=f"Table_{i+1}", index=False)
        output.seek(0)

        st.download_button(
            label="📥 Download Extracted Excel",
            data=output,
            file_name="pdf_extracted_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # --- Cleanup temp file ---
    os.remove(tmp_path)
