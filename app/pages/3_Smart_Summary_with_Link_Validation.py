#3_Smart_Summary_with_Link_Validation.py

"""
Article Processing and Management System
--------------------------------------

A comprehensive system for processing, validating, summarizing and managing article content
from multiple sources with MongoDB integration.

Core Components:

1. Content Processing (via ContentProcessor):
   - Multi-source article scraping (newspaper3k + SmartScraperGraph fallback)
   - Topic validation using LLM
   - AI-powered content summarization
   - Configurable via summary_prompt_path

2. Storage Management (via ArticleStorageManager):
   MongoDB Collections Schema:

   a) users:
   {
     "_id": ObjectId,
     "email": String (unique index),
     "articles": {
       "DDMMYYYY": [String]  // Date-based array of article ObjectId references
     }
   }

   b) articles:
   {
     "_id": ObjectId,
     "metadata": {
       "url": String (unique index),
       "title": String,
       "content": String,
       "authors": Array<String>,
       "published_date": String (ISO format),
       "processing_date": String (ISO format),
       "keywords": Array<String>
     },
     "summary": {
       "model_used": String,
       "text": String
     }
   }

Key Features:
- Multi-source article content extraction
- Intelligent fallback scraping system
- Topic relevance validation
- AI-powered content summarization
- User authentication and session management
- Date-based article organization
- MongoDB-based persistent storage
- Batch processing capabilities
"""
import streamlit as st
import logging
import yaml
from datetime import datetime
from pymongo import MongoClient


from modules.summarizer.summary_agent import ContentProcessor
from modules.mongodb_manager.mongodb_query_manager import ArticleStorageManager, MongoDBQueryManager
from modules.utils.helpers import auth_check

# Load configuration from config.yml
with open("./config.yml", "r") as file:
    config = yaml.safe_load(file)

auth_check()

# Get current user's email from session state
user_email = st.session_state.user_email

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MongoDB Setup
def get_mongo_manager():
    """Creates a MongoDB manager instance."""
    return ArticleStorageManager(uri="mongodb://localhost:27017/")

# Initialize Content Processor
def get_content_processor():
    """Creates a ContentProcessor instance."""
    return ContentProcessor(summary_prompt_path=config['file_paths']['summary_in_mongo_prompt'])

# Streamlit app
st.header("Summary - Topic Validation on Links")

# MongoDB and Processor Instances
try:
    db_manager = get_mongo_manager()
    content_processor = get_content_processor()
except Exception as e:
    st.error("Error initializing database or content processor. Check logs for details.")
    logger.error(f"Initialization failed: {str(e)}", exc_info=True)

# Check if user is authenticated (using session state from introduction.py)
if not st.session_state.get('user_email'):
    st.warning("Please log in using the sidebar to access the article summarizer.")
    st.stop()

# Get current user's email from session state
user_email = st.session_state.user_email

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
    st.write("Moved to MongoD Article Viewer Page")
    # try:
    #     # Create an expander for query management
    #     with st.expander("Query Management", expanded=True):
    #         # Fetch unique processing dates from the articles
    #         unique_dates = db_manager.article_collection.distinct("metadata.processing_date")
    #         selected_dates = st.multiselect("Select processing dates:", unique_dates)

    #         # Checkbox for filtering by important entities
    #         filter_entities = st.checkbox("Filter by Important Entities")
    #         entities_input = st.text_input("Enter important entities (comma-separated):", placeholder="e.g., AI, Machine Learning")

    #         # Pagination controls
    #         articles_per_page = 10
    #         query = {"summary": {"$exists": True}}

    #         if selected_dates:
    #             query["metadata.processing_date"] = {"$in": selected_dates}

    #         # If filtering is enabled, modify the query to include the entities
    #         if filter_entities and entities_input:
    #             entities = [entity.strip() for entity in entities_input.split(",")]
    #             query["metadata.content"] = {"$regex": "|".join(entities), "$options": "i"}

    #         total_articles = db_manager.article_collection.count_documents(query)
    #         st.info(f"Total Number of Articles in Selected Collection is {total_articles}")

    #     total_pages = (total_articles // articles_per_page) + (1 if total_articles % articles_per_page > 0 else 0)
    #     current_page = st.sidebar.number_input("Select page:", min_value=1, max_value=total_pages, value=1)

    #     # Fetch articles for the current page
    #     skip = (current_page - 1) * articles_per_page
    #     articles = db_manager.article_collection.find(query).sort("metadata.processing_date", -1).skip(skip).limit(articles_per_page)

    #     # Display articles in a scrollable container
    #     with st.container():
    #         with st.expander("View Summaries", expanded=True):
    #             for article in articles:
    #                 st.subheader(article["metadata"]["title"])
    #                 summary = article['summary']['text'].replace("### Date of Article 📅", "\n\n### Date of Article 📅")
    #                 st.write(summary)
    #                 st.write(f"Processing Date: {article['metadata']['processing_date']}")
    #                 st.write(f"URL: {article['metadata']['url']}")
    #                 st.write("---")
    # except Exception as e:
    #     st.error("Error retrieving articles from database. Check logs for details.")
        # logger.error(f"Error retrieving summaries: {str(e)}", exc_info=True)


