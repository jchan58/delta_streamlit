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
    cols_per_row = 3
    cols = st.columns(cols_per_row)

    for i, module in enumerate(modules):
        col = cols[i % cols_per_row]

        with col:
            # Card container (Streamlit-native)
            st.markdown(
                f"<div style='font-size:18px;font-weight:600;margin-bottom:8px;'>"
                f"{module['title']}</div>",
                unsafe_allow_html=True
            )

            if module.get("thumbnail"):
                st.image(module["thumbnail"], use_container_width=True)
            else:
                st.image(
                    "https://via.placeholder.com/300x200.png?text=No+Image",
                    use_container_width=True
                )

            btn1, btn2 = st.columns(2)
            with btn1:
                if st.button("✏️ Edit", key=f"edit_{module['_id']}"):
                    st.switch_page(
                        f"pages/edit_module?module_id={module['_id']}"
                    )

            with btn2:
                if st.button("🗑 Delete", key=f"delete_{module['_id']}"):
                    modules_collection.delete_one(
                        {"_id": module["_id"]}
                    )
                    st.warning("Module deleted.")
                    st.rerun()