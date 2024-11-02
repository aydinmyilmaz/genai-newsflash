import yaml
import json
import subprocess
import streamlit as st

def load_config():
    """Load configuration from the config.yml file."""
    with open('./config.yml', 'r') as file:
        return yaml.safe_load(file)

def load_file(file_path):
    """Load the content of a text file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def save_file(file_path, content):
    """Save the updated content back to a text file."""
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

def load_json(file_path):
    """Load JSON data from a file."""
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def count_items_in_json(file_path):
    """Count the number of items in a JSON file."""
    data = load_json(file_path)
    return sum(len(items) for items in data.values())  # Summing items in each category

def run_get_link_module():
    """Function to run the get_link module which updates the JSON file."""
    # Assuming the module is a Python script you can execute
    result = subprocess.run(['python', 'modules/get_link.py'], capture_output=True, text=True)
    return result

def load_data(scrapped_result_file_path):
    """Load data from the scrapped results JSON file."""
    with open(scrapped_result_file_path, 'r') as f:
        data = json.load(f)
    return data

def load_prompt(prompt_file_path):
    """Load the prompt from the specified file path."""
    with open(prompt_file_path, 'r') as f:
        return f.read()

def save_prompt(updated_prompt, prompt_file_path):
    """Save the updated prompt to the specified file path."""
    with open(prompt_file_path, 'w') as f:
        f.write(updated_prompt)

def auth_check():
    # Authentication check at the start
    if not st.session_state.get('user_email'):
        st.warning("⚠️ Please log in using the Intro sidebar to access the Smart Link Summarizer.")
        st.info("👉 Use the authentication panel in the sidebar to log in or sign up.")
        st.stop()

# Function to update configuration via Streamlit
def update_config():
    with st.sidebar.expander("Update Configuration", expanded=False):
        # Input fields for API key and model name
        new_api_key = st.text_input("API Key", placeholder="Enter your API key here")

        # Dropdown for model selection
        model_options = ["gpt-4o", "gpt-4o-mini", "llama-3.1-8b-instruct"]
        new_model_name = st.selectbox("Model Selection:", model_options)

        if st.button("Save Configuration"):
            with open('config.yml', 'r') as file:
                config = yaml.safe_load(file)

            # Update the config
            config['OPENAI_API_KEY'] = new_api_key
            config['openai_model_name'] = new_model_name

            # Write back to the config file
            with open('config.yml', 'w') as file:
                yaml.dump(config, file)

            st.success("Config updated successfully.")
        else:
            st.warning("Please approve the changes to update the config.")
