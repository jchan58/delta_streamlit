import streamlit as st
from pymongo import MongoClient
from gridfs import GridFS
from bson import ObjectId
import base64

client = MongoClient(st.secrets["MONGO_URI"])
db = client["delta"]
fs = GridFS(db)
modules_collection = db["modules"]

def preview_file(file_obj, filename):
    content = file_obj.read()
    
    if file_obj.content_type == "application/pdf":
        b64_pdf = base64.b64encode(content).decode("utf-8")
        pdf_display = f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    
    elif file_obj.content_type.startswith("video/"):
        st.video(content)
    
    elif file_obj.content_type.startswith("image/"):
        st.image(content)
    
    else:
        st.markdown(f"📎 **{filename}** (preview not supported)")

module_id = st.session_state.get("module_id")
if module_id is None:
    st.error("Missing module_id in session state.")
    st.stop()

module_id = int(module_id)

module = modules_collection.find_one({"module_id": module_id})
if module is None:
    st.error("Module not found.")
    st.stop()

if "show_create_unit" not in st.session_state:
    st.session_state.show_create_unit = False

if "new_unit_items" not in st.session_state:
    st.session_state.new_unit_items = []

st.title(f"📘 {module['title']}")
st.markdown("---")

c1, c2 = st.columns([0.8, 0.2])
with c1:
    st.subheader("Units")
with c2:
    if st.button("➕ Add Unit"):
        st.session_state.show_create_unit = True
        st.session_state.new_unit_items = []

units = module.get("units", [])
if not units:
    st.info("No units yet.")
else:
    for u in sorted(units, key=lambda x: x["unit_id"]):
        st.write(f"Unit {u['unit_id']}: {u['title']}")

        for item in u.get("items", []):
            st.write(f"• {item['title']} ({item['type']})")

            if item["type"] == "file" and "file_id" in item:
                try:
                    file = fs.get(ObjectId(item["file_id"]))
                    preview_file(file, item["filename"])
                except Exception as e:
                    st.warning(f"Unable to preview file: {e}")

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
        item_title = st.text_input("Item title")
        item_type = st.selectbox(
            "Item type",
            ["video", "file", "quiz"]
        )

        uploaded_file = st.file_uploader(
            "Upload a file (PDF, video, image, etc.)"
        )

        add_item = st.form_submit_button("➕ Add item")
        create_unit = st.form_submit_button("Create Unit")
        cancel = st.form_submit_button("Cancel")


    if add_item:
        if not item_title.strip():
            st.error("Item title is required.")
        elif item_type == "file" and uploaded_file is None:
            st.error("Please upload a file.")
        else:
            file_id = None
            filename = None
            mime_type = None

            if uploaded_file:
                file_bytes = uploaded_file.read()
                filename = uploaded_file.name
                mime_type = uploaded_file.type

                file_id = fs.put(
                    file_bytes,
                    filename=filename,
                    content_type=mime_type
                )

            next_item_id = len(st.session_state.new_unit_items)
            new_item = {
                "item_id": next_item_id,
                "title": item_title.strip(),
                "type": item_type
            }

            if item_type == "file":
                new_item["file_id"] = str(file_id)
                new_item["filename"] = filename
                new_item["mime_type"] = mime_type

            st.session_state.new_unit_items.append(new_item)
            st.rerun()
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
