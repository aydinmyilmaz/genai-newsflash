import os
import json
import streamlit as st
import logging
from datetime import datetime
from docx import Document  # Import the Document class from python-docx
import re  # Import re for sanitizing filenames

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_summary_files():
    summaries_dir = os.path.join(os.getcwd(), 'data', 'summaries')
    logger.debug(f"Summaries directory path: {summaries_dir}")

    if not os.path.exists(summaries_dir):
        logger.error(f"The summaries directory does not exist: {summaries_dir}")
        return []

    json_files = [f for f in os.listdir(summaries_dir) if f.endswith('.json')]
    if not json_files:
        logger.error("No summary files found.")
        return []

    json_files.sort(key=lambda x: os.path.getmtime(os.path.join(summaries_dir, x)), reverse=True)
    file_options = [(f, datetime.fromtimestamp(os.path.getmtime(os.path.join(summaries_dir, f))).strftime('%Y-%m-%d %H:%M:%S')) for f in json_files]
    return file_options

def load_summary_content(file_name):
    summaries_dir = os.path.join(os.getcwd(), 'data', 'summaries')
    file_path = os.path.join(summaries_dir, file_name)
    try:
        with open(file_path, 'r') as json_file:
            content = json.load(json_file)
        logger.debug(f"Successfully loaded content from {file_name}")
        return content
    except json.JSONDecodeError as e:
        logger.error(f"JSON decoding error in {file_name}: {e}")
        st.error(f"Error decoding JSON in {file_name}. Displaying raw content.")
        with open(file_path, 'r') as file:
            return file.read()
    except Exception as e:
        logger.error(f"Error loading content from {file_name}: {e}")
        return None

def display_dictionary_content(dictionary, selected_keys):
    """Display selected keys from a dictionary using Markdown."""
    for key in selected_keys:
        if key in dictionary:
            value = dictionary[key]
            st.markdown(f"#### {key}")  # Use Markdown for key headings
            if isinstance(value, list):
                # Join list items into a Markdown-friendly string with bullet points
                list_items = '\n'.join(f"- {item}" for item in value)
                st.markdown(list_items)
            else:
                # Display other types of values directly as text
                st.markdown(value)
            st.markdown("---")  # Add a separator for readability

def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def save_to_docx(content, json_file_name, selected_keys):
    """Save the selected parts of the displayed content to a .docx file in the output folder."""
    doc = Document()
    base_name = os.path.splitext(json_file_name)[0]  # Get the base name without extension
    doc.add_heading(base_name, level=1)

    if isinstance(content, list):
        for index, item in enumerate(content):
            if isinstance(item, dict):
                # Only include the selected keys
                filtered_item = {key: item[key] for key in selected_keys if key in item}
                doc.add_heading(f"Item {index + 1}", level=2)
                for key, value in filtered_item.items():
                    doc.add_heading(key, level=3)
                    if isinstance(value, list):
                        for list_item in value:
                            doc.add_paragraph(f"- {list_item}")
                    else:
                        doc.add_paragraph(str(value))
            else:
                doc.add_paragraph(str(item))
    else:
        doc.add_paragraph(json.dumps(content, indent=4))

    output_folder = "output"  # Specify the output folder
    os.makedirs(output_folder, exist_ok=True)  # Create the folder if it doesn't exist
    file_path = os.path.join(output_folder, f"{sanitize_filename(base_name)}.docx")  # Save in the output folder
    try:
        doc.save(file_path)
        st.success(f"Saved {file_path} successfully!")
        return file_path  # Return the file path for download
    except Exception as e:
        logger.error(f"Error saving .docx file: {e}")
        st.error("Failed to save the .docx file.")
        return None

def display_content_in_new_page(content):
    st.subheader("Content in New Page")
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict):
                display_dictionary_content(item, st.session_state.selected_keys)
            else:
                st.error("The selected item is not a dictionary.")
    else:
        st.warning("Content is not in list format. Displaying all content as JSON.")
        st.json(content)

def view_link_summaries():
    file_options = load_summary_files()
    if not file_options:
        st.error("No summary files found.")
        return

    selected_file = st.selectbox("Select a summary file to view:", options=file_options, format_func=lambda x: f"{x[0]} (Last modified: {x[1]})")

    if selected_file:
        content = load_summary_content(selected_file[0])
        if content:
            if isinstance(content, list):
                item_options = [f"Item {i + 1}" for i in range(len(content))]
                selected_items = st.multiselect("Select items to display:", item_options)
                selected_indices = [int(item.split()[-1]) - 1 for item in selected_items]

                # Collect all possible keys from the selected items in the content
                all_possible_keys = set()
                for index in selected_indices:
                    if isinstance(content[index], dict):
                        all_possible_keys.update(content[index].keys())

                # Convert the set to a list
                possible_keys = list(all_possible_keys)

                # Multi-select box for all possible text parts, with default as all possible keys
                selected_keys = st.multiselect(
                    "Select parts to display for selected items:",
                    possible_keys,
                    default=possible_keys  # Set default selections to all possible keys
                )

                # Checkbox to control display of selected parts
                display_selected = st.checkbox("Display selected parts")

                # Display the selected parts for all selected items if the checkbox is checked
                if display_selected:
                    for index in selected_indices:
                        dictionary = content[index]
                        if isinstance(dictionary, dict):
                            display_dictionary_content(dictionary, selected_keys)
                        else:
                            st.error("The selected item is not a dictionary.")
            else:
                st.warning("Content is not in list format. Displaying all content as JSON.")
                st.json(content)

            # Move the "Save as .docx" button below the checkbox
            if st.button("Save as .docx"):
                if selected_keys:
                    file_path = save_to_docx(content, selected_file[0], selected_keys)  # Pass the selected keys
                    if file_path:  # If the file was saved successfully
                        with open(file_path, "rb") as f:
                            st.download_button(
                                label="Download .docx file",
                                data=f,
                                file_name=os.path.basename(file_path),
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            )
                else:
                    st.error("Please select parts to display before saving.")
        else:
            st.error("Failed to load the selected file content.")

if __name__ == "__main__":
    view_link_summaries()




