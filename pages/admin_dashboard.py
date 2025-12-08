import streamlit as st
from pymongo import MongoClient

if "is_authenticated" not in st.session_state or not st.session_state.is_authenticated:
    st.error("Access denied. Please log in as an admin.")
    st.stop()

if st.session_state.get("user_role") != "admin":
    st.error("Only administrators can access this page.")
    st.stop()

MONGO_URI = st.secrets["MONGO_URI"]
client = MongoClient(MONGO_URI)
db = client["delta"]
modules_collection = db["modules"]
st.title("🛠️ Admin Dashboard")
st.write(f"Logged in as: **{st.session_state.user_email}**")
menu_choice = st.sidebar.radio(
    "Admin Menu",
    [
        "Dashboard",
        "Create New Module",
        "Manage Existing Modules",
        "Logout"
    ]
)

if menu_choice == "Dashboard":
    st.subheader("Welcome, Administrator")
    st.write("Use the sidebar to manage learning modules.")

# create new modules 
elif menu_choice == "Create New Module":
    st.subheader("📚 Create a New Module")
    module_title = st.text_input("Module Title")
    module_description = st.text_area("Module Description")
    
    if st.button("Create Module"):
        if not module_title:
            st.error("Module title is required.")
        else:
            module_doc = {
                "title": module_title,
                "description": module_description,
                "units": [], 
                "created_by": st.session_state.user_email
            }
            modules_collection.insert_one(module_doc)
            st.success("Module created successfully!")

elif menu_choice == "Manage Existing Modules":
    st.subheader("🗂️ Manage Modules")
    modules = list(modules_collection.find())
    if not modules:
        st.info("No modules created yet.")
    else:
        module_names = [f"{m['title']} (ID: {m['_id']})" for m in modules]
        selected = st.selectbox("Select a module to manage:", module_names)
        module = modules[module_names.index(selected)]

        st.write("### Module Overview")
        st.write(f"**Title:** {module['title']}")
        st.write(f"**Description:** {module.get('description', '')}")
        st.write("**Units:**", module.get("units", []))

elif menu_choice == "Logout":
    st.session_state.is_authenticated = False
    st.session_state.user_email = None
    st.session_state.user_role = None
    st.success("Logged out successfully.")
    st.rerun()
