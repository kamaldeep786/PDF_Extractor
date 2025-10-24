import streamlit as st
import pdfplumber
import camelot
import pandas as pd
import io

st.set_page_config(page_title="PDF Extractor", layout="wide")

st.title("📄 PDF Table & Text Extractor")

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if uploaded_file is not None:
    st.success("✅ File uploaded successfully!")

    # --- Step 1: Extract text content ---
    text_content = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text_content += page.extract_text() + "\n"

    # --- Step 2: Extract tables using Camelot ---
    # Camelot only works on file paths, so save temporarily
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.read())

    try:
        tables = camelot.read_pdf("temp.pdf", pages="all", flavor="lattice")
    except:
        tables = []

    # --- Step 3: Display extracted data ---
    st.subheader("📝 Extracted Text")
    st.text_area("Paragraphs", text_content, height=250)

    st.subheader("📊 Extracted Tables")
    if tables and len(tables) > 0:
        for i, table in enumerate(tables):
            df = table.df
            st.write(f"**Table {i+1}**")
            st.dataframe(df)
    else:
        st.warning("No tables found in this PDF.")

    # --- Step 4: Export all data to Excel ---
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # write tables
        if tables and len(tables) > 0:
            for i, table in enumerate(tables):
                table.df.to_excel(writer, sheet_name=f"Table_{i+1}", index=False)
        # write text
        pd.DataFrame({"Text": [text_content]}).to_excel(writer, sheet_name="Text", index=False)
    output.seek(0)

    st.download_button(
        label="📥 Download Extracted Data (Excel)",
        data=output,
        file_name="pdf_extracted.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
