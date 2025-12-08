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

    colA, colB = st.columns([1,1])
    with colA:
        create = st.button("Save Module")
    with colB:
        cancel = st.button("Cancel")

    if create:
        if not new_title:
            st.error("Module title is required.")
        else:
            modules_collection.insert_one({
                "title": new_title,
                "description": new_desc,
                "units": [],
                "created_by": st.session_state.user_email
            })
            st.success("Module created.")
            st.session_state.show_create_form = False
            st.experimental_rerun()

    if cancel:
        st.session_state.show_create_form = False
        st.experimental_rerun()

st.markdown("---")

# ------------------------
# Existing Modules List
# ------------------------
modules = list(modules_collection.find())

if not modules:
    st.info("No modules created yet.")
else:
    for module in modules:
        st.subheader(module["title"])
        st.write(f"**Description:** {module.get('description', '')}")
        st.write(f"**Units:** {len(module.get('units', [])})")

        col1, col2 = st.columns([1,1])

        with col1:
            if st.button("✏️ Edit", key=f"edit_{module['_id']}"):
                st.switch_page(f"pages/edit_module?module_id={module['_id']}")

        with col2:
            if st.button("🗑️ Delete", key=f"delete_{module['_id']}"):
                modules_collection.delete_one({"_id": module["_id"]})
                st.warning("Module deleted.")
                st.experimental_rerun()

        st.markdown("---")