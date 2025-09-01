import streamlit as st
import fitz  # PyMuPDF
import cv2
import numpy as np
import img2pdf
import os
from tempfile import TemporaryDirectory
from zipfile import ZipFile

st.set_page_config(page_title="PDF to B/W Converter", layout="wide")
st.title("Badri's cheating copy for - PDF to Black & White Converter ")
st.write("Convert your PDFs to high-contrast black & white and monitor progress.")

# Upload multiple PDFs
uploaded_files = st.file_uploader(
    "Upload PDF files",
    type="pdf",
    accept_multiple_files=True
)

threshold = st.slider(
    "Threshold (lower = darker, higher = lighter)",
    min_value=50,
    max_value=255,
    value=180
)

if st.button("Convert PDFs") and uploaded_files:
    with TemporaryDirectory() as tmpdir:
        output_paths = []

        # Placeholder for overall log
        log_placeholder = st.empty()

        for pdf_idx, uploaded_file in enumerate(uploaded_files):
            input_pdf_path = os.path.join(tmpdir, uploaded_file.name)
            output_pdf_path = os.path.join(tmpdir, f"bw_{uploaded_file.name}")

            # Save uploaded PDF
            with open(input_pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Initialize log and progress bar
            log_lines = [f"Processing PDF {pdf_idx + 1}/{len(uploaded_files)}: {uploaded_file.name}"]
            log_placeholder.text("\n".join(log_lines))

            temp_images = []

            # Open PDF safely using context manager
            with fitz.open(input_pdf_path) as doc:
                progress_bar = st.progress(0)

                for page_num in range(len(doc)):
                    pix = doc[page_num].get_pixmap(dpi=300)
                    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)

                    if pix.n == 4:
                        img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)

                    # Convert to grayscale
                    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
                    _, bw = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)

                    temp_img_path = os.path.join(tmpdir, f"{uploaded_file.name}_page_{page_num+1}.png")
                    cv2.imwrite(temp_img_path, bw)
                    temp_images.append(temp_img_path)

                    # Update log and progress
                    log_lines.append(f"  Page {page_num + 1}/{len(doc)} processed")
                    log_placeholder.text("\n".join(log_lines))
                    progress_bar.progress((page_num + 1) / len(doc))

            # Convert temp images to B/W PDF after closing PDF
            with open(output_pdf_path, "wb") as f:
                f.write(img2pdf.convert(temp_images))
            output_paths.append(output_pdf_path)
            log_lines.append(f"✅ PDF saved: {os.path.basename(output_pdf_path)}")
            log_placeholder.text("\n".join(log_lines))

            # Clean up temp images
            for img_path in temp_images:
                if os.path.exists(img_path):
                    os.remove(img_path)

        # Create ZIP file for download
        zip_path = os.path.join(tmpdir, "bw_pdfs.zip")
        with ZipFile(zip_path, "w") as zipf:
            for pdf_path in output_paths:
                zipf.write(pdf_path, os.path.basename(pdf_path))

        # Download button
        with open(zip_path, "rb") as f:
            st.download_button(
                label="Download All PDFs as ZIP",
                data=f,
                file_name="bw_pdfs.zip",
                mime="application/zip"
            )

        st.success("All PDFs processed successfully!")
