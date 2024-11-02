import os
import json
import streamlit as st
import logging

# Ensure these modules are correctly handling the paths and parameters
from modules.utils.helpers import load_file, save_file, count_items_in_json, load_json, load_config
# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Create a logger for this module
logger = logging.getLogger(__name__)

# Optionally, you can add a file handler
file_handler = logging.FileHandler('app.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

def file_editor(tab_title, file_path):
    with st.container():
        st.subheader(f"Edit {tab_title}")
        current_content = load_file(file_path)
        updated_content = st.text_area("Edit the content:", value=current_content, height=300, key=f"{tab_title}_content")

        col1, col2 = st.columns(2)

        with col1:
            if st.button(f"Add to {tab_title}", key=f"add_{tab_title}"):
                save_file(file_path, updated_content)
                st.success("Changes saved successfully!")
                st.balloons()
                logger.info(f"Changes saved to {file_path}")
                st.rerun()

        with col2:
            if st.button(f"🗑️ Delete {tab_title} Content", key=f"delete_{tab_title}"):
                st.session_state[f"{tab_title}_delete_confirm"] = True  # Set deletion confirm state
                st.warning("Are you sure you want to delete the content? Click 'Confirm Deletion' to proceed.")
                logger.warning(f"Deletion of {tab_title} content initiated")

            if st.session_state.get(f"{tab_title}_delete_confirm", False):  # Check if deletion has been initiated
                if st.button("⚠️ Confirm Deletion", key=f"confirm_delete_{tab_title}"):
                    save_file(file_path, "")  # Clear the file content
                    st.success(f"{tab_title} content deleted successfully!")
                    del st.session_state[f"{tab_title}_delete_confirm"]  # Reset the deletion confirm state
                    logger.info(f"{tab_title} content deleted from {file_path}")
                    st.rerun()

def display_file_content(file_path):
    """Display the content of a file."""
    content = load_file(file_path)
    st.text_area("File Content:", value=content, height=200, disabled=True)
    logger.debug(f"Displayed content of {file_path}")

def display_links_as_strings(file_path):
    """Display links as strings, not clickable links."""
    data = load_json(file_path)
    if not data:
        st.write("No data available in the search result file.")
        logger.warning(f"No data found in {file_path}")
        return
    topic = st.selectbox("Select a topic to view links", list(data.keys()))
    if topic in data:
        st.subheader(f"Links for topic: {topic}")
        for item in data[topic]:
            st.write(f"Title: {item['title']}")
            st.write(f"Link (string): {item['link']}")
            st.write(f"Snippet: {item['snippet']}")
            st.write("---")  # Line separator
        logger.info(f"Displayed links for topic {topic} from {file_path}")


def link_content_manager():
    logger.info("Starting Streamlit application")
    config = load_config()

    # Verify that 'file_paths' exists in the config and contains 'link_file'
    if 'file_paths' in config and 'edited_link_file' in config['file_paths']:
        link_file_path = config['file_paths']['edited_link_file']
    else:
        st.error("Configuration for 'link_file' is missing or incorrect.")
        logger.error("Configuration for 'link_file' is missing or incorrect.")
        return

    topic_path = config['file_paths'].get('topic_file', './sources/topic.txt')
    link_path = config['file_paths'].get('edited_link_file', './sources/article_links.txt')
    search_result_path = link_file_path  # Using the corrected variable

    file_editor("Link File", link_path)
    # Create tabs instead of expanders
    tabs = st.tabs(["🔗 View Links Details", "📋 View Link File Content"])

    with tabs[0]:
        display_links_as_strings(search_result_path)

    with tabs[1]:
        if st.button("🔍 Show Link Content"):
            display_file_content(link_path)


if __name__ == '__main__':
    link_content_manager()
