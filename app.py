import streamlit as st
import cv2
import numpy as np
import io
import zipfile

def crop_image_logic(image_bytes):
    # Convert the uploaded file bytes into an OpenCV image
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None: return None

    h, w, _ = img.shape
    bg_color = img[5, 5]

    # Masking and logic (Your artifact-proof code)
    lower_bound = np.clip(bg_color - 25, 0, 255)
    upper_bound = np.clip(bg_color + 25, 0, 255)
    bg_mask = cv2.inRange(img, lower_bound, upper_bound)
    fg_mask = cv2.bitwise_not(bg_mask)

    col_counts = np.sum(fg_mask == 255, axis=0)
    row_counts = np.sum(fg_mask == 255, axis=1)

    valid_cols = np.where(col_counts > (h * 0.25))[0]
    valid_rows = np.where(row_counts > (w * 0.25))[0]

    if len(valid_cols) > 0 and len(valid_rows) > 0:
        left, right = valid_cols[0], valid_cols[-1]
        top, bottom = valid_rows[0], valid_rows[-1]
        
        cropped_img = img[top:bottom, left:right]

        # Convert the cropped image back to bytes so the browser can download it
        is_success, buffer = cv2.imencode(".jpg", cropped_img)
        if is_success:
            return buffer.tobytes()
    return None

# --- Web App UI Design ---
st.set_page_config(page_title="GRE Smart Cropper", page_icon="✂️", layout="centered")

st.title("✂️ Smart GRE Screenshot Cropper")
st.write("Upload a batch of messy practice screenshots. The app will automatically remove the blue margins, ignore corner artifacts, and give you a clean `.zip` file to download.")

# Drag and drop file uploader
uploaded_files = st.file_uploader("Drop screenshots here", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)

if uploaded_files:
    if st.button("Crop Images"):
        with st.spinner(f"Processing {len(uploaded_files)} images..."):
            
            # Create an invisible, in-memory ZIP file
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                success_count = 0
                
                # Process each image
                for file in uploaded_files:
                    cropped_bytes = crop_image_logic(file.getvalue())
                    if cropped_bytes:
                        # Add the cropped image to the ZIP file
                        zip_file.writestr(f"cropped_{file.name}", cropped_bytes)
                        success_count += 1
            
            # Display results
            if success_count > 0:
                st.success(f"Successfully cropped {success_count} out of {len(uploaded_files)} images!")
                st.download_button(
                    label="⬇️ Download Cropped Batch (.zip)",
                    data=zip_buffer.getvalue(),
                    file_name="cropped_screenshots.zip",
                    mime="application/zip"
                )
            else:
                st.error("Could not detect the main window in any of the uploaded images.")