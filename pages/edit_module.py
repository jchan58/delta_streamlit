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
        with st.expander(f"Unit {u['unit_id']} — {u['title']}", expanded=False):
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

if st.session_state.show_create_unit:
    st.markdown("---")
    with st.form("create_unit_form"):
        st.markdown("## Create Unit")

        unit_title = st.text_input("Unit title")
        unit_instruction = st.text_area("Unit instructions", placeholder="Enter instructional text for this subunit")

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

            add_q = st.form_submit_button("➕ Save Question", key="save_question_btn")

    if add_q:
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

    st.markdown("### 📋 {item_title}")
    questions = st.session_state.quiz_builder["questions"]
    if not questions:
        st.caption("No questions added yet.")
    else:
        for i, q in enumerate(questions):

            # If this question is in edit mode
            if st.session_state.editing_question_index == i:

                st.markdown(f"### ✏️ Editing Question {i+1}")

                # Editable fields
                new_q_text = st.text_input(
                    "Question text",
                    value=q["question"],
                    key=f"edit_qtext_{i}"
                )

                st.markdown("Answer choices")

                new_choices = []
                for j, c in enumerate(q["choices"]):
                    new_choices.append(
                        st.text_input(
                            f"Choice {j+1}",
                            value=c,
                            key=f"edit_choice_{i}_{j}"
                        )
                    )

                new_correct = st.radio(
                    "Correct answer",
                    options=range(len(new_choices)),
                    index=q["correct_index"],
                    format_func=lambda k: f"Choice {k+1}",
                    key=f"edit_correct_{i}"
                )

                colA, colB = st.columns(2)

                # Save edits
                with colA:
                    if st.button("💾 Save", key=f"save_edit_{i}"):

                        questions[i] = {
                            "question": new_q_text.strip(),
                            "choices": new_choices,
                            "correct_index": new_correct
                        }

                        st.session_state.editing_question_index = None
                        st.success("Question updated.")
                        st.rerun()

                # Cancel editing
                with colB:
                    if st.button("❌ Cancel", key=f"cancel_edit_{i}"):
                        st.session_state.editing_question_index = None
                        st.rerun()

            else:
                # Normal view mode
                with st.container():
                    st.markdown(f"**Q{i+1}. {q['question']}**")

                    for j, c in enumerate(q["choices"]):
                        mark = "✅" if j == q["correct_index"] else "➖"
                        st.write(f"{mark} {c}")

                    col1, col2 = st.columns(2)

                    # Edit button
                    with col1:
                        if st.button("✏️ Edit", key=f"edit_q_{i}"):
                            st.session_state.editing_question_index = i
                            st.rerun()

                    # Delete button
                    with col2:
                        if st.button("🗑️ Delete", key=f"delete_q_{i}"):
                            questions.pop(i)
                            st.rerun()


        item_instruction = st.text_area(
            "Subunit instructions (optional)",
            placeholder="Page Instruction"
        )

        uploaded_files = st.file_uploader(
            "Upload files (multiple images allowed)",
            key=f"uploader_{st.session_state.uploader_key}",
            accept_multiple_files=True
        )

        add_item = st.form_submit_button("➕ Add item")
        create_unit = st.form_submit_button("Create Unit")
        cancel = st.form_submit_button("Cancel")


    if add_item:
        if not item_title.strip():
            st.error("Item title is required.")
        elif item_type == "file" and not uploaded_files:
            st.error("Please upload at least one file.")

        else:
            if item_type == "file" and uploaded_files:

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
                # Non-file item (quiz, video, etc.)
                next_item_id = len(st.session_state.new_unit_items)

                new_item = {
                    "item_id": next_item_id,
                    "title": item_title.strip(),
                    "type": item_type,
                    "instruction": item_instruction.strip()
                }
                st.session_state.new_unit_items.append(new_item)

            # reset uploader for next add
            st.session_state.uploader_key += 1
            st.rerun()

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
