# app.py
import streamlit as st
import logging
from datetime import datetime


from modules.mongodb_manager.mongodb_query_manager import MongoDBQueryManager
from modules.utils.helpers import auth_check

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Authentication check at the start
auth_check()
# Get current user's email from session state
user_email = st.session_state.user_email

ARTICLES_PER_PAGE = 10

def initialize_session_state():
    """Initialize session state variables"""
    if 'selected_dates' not in st.session_state:
        st.session_state.selected_dates = []
    if 'selected_entities' not in st.session_state:
        st.session_state.selected_entities = []
    if 'has_active_filters' not in st.session_state:
        st.session_state.has_active_filters = False
    if 'article_ids' not in st.session_state:
        st.session_state.article_ids = []
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1

def display_article(article: dict, db_manager:  MongoDBQueryManager, index: int):
    """Display single article in an expander"""
    try:
        with st.expander(f"📄 {article['metadata']['title']}", expanded=False):
            summary = db_manager.format_article_summary(article)
            st.write(summary)
            st.write(f"Processing Date: {article['metadata']['processing_date']}")
            st.write(f"URL: {article['metadata']['url']}")
    except Exception as e:
        logger.error(f"Error displaying article: {str(e)}", exc_info=True)
        st.error(f"Error displaying article {index}")

def apply_filters(dates, entities, db_manager:  MongoDBQueryManager):
    """Apply filters and update session state"""
    st.session_state.selected_dates = dates
    st.session_state.selected_entities = entities
    st.session_state.has_active_filters = True
    st.session_state.current_page = 1

    # Get article IDs and store them in session state
    article_ids = db_manager.get_article_ids_for_dates(dates)
    st.session_state.article_ids = article_ids

    # Get filtered articles count
    articles, _ = db_manager.fetch_articles_paginated(article_ids, 1, ARTICLES_PER_PAGE, entities)
    return len(articles)

def render_query_management(db_manager:  MongoDBQueryManager):
    """Render query management section"""
    st.subheader("Filter Settings")

    # Get available dates
    available_dates = db_manager.get_available_dates()

    # Date selection
    selected_dates = st.multiselect(
        "Select processing dates:",
        options=available_dates,
        default=st.session_state.selected_dates,
        max_selections=3
    )

    # Show article counts for selected dates
    if selected_dates:
        st.write("Articles per selected date:")
        for date in selected_dates:
            count = db_manager.get_articles_count_for_date(date)
            st.write(f"📅 {date}: {count} articles")

    # Entity filtering
    filter_entities = st.checkbox("Filter by Important Entities",
                                value=bool(st.session_state.selected_entities))

    current_entities = ", ".join(st.session_state.selected_entities) if st.session_state.selected_entities else ""
    entities_input = st.text_input(
        "Enter important entities (comma-separated):",
        value=current_entities,
        placeholder="e.g., AI, Machine Learning"
    )

    # Process entities
    entities = []
    if filter_entities and entities_input:
        entities = [entity.strip() for entity in entities_input.split(",") if entity.strip()]

    # Add approval button
    if st.button("Apply Filters"):
        if selected_dates:
            filtered_count = apply_filters(selected_dates, entities, db_manager)
            if filtered_count:
                st.success("Filters applied! See articles on View Tab")

                # Show current filter status
                st.info("Current active filters:")
                st.write("📅 Selected dates:", ", ".join(selected_dates))
                if entities:
                    st.write("🏷️ Selected entities:", ", ".join(entities))
            else:
                st.warning("Please select at least one date.")
                st.session_state.has_active_filters = False

def render_pagination(total_pages: int):
    """Render pagination controls in sidebar"""
    st.sidebar.write("### Navigation")

    # Page selection
    page = st.sidebar.number_input(
        "Page",
        min_value=1,
        max_value=max(1, total_pages),
        value=st.session_state.current_page
    )

    # Update current page
    st.session_state.current_page = page

    # Display page info
    st.sidebar.write(f"Page {page} of {total_pages}")

    # Previous/Next buttons
    col1, col2 = st.sidebar.columns(2)

    if col1.button("← Previous", disabled=page <= 1):
        st.session_state.current_page -= 1
        st.rerun()

    if col2.button("Next →", disabled=page >= total_pages):
        st.session_state.current_page += 1
        st.rerun()

def render_articles(db_manager:  MongoDBQueryManager):
    """Render articles with pagination"""
    if not st.session_state.has_active_filters:
        st.warning("Please set and approve filters in the Query Management tab first.")
        return

    if not st.session_state.article_ids:
        st.warning("No articles found matching the selected filters.")
        return

    # Fetch articles for current page
    articles, total_pages = db_manager.fetch_articles_paginated(
        st.session_state.article_ids,
        st.session_state.current_page,
        ARTICLES_PER_PAGE,
        st.session_state.selected_entities
    )

    if not articles:
        st.warning("No articles found matching the selected filters.")
        return

    start_idx = (st.session_state.current_page - 1) * ARTICLES_PER_PAGE + 1
    end_idx = start_idx + len(articles) - 1
    total_filtered = (total_pages - 1) * ARTICLES_PER_PAGE + len(articles)

    st.info(f"Showing articles {start_idx} to {end_idx} of {total_filtered} matching articles")

    # Render pagination controls
    render_pagination(total_pages)

    # Display articles in expanders
    for i, article in enumerate(articles, start=start_idx):
        display_article(article, db_manager, i)

def reset_filters():
    """Reset all filters and session state"""
    st.session_state.selected_dates = []
    st.session_state.selected_entities = []
    st.session_state.has_active_filters = False
    st.session_state.article_ids = []
    st.session_state.current_page = 1

def main():
    # st.set_page_config(page_title="Article Summary Viewer", layout="wide")
    st.title("Article Summary Viewer")

    # Initialize session state
    initialize_session_state()

    try:
        # Initialize MongoDB manager with user email
        db_manager =  MongoDBQueryManager(user_email="amrtyilmaz@gmail.com")

        # Create tabs
        tab1, tab2 = st.tabs(["Query Management", "View Summaries"])

        with tab1:
            render_query_management(db_manager)

        with tab2:
            render_articles(db_manager)

        # Add reset button to sidebar
        if st.sidebar.button("Reset Filters"):
            reset_filters()
            st.rerun()

    except Exception as e:
        st.error("Error retrieving articles from database. Check logs for details.")
        logger.error(f"Error in main application: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()