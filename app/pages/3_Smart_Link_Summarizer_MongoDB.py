#3_Smart_Linkk_Summarizer_MongoDB.py
"""
Article Summary Management App
----------------------------

Integration with summary_agent.py:
1. ContentProcessor Usage:
   - Scrapes and processes article content from URLs
   - Validates articles against specified topics
   - Generates summaries using configured LLM model
   - Configured via summary_prompt_path from config.yml

2. MongoDBManager Usage:
   - Manages user authentication and article storage
   - Associates articles with users by processing date
   - Handles article retrieval and pagination
   - Collections:
     * users: {email, articles{date: [article_ids]}}
     * articles: {metadata, summary}

Features:
- User authentication and session management
- Batch article processing from file or manual input
- Topic-based content validation
- Date-based article organization
- Paginated summary viewing with filters
"""
import streamlit as st
import logging
import yaml
from datetime import datetime
from pymongo import MongoClient
from modules.summary_agent import ContentProcessor, MongoDBManager
import re

# Load configuration from config.yml
with open("./config.yml", "r") as file:
    config = yaml.safe_load(file)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MongoDB Setup
def get_mongo_manager():
    """Creates a MongoDB manager instance."""
    return MongoDBManager(uri="mongodb://localhost:27017/")

# Initialize Content Processor
def get_content_processor():
    """Creates a ContentProcessor instance."""
    return ContentProcessor(summary_prompt_path=config['file_paths']['summary_in_mongo_prompt'])

# Email validation function
def is_valid_email(email):
    """Check if the provided email is valid."""
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None

# Streamlit app
st.title("Article Summary Management App")

# Sidebar
if 'user_email' not in st.session_state:
    st.session_state.user_email = None  # Default to None for unauthenticated users

# MongoDB and Processor Instances
try:
    db_manager = get_mongo_manager()  # Initialize db_manager first
    content_processor = get_content_processor()
except Exception as e:
    st.error("Error initializing database or content processor. Check logs for details.")
    logger.error(f"Initialization failed: {str(e)}", exc_info=True)

# User Authentication
with st.sidebar.expander("User Authentication", expanded=True):
    user_email = st.text_input("Email Address:", value=st.session_state.user_email if st.session_state.user_email else "", placeholder="example@gmail.com")
    auth_key = st.text_input("Authentication Key:", type="password")

    # Check if user exists after user_email is defined
    user_exists = db_manager.user_collection.find_one({"email": user_email})

    # Validate email
    if user_email and not is_valid_email(user_email):
        st.sidebar.error("Invalid email address. Please enter a valid email.")

    # Create a container for buttons to align them side by side
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Sign Up"):
            if user_exists:
                st.sidebar.error("User already exists. Please log in.")
            elif auth_key == config['USER_AUTH_KEY']:  # Check against the new auth key in config
                # Add new user to the database
                db_manager.user_collection.insert_one({"email": user_email, "articles": {}})
                st.sidebar.success("User signed up successfully!")
                st.session_state.user_email = user_email  # Set the session email
            else:
                st.sidebar.error("Invalid authentication key. Please try again.")

    with col2:
        if st.button("Log In"):
            if user_exists and auth_key == config['USER_AUTH_KEY']:
                st.sidebar.success("Logged in successfully!")
                st.session_state.user_email = user_email  # Set the session email
            else:
                st.sidebar.error("Invalid email or authentication key. Please try again.")

# Check if user exists
user_exists = db_manager.user_collection.find_one({"email": user_email})

# Tabs
summary_tab, view_tab = st.tabs(["Process Articles", "View Summaries"])

# Tab 1: Process Articles
with summary_tab:
    st.header("Process Articles")

    # File uploader for links
    uploaded_file = st.file_uploader("Upload a file with article links (one link per line):", type=["txt"])

    # Text area for manual link entry
    manual_links = st.text_area("Or enter article links manually (one link per line):", height=150)

    # Combine links from both sources
    links = []
    if uploaded_file is not None:
        links.extend(uploaded_file.read().decode("utf-8").splitlines())
    if manual_links:
        links.extend(manual_links.splitlines())

    if links:
        st.write("Links to process:")
        st.write(links)

    topic = st.text_input("Enter topic for validation:", "artificial intelligence")

    if st.button("Process Articles"):
        if links:
            for article_link in links:
                try:
                    st.info(f"Processing article from: {article_link}")
                    # Fetch article data
                    article_data = content_processor.fetch_article_data(article_link)
                    if article_data:
                        # Validate topic
                        if content_processor.validate_topic(article_data['metadata']['content'], topic):
                            summary = content_processor.generate_summary(article_data['metadata']['content'])
                            if summary:
                                article_data['summary'] = {"text": summary, "model_used": content_processor.model}
                                article_id = db_manager.save_article(article_data)
                                if article_id:
                                    processing_date = datetime.now().strftime("%d%m%Y")
                                    db_manager.add_article_to_user(user_email, article_id, processing_date)
                                    st.success(f"Article processed and saved successfully for link: {article_link}!")
                                else:
                                    st.error(f"Failed to save article to database for link: {article_link}.")
                            else:
                                st.error(f"Summary generation failed for link: {article_link}.")
                        else:
                            st.error(f"Article did not pass topic validation for link: {article_link}.")
                    else:
                        st.error(f"Failed to fetch article data for link: {article_link}.")
                except Exception as e:
                    st.error(f"Error occurred while processing article: {article_link}. Check logs for details.")
                    logger.error(f"Error processing article: {article_link}: {str(e)}", exc_info=True)
        else:
            st.warning("Please upload a valid file with article links or enter links manually.")

# Tab 2: View Summaries
with view_tab:
    st.header("View Summaries")
    try:
        # Create an expander for query management
        with st.expander("Query Management", expanded=True):
            # Fetch unique processing dates from the articles
            unique_dates = db_manager.article_collection.distinct("metadata.processing_date")
            selected_dates = st.multiselect("Select processing dates:", unique_dates)

            # Checkbox for filtering by important entities
            filter_entities = st.checkbox("Filter by Important Entities")
            entities_input = st.text_input("Enter important entities (comma-separated):", placeholder="e.g., AI, Machine Learning")

            # Pagination controls
            articles_per_page = 10
            query = {"summary": {"$exists": True}}

            if selected_dates:
                query["metadata.processing_date"] = {"$in": selected_dates}

            # If filtering is enabled, modify the query to include the entities
            if filter_entities and entities_input:
                entities = [entity.strip() for entity in entities_input.split(",")]
                query["metadata.content"] = {"$regex": "|".join(entities), "$options": "i"}  # Case-insensitive search

            total_articles = db_manager.article_collection.count_documents(query)
            st.info(f"Total Number of Articles in Selected Collection is {total_articles}")

        total_pages = (total_articles // articles_per_page) + (1 if total_articles % articles_per_page > 0 else 0)
        current_page = st.sidebar.number_input("Select page:", min_value=1, max_value=total_pages, value=1)

        # Fetch articles for the current page
        skip = (current_page - 1) * articles_per_page
        articles = db_manager.article_collection.find(query).sort("metadata.processing_date", -1).skip(skip).limit(articles_per_page)  # Sort by processing_date descending

        # Display articles in a scrollable container
        with st.container():
            with st.expander("View Summaries", expanded=True):
                for article in articles:
                    st.subheader(article["metadata"]["title"])
                    summary = article['summary']['text'].replace("### Date of Article 📅", "\n\n### Date of Article 📅")
                    st.write(summary)
                    st.write(f"Processing Date: {article['metadata']['processing_date']}")
                    st.write(f"URL: {article['metadata']['url']}")
                    st.write("---")
    except Exception as e:
        st.error("Error retrieving articles from database. Check logs for details.")
        logger.error(f"Error retrieving summaries: {str(e)}", exc_info=True)
