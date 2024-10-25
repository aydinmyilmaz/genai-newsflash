#smart_link_sumarizer.py
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
from docx import Document

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
    filename = f"article_summary_results_{timestamp}.json"

    # Get the output directory from config, or use a default if not found
    output_dir = config.get('file_paths', {}).get('output_dir_article')

    file_path = os.path.join(output_dir, filename)

    os.makedirs(output_dir, exist_ok=True)

    # Save the results as a list of dictionaries
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    return file_path

def save_results_to_docx(results):
    """
    Saves the processed results to a DOCX file with a timestamp.

    Args:
        results (list): The list of processed results.

    Returns:
        str: The file path of the saved DOCX file.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"article_summary_results_{timestamp}.docx"
    file_path = os.path.join(tempfile.gettempdir(), filename)

    doc = Document()
    doc.add_heading('Article Summary Results', level=1)

    for result in results:
        doc.add_heading(result.get('url', 'URL not available'), level=2)
        for key, value in result.items():
            # if key != 'url':
                doc.add_paragraph(f"{key.replace('_', ' ').title()}: {value}")

    doc.save(file_path)
    return file_path

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
        tuple: List of processed results and total duration of processing.
    """
    results = []
    start_time = time.time()

    # Create a progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, url in enumerate(urls, 1):
        url_start_time = time.time()
        status_text.text(f"Processing URL {i}/{len(urls)}: {url}")

        result = cached_process_url(url, config, prompt)
        if isinstance(result, dict):
            results.append(result)  # Append the result as a new dictionary in the list

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
    Main function to load, edit, and save prompts.

    Args:
        config (dict): The configuration dictionary.

    Returns:
        str: The edited prompt text.
    """
    prompt_folder = config['file_paths']['prompt_folder']

    # Step 1: Load available prompts and main prompt
    prompts, main_prompt = load_prompts_and_main(prompt_folder, config)

    if not prompts and main_prompt is None:
        st.warning("No prompt files found and no main_prompt.txt exists.")
        return None

    # Step 2: Select a prompt to edit
    selected_prompt, current_prompt = select_and_display_prompt(prompts, main_prompt)
    if current_prompt is None:
        return None

    # Step 3: Edit and save the selected prompt
    edited_prompt = edit_prompt(current_prompt)

    # Step 4: Save the edited prompt to the appropriate files
    if st.button("Save Prompt"):
        save_edited_prompt(prompt_folder, selected_prompt, edited_prompt)

    return edited_prompt


def load_prompts_and_main(prompt_folder, config):
    """Loads available prompts and the main prompt."""
    prompts = load_prompts(prompt_folder)
    main_prompt = load_main_prompt(config)
    return prompts, main_prompt


def select_and_display_prompt(prompts, main_prompt):
    """Handles prompt selection and displays the selected prompt."""
    prompt_options = list(prompts.keys()) + ["main_prompt.txt"]
    selected_prompt = st.selectbox("Select a prompt", prompt_options)

    if selected_prompt == "main_prompt.txt":
        current_prompt = main_prompt if main_prompt is not None else ""
    elif selected_prompt:
        current_prompt = prompts[selected_prompt]
    else:
        st.warning("Please select a prompt.")
        current_prompt = None

    return selected_prompt, current_prompt


def edit_prompt(current_prompt):
    """Displays a text area for the user to edit the prompt."""
    return st.text_area("Edit Prompt", current_prompt, height=300)


def save_edited_prompt(prompt_folder, selected_prompt, edited_prompt):
    """Saves the edited prompt to main_prompt.txt and, optionally, another file."""
    try:
        # Save the edited prompt to main_prompt.txt
        main_prompt_path = os.path.join(prompt_folder, 'main_prompt_link.txt')
        save_prompt_to_file(main_prompt_path, edited_prompt)
        st.success("Prompt saved successfully to main_prompt.txt!")

        # Save the edited prompt to the selected prompt file (if not main_prompt.txt)
        if selected_prompt != "main_prompt.txt":
            prompt_path = os.path.join(prompt_folder, selected_prompt)
            save_prompt_to_file(prompt_path, edited_prompt)
            st.success(f"Prompt also saved to {selected_prompt}!")
    except Exception as e:
        st.error(f"Error saving prompt: {e}")


def save_prompt_to_file(file_path, content):
    """Saves the given content to the specified file path."""
    with open(file_path, 'w') as f:
        f.write(content)

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

def is_valid_url(url):
    # List of file extensions to exclude
    excluded_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp', '.ico', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']

    # Check if the URL ends with any of the excluded extensions
    return not any(url.lower().endswith(ext) for ext in excluded_extensions)


def fetch_ai_news_links():
    """Main function to fetch AI news links and manage the UI flow."""
    config_2 = load_config()

    # Step 1: User Input for URLs and Number of Links
    urls, n_value = get_user_input()

    # Step 2: Handle URL processing if the "Generate Links" button is clicked
    if st.button("Generate Links"):
        if urls:
            process_urls_and_save_results(urls, n_value, config_2)
        else:
            st.warning("Please enter at least one URL.")


def get_user_input():
    """Handles user input for URLs and number of links to retrieve."""
    urls_input = st.text_area("Enter URLs (one per line)", height=200, help="Input up to 10 URLs to be processed.")
    urls = urls_input.strip().splitlines()[:10]  # Limit input to 10 URLs

    n_value = st.number_input(
        "Select number of links to retrieve from each URL:",
        min_value=1,
        max_value=20,
        value=5,
        help="Set how many links to retrieve from each URL."
    )

    return urls, n_value


def process_urls_and_save_results(urls, n_value, config_2):
    """Processes URLs and saves the results to JSON and text files."""
    with st.spinner("Processing URLs..."):
        combined_results, successful_count = fetch_and_process_links(urls, n_value)

        if combined_results:
            # Step 3: Save the combined results
            save_combined_results(combined_results, successful_count, config_2)
        else:
            st.warning("No links found to save.")


def fetch_and_process_links(urls, n_value):
    """Fetches and processes links from the provided URLs."""
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
            result = process_single_url(url, prompt, n_value)
            if result:
                # Merge the result into combined_results
                combined_results = merge_results(combined_results, result, n_value)
                st.success(f"Links from URL {i + 1} processed successfully.")
                successful_count += 1
            else:
                st.warning(f"No links found for URL {i + 1}: {url}")
        except Exception as e:
            st.error(f"Error processing URL {i + 1}: {url}. Error: {e}")

    return combined_results, successful_count


def process_single_url(url, prompt, n_value):
    """Processes a single URL and returns the result."""
    try:
        result, _ = process_urls([url], load_config(), prompt)
        if isinstance(result, str) and result.startswith("Links:"):
            result = result.replace("Links:", "").strip()
            result = json.loads(result)  # Convert string to JSON

        return result
    except Exception as e:
        logger.error(f"Error processing URL {url}: {e}", exc_info=True)
        return None


def merge_results(combined_results, result, n_value):
    """Merges the result from a single URL into the combined results."""
    if isinstance(result, list):
        for portal_data in result:
            for key, articles in portal_data.items():
                # Limit the number of items in the JSON list to n_value
                articles = articles[:n_value]

                if key in combined_results:
                    combined_results[key].extend(articles)
                else:
                    combined_results[key] = articles

    return combined_results


def save_combined_results(combined_results, successful_count, config_2):
    """Saves the combined results to JSON and text files."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_dir = config_2['file_paths']['generated_article_links']
    output_file_path = f"{folder_dir}/links_{timestamp}.json"

    # Save combined results to JSON file
    with open(output_file_path, 'w') as f:
        json.dump(combined_results, f, indent=4)
    st.info(f"Successfully saved links from {successful_count} portal(s) to file: {output_file_path}")

    # Save links to article_links.txt
    save_links_to_txt(combined_results)


def save_links_to_txt(combined_results):
    """Saves the article links to a text file."""
    with open('sources/article_links.txt', 'w') as f:
        for portal, articles in combined_results.items():
            for article in articles:
                url = article['url']
                if is_valid_url(url):
                    f.write(f"{url}\n")

    st.info("Links have been written to sources/article_links.txt")


def manage_link_content():
    """Handles the UI for managing link content."""
    with st.expander("📌 Manage Link Content", expanded=True):
        tabs = st.tabs(["🔗 Manual Link Input", "🤖 Automated Link Generator"])

        with tabs[0]:
            link_content_manager()  # Call the link_content_manager function

        with tabs[1]:
            fetch_ai_news_links()


def load_and_display_config():
    """Loads and displays the configuration."""
    try:
        config = load_config()
    except Exception as e:
        st.error(f"⚠️ Error loading configuration: {e}")
        logger.error(f"Error loading configuration: {e}", exc_info=True)
        return None
    return config


def process_links(config):
    """Handles the processing of articles based on user input."""
    if not config:
        return

    with st.expander("⚙️ Process Links", expanded=True):
        tabs = st.tabs(["🔍Review and Edit Prompt", "🚀 Process Articles"])

        with tabs[0]:
            prompt = manage_prompt(config)

        with tabs[1]:
            selected_urls = select_articles_to_process(config)
            if selected_urls:
                process_selected_articles(selected_urls, config, prompt)


def manage_prompt(config):
    """Handles prompt selection and editing."""
    show_prompt = st.checkbox("Show and edit prompt", help="Enable this to view and modify the processing prompt")
    if show_prompt:
        prompt = load_and_edit_prompt(config)
        if prompt is None:
            st.warning("⚠️ No prompt selected or available.")
    else:
        prompt = load_main_prompt(config)
    return prompt


def select_articles_to_process(config):
    """Manages article selection for processing."""
    all_urls = display_links_selection(config)

    st.caption("Select whether to process specific articles or all available articles 🔄")
    process_option = st.radio("Choose processing option: 📈", ["Select specific articles", "Process all articles"])

    if process_option == "Select specific articles":
        selected_urls = st.multiselect("Select articles to process: 📚", all_urls, help="Choose one or more articles from the list to process")
    else:
        selected_urls = all_urls

    return selected_urls


def process_selected_articles(selected_urls, config, prompt):
    """Processes the selected articles and handles the results."""
    st.caption("Start processing the selected articles using the chosen prompt ⚙️")
    if st.button("🚀 Confirm and Process Selected Links"):
        with st.spinner("Processing selected links... ⏳"):
            try:
                results, total_duration = process_urls(selected_urls, config, prompt)

                # Handle results
                handle_processing_results(results, config, total_duration)

            except Exception as e:
                st.error(f"❌ Error during processing: {e}")
                logger.error(f"Error during processing: {e}", exc_info=True)


def handle_processing_results(results, config, total_duration):
    """Saves and displays the results of the processed articles."""
    # Save results to file
    json_file_path = save_results_to_file(results, config)

    # Store results and file_path in session state
    st.session_state.results = results
    st.session_state.json_file_path = json_file_path
    st.session_state.total_duration = total_duration

    st.success(f"✅ Processing completed successfully! Results saved to {json_file_path}")
    st.info(f"⏱ Total processing time: {total_duration:.2f} seconds")

    # Save results as .docx
    docx_file_path = save_results_to_docx(results)
    if docx_file_path:
        # Store the path of the last saved .docx file in session state
        st.session_state.docx_file_path = docx_file_path
        st.success(f"✅ .docx file saved successfully at {docx_file_path}")  # Confirm file creation
    else:
        st.error("❌ Failed to save .docx file.")


def view_article_summaries():
    """Displays the summaries of processed articles."""
    with st.expander("📄 View Article Summaries", expanded=False):
        view_link_summaries()  # Call the function to display article summaries


def main():
    st.title("🔍 Smart Article-Link Summarizer")

    # Link content management
    manage_link_content()

    # Configuration loading
    config = load_and_display_config()

    # Link processing management
    process_links(config)

    # View article summaries
    view_article_summaries()

if __name__ == "__main__":
    main()
