import streamlit as st
import pandas as pd
from pymongo import MongoClient

# sesssion state variables
if "is_authenticated" not in st.session_state:
    st.session_state.is_authenticated = False
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "user_role" not in st.session_state:
    st.session_state.user_role = None

# remove the pages sidebar
st.markdown("""
<style>
[data-testid="stSidebarNav"] { 
    display: none !important; 
}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_mongo_client():
    return MongoClient(st.secrets["MONGO_URI"])
MONGO_URI = st.secrets["MONGO_URI"]
client = MongoClient(MONGO_URI)
db = client["delta"]
users_collection = db["admins"]
module_collection = db["modules"]

# load approved IDs and dataframe for all the abstracts etc., 
admin_df = pd.read_csv("approved_admin_ids.csv")   # file: admin_id,password
admin_df["admin_id"] = admin_df["admin_id"].astype(str).str.strip().str.lower()

# create helper functions
def normalize_email(email: str) -> str:
    return email.strip().lower()

def verify_admin(email, password):
    email = normalize_email(email)
    row = admin_df[admin_df["admin_id"] == email]
    if row.empty:
        return False 
    correct_pw = str(row.iloc[0]["password"]).strip()
    return password == correct_pw

st.title("🔐 Admin Login")

email = st.text_input("Admin Email")
password = st.text_input("Password", type="password")

if st.button("Login"):
    if verify_admin(email, password):
        st.session_state.is_authenticated = True
        st.session_state.user_role = "admin"
        st.session_state.user_email = normalize_email(email)
        st.success("Login successful.")
        st.switch_page("pages/admin_dashboard.py") 
    else:
        st.error("Invalid admin credentials.")


