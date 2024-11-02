# # pages/5_🔐_Admin_Dashboard.py

# import streamlit as st
# import plotly.express as px
# import plotly.graph_objects as go
# import pandas as pd
# from modules.mongodb_manager.mongo_admin_manager import MongoDBAdminManager
# from datetime import datetime
# import json

# # Configuration
# ADMIN_EMAILS = {"admin@example.com", "amrtyilmaz@gmail.com"}

# def check_admin_access():
#     """Check if current user has admin access"""
#     user_email = st.session_state.get('user_email')
#     if not user_email or user_email not in ADMIN_EMAILS:
#         st.error("⛔ Access Denied. This page is only accessible to administrators.")
#         st.stop()

# def show_schema_explorer(admin_manager):
#     """Display MongoDB schema information"""
#     st.header("🔍 Schema Explorer")

#     try:
#         # Get schema analysis
#         schema_data = admin_manager.get_schema_analysis()

#         # Create tabs for different collections
#         users_tab, articles_tab = st.tabs(["👥 Users Collection", "📚 Articles Collection"])

#         with users_tab:
#             st.subheader("Users Collection Schema")

#             # Base Schema
#             st.markdown("#### Base Fields")
#             users_schema = schema_data.get("users_schema", [])
#             if users_schema:
#                 for field in users_schema:
#                     st.markdown(f"- `{field}`")
#             else:
#                 st.info("No schema data available for users collection")

#             # Articles Schema in Users
#             st.markdown("#### Articles Field Structure")
#             articles_in_users = schema_data.get("articles_in_users", [])
#             if articles_in_users:
#                 st.write("Available dates:")
#                 for field in sorted(articles_in_users):
#                     st.markdown(f"- `{field}`")

#             # Sample User Document
#             st.markdown("#### Sample Document")
#             with st.expander("View sample user document"):
#                 sample_user = admin_manager.db.users.find_one()
#                 if sample_user:
#                     st.json(sample_user)
#                 else:
#                     st.info("No sample user document available")

#         with articles_tab:
#             st.subheader("Articles Collection Schema")

#             col1, col2 = st.columns(2)

#             with col1:
#                 # Base Schema
#                 st.markdown("#### Base Fields")
#                 articles_schema = schema_data.get("articles_schema", [])
#                 if articles_schema:
#                     for field in articles_schema:
#                         st.markdown(f"- `{field}`")

#                 # Metadata Schema
#                 st.markdown("#### Metadata Fields")
#                 metadata_schema = schema_data.get("metadata_schema", [])
#                 if metadata_schema:
#                     for field in metadata_schema:
#                         st.markdown(f"- `{field}`")

#             with col2:
#                 # Summary Schema
#                 st.markdown("#### Summary Fields")
#                 summary_schema = schema_data.get("summary_schema", [])
#                 if summary_schema:
#                     for field in summary_schema:
#                         st.markdown(f"- `{field}`")

#                 # Sample Article Document
#                 st.markdown("#### Sample Document")
#                 with st.expander("View sample article document"):
#                     sample_article = admin_manager.db.articles.find_one()
#                     if sample_article:
#                         st.json(sample_article)
#                     else:
#                         st.info("No sample article document available")

#         # Collection Statistics
#         st.subheader("📊 Collection Statistics")
#         col1, col2 = st.columns(2)

#         with col1:
#             users_count = admin_manager.db.users.count_documents({})
#             st.metric("Total Users", users_count)

#         with col2:
#             articles_count = admin_manager.db.articles.count_documents({})
#             st.metric("Total Articles", articles_count)

#     except Exception as e:
#         st.error(f"Error exploring schema: {str(e)}")
#         st.exception(e)

# def main():
#     st.set_page_config(page_title="Admin Dashboard", page_icon="🔐", layout="wide")

#     check_admin_access()

#     st.title("🔐 MongoDB Admin Dashboard")

#     admin_manager = MongoDBAdminManager()

#     tabs = st.tabs([
#         "📊 Overview",
#         "👥 User Analysis",
#         "📚 Article Analysis",
#         "🔍 Schema Explorer",
#         "⚙️ Management"
#     ])

#     with tabs[0]:
#         show_overview(admin_manager)

#     with tabs[1]:
#         show_user_analysis(admin_manager)

#     with tabs[2]:
#         show_article_analysis(admin_manager)

#     with tabs[3]:
#         show_schema_explorer(admin_manager)

#     with tabs[4]:
#         show_management_tools(admin_manager)

# def show_overview(admin_manager):
#     st.header("📊 System Overview")

#     # Get analysis data
#     user_analysis = admin_manager.get_user_analysis()
#     article_analysis = admin_manager.get_article_analysis()

#     # Display key metrics
#     col1, col2, col3, col4 = st.columns(4)
#     with col1:
#         st.metric("Total Users", user_analysis["total_users"])
#     with col2:
#         st.metric("Active Users", user_analysis["users_with_articles"])
#     with col3:
#         st.metric("Total Articles", article_analysis["total_articles"])
#     with col4:
#         st.metric("Avg Articles/User", f"{user_analysis['average_articles_per_user']:.1f}")

#     # Activity Timeline
#     st.subheader("Activity Timeline")
#     dates_df = pd.DataFrame([
#         {"date": date, "articles": count}
#         for date, count in article_analysis["dates"].items()
#     ])
#     if not dates_df.empty:
#         dates_df['date'] = pd.to_datetime(dates_df['date'])
#         fig = px.line(dates_df, x='date', y='articles', title="Articles by Date")
#         st.plotly_chart(fig)

# def show_user_analysis(admin_manager):
#     st.header("👥 User Analysis")

#     user_analysis = admin_manager.get_user_analysis()

#     # User Statistics
#     st.subheader("User Statistics")
#     col1, col2, col3 = st.columns(3)
#     with col1:
#         st.metric("Max Articles", user_analysis["max_articles_per_user"])
#     with col2:
#         st.metric("Min Articles", user_analysis["min_articles_per_user"])
#     with col3:
#         st.metric("Average Articles", f"{user_analysis['average_articles_per_user']:.1f}")

#     # User Details Table
#     st.subheader("User Details")
#     if user_analysis["user_details"]:
#         df = pd.DataFrame(user_analysis["user_details"])
#         st.dataframe(df)

#     # Articles by Date and User
#     st.subheader("Articles by Date and User")
#     date_user_data = user_analysis["article_counts_by_date"]
#     if date_user_data:
#         fig = go.Figure()
#         for user_email in set(sum([list(users.keys()) for users in date_user_data.values()], [])):
#             dates = []
#             counts = []
#             for date, users in date_user_data.items():
#                 dates.append(date)
#                 counts.append(users.get(user_email, 0))
#             fig.add_trace(go.Bar(name=user_email, x=dates, y=counts))
#         fig.update_layout(barmode='stack', title="Articles by Date and User")
#         st.plotly_chart(fig)

# def show_article_analysis(admin_manager):
#     st.header("📚 Article Analysis")

#     article_analysis = admin_manager.get_article_analysis()

#     # Sources Distribution
#     st.subheader("Article Sources")
#     sources_df = pd.DataFrame([
#         {"source": source, "count": count}
#         for source, count in article_analysis["sources"].items()
#     ])
#     if not sources_df.empty:
#         fig = px.pie(sources_df, values="count", names="source", title="Articles by Source")
#         st.plotly_chart(fig)

#     # Keywords Analysis
#     st.subheader("Top Keywords")
#     keywords_df = pd.DataFrame([
#         {"keyword": kw, "count": count}
#         for kw, count in sorted(article_analysis["keywords"].items(), key=lambda x: x[1], reverse=True)
#     ]).head(20)
#     if not keywords_df.empty:
#         fig = px.bar(keywords_df, x="keyword", y="count", title="Top 20 Keywords")
#         st.plotly_chart(fig)

#     # Model Distribution
#     st.subheader("AI Models Used")
#     models_df = pd.DataFrame([
#         {"model": model, "count": count}
#         for model, count in article_analysis["model_distribution"].items()
#     ])

# def show_management_tools(admin_manager):
#     st.header("⚙️ Data Management")

#     # Create two columns for Users and Articles management
#     user_col, article_col = st.columns(2)

#     with user_col:
#         st.subheader("👤 User Management")

#         # List and Delete Users
#         st.markdown("#### Delete User")
#         user_analysis = admin_manager.get_user_analysis()
#         user_emails = [user["email"] for user in user_analysis["user_details"]]

#         selected_user = st.selectbox(
#             "Select user to manage:",
#             options=user_emails,
#             key="user_select"
#         )

#         col1, col2 = st.columns(2)
#         with col1:
#             delete_articles = st.checkbox("Also delete user's articles")
#         with col2:
#             if st.button("Delete User", key="delete_user"):
#                 if selected_user == st.session_state.get('user_email'):
#                     st.error("Cannot delete your own account!")
#                 else:
#                     confirm = st.checkbox("I understand this action cannot be undone")
#                     if confirm:
#                         result = admin_manager.delete_user_data(selected_user, delete_articles)
#                         if result["success"]:
#                             st.success(f"User deleted: {selected_user}")
#                             if delete_articles:
#                                 st.info(f"Deleted {result['articles_deleted']} articles")
#                         else:
#                             st.error(f"Error: {result.get('error', 'Unknown error')}")

#     with article_col:
#         st.subheader("📄 Article Management")

#         # Delete Articles by Date
#         st.markdown("#### Delete Articles by Date")
#         dates = sorted(list(admin_manager.get_article_analysis()["dates"].keys()), reverse=True)
#         selected_date = st.selectbox(
#             "Select date to delete articles from:",
#             options=dates,
#             key="date_select"
#         )

#         if selected_date:
#             articles = admin_manager.get_articles_by_date(selected_date)
#             st.info(f"Found {len(articles)} articles for {selected_date}")

#             if st.button("Delete Articles", key="delete_articles"):
#                 confirm = st.checkbox("Confirm deletion of all articles from this date")
#                 if confirm:
#                     found, deleted = admin_manager.delete_articles_by_date(selected_date)
#                     st.success(f"Deleted {deleted} out of {found} articles")

#         # Delete Individual Article
#         st.markdown("#### Delete Individual Article")
#         article_id = st.text_input("Enter Article ID:")
#         if article_id:
#             article = admin_manager.get_article_by_id(article_id)
#             if article:
#                 st.write(f"Title: {article.get('metadata', {}).get('title', 'Unknown')}")
#                 if st.button("Delete Article", key="delete_single"):
#                     if admin_manager.delete_article(article_id):
#                         st.success("Article deleted successfully")
#                     else:
#                         st.error("Failed to delete article")
#             else:
#                 st.warning("Article not found")

#     # Database Cleanup Section
#     st.subheader("🧹 Database Cleanup")

#     cleanup_col1, cleanup_col2 = st.columns(2)

#     with cleanup_col1:
#         st.markdown("#### Clean Orphaned Articles")
#         if st.button("Remove Orphaned Articles", key="cleanup_articles"):
#             confirm = st.checkbox("Confirm cleanup of orphaned articles")
#             if confirm:
#                 result = admin_manager.cleanup_database()
#                 if result["success"]:
#                     st.success(f"Removed {result['orphaned_articles_removed']} orphaned articles")
#                     st.info(f"Removed {result['empty_users_removed']} empty users")
#                 else:
#                     st.error(f"Error during cleanup: {result.get('error', 'Unknown error')}")

#     with cleanup_col2:
#         st.markdown("#### Database Statistics")
#         stats = admin_manager.get_database_stats()
#         st.metric("Storage Size (MB)", f"{stats.get('total_storage_size', 0):.2f}")
#         last_updated = stats.get('last_updated', 'Unknown')
#         st.write(f"Last Updated: {last_updated}")

# def show_article_details(article):
#     """Helper function to display article details"""
#     if not article:
#         return

#     st.write("Title:", article.get('metadata', {}).get('title', 'Unknown'))
#     st.write("URL:", article.get('metadata', {}).get('url', 'Unknown'))
#     st.write("Processing Date:", article.get('metadata', {}).get('processing_date', 'Unknown'))
#     if st.checkbox("Show full article details"):
#         st.json(article)

# if __name__ == "__main__":
#     main()


# pages/0_Admin_Dashboard.py

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from modules.mongodb_manager.mongo_admin_manager import MongoDBAdminManager
from datetime import datetime
import json

# Configuration
ADMIN_EMAILS = {"admin@example.com", "amrtyilmaz@gmail.com"}

def check_admin_access():
    """Check if current user has admin access"""
    user_email = st.session_state.get('user_email')
    if not user_email or user_email not in ADMIN_EMAILS:
        st.error("⛔ Access Denied. This page is only accessible to administrators.")
        st.stop()

def show_overview(admin_manager):
    """Display overview statistics and charts"""
    st.header("📊 System Overview")

    # Get analysis data
    user_analysis = admin_manager.get_user_analysis()
    article_analysis = admin_manager.get_article_analysis()

    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Users", user_analysis["total_users"])
    with col2:
        st.metric("Active Users", user_analysis["users_with_articles"])
    with col3:
        st.metric("Total Articles", article_analysis["total_articles"])
    with col4:
        st.metric("Avg Articles/User", f"{user_analysis['average_articles_per_user']:.1f}")

    # Activity Timeline
    st.subheader("Activity Timeline")
    dates_df = pd.DataFrame([
        {"date": date, "articles": count}
        for date, count in article_analysis["dates"].items()
    ])
    if not dates_df.empty:
        dates_df['date'] = pd.to_datetime(dates_df['date'], format='mixed')
        fig = px.line(dates_df, x='date', y='articles', title="Articles by Date")
        st.plotly_chart(fig)

def show_user_analysis(admin_manager):
    """Display user statistics and analysis"""
    st.header("👥 User Analysis")

    user_analysis = admin_manager.get_user_analysis()

    # User Statistics
    st.subheader("User Statistics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Max Articles", user_analysis["max_articles_per_user"])
    with col2:
        st.metric("Min Articles", user_analysis["min_articles_per_user"])
    with col3:
        st.metric("Average Articles", f"{user_analysis['average_articles_per_user']:.1f}")

    # User Details Table
    st.subheader("User Details")
    if user_analysis["user_details"]:
        df = pd.DataFrame(user_analysis["user_details"])
        st.dataframe(df)

    # Articles by Date and User
    st.subheader("Articles by Date and User")
    date_user_data = user_analysis["article_counts_by_date"]
    if date_user_data:
        fig = go.Figure()
        for user_email in set(sum([list(users.keys()) for users in date_user_data.values()], [])):
            dates = []
            counts = []
            for date, users in date_user_data.items():
                dates.append(date)
                counts.append(users.get(user_email, 0))
            fig.add_trace(go.Bar(name=user_email, x=dates, y=counts))
        fig.update_layout(barmode='stack', title="Articles by Date and User")
        st.plotly_chart(fig)

def show_article_analysis(admin_manager):
    """Display article statistics and analysis"""
    st.header("📚 Article Analysis")

    article_analysis = admin_manager.get_article_analysis()

    # Sources Distribution
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Article Sources")
        sources_df = pd.DataFrame([
            {"source": source, "count": count}
            for source, count in article_analysis["sources"].items()
        ])
        if not sources_df.empty:
            fig = px.pie(sources_df, values="count", names="source", title="Articles by Source")
            st.plotly_chart(fig)

    with col2:
        # Model Distribution
        st.subheader("AI Models Used")
        models_df = pd.DataFrame([
            {"model": model, "count": count}
            for model, count in article_analysis["model_distribution"].items()
        ])
        if not models_df.empty:
            fig = px.bar(models_df, x="model", y="count", title="AI Models Distribution")
            st.plotly_chart(fig)

    # Keywords Analysis
    st.subheader("Top Keywords")
    keywords_df = pd.DataFrame([
        {"keyword": kw, "count": count}
        for kw, count in sorted(article_analysis["keywords"].items(), key=lambda x: x[1], reverse=True)
    ]).head(20)
    if not keywords_df.empty:
        fig = px.bar(keywords_df, x="keyword", y="count", title="Top 20 Keywords")
        st.plotly_chart(fig)

def show_schema_explorer(admin_manager):
    """Display MongoDB schema information"""
    st.header("🔍 Schema Explorer")

    try:
        # Get schema analysis
        schema_data = admin_manager.get_schema_analysis()

        # Create tabs for different collections
        users_tab, articles_tab = st.tabs(["👥 Users Collection", "📚 Articles Collection"])

        with users_tab:
            st.subheader("Users Collection Schema")
            col1, col2 = st.columns(2)

            with col1:
                # Base Schema
                st.markdown("#### Base Fields")
                users_schema = schema_data.get("users_schema", [])
                if users_schema:
                    for field in sorted(users_schema):
                        st.markdown(f"- `{field}`")
                else:
                    st.info("No schema data available")

                # Collection Stats
                users_count = admin_manager.db.users.count_documents({})
                st.metric("Total Users", users_count)

            with col2:
                # Articles Schema in Users
                st.markdown("#### Articles Structure")
                articles_in_users = schema_data.get("articles_in_users", [])
                if articles_in_users:
                    for field in sorted(articles_in_users):
                        st.markdown(f"- `{field}`")

                # Sample Document
                with st.expander("View sample user document"):
                    sample_user = admin_manager.db.users.find_one()
                    if sample_user:
                        st.json(sample_user)

        with articles_tab:
            st.subheader("Articles Collection Schema")
            col1, col2 = st.columns(2)

            with col1:
                # Base Schema
                st.markdown("#### Base Fields")
                articles_schema = schema_data.get("articles_schema", [])
                if articles_schema:
                    for field in sorted(articles_schema):
                        st.markdown(f"- `{field}`")

                # Metadata Schema
                st.markdown("#### Metadata Fields")
                metadata_schema = schema_data.get("metadata_schema", [])
                if metadata_schema:
                    for field in sorted(metadata_schema):
                        st.markdown(f"- `{field}`")

                # Collection Stats
                articles_count = admin_manager.db.articles.count_documents({})
                st.metric("Total Articles", articles_count)

            with col2:
                # Summary Schema
                st.markdown("#### Summary Fields")
                summary_schema = schema_data.get("summary_schema", [])
                if summary_schema:
                    for field in sorted(summary_schema):
                        st.markdown(f"- `{field}`")

                # Sample Document
                with st.expander("View sample article document"):
                    sample_article = admin_manager.db.articles.find_one()
                    if sample_article:
                        st.json(sample_article)

    except Exception as e:
        st.error(f"Error exploring schema: {str(e)}")
        st.exception(e)

def show_user_management_section(admin_manager):
    """Handle user deletion and management"""
    st.markdown("#### Delete User")

    # Get user list
    user_analysis = admin_manager.get_user_analysis()
    user_emails = [user["email"] for user in user_analysis["user_details"]]

    # Initialize session states
    if 'show_user_confirm' not in st.session_state:
        st.session_state.show_user_confirm = False
    if 'delete_with_articles' not in st.session_state:
        st.session_state.delete_with_articles = False

    # User selection and options
    selected_user = st.selectbox(
        "Select user to manage:",
        options=user_emails,
        key="user_select"
    )

    delete_with_articles = st.checkbox(
        "Also delete user's articles",
        key="delete_articles_check",
        value=st.session_state.delete_with_articles
    )

    # Deletion process
    if st.button("Delete User", key="init_delete"):
        if selected_user == st.session_state.get('user_email'):
            st.error("Cannot delete your own account!")
        else:
            st.session_state.show_user_confirm = True
            st.session_state.delete_with_articles = delete_with_articles

    # Confirmation dialog
    if st.session_state.show_user_confirm:
        st.warning(f"Are you sure you want to delete user: {selected_user}?")
        confirm = st.checkbox("I understand this action cannot be undone", key="user_confirm")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Confirm Delete", key="final_delete"):
                if confirm:
                    result = admin_manager.delete_user_data(
                        selected_user,
                        st.session_state.delete_with_articles
                    )
                    if result["success"]:
                        st.success(f"User deleted: {selected_user}")
                        if st.session_state.delete_with_articles:
                            st.info(f"Deleted {result['articles_deleted']} articles")
                        st.session_state.show_user_confirm = False
                        st.rerun()
                    else:
                        st.error(f"Error: {result.get('error', 'Unknown error')}")
                else:
                    st.error("Please confirm the deletion")

        with col2:
            if st.button("Cancel", key="cancel_delete"):
                st.session_state.show_user_confirm = False
                st.rerun()

def show_article_management_section(admin_manager):
    """Handle article deletion and management"""
    # Delete Articles by Date
    st.markdown("#### Delete Articles by Date")

    dates = sorted(list(admin_manager.get_article_analysis()["dates"].keys()), reverse=True)
    if 'show_date_confirm' not in st.session_state:
        st.session_state.show_date_confirm = False

    selected_date = st.selectbox(
        "Select date to delete articles from:",
        options=dates,
        key="date_select"
    )

    if selected_date:
        articles = admin_manager.get_articles_by_date(selected_date)
        st.info(f"Found {len(articles)} articles for {selected_date}")

        if st.button("Delete Articles", key="init_date_delete"):
            st.session_state.show_date_confirm = True

        if st.session_state.show_date_confirm:
            st.warning(f"Are you sure you want to delete all articles from {selected_date}?")
            confirm = st.checkbox("I understand this action cannot be undone", key="date_confirm")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Confirm Delete", key="final_date_delete"):
                    if confirm:
                        found, deleted = admin_manager.delete_articles_by_date(selected_date)
                        st.success(f"Deleted {deleted} out of {found} articles")
                        st.session_state.show_date_confirm = False
                        st.rerun()
                    else:
                        st.error("Please confirm the deletion")

            with col2:
                if st.button("Cancel", key="cancel_date_delete"):
                    st.session_state.show_date_confirm = False
                    st.rerun()

    # Delete Individual Article
    st.markdown("#### Delete Individual Article")
    article_id = st.text_input("Enter Article ID:")
    if article_id:
        article = admin_manager.get_article_by_id(article_id)
        if article:
            st.write(f"Title: {article.get('metadata', {}).get('title', 'Unknown')}")
            with st.expander("View article details"):
                st.json(article)
            confirm = st.checkbox("Confirm deletion of this article", key="article_confirm")
            if st.button("Delete Article", key="delete_single", disabled=not confirm):
                if confirm:
                    if admin_manager.delete_article(article_id):
                        st.success("Article deleted successfully")
                        st.rerun()
                    else:
                        st.error("Failed to delete article")
        else:
            st.warning("Article not found")

def show_database_management_section(admin_manager):
    """Handle database statistics and cleanup operations"""
    # Database Statistics
    st.subheader("📊 Database Statistics")
    stats = admin_manager.get_database_stats()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Storage (MB)", f"{stats['total_storage_size']:.2f}")
        st.metric("Users Storage (MB)", f"{stats['users_storage_size']:.2f}")
        st.metric("Articles Storage (MB)", f"{stats['articles_storage_size']:.2f}")

    with col2:
        st.metric("Total Users", stats['total_users'])
        st.metric("Total Articles", stats['total_articles'])
        st.metric("Collections", len(stats['collections']))

    with col3:
        st.metric("Avg Article Size (MB)", f"{stats['avg_article_size']:.2f}")
        st.metric("Avg User Size (MB)", f"{stats['avg_user_size']:.2f}")
        st.write("Last Updated:", stats['last_updated'])

    # Database Cleanup
    st.subheader("🧹 Database Cleanup")
    cleanup_col1, cleanup_col2 = st.columns(2)

    with cleanup_col1:
        st.markdown("#### Clean Orphaned Articles")
        confirm = st.checkbox("Confirm cleanup of orphaned articles", key="cleanup_confirm")
        if st.button("Remove Orphaned Articles", key="cleanup_articles", disabled=not confirm):
            if confirm:
                result = admin_manager.cleanup_database()
                if result["success"]:
                    st.success(f"Removed {result['orphaned_articles_removed']} orphaned articles")
                    st.info(f"Removed {result['empty_users_removed']} empty users")
                    st.rerun()
                else:
                    st.error(f"Error during cleanup: {result.get('error', 'Unknown error')}")

    with cleanup_col2:
            st.markdown("#### Database Info")
            st.write("Database Name:", stats['database_name'])
            st.write("Collections:", ", ".join(stats['collections']))

def show_management_tools(admin_manager):
    """Main management interface"""
    st.header("⚙️ Data Management")

    # Create two columns for Users and Articles management
    user_col, article_col = st.columns(2)

    with user_col:
        st.subheader("👤 User Management")
        show_user_management_section(admin_manager)

    with article_col:
        st.subheader("📄 Article Management")
        show_article_management_section(admin_manager)

    # Database Management Section
    show_database_management_section(admin_manager)

def main():
    """Main function to run the admin dashboard"""
    st.set_page_config(page_title="Admin Dashboard", page_icon="🔐", layout="wide")

    check_admin_access()

    st.title("🔐 MongoDB Admin Dashboard")

    admin_manager = MongoDBAdminManager()

    tabs = st.tabs([
        "📊 Overview",
        "👥 User Analysis",
        "📚 Article Analysis",
        "🔍 Schema Explorer",
        "⚙️ Management"
    ])

    with tabs[0]:
        show_overview(admin_manager)

    with tabs[1]:
        show_user_analysis(admin_manager)

    with tabs[2]:
        show_article_analysis(admin_manager)

    with tabs[3]:
        show_schema_explorer(admin_manager)

    with tabs[4]:
        show_management_tools(admin_manager)

if __name__ == "__main__":
    main()