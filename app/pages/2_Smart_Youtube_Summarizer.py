# #Smart_Youtube_Summarizer.py
# import os
# import re
# import json
# import yaml
# import sys
# import logging
# import streamlit as st
# from datetime import datetime
# from docx import Document
# import tiktoken

# from langchain.llms import OpenAI
# from langchain.callbacks import StdOutCallbackHandler
# from langchain.chat_models import ChatOpenAI
# from langchain.schema import HumanMessage
# from langchain.prompts import PromptTemplate

# from modules.youtube_summary_manager import youtube_summary_manager, save_youtube_summary_to_docx

# # Set up logging
# logging.basicConfig(level=logging.INFO,
#                     format='%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s')
# logger = logging.getLogger(__name__)

# with open('./config.yml', 'r') as config_file:
#     config = yaml.safe_load(config_file)
#     logger.info("Config loaded successfully.")
#     # Set the environment variable for the API key
#     os.environ['OPENAI_API_KEY'] = config['OPENAI_API_KEY']
#     model_name = config['openai_model_name']


# # Ensure the necessary directories exist
# os.makedirs('./output/transcripts_youtube', exist_ok=True)
# os.makedirs('./outpur/summaries_youtube', exist_ok=True)
# os.makedirs('./output/summaries_article', exist_ok=True)


# # Set Streamlit page configuration
# st.set_page_config(layout="wide", page_title="YouTube Transcript Summarizer")

# def load_transcript_json():
#     """
#     Loads a JSON file containing transcript data from the specified directory.

#     Returns:
#         tuple: Loaded transcripts data and the selected file name.
#     """
#     transcripts_folder = config['file_paths']['youtube_transcripts_folder']
#     # Correctly list the files in the transcripts folder
#     transcript_files = [f for f in os.listdir(transcripts_folder) if f.endswith('.json')]
#     if not transcript_files:
#         st.warning(f"No transcript files found in {transcripts_folder}. Please run the transcript retrieval process first.")
#         return None, None

#     selected_file = st.selectbox("Select a transcript JSON file to load:", transcript_files)
#     file_path = os.path.join(transcripts_folder, selected_file)  # Correctly construct the file path
#     with open(file_path, 'r', encoding='utf-8') as f:
#         transcripts_data = json.load(f)

#     return transcripts_data, selected_file

# def load_main_prompt():
#     """
#     Loads the main prompt from the prompt folder.

#     Returns:
#         str: The main prompt text, if available.
#     """
#     prompt_path = config['file_paths']['main_prompt_youtube'] #'./sources/prompts/main_prompt_youtube.txt'
#     if os.path.exists(prompt_path):
#         with open(prompt_path, 'r', encoding='utf-8') as f:
#             return f.read().strip()
#     else:
#         return (
#             "You are an expert summarizer. Your task is to summarize the following YouTube transcript:\n\n"
#             "{transcript}\n\n"
#             "Please provide a concise summary that captures the main points."
#         )

# def load_and_edit_prompt():
#     """
#     Allows the user to load, edit, and save the main prompt for summarization.

#     Returns:
#         str: The edited prompt text.
#     """
#     default_prompt = load_main_prompt()
#     if "{transcript}" not in default_prompt:
#         st.error("The prompt must contain the placeholder '{transcript}' to correctly format the transcript.")
#     edited_prompt = st.text_area("Edit Prompt", default_prompt, height=200)
#     return edited_prompt

# def generate_summaries(transcripts_data, prompt_template, model_name=model_name):
#     """
#     Generates summaries for the provided transcripts using the specified prompt template.

#     Args:
#         transcripts_data (dict): The dictionary containing transcript data.
#         prompt_template (str): The prompt template to use for summarization.
#         model_name (str): The name of the model to use (default is model_name).

#     Returns:
#         dict: Dictionary containing summaries for each video.
#     """
#     # Initialize LangChain Chat model
#     chat_model = ChatOpenAI(temperature=0.1, model=model_name)

#     # Create a callback handler to capture verbose output
#     handler = StdOutCallbackHandler()

#     # Create a PromptTemplate
#     try:
#         prompt = PromptTemplate(template=prompt_template, input_variables=["transcript"])
#     except Exception as e:
#         st.error(f"Error in prompt template: {e}")
#         return {}

#     summaries = {}
#     progress_bar = st.progress(0)
#     total_transcripts = len(transcripts_data)

#     for idx, (video_id, data) in enumerate(transcripts_data.items()):
#         progress = (idx + 1) / total_transcripts
#         progress_bar.progress(progress)

#         transcript = data.get('transcript')
#         if transcript:
#             # Use tiktoken to count tokens and truncate if necessary
#             try:
#                 encoding = tiktoken.encoding_for_model(model_name)
#             except KeyError:
#                 st.error(f"Unknown encoding for model: {model_name}")
#                 continue
#             tokens = encoding.encode(transcript)
#             token_limit = 16000

#             if len(tokens) > token_limit:
#                 tokens = tokens[:15000]
#                 transcript = encoding.decode(tokens)
#                 truncated_message = f"[INFO] The transcript was truncated from {len(tokens)} tokens to 15,000 tokens."
#                 st.info(truncated_message)
#                 logger.info(truncated_message)

#             # Format the prompt with the transcript
#             try:
#                 formatted_prompt = prompt.format(transcript=transcript)
#             except KeyError as e:
#                 st.error(f"Missing placeholder in prompt: {e}")
#                 continue

#             messages = [HumanMessage(content=formatted_prompt)]

#             # Redirect stdout to capture verbose output
#             original_stdout = sys.stdout
#             sys.stdout = sys.__stdout__  # Use the original stdout for printing

#             # Generate the summary
#             try:
#                 response = chat_model.generate([messages], callbacks=[handler])
#                 summary = response.generations[0][0].text
#             except Exception as e:
#                 st.error(f"Error during summary generation: {e}")
#                 summary = "Error generating summary."

#             # Restore the original stdout
#             sys.stdout = original_stdout

#             summaries[video_id] = {
#                 'summary': summary,
#                 'token_count': data.get('token_count'),
#                 'link': data.get('link'),
#                 'truncated': len(tokens) > token_limit
#             }
#         else:
#             summaries[video_id] = {
#                 'summary': "Transcript not available",
#                 'token_count': data.get('token_count'),
#                 'link': data.get('link')
#             }

#     return summaries

# def save_summaries_to_json(summaries):
#     """
#     Saves the generated summaries to a JSON file.

#     Args:
#         summaries (dict): The dictionary containing summaries.

#     Returns:
#         str: The file path where the summaries are saved.
#     """
#     current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
#     folder = config['file_paths']['output_dir_youtube']
#     output_file_path = f"{folder}/summaries_{current_time}.json"

#     with open(output_file_path, 'w', encoding='utf-8') as f:
#         json.dump(summaries, f, ensure_ascii=False, indent=4)

#     return output_file_path

# def load_summary_files():
#     """
#     Loads summary files from the summaries directory.

#     Returns:
#         list: List of summary files with modification timestamps.
#     """

#     #summaries_dir = os.path.join(os.getcwd(), 'data', 'summaries')
#     summaries_dir = config['file_paths']['output_dir_youtube']
#     logger.debug(f"Summaries directory path: {summaries_dir}")

#     if not os.path.exists(summaries_dir):
#         logger.error(f"The summaries directory does not exist: {summaries_dir}")
#         return []

#     json_files = [f for f in os.listdir(summaries_dir) if f.endswith('.json')]
#     if not json_files:
#         logger.error("No summary files found.")
#         return []

#     json_files.sort(key=lambda x: os.path.getmtime(os.path.join(summaries_dir, x)), reverse=True)
#     file_options = [(f, datetime.fromtimestamp(os.path.getmtime(os.path.join(summaries_dir, f))).strftime('%Y-%m-%d %H:%M:%S')) for f in json_files]
#     return file_options

# def load_summary_content(file_name):
#     """
#     Loads the content of a summary file.

#     Args:
#         file_name (str): The name of the summary file to load.

#     Returns:
#         dict or str: Loaded content of the summary file or raw text if JSON decoding fails.
#     """
#     # summaries_dir = os.path.join(os.getcwd(), 'data', 'summaries')
#     summaries_dir = config['file_paths']['output_dir_youtube']
#     file_path = os.path.join(summaries_dir, file_name)
#     try:
#         with open(file_path, 'r') as json_file:
#             content = json.load(json_file)
#         logger.debug(f"Successfully loaded content from {file_name}")
#         return content
#     except json.JSONDecodeError as e:
#         logger.error(f"JSON decoding error in {file_name}: {e}")
#         st.error(f"Error decoding JSON in {file_name}. Displaying raw content.")
#         with open(file_path, 'r') as file:
#             return file.read()
#     except Exception as e:
#         logger.error(f"Error loading content from {file_name}: {e}")
#         return None

# def view_summaries():
#     file_options = load_summary_files()
#     if not file_options:
#         st.error("No summary files found.")
#         return

#     selected_file = st.selectbox("Select a summary file to view:", options=file_options, format_func=lambda x: f"{x[0]} (Last modified: {x[1]})")
#     if selected_file:
#         content = load_summary_content(selected_file[0])
#         if content and st.checkbox('Show Content'):
#             st.subheader(f"Summary File: {selected_file[0]}")
#             st.json(content)

#             # Remove the multiselect and save everything directly
#         if st.button("Save as .docx"):
#             file_path = save_youtube_summary_to_docx(content, selected_file[0])
#             if file_path:  # If the file was saved successfully
#                 with open(file_path, "rb") as f:
#                     st.download_button(
#                         label="Download .docx file",
#                         data=f,
#                         file_name=os.path.basename(file_path),
#                         mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
#                     )

# def main():
#     st.header("🔍 Smart YouTube Summarizer")

#     # Expander for YouTube summary generation with an updated name
#     with st.expander("📼 Generate YouTube Transcripts", expanded=False):
#         youtube_summary_manager()  # Call the youtube_summary_manager function

#     # Expander for summary process management
#     with st.expander("📝 Manage Summarization Process", expanded=True):
#         tabs = st.tabs(["📂 Load Transcript Data", "📝 Edit Prompt", "⚙️ Generate Summaries"])

#         with tabs[0]:
#             transcripts_data, selected_file = load_transcript_json()
#             if transcripts_data:
#                 st.success(f"Loaded transcript file: {selected_file}")

#         with tabs[1]:
#             st.caption("Edit the prompt to customize how the transcript will be summarized.")
#             prompt_template = load_and_edit_prompt()

#             # Add Approval Button
#             approved = st.button("✅ Approve Prompt")
#             if approved:
#                 if "{transcript}" in prompt_template:
#                     st.session_state['prompt_approved'] = prompt_template
#                     st.success("Prompt approved successfully! You can now generate summaries.")
#                 else:
#                     st.error("The prompt must contain the placeholder '{transcript}' to be approved.")

#         with tabs[2]:
#             if 'prompt_approved' in st.session_state:
#                 if st.button("🚀 Generate Summaries"):
#                     with st.spinner("Generating summaries... ⏳"):
#                         summaries = generate_summaries(transcripts_data, st.session_state['prompt_approved'])
#                         st.success("Summaries generated successfully!")

#                         # Save summaries to JSON file
#                         output_file_path = save_summaries_to_json(summaries)
#                         st.success(f"Summaries saved to '{output_file_path}'")

#     # Expander for viewing generated summaries
#     with st.expander("📄 View Summaries", expanded=False):
#         view_summaries()

# if __name__ == "__main__":
#     main()

import os
import re
import json
import yaml
import sys
import logging
import streamlit as st
from datetime import datetime
from docx import Document
import tiktoken

from langchain.llms import OpenAI
from langchain.callbacks import StdOutCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from langchain.prompts import PromptTemplate

from modules.youtube_summary_manager import youtube_summary_manager, save_youtube_summary_to_docx

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s')
logger = logging.getLogger(__name__)

with open('./config.yml', 'r') as config_file:
    config = yaml.safe_load(config_file)
    logger.info("Config loaded successfully.")
    # Set the environment variable for the API key
    os.environ['OPENAI_API_KEY'] = config['OPENAI_API_KEY']
    model_name = config['openai_model_name']

# Ensure the necessary directories exist
def ensure_directories():
    """
    Ensure that the necessary directories exist for output files.
    """
    directories = ['./output/transcripts_youtube', './output/summaries_youtube', './output/summaries_article']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Ensured existence of directory: {directory}")

ensure_directories()

# Set Streamlit page configuration
st.set_page_config(layout="wide", page_title="YouTube Transcript Summarizer")


def load_transcripts_folder():
    """
    Loads the list of available transcript files from the configured folder.

    Returns:
        list: List of transcript file names.
    """
    transcripts_folder = config['file_paths']['youtube_transcripts_folder']
    transcript_files = [f for f in os.listdir(transcripts_folder) if f.endswith('.json')]
    logger.info(f"Transcript files loaded from {transcripts_folder}: {transcript_files}")
    return transcripts_folder, transcript_files


def load_selected_transcript(transcripts_folder, selected_file):
    """
    Load the content of the selected transcript file.

    Args:
        transcripts_folder (str): Path to the transcripts folder.
        selected_file (str): Name of the selected file.

    Returns:
        dict: Loaded transcript data.
    """
    file_path = os.path.join(transcripts_folder, selected_file)
    with open(file_path, 'r', encoding='utf-8') as f:
        transcripts_data = json.load(f)
    logger.info(f"Transcript file loaded: {selected_file}")
    return transcripts_data


def load_transcript_json():
    """
    Load a JSON file containing transcript data from the specified directory.

    Returns:
        tuple: Loaded transcripts data and the selected file name.
    """
    transcripts_folder, transcript_files = load_transcripts_folder()
    if not transcript_files:
        st.warning(f"No transcript files found in {transcripts_folder}. Please run the transcript retrieval process first.")
        return None, None

    selected_file = st.selectbox("Select a transcript JSON file to load:", transcript_files)
    transcripts_data = load_selected_transcript(transcripts_folder, selected_file)
    return transcripts_data, selected_file


def load_main_prompt():
    """
    Loads the main prompt from the prompt folder.

    Returns:
        str: The main prompt text, if available.
    """
    prompt_path = config['file_paths']['main_prompt_youtube']
    if os.path.exists(prompt_path):
        with open(prompt_path, 'r', encoding='utf-8') as f:
            logger.info("Main prompt loaded successfully.")
            return f.read().strip()
    else:
        logger.warning("Main prompt not found, using default prompt.")
        return (
            "You are an expert summarizer. Your task is to summarize the following YouTube transcript:\n\n"
            "{transcript}\n\n"
            "Please provide a concise summary that captures the main points."
        )


def load_and_edit_prompt():
    """
    Allows the user to load, edit, and save the main prompt for summarization.

    Returns:
        str: The edited prompt text.
    """
    default_prompt = load_main_prompt()
    if "{transcript}" not in default_prompt:
        st.error("The prompt must contain the placeholder '{transcript}' to correctly format the transcript.")
    edited_prompt = st.text_area("Edit Prompt", default_prompt, height=200)
    logger.info("Prompt loaded for editing.")
    return edited_prompt


def process_transcript(transcript, model_name):
    """
    Processes the transcript by truncating it if it exceeds the token limit.

    Args:
        transcript (str): Transcript content.
        model_name (str): The name of the model to use.

    Returns:
        tuple: Truncated transcript if needed, and a flag indicating truncation.
    """
    try:
        encoding = tiktoken.encoding_for_model(model_name)
    except KeyError:
        st.error(f"Unknown encoding for model: {model_name}")
        return transcript, False

    tokens_original = encoding.encode(transcript)
    token_limit = 16000

    if len(tokens_original) > token_limit:
        tokens = tokens_original[:15500]
        transcript = encoding.decode(tokens)
        truncated_message = f"[INFO] The transcript was truncated from {len(tokens_original)} tokens to 15,500 tokens."
        st.info(truncated_message)
        logger.info(truncated_message)
        return transcript, True

    return transcript, False


def generate_summary(chat_model, prompt, transcript):
    """
    Generates a summary for a given transcript using the chat model.

    Args:
        chat_model: The chat model instance.
        prompt: The formatted prompt.
        transcript: The transcript to summarize.

    Returns:
        str: Generated summary or error message.
    """
    try:
        messages = [HumanMessage(content=prompt)]
        response = chat_model.generate([messages])
        summary = response.generations[0][0].text
        return summary
    except Exception as e:
        error_message = f"Error during summary generation: {e}"
        st.error(error_message)
        logger.error(error_message)
        return "Error generating summary."


def generate_summaries(transcripts_data, prompt_template, model_name=model_name):
    """
    Generates summaries for the provided transcripts using the specified prompt template.

    Args:
        transcripts_data (dict): The dictionary containing transcript data.
        prompt_template (str): The prompt template to use for summarization.
        model_name (str): The name of the model to use.

    Returns:
        dict: Dictionary containing summaries for each video.
    """
    chat_model = ChatOpenAI(temperature=0.1, model=model_name)
    summaries = {}
    progress_bar = st.progress(0)
    total_transcripts = len(transcripts_data)

    for idx, (video_id, data) in enumerate(transcripts_data.items()):
        progress_bar.progress((idx + 1) / total_transcripts)
        transcript = data.get('transcript')

        if transcript:
            transcript, truncated = process_transcript(transcript, model_name)
            try:
                prompt = PromptTemplate(template=prompt_template, input_variables=["transcript"]).format(transcript=transcript)
            except KeyError as e:
                st.error(f"Missing placeholder in prompt: {e}")
                logger.error(f"Error in prompt template: {e}")
                continue

            summary = generate_summary(chat_model, prompt, transcript)
            summaries[video_id] = {
                'summary': summary,
                'token_count': data.get('token_count'),
                'link': data.get('link'),
                'truncated': truncated
            }
        else:
            summaries[video_id] = {
                'summary': "Transcript not available",
                'token_count': data.get('token_count'),
                'link': data.get('link')
            }

    logger.info("Summaries generation completed.")
    return summaries


def save_summaries_to_json(summaries):
    """
    Saves the generated summaries to a JSON file.

    Args:
        summaries (dict): The dictionary containing summaries.

    Returns:
        str: The file path where the summaries are saved.
    """
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = config['file_paths']['output_dir_youtube']
    output_file_path = f"{folder}/summaries_{current_time}.json"

    with open(output_file_path, 'w', encoding='utf-8') as f:
        json.dump(summaries, f, ensure_ascii=False, indent=4)

    logger.info(f"Summaries saved to file: {output_file_path}")
    return output_file_path


def load_summary_files():
    """
    Loads summary files from the summaries directory.

    Returns:
        list: List of summary files with modification timestamps.
    """
    summaries_dir = config['file_paths']['output_dir_youtube']
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
    """
    Loads the content of a summary file.

    Args:
        file_name (str): The name of the summary file to load.

    Returns:
        dict or str: Loaded content of the summary file or raw text if JSON decoding fails.
    """
    summaries_dir = config['file_paths']['output_dir_youtube']
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


def view_summaries():
    """
    Provides an interface for viewing generated summaries.
    """
    file_options = load_summary_files()
    if not file_options:
        st.error("No summary files found.")
        return

    selected_file = st.selectbox("Select a summary file to view:", options=file_options, format_func=lambda x: f"{x[0]} (Last modified: {x[1]})")
    if selected_file:
        content = load_summary_content(selected_file[0])
        if content and st.checkbox('Show Content'):
            st.subheader(f"Summary File: {selected_file[0]}")
            st.json(content)

            # Remove the multiselect and save everything directly
        if st.button("Save as .docx"):
            file_path = save_youtube_summary_to_docx(content, selected_file[0])
            if file_path:  # If the file was saved successfully
                with open(file_path, "rb") as f:
                    st.download_button(
                        label="Download .docx file",
                        data=f,
                        file_name=os.path.basename(file_path),
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )


def main():
    st.header("\U0001F50D Smart YouTube Summarizer")

    # Expander for YouTube summary generation with an updated name
    with st.expander("\U0001F4FC Generate YouTube Transcripts", expanded=False):
        youtube_summary_manager()  # Call the youtube_summary_manager function

    # Expander for summary process management
    with st.expander("\U0001F4DD Manage Summarization Process", expanded=True):
        tabs = st.tabs(["\U0001F4C2 Load Transcript Data", "\U0001F4DD Edit Prompt", "\u2699\ufe0f Generate Summaries"])

        transcripts_data = None
        with tabs[0]:
            transcripts_data, selected_file = load_transcript_json()
            if transcripts_data:
                st.success(f"Loaded transcript file: {selected_file}")

        prompt_template = None
        with tabs[1]:
            st.caption("Edit the prompt to customize how the transcript will be summarized.")
            prompt_template = load_and_edit_prompt()

            # Add Approval Button
            approved = st.button("\u2705 Approve Prompt")
            if approved:
                if "{transcript}" in prompt_template:
                    st.session_state['prompt_approved'] = prompt_template
                    st.success("Prompt approved successfully! You can now generate summaries.")
                else:
                    st.error("The prompt must contain the placeholder '{transcript}' to be approved.")

        if transcripts_data and 'prompt_approved' in st.session_state:
            with tabs[2]:
                if st.button("\U0001F680 Generate Summaries"):
                    with st.spinner("Generating summaries... \u23F3"):
                        summaries = generate_summaries(transcripts_data, st.session_state['prompt_approved'])
                        st.success("Summaries generated successfully!")

                        # Save summaries to JSON file
                        output_file_path = save_summaries_to_json(summaries)
                        st.success(f"Summaries saved to '{output_file_path}'")

    # Expander for viewing generated summaries
    with st.expander("\U0001F4C4 View Summaries", expanded=False):
        view_summaries()


if __name__ == "__main__":
    main()
