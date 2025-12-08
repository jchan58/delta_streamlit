import streamlit as st
from pymongo import MongoClient
from bson import ObjectId
from bson.binary import Binary
import base64
from PIL import Image
import io

def get_thumbnail_src(module):
    thumb = module.get("thumbnail")
    if not thumb:
        return "https://via.placeholder.com/300x200.png?text=No+Image"
    if isinstance(thumb, Binary):
        thumb = bytes(thumb)
    img = Image.open(io.BytesIO(thumb))
    img.thumbnail((300, 200))
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    small_png = buffer.getvalue()

    encoded = base64.b64encode(small_png).decode("utf-8")
    return f"data:image/png;base64,{encoded}"

# ------------------------
# Authentication check
# ------------------------
if "is_authenticated" not in st.session_state or not st.session_state.is_authenticated:
    st.error("Access denied. Please log in as an admin.")
    st.stop()

if st.session_state.get("user_role") != "admin":
    st.error("Only administrators can access this page.")
    st.stop()

# ------------------------
# MongoDB setup
# ------------------------
client = MongoClient(st.secrets["MONGO_URI"])
db = client["delta"]
modules_collection = db["modules"]

# ------------------------
# Page Header
# ------------------------
col1, col2 = st.columns([0.8, 0.2])

with col1:
    st.title("📚 Modules")

with col2:
    # The + button
    if st.button("➕ Create Module"):
        st.session_state["show_create_form"] = True


if st.session_state.get("show_create_form", False):
    with st.form("create_module_form", clear_on_submit=False):
        st.subheader("Create New Module")

        new_title = st.text_input("Module Title")
        thumbnail_file = st.file_uploader(
            "Upload Thumbnail Image (optional)",
            type=["png", "jpg", "jpeg"]
        )

        thumbnail_bytes = None
        if thumbnail_file:
            thumbnail_bytes = thumbnail_file.read()
            st.image(thumbnail_bytes)

        # Form buttons
        submitted = st.form_submit_button("Save")
        canceled = st.form_submit_button("Cancel")

        if submitted:
            if not new_title.strip():
                st.error("Module title is required.")
            else:
                module_doc = {
                    "title": new_title.strip(),
                    "thumbnail": thumbnail_bytes,
                    "units": [],
                    "created_by": st.session_state.user_email
                }

                modules_collection.insert_one(module_doc)
                st.success("Module created.")
                st.session_state.show_create_form = False
                st.rerun()

        if canceled:
            st.session_state.show_create_form = False
            st.rerun()

st.markdown("---")

modules = list(modules_collection.find())

if not modules:
    st.info("No modules created yet.")

else:
    card_css = """
    <style>
    .module-wrapper {
        width: 230px;
        margin-bottom: 15px;
    }
    .module-title {
        font-size: 18px;
        font-weight: 600;
        text-align: center;
        margin-bottom: 6px;
    }
    .module-card {
        position: relative;
        width: 100%;
        height: 150px;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.12);
        cursor: pointer;
        transition: transform 0.2s ease;
    }
    .module-card:hover {
        transform: scale(1.02);
    }
    .module-image {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .module-overlay {
        position: absolute;
        top: 0; left: 0;
        width: 100%; 
        height: 100%;
        background: rgba(0,0,0,0.65);
        color: white;
        opacity: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 10px;
        font-size: 14px;
        transition: opacity 0.25s ease;
    }
    .module-card:hover .module-overlay {
        opacity: 1;
    }
    </style>
    """
    st.markdown(card_css, unsafe_allow_html=True)
    for module in modules:
        title = module["title"]
        thumb_bytes = module.get("thumbnail")
        description = module.get("description", "No description available.")

        st.write(f"### {title}")
        if thumb_bytes:
            st.image(thumb_bytes, width=230)
        else:
            st.image("https://via.placeholder.com/300x200.png?text=No+Image", width=230)
        card_html = f"""
        <div class="module-card">
            <div class="module-overlay">{description}</div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)
        # Edit/Delete buttons
        colA, colB = st.columns([1, 1])
        with colA:
            if st.button("✏️ Edit", key=f"edit_{module['_id']}"):
                st.switch_page(f"pages/edit_module?module_id={module['_id']}")

        with colB:
            if st.button("🗑️ Delete", key=f"delete_{module['_id']}"):
                modules_collection.delete_one({"_id": module["_id"]})
                st.warning("Module deleted.")
                st.rerun()