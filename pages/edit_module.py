import streamlit as st
from pymongo import MongoClient
from gridfs import GridFS
from bson import ObjectId
import base64

client = MongoClient(st.secrets["MONGO_URI"])
db = client["delta"]
fs = GridFS(db)
modules_collection = db["modules"]

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

if "quiz_builder" not in st.session_state:
    st.session_state.quiz_builder = {"questions": []}

if "editing_question_index" not in st.session_state:
    st.session_state.editing_question_index = None

import tempfile
import streamlit.components.v1 as components

def preview_file(file_obj, filename):
    content = file_obj.read()
    mime = file_obj.content_type or ""
    fname = filename.lower()
    if mime == "application/pdf" or fname.endswith(".pdf"):
        st.download_button("📄 Open PDF", content, filename, "application/pdf", key=f"pdf_{file_obj._id}")

    elif mime.startswith("video/") or fname.endswith((".mp4", ".mov", ".webm", ".avi", ".mp3")):
        st.video(content)

    elif mime.startswith("image/") or fname.endswith((".png", ".jpg", ".jpeg", ".gif")):
        st.image(content)

    else:
        st.write("Unknown type:", mime, filename)

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
        st.session_state.open_add_unit = True
        st.session_state.new_unit_items = []

units = module.get("units", [])
if not units:
    st.info("No units yet.")
else:
    for u in sorted(units, key=lambda x: x["unit_id"]):
        colA, colB = st.columns([0.9, 0.1])

        with colA:
            exp = st.expander(f"Unit {u['unit_id']} — {u['title']}", expanded=False)
        with colB:
            delete_unit = st.button("🗑️", key=f"delete_unit_{u['unit_id']}")

        if delete_unit:
            new_units = [x for x in units if x["unit_id"] != u["unit_id"]]
            for i, unit in enumerate(new_units):
                unit["unit_id"] = i
            modules_collection.update_one(
                {"module_id": module_id},
                {"$set": {"units": new_units}}
            )
            st.rerun()

        with exp:
            instruction = u.get("instruction", "").strip()
            if instruction:
                st.markdown(f"📝 **Instructions:** {instruction}")
            items = u.get("items", [])
            if not items:
                st.caption("No items in this unit yet.")
            else:
                for item in items:
                    item_title = item["title"]
                    item_type = item["type"]
                    with st.expander(f"{item_title}"):
                        st.markdown(f"**Type:** `{item_type}`")
                        instruction = item.get("instruction", "").strip()
                        if instruction:
                            st.markdown(f"📝 **Instructions:** {instruction}")
                        if "file_id" in item:
                            try:
                                fobj = fs.get(ObjectId(item["file_id"]))
                                preview_file(fobj, item.get("filename", ""))
                            except Exception as e:
                                st.warning(f"Unable to preview file: {e}")

if st.session_state.get("open_add_unit", False):
    with st.dialog("Create Unit"):
        with st.form("create_unit_form"):
            st.markdown("## Create Unit")

            unit_title = st.text_input("Unit title")
            unit_instruction = st.text_area(
                "Unit instructions",
                placeholder="Enter instructional text for this subunit"
            )

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

            # ------------------------
            # QUIZ BUILDER
            # ------------------------
            if item_type == "quiz":
                st.markdown("### ✍️ Add Quiz Question")

                q_text = st.text_input("Question text")

                st.markdown("Answer choices")
                choices = [st.text_input(f"Choice {i+1}") for i in range(4)]

                correct_index = st.radio(
                    "Correct answer",
                    options=range(4),
                    format_func=lambda i: f"Choice {i+1}"
                )

                col_q1, col_q2 = st.columns(2)
                with col_q1:
                    save_q = st.form_submit_button("💾 Save Question", key="save_question_btn")

                with col_q2:
                    add_more = st.form_submit_button("➕ Add Another Question", key="add_more_question_btn")

                if save_q or add_more:
                    if not q_text.strip() or any(c.strip() == "" for c in choices):
                        st.error("Please fill in the question and all choices.")
                    else:
                        st.session_state.quiz_builder["questions"].append({
                            "question": q_text.strip(),
                            "choices": choices,
                            "correct_index": correct_index,
                        })

                        st.success("Question added!")
                        st.rerun()

                st.markdown("### 📋 Current Questions")
                questions = st.session_state.quiz_builder["questions"]

                if not questions:
                    st.caption("No questions added yet.")
                else:
                    for i, q in enumerate(questions):

                        if st.session_state.editing_question_index == i:

                            st.markdown(f"### ✏️ Editing Question {i+1}")

                            new_q_text = st.text_input(
                                "Question text",
                                value=q["question"],
                                key=f"edit_qtext_{i}"
                            )

                            st.markdown("Answer choices")

                            new_choices = [
                                st.text_input(
                                    f"Choice {j+1}",
                                    value=c,
                                    key=f"edit_choice_{i}_{j}"
                                )
                                for j, c in enumerate(q["choices"])
                            ]

                            new_correct = st.radio(
                                "Correct answer",
                                options=range(len(new_choices)),
                                index=q["correct_index"],
                                format_func=lambda k: f"Choice {k+1}",
                                key=f"edit_correct_{i}"
                            )

                            colA, colB = st.columns(2)

                            with colA:
                                if st.form_submit_button("💾 Save", key=f"save_edit_{i}"):
                                    questions[i] = {
                                        "question": new_q_text.strip(),
                                        "choices": new_choices,
                                        "correct_index": new_correct
                                    }
                                    st.session_state.editing_question_index = None
                                    st.success("Question updated.")
                                    st.rerun()

                            with colB:
                                if st.form_submit_button("❌ Cancel", key=f"cancel_edit_{i}"):
                                    st.session_state.editing_question_index = None
                                    st.rerun()

                        else:
                            st.markdown(f"**Q{i+1}. {q['question']}**")

                            for j, c in enumerate(q["choices"]):
                                icon = "✅" if j == q["correct_index"] else "➖"
                                st.write(f"{icon} {c}")

                            col1, col2 = st.columns(2)

                            with col1:
                                if st.form_submit_button("✏️ Edit", key=f"edit_q_{i}"):
                                    st.session_state.editing_question_index = i
                                    st.rerun()

                            with col2:
                                if st.form_submit_button("🗑️ Delete", key=f"delete_q_{i}"):
                                    questions.pop(i)
                                    st.rerun()

            # ------------------------
            # COMMON FIELDS
            # ------------------------
            item_instruction = st.text_area(
                "Subunit instructions (optional)",
                placeholder="Page Instruction"
            )

            uploaded_files = st.file_uploader(
                "Upload files (multiple images allowed)",
                key=f"uploader_{st.session_state.uploader_key}",
                accept_multiple_files=True
            )

            # ------------------------
            # MUST BE INSIDE FORM
            # ------------------------
            add_item = st.form_submit_button("➕ Add item")
            create_unit = st.form_submit_button("Create Unit")
            cancel = st.form_submit_button("Cancel")

    if add_item:
        if not item_title.strip():
            st.error("Item title is required.")
        elif item_type in ["file", "video"] and not uploaded_files:
            st.error("Please upload at least one file.")

        else:
            if item_type in ["file", "video"] and uploaded_files:

                for f in uploaded_files:
                    file_bytes = f.read()
                    filename = f.name
                    mime_type = f.type

                    file_id = fs.put(
                        file_bytes,
                        filename=filename,
                        content_type=mime_type
                    )

                    next_item_id = len(st.session_state.new_unit_items)

                    new_item = {
                        "item_id": next_item_id,
                        "title": f"{item_title.strip()} — {filename}",
                        "type": "file",
                        "file_id": str(file_id),
                        "filename": filename,
                        "mime_type": mime_type,
                        "instruction": item_instruction.strip()
                    }

                    st.session_state.new_unit_items.append(new_item)

            else:
                next_item_id = len(st.session_state.new_unit_items)

                new_item = {
                    "item_id": next_item_id,
                    "title": item_title.strip(),
                    "type": item_type,
                    "instruction": item_instruction.strip()
                }

                # attach quiz questions if quiz item
                if item_type == "quiz":
                    new_item["quiz"] = st.session_state.quiz_builder["questions"]

                st.session_state.new_unit_items.append(new_item)

                # reset quiz state after saving quiz item
                st.session_state.quiz_builder = {"questions": []}
                st.session_state.editing_question_index = None
                st.session_state.uploader_key += 1


    if cancel:
        st.session_state.show_create_unit = False
        st.session_state.new_unit_items = []
        st.rerun()

    if create_unit:
        if not unit_title.strip():
            st.error("Unit title is required.")
        else:
            new_unit = {
                "unit_id": len(units),
                "title": unit_title.strip(),
                "instruction": unit_instruction.strip(),
                "items": st.session_state.new_unit_items
            }

            modules_collection.update_one(
                {"module_id": module_id},
                {"$push": {"units": new_unit}}
            )

            st.success("Unit created successfully!")
            st.session_state.show_create_unit = False
            st.session_state.new_unit_items = []
            st.rerun()
