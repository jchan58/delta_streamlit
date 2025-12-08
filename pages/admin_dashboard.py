import streamlit as st
from pymongo import MongoClient
from bson import ObjectId

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


# ------------------------
# Create Module Form (Shown only when + is clicked)
# ------------------------
if st.session_state.get("show_create_form", False):

    st.subheader("Create New Module")

    new_title = st.text_input("Module Title")
    new_desc = st.text_area("Module Description")

    # Thumbnail upload
    thumbnail_file = st.file_uploader(
        "Upload Thumbnail Image (optional)", 
        type=["png", "jpg", "jpeg"]
    )

    # Show preview if uploaded
    if thumbnail_file:
        st.image(thumbnail_file, width=200, caption="Thumbnail Preview")

    # Buttons
    colA, colSpacer, colG = st.columns([1,5,1])
    with colA:
        create = st.button("Save")
    with colG:
        cancel = st.button("Cancel")

    if create:
        if not new_title.strip():
            st.error("Module title is required.")
        else:

            # Save thumbnail (optional)
            thumbnail_bytes = None
            if thumbnail_file:
                thumbnail_bytes = thumbnail_file.read()  # stored as raw bytes

            module_doc = {
                "title": new_title.strip(),
                "description": new_desc.strip(),
                "thumbnail": thumbnail_bytes,   # store raw file bytes
                "units": [],
                "created_by": st.session_state.user_email
            }

            modules_collection.insert_one(module_doc)

            st.success("Module created.")
            st.session_state.show_create_form = False
            st.rerun()

    if cancel:
        st.session_state.show_create_form = False
        st.rerun()

st.markdown("---")

modules = list(modules_collection.find())

if not modules:
    st.info("No modules created yet.")
else:
    for module in modules:
        title = module["title"]
        description = module.get("description", "No description available.")
        thumbnail = module.get("thumbnail_url", "default_thumbnail.png")

        card_html = f"""
        <style>
        .module-wrapper {{
            width: 230px;
            margin-bottom: 15px;
        }}

        .module-title {{
            font-size: 18px;
            font-weight: 600;
            text-align: center;
            margin-bottom: 6px;
        }}

        .module-card {{
            position: relative;
            width: 100%;
            height: 150px;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.12);
            cursor: pointer;
            transition: transform 0.2s ease;
        }}

        .module-card:hover {{
            transform: scale(1.02);
        }}

        .module-image {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }}

        .module-overlay {{
            position: absolute;
            top: 0; left: 0;
            width: 100%; height: 100%;
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
        }}

        .module-card:hover .module-overlay {{
            opacity: 1;
        }}
        </style>

        <div class="module-wrapper">
            <div class="module-title">{title}</div>

            <div class="module-card">
                <img src="{thumbnail}" class="module-image"/>
                <div class="module-overlay">{description}</div>
            </div>
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