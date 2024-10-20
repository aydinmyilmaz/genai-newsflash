import streamlit as st
import json
import os
from modules.smart_graph_scraper import smart_graph_scrap, load_config
from modules.link_content_manager import link_content_manager
from modules.view_link_summaries import view_link_summaries
import tempfile
import logging
from datetime import datetime
import time
import hashlib

# Set page configuration at the top
st.set_page_config(layout="wide", page_title="Smart Link Summarizer")

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s')
logger = logging.getLogger(__name__)

# Add custom CSS for styling
st.markdown(
    """
    <style>
    .stButton > button {
        background-color: #007BFF; /* Blue */
        color: white;
        border: 2px solid #007BFF; /* Blue border */
        padding: 10px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 5px;
        transition: background-color 0.3s, border-color 0.3s, color 0.3s;
    }
    .stButton > button:hover {
        background-color: #0056b3; /* Darker blue */
        border-color: #0056b3; /* Darker blue border */
        color: white; /* Keep text white on hover */
    }
    .stButton > button:focus {
        outline: none; /* Remove default focus outline */
        box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.5); /* Add a blue shadow on focus */
    }
    .stTextInput input, .stTextArea textarea {
        border: 2px solid #007BFF; /* Blue */
        border-radius: 5px;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #0056b3; /* Darker blue */
    }
    .stCheckbox > label {
        color: #007BFF; /* Blue */
    }
    .stMarkdown {
        color: #333; /* Dark gray */
    }
    </style>
    """,
    unsafe_allow_html=True
)

def tooltip(text, help_text):
    """
    Returns a tooltip HTML string for the given text and help text.

    Args:
        text (str): The text to display.
        help_text (str): The help text for the tooltip.

    Returns:
        str: The HTML string with the tooltip.
    """
    return f'<span title="{help_text}">{text}</span>'

def display_links_selection(config):
    """
    Displays the list of available links to select from.

    Args:
        config (dict): The configuration dictionary.

    Returns:
        list: List of URLs available for processing.
    """
    try:
        with open(config['file_paths']['edited_link_file'], 'r') as file:
            urls = file.read().splitlines()
    except Exception as e:
        st.error(f"Error loading link data: {e}")
        logger.error(f"Error loading link data: {e}", exc_info=True)
        return []

    return urls

def save_results_to_file(results, config):
    """
    Saves the processed results to a JSON file with a timestamp.

    Args:
        results (list): The list of processed results.
        config (dict): The configuration dictionary.

    Returns:
        str: The file path of the saved results.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"scrape_results_{timestamp}.json"

    # Get the output directory from config, or use a default if not found
    output_dir = config.get('file_paths', {}).get('output_dir', 'output')

    file_path = os.path.join(output_dir, filename)

    os.makedirs(output_dir, exist_ok=True)

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    return file_path

#@st.cache_data
def cached_process_url(url, config, prompt):
    """
    Processes a URL using a cached function to avoid repeated processing of the same URL.
    """
    logger.info(f"Starting to process URL: {url}")

    try:
        logger.debug(f"Calling smart_graph_scrap with URL: {url}")
        result = smart_graph_scrap([url], config_path='config.yml', custom_prompt=prompt)

        logger.debug(f"Result from smart_graph_scrap: {result}")
        logger.debug(f"Type of result: {type(result)}")

        if isinstance(result, list):
            logger.info("Result is a list")
            if result:
                first_item = result[0]
                if isinstance(first_item, dict):
                    logger.info(f"Returning first item of list: {first_item}")
                    return first_item
                else:
                    logger.warning(f"First item is not a dictionary: {first_item}")
                    return {"url": url, "error": "Unexpected result structure"}
            else:
                logger.warning("Result list is empty")
                return {"url": url, "error": "Empty result list"}
        elif isinstance(result, dict):
            logger.info(f"Result is a dictionary: {result}")
            return result
        else:
            logger.warning(f"Unexpected result type: {type(result)}")
            return {"url": url, "error": f"Unexpected result type: {type(result)}"}
    except Exception as e:
        logger.error(f"Error processing URL {url}: {str(e)}", exc_info=True)
        return {"url": url, "error": str(e)}
    finally:
        logger.info(f"Finished processing URL: {url}")

def process_urls(urls, config, prompt):
    """
    Processes a list of URLs and returns the results.

    Args:
        urls (list): List of URLs to process.
        config (dict): The configuration dictionary.
        prompt (str): The prompt to use during processing.

    Returns:
        tuple: Processed results and total duration of processing.
    """
    results = {}
    start_time = time.time()

    # Create a progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, url in enumerate(urls, 1):
        url_start_time = time.time()
        status_text.text(f"Processing URL {i}/{len(urls)}: {url}")

        result = cached_process_url(url, config, prompt)
        if isinstance(result, dict):
            results.update(result)

        url_end_time = time.time()
        url_duration = url_end_time - url_start_time
        logger.info(f"Finished processing URL {i}/{len(urls)} in {url_duration:.2f} seconds")

        # Update progress bar
        progress_bar.progress(i / len(urls))

    end_time = time.time()
    total_duration = end_time - start_time
    logger.info(f"Total processing time: {total_duration:.2f} seconds")
    status_text.text(f"Processing completed in {total_duration:.2f} seconds")

    return results, total_duration

def load_prompts(prompt_folder):
    """
    Loads prompts from the specified folder.

    Args:
        prompt_folder (str): The folder containing the prompt files.

    Returns:
        dict: Dictionary with prompt filenames as keys and prompt text as values.
    """
    prompts = {}
    for filename in os.listdir(prompt_folder):
        if filename.endswith('.txt'):
            with open(os.path.join(prompt_folder, filename), 'r') as f:
                prompts[filename] = f.read().strip()
    return prompts

def load_main_prompt(config):
    """
    Loads the main prompt from the prompt folder.

    Args:
        config (dict): The configuration dictionary.

    Returns:
        str: The main prompt text, if available.
    """
    prompt_folder = config['file_paths']['prompt_folder']
    main_prompt_path = os.path.join(prompt_folder, 'main_prompt.txt')

    if os.path.exists(main_prompt_path):
        with open(main_prompt_path, 'r') as f:
            return f.read().strip()
    else:
        return None

def load_and_edit_prompt(config):
    """
    Allows the user to load, edit, and save prompts from the prompt folder.

    Args:
        config (dict): The configuration dictionary.

    Returns:
        str: The edited prompt text.
    """
    prompt_folder = config['file_paths']['prompt_folder']
    prompts = load_prompts(prompt_folder)
    main_prompt = load_main_prompt(config)

    if not prompts and main_prompt is None:
        st.warning("No prompt files found and no main_prompt.txt exists.")
        return None

    prompt_options = list(prompts.keys()) + ["main_prompt.txt"]
    selected_prompt = st.selectbox("Select a prompt", prompt_options)

    if selected_prompt == "main_prompt.txt":
        current_prompt = main_prompt if main_prompt is not None else ""
    elif selected_prompt:
        current_prompt = prompts[selected_prompt]
    else:
        st.warning("Please select a prompt.")
        return None

    edited_prompt = st.text_area("Edit Prompt", current_prompt, height=300)

    if st.button("Save Prompt"):
        try:
            # Always save the edited prompt to main_prompt.txt
            main_prompt_path = os.path.join(prompt_folder, 'main_prompt.txt')
            with open(main_prompt_path, 'w') as f:
                f.write(edited_prompt)
            st.success("Prompt saved successfully to main_prompt.txt!")

            # If a different prompt was selected, also update that file
            if selected_prompt != "main_prompt.txt":
                with open(os.path.join(prompt_folder, selected_prompt), 'w') as f:
                    f.write(edited_prompt)
                st.success(f"Prompt also saved to {selected_prompt}!")
        except Exception as e:
            st.error(f"Error saving prompt: {e}")

    return edited_prompt

def display_article_details(results):
    """
    Displays the details of a selected article.

    Args:
        results (dict): Dictionary of processed articles.
    """
    if 'results' not in st.session_state or not st.session_state.results:
        st.warning("No articles loaded to display. Please process links first.")
        return

    article_ids = list(range(len(st.session_state.results)))  # Assuming each result corresponds to an article
    selected_id = st.selectbox("Select an article number to display:", article_ids)

    if selected_id is not None and selected_id < len(st.session_state.results):
        article = st.session_state.results[selected_id]
        if article:
            with st.expander("Article Details", expanded=True):
                for key, value in article.items():
                    if isinstance(value, list):
                        st.write(f"**{key.replace('_', ' ').title()}:**")
                        for idx, item in enumerate(value):
                            if isinstance(item, dict):
                                st.write(f"  - **{item.get('author', 'Author Unknown')}** says: \"{item.get('quote', 'No quote available')}\"")
                            else:
                                st.write(f"- {item}")
                    elif isinstance(value, dict):
                        for subkey, subvalue in value.items():
                            st.write(f"**{subkey.replace('_', ' ').title()}:** {subvalue}")
                    else:
                        st.write(f"**{key.replace('_', ' ').title()}:** {value}")
        else:
            st.error("Selected article data is not available.")

def fetch_ai_news_links():
    """
    Fetches AI news links from the provided URLs and generates JSON data with article details.
    """
    urls_input = st.text_area("Enter URLs (one per line)", height=200, help="Input up to 10 URLs to be processed.")
    urls = urls_input.strip().splitlines()[:10]  # Limit input to 10 URLs

    n_value = st.number_input("Select number of links to retrieve from each URL:", min_value=1, max_value=20, value=5, help="Set how many links to retrieve from each URL.")

    if st.button("Generate Links"):
        if urls:
            with st.spinner("Processing URLs..."):
                # Create a timestamp for the filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file_path = f"sources/links_{timestamp}.json"

                prompt = (
                    "Return full url (to access the article), title and date (usually found at the top of article) of available articles from the extracted web page data as json. "
                    "Name main json key as portal name. The JSON should be in the following format: "
                    "{\"WIRED\": [\n"
                    "    {\"url\": \"https://www.wired.com/story/worldcoin-sam-altman-orb/\", \"title\": \"Sam Altman’s Eye-Scanning Orb Has a New Look—and Will Come Right to Your Door\", \"datetime\": \"May 31, 2023\"},\n"
                    "    {\"url\": \"https://www.wired.com/story/filmmakers-are-worried-about-ai-big-tech-wants-them-to-see-whats-possible/\", \"title\": \"Filmmakers Are Worried About AI. Big Tech Wants Them to See 'What's Possible'\", \"datetime\": \"1 day ago\"}\n"
                    "]}"
                )

                combined_results = {}
                successful_count = 0

                for i, url in enumerate(urls):
                    try:
                        # Process each URL individually
                        result, _ = process_urls([url], load_config(), prompt)
                        if result:
                            # Limit the number of items in the JSON list to n_value
                            for key, articles in result.items():
                                result[key] = articles[:n_value]

                            # Merge the result into combined_results
                            combined_results.update(result)
                            st.success(f"Links from URL {i + 1} processed successfully.")
                            successful_count += 1
                        else:
                            st.warning(f"No links found for URL {i + 1}: {url}")
                    except Exception as e:
                        st.error(f"Error processing URL {i + 1}: {url}. Error: {e}")

                # Save combined results to a single JSON file
                if combined_results:
                    with open(output_file_path, 'w') as f:
                        json.dump(combined_results, f, indent=4)
                    st.info(f"Successfully saved links from {successful_count} portal(s) to file: {output_file_path}")
        else:
            st.warning("Please enter at least one URL.")

def main():
    st.title("🔍 Smart Article-Link Summarizer")

    # Add the link_content_manager expander with a friendly title and emoji
    with st.expander("📌 Manage Link Content", expanded=True):
        tabs = st.tabs(["🔗 Manual Link Input", "🤖 Automated Link Generator"])

        with tabs[0]:
            link_content_manager()  # Call the link_content_manager function

        with tabs[1]:
            fetch_ai_news_links()

    try:
        config = load_config()
    except Exception as e:
        st.error(f"⚠️ Error loading configuration: {e}")
        logger.error(f"Error loading configuration: {e}", exc_info=True)
        return

    # Add expander for link process manager with an updated name
    with st.expander("⚙️ Process Links", expanded=True):
        tabs = st.tabs(["🖋️ Review and Edit Prompt", "🚀 Process Articles"])
        with tabs[0]:
            show_prompt = st.checkbox("Show and edit prompt 🖋️", help="Enable this to view and modify the processing prompt")
            if show_prompt:
                prompt = load_and_edit_prompt(config)
                if prompt is None:
                    st.warning("⚠️ No prompt selected or available.")
            else:
                prompt = load_main_prompt(config)

        with tabs[1]:
                all_urls = display_links_selection(config)

                st.caption("Select whether to process specific articles or all available articles 🔄")
                process_option = st.radio("Choose processing option: 📈", ["Select specific articles", "Process all articles"])

                if process_option == "Select specific articles":
                    selected_urls = st.multiselect("Select articles to process: 📚", all_urls, help="Choose one or more articles from the list to process")
                else:
                    selected_urls = all_urls

                st.caption("Start processing the selected articles using the chosen prompt ⚙️")
                if st.button("🚀 Confirm and Process Selected Links"):
                    if selected_urls:
                        with st.spinner("Processing selected links... ⏳"):
                            try:
                                results, total_duration = process_urls(selected_urls, config, prompt)

                                # Save results to file
                                file_path = save_results_to_file(results, config)

                                # Store results and file_path in session state
                                st.session_state.results = results
                                st.session_state.file_path = file_path
                                st.session_state.total_duration = total_duration

                                st.success(f"✅ Processing completed successfully! Results saved to {file_path}")
                                st.info(f"⏱ Total processing time: {total_duration:.2f} seconds")

                            except Exception as e:
                                st.error(f"❌ Error during processing: {e}")
                                logger.error(f"Error during processing: {e}", exc_info=True)
                    else:
                        st.warning("🚨 Please select at least one article to process or choose to process all articles.")

    # Add the view link summaries expander with a friendly title
    with st.expander("📄 View Article Summaries", expanded=False):
        view_link_summaries()  # Call the link_content_manager function

if __name__ == "__main__":
    main()
