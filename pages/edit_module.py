import streamlit as st
from pymongo import MongoClient

client = MongoClient(st.secrets["MONGO_URI"])
db = client["delta"]
modules_collection = db["modules"]

params = st.query_params
module_id = params.get("module_id")

if module_id is None:
    st.error("Missing module_id")
    st.stop()

module_id = int(module_id)

module = modules_collection.find_one({"module_id": module_id})
if module is None:
    st.error("Module not found")
    st.stop()

st.title(f"📘 {module['title']}")
st.caption(f"Module ID: {module_id}")

st.markdown("---")

c1, c2 = st.columns([0.8, 0.2])
with c1:
    st.subheader("Units")
with c2:
    if st.button("➕ Add Unit"):
        st.session_state.show_create_unit = True