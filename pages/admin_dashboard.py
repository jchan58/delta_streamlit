import streamlit as st
from pymongo import MongoClient
from bson import ObjectId

if "is_authenticated" not in st.session_state or not st.session_state.is_authenticated:
    st.error("Access denied. Please log in as an admin.")
    st.stop()

if st.session_state.get("user_role") != "admin":
    st.error("Only administrators can access this page.")
    st.stop()

client = MongoClient(st.secrets["MONGO_URI"])
db = client["delta"]
modules_collection = db["modules"]

st.title("📚 Module Manager")
st.write(f"Logged in as: **{st.session_state.user_email}**")

st.markdown("---")

st.header("➕ Create a New Module")

module_title = st.text_input("Module Title")
module_description = st.text_area("Module Description")

if st.button("Create Module"):
    if not module_title:
        st.error("Module title is required.")
    else:
        module_doc = {
            "title": module_title,
            "description": module_description,
            "units": [],               # Empty list (units added later)
            "created_by": st.session_state.user_email
        }
        modules_collection.insert_one(module_doc)
        st.success("Module created successfully!")
        st.experimental_rerun()

st.markdown("---")

st.header("🗂️ Existing Modules")
modules = list(modules_collection.find())
if not modules:
    st.info("No modules created yet.")
else:
    for module in modules:
        st.subheader(f"📘 {module['title']}")
        st.write(f"**Description:** {module.get('description', '')}")
        st.write(f"**Units:** {len(module.get('units', []))}")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button(f"Edit Module", key=f"edit_{module['_id']}"):
                st.switch_page(f"pages/edit_module?module_id={module['_id']}")

        with col2:
            if st.button(f"Delete", key=f"delete_{module['_id']}"):
                modules_collection.delete_one({"_id": module["_id"]})
                st.warning("Module deleted.")
                st.rerun()

        st.markdown("---")
