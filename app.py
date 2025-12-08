import streamlit as st

st.set_page_config(page_title="Training Platform", page_icon="📘")

# Initialize session state variables if not present
if "is_authenticated" not in st.session_state:
    st.session_state.is_authenticated = False
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None

st.title("📘 Modules Platform for the Hunterian Laboratory")

st.write("Please select how you want to log in:")

col1, col2 = st.columns(2)

with col1:
    if st.button("🔐 Admin Login"):
        st.switch_page("pages/admin_login")
with col2:
    if st.button("👤 User Login / Sign Up"):
        st.switch_page("pages/user_login") 