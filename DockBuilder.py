import os
from io import BytesIO

import streamlit as st
from PIL import Image

from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


st.set_page_config(
    page_title="Conditional Documentation Builder",
    layout="centered",
)

IMAGE_FOLDER = "images"
PAGE_SIZE = landscape(letter)


LAYOUT_OPTIONS = [
    "1 Dock with Dock POE",
    "1 Dock with Customer Switch POE",
    "2 Docks with Dock POE",
    "2 Docks with Customer Switch POE",
]

POWER_OPTIONS = [
    "110-120 Volt Power",
    "208-240 Volt Power",
]

ANTENNA_OPTIONS = [
    "Non-Penetrating Antenna",
    "Wall Mounted Antenna",
]

BASE_OPTIONS = [
    "Dock Boots",
    "Bolted to Ground",
    "Custom",
]


def find_image_path(image_code):
    for ext in ["png", "jpg", "jpeg"]:
        path = os.path.join(IMAGE_FOLDER, f"{image_code}.{ext}")
        if os.path.exists(path):
            return path
    return None


def add_image_page(pdf_canvas, image_source, page_width, page_height):
    margin = 24

    if isinstance(image_source, Image.Image):
        img = image_source.convert("RGB")
        img_reader = ImageReader(img)
        img_width, img_height = img.size
    else:
        img = Image.open(image_source).convert("RGB")
        img_reader = ImageReader(img)
        img_width, img_height = img.size

    available_width = page_width - (margin * 2)
    available_height = page_height - (margin * 2)

    scale = min(
        available_width / img_width,
        available_height / img_height,
    )

    draw_width = img_width * scale
    draw_height = img_height * scale

    x = (page_width - draw_width) / 2
    y = (page_height - draw_height) / 2

    pdf_canvas.drawImage(
        img_reader,
        x,
        y,
        width=draw_width,
        height=draw_height,
        preserveAspectRatio=True,
        mask="auto",
    )

    pdf_canvas.showPage()


def get_selected_image_codes(layout, power, antenna, base):
    image_codes = []

    # Always first
    image_codes.extend(["A1", "A2", "A3", "A4"])

    # B pages
    if "Dock POE" in layout:
        image_codes.append("B1")
    elif "Customer Switch POE" in layout:
        image_codes.append("B2")

    # C pages
    if power == "208-240 Volt Power":
        image_codes.append("C1")
    elif power == "110-120 Volt Power":
        image_codes.append("C2")

    # D pages
    if layout == "1 Dock with Customer Switch POE":
        image_codes.append("D1")
    elif layout == "1 Dock with Dock POE":
        image_codes.append("D2")
    elif layout == "2 Docks with Dock POE":
        image_codes.append("D3")
    elif layout == "2 Docks with Customer Switch POE":
        image_codes.append("D4")

    # E pages
    if layout == "1 Dock with Customer Switch POE":
        image_codes.append("E1")
    elif layout == "2 Docks with Customer Switch POE":
        image_codes.append("E2")
    elif layout == "1 Dock with Dock POE":
        image_codes.append("E3")
    elif layout == "2 Docks with Dock POE":
        image_codes.append("E4")

    # F pages
    if layout == "2 Docks with Dock POE":
        image_codes.append("F1")
    elif layout == "2 Docks with Customer Switch POE":
        image_codes.append("F2")
    elif layout == "1 Dock with Dock POE":
        image_codes.append("F3")
    elif layout == "1 Dock with Customer Switch POE":
        image_codes.append("F4")

    # G pages
    if "Customer Switch POE" in layout:
        image_codes.append("G1")
    elif "Dock POE" in layout:
        image_codes.append("G2")

    # Always after G
    image_codes.extend(["A5", "A6"])

    # H pages
    if antenna == "Wall Mounted Antenna":
        image_codes.append("H1")
    elif antenna == "Non-Penetrating Antenna":
        image_codes.append("H2")

    # I pages
    if base == "Dock Boots":
        image_codes.append("I1")
    elif base == "Custom":
        image_codes.append("I2")
    elif base == "Bolted to Ground":
        image_codes.append("I3")

    # Always last
    image_codes.append("Z")

    return image_codes


def build_pdf(site_layout_image, image_codes):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=PAGE_SIZE)
    page_width, page_height = PAGE_SIZE

    # Site layout drawing gets inserted after title page A1
    for index, image_code in enumerate(image_codes):
        image_path = find_image_path(image_code)

        if image_path:
            add_image_page(pdf, image_path, page_width, page_height)

        # Add uploaded site drawing right after A1
        if index == 0 and site_layout_image is not None:
            add_image_page(pdf, site_layout_image, page_width, page_height)

    pdf.save()
    buffer.seek(0)
    return buffer


st.title("Conditional Documentation Builder")

st.subheader("Upload Site Layout Drawing")
st.write(
    "Bare Minimum to Include: Dock locations, Antenna Locations, "
    "Distance Measurement / Dimensions"
)

uploaded_site_layout = st.file_uploader(
    "Upload site layout drawing",
    type=["png", "jpg", "jpeg"],
)

site_layout_image = None

if uploaded_site_layout:
    site_layout_image = Image.open(uploaded_site_layout).convert("RGB")
    st.image(site_layout_image, caption="Uploaded Site Layout Drawing", use_container_width=True)

st.divider()

layout = st.radio("Layout", LAYOUT_OPTIONS)
power = st.radio("Power", POWER_OPTIONS)
antenna = st.radio("Antenna", ANTENNA_OPTIONS)
base = st.radio("Base", BASE_OPTIONS)

image_codes = get_selected_image_codes(layout, power, antenna, base)

missing_images = [
    code for code in image_codes
    if find_image_path(code) is None
]

if missing_images:
    st.warning(
        "Missing image files: "
        + ", ".join(missing_images)
        + ". Add these files to the images folder before generating the final PDF."
    )

if uploaded_site_layout is None:
    st.info("Upload a site layout drawing before generating the PDF.")

generate_disabled = uploaded_site_layout is None or len(missing_images) > 0

if st.button("Generate PDF", disabled=generate_disabled):
    pdf_file = build_pdf(site_layout_image, image_codes)

    st.download_button(
        label="Download Landscape PDF",
        data=pdf_file,
        file_name="conditional_documentation.pdf",
        mime="application/pdf",
    )