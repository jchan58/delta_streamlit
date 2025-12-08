import streamlit as st
from pymongo import MongoClient
import datetime
import time

if "is_authenticated" not in st.session_state:
    st.session_state.is_authenticated = False
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None

@st.cache_resource
def get_mongo_client():
    return MongoClient(st.secrets["MONGO_URI"])

db = get_mongo_client()["delta"]
users_collection = db["users"]

def normalize_email(email: str) -> str:
    return email.strip().lower()

def user_exists(email):
    return users_collection.find_one({"email": email}) is not None

def validate_user(email, password):
    user = users_collection.find_one({"email": email})
    if not user:
        return False
    return user.get("password") == password 

def register_user(email, password):
    users_collection.insert_one({
        "email": email,
        "password": password,
        "created_at": datetime.datetime.utcnow(),
        "progress": {}
    })

st.title("👤 User Login / Signup")
tab_login, tab_signup = st.tabs(["Login", "Sign Up"])
with tab_login:
    st.subheader("Login")
    login_email = st.text_input("Email", key="login_email")
    login_pw = st.text_input("Password", type="password", key="login_pw")
    if st.button("Login", key="login_btn"):
        email = normalize_email(login_email)
        if validate_user(email, login_pw):
            st.success("Login successful!")
            st.session_state.is_authenticated = True
            st.session_state.user_role = "user"
            st.session_state.user_email = email
            st.switch_page("pages/user_dashboard.py")
        else:
            st.error("Invalid email or password.")

with tab_signup:
    st.subheader("Create an Account")
    signup_email = st.text_input("Email", key="signup_email")
    signup_pw = st.text_input("Password", type="password", key="signup_pw")
    if st.button("Sign Up", key="signup_btn"):
        email = normalize_email(signup_email)
        if user_exists(email):
            st.error("An account with this email already exists.")
        else:
            register_user(email, signup_pw)
            st.success("Account created! Please log in now.")
