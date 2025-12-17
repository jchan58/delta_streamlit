import streamlit as st
from pymongo import MongoClient

# ------------------------
# MongoDB setup
# ------------------------
client = MongoClient(st.secrets["MONGO_URI"])
db = client["delta"]
modules_collection = db["modules"]

# ------------------------
# Load module context
# ------------------------
module_id = st.session_state.get("module_id")
if module_id is None:
    st.error("Missing module_id in session state.")
    st.stop()

module_id = int(module_id)

module = modules_collection.find_one({"module_id": module_id})
if module is None:
    st.error("Module not found.")
    st.stop()

# ------------------------
# Initialize session state
# ------------------------
if "show_create_unit" not in st.session_state:
    st.session_state.show_create_unit = False

if "new_unit_items" not in st.session_state:
    st.session_state.new_unit_items = []

if "new_item_title" not in st.session_state:
    st.session_state.new_item_title = ""

if "new_item_type" not in st.session_state:
    st.session_state.new_item_type = "video"
# ------------------------
# Page header
# ------------------------
st.title(f"📘 {module['title']}")
st.markdown("---")

c1, c2 = st.columns([0.8, 0.2])
with c1:
    st.subheader("Units")
with c2:
    if st.button("➕ Add Unit"):
        st.session_state.show_create_unit = True
        st.session_state.new_unit_items = []

# ------------------------
# Existing units
# ------------------------
units = module.get("units", [])
if not units:
    st.info("No units yet.")
else:
    for u in sorted(units, key=lambda x: x["unit_id"]):
        st.write(f"Unit {u['unit_id']}: {u['title']}")

# ------------------------
# Create Unit form
# ------------------------
if st.session_state.show_create_unit:
    st.markdown("---")
    with st.form("create_unit_form"):
        st.markdown("## Create Unit")

        unit_title = st.text_input("Unit title")

        st.markdown("### Items in this unit")
        if not st.session_state.new_unit_items:
            st.caption("No items added yet.")
        else:
            for i, item in enumerate(st.session_state.new_unit_items):
                st.write(f"{i + 1}. {item['title']} ({item['type']})")

        st.markdown("### Add an item")
        item_title = st.text_input(
            "Item title",
            key="new_item_title"
        )

        item_type = st.selectbox(
            "Item type",
            ["video", "file", "quiz"],
            key="new_item_type"
        )

        add_item = st.form_submit_button("➕ Add item")
        create_unit = st.form_submit_button("Create Unit")
        cancel = st.form_submit_button("Cancel")

    # ------------------------
    # Handle Add Item
    # ------------------------
    if add_item:
        if not st.session_state.new_item_title.strip():
            st.error("Item title is required.")
        else:
            next_item_id = len(st.session_state.new_unit_items)

            st.session_state.new_unit_items.append({
                "item_id": next_item_id,
                "title": st.session_state.new_item_title.strip(),
                "type": st.session_state.new_item_type
            })
            st.session_state["new_item_title"] = ""
            st.session_state["new_item_type"] = "video"
            st.rerun()

    # ------------------------
    # Handle Create Unit
    # ------------------------
    if create_unit:
        if not unit_title.strip():
            st.error("Unit title is required.")
        else:
            next_unit_id = max(
                [u["unit_id"] for u in units],
                default=-1
            ) + 1

            new_unit = {
                "unit_id": next_unit_id,
                "title": unit_title.strip(),
                "items": st.session_state.new_unit_items
            }

            modules_collection.update_one(
                {"module_id": module_id},
                {"$push": {"units": new_unit}}
            )

            st.session_state.show_create_unit = False
            st.session_state.new_unit_items = []

            st.success(f"Unit {next_unit_id} created.")
            st.rerun()

    if cancel:
        st.session_state.show_create_unit = False
        st.session_state.new_unit_items = []
        st.rerun()
