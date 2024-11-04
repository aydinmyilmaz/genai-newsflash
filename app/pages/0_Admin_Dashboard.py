
# pages/0_Admin_Dashboard.py
import io
import json
import re

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from datetime import datetime
from wordcloud import WordCloud
from collections import defaultdict
import matplotlib.pyplot as plt

from modules.mongodb_manager.mongo_admin_manager import MongoDBAdminManager
from modules.mongodb_manager.token_cost_analyzer import TokenCostAnalyzer

# Configuration
ADMIN_EMAILS = {"admin@example.com", "amrtyilmaz@gmail.com"}

def check_admin_access():
    """Check if current user has admin access"""
    user_email = st.session_state.get('user_email')
    if not user_email or user_email not in ADMIN_EMAILS:
        st.error("⛔ Access Denied. This page is only accessible to administrators.")
        st.stop()

def normalize_keyword(keyword: str) -> str:
    """Normalize keywords by converting to lowercase and removing special characters"""
    # Convert to lowercase
    keyword = keyword.lower()
    # Remove special characters and replace with space
    keyword = re.sub(r'[^a-z0-9\s]', ' ', keyword)
    # Replace multiple spaces with single space and strip
    keyword = ' '.join(keyword.split())
    return keyword

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
    """Display article statistics and analysis with improved visualizations"""
    st.header("📚 Article Analysis")

    article_analysis = admin_manager.get_article_analysis()

    # Process sources to combine those less than 1%
    sources_df = pd.DataFrame([
        {"source": source, "count": count}
        for source, count in article_analysis["sources"].items()
    ])

    if not sources_df.empty:
        # Calculate percentages
        total_articles = sources_df['count'].sum()
        sources_df['percentage'] = (sources_df['count'] / total_articles * 100).round(2)

        # Separate sources into main and others
        main_sources = sources_df[sources_df['percentage'] >= 1].copy()
        other_sources = sources_df[sources_df['percentage'] < 1]

        # Add "Others" row if there are any small sources
        if not other_sources.empty:
            others_row = pd.DataFrame([{
                'source': 'Others',
                'count': other_sources['count'].sum(),
                'percentage': other_sources['percentage'].sum()
            }])
            main_sources = pd.concat([main_sources, others_row])

        # Sort by percentage descending
        main_sources = main_sources.sort_values('percentage', ascending=False)

        # Display pie chart
        fig = px.pie(
            main_sources,
            values='percentage',
            names='source',
            title='Article Sources Distribution (>1%)'
        )
        st.plotly_chart(fig)

    # Process and normalize keywords
    normalized_keywords = defaultdict(int)
    for keyword, count in article_analysis["keywords"].items():
        norm_keyword = normalize_keyword(keyword)
        if norm_keyword:  # Skip empty strings
            normalized_keywords[norm_keyword] += count

    # Convert to DataFrame and sort
    keywords_df = pd.DataFrame([
        {"keyword": kw, "count": count}
        for kw, count in normalized_keywords.items()
    ]).sort_values('count', ascending=False).head(30)

    # Create tabs for different visualizations
    keyword_tabs = st.tabs(["Bar Chart", "Word Cloud"])

    with keyword_tabs[0]:
        st.subheader("Top 30 Keywords")
        if not keywords_df.empty:
            fig = px.bar(
                keywords_df,
                x="keyword",
                y="count",
                title="Top 30 Keywords Distribution"
            )
            fig.update_layout(
                xaxis_tickangle=-45,
                xaxis_title="Keyword",
                yaxis_title="Count"
            )
            st.plotly_chart(fig)

    with keyword_tabs[1]:
        st.subheader("Keywords Word Cloud")
        if not keywords_df.empty:
            # Create word cloud
            wordcloud = WordCloud(
                width=800,
                height=400,
                background_color='white',
                max_words=30
            ).generate_from_frequencies(dict(zip(keywords_df.keyword, keywords_df['count'])))

            # Create matplotlib figure
            plt.figure(figsize=(10, 5))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')

            # Convert plot to image
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
            buf.seek(0)
            st.image(buf)
            plt.close()

    # Display model distribution
    st.subheader("AI Models Used")
    models_df = pd.DataFrame([
        {"model": model, "count": count}
        for model, count in article_analysis["model_distribution"].items()
    ])
    if not models_df.empty:
        fig = px.bar(models_df, x="model", y="count", title="AI Models Distribution")
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

def show_cost_analysis(admin_manager):
    """Display token and cost analysis"""
    st.header("💰 Cost Analysis")

    # Initialize analyzer
    analyzer = TokenCostAnalyzer()

    # Get all articles
    articles = list(admin_manager.db.articles.find())

    if not articles:
        st.warning("No articles found in the database")
        return

    # Calculate costs
    cost_analysis = analyzer.aggregate_costs(articles)

    # Display overall metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Articles", len(articles))
        st.metric("Content Tokens", f"{cost_analysis['total_content_tokens']:,}")
    with col2:
        st.metric("Prompt Tokens", f"{cost_analysis['total_prompt_tokens']:,}")
        st.metric("Output Tokens", f"{cost_analysis['total_output_tokens']:,}")
    with col3:
        st.metric("Total Cost", f"${cost_analysis['total_cost']:.2f}")
        avg_cost = cost_analysis['total_cost'] / len(articles)
        st.metric("Average Cost/Article", f"${avg_cost:.4f}")

    # Display cost breakdown by model
    st.subheader("Cost Breakdown by Model")

    # Create DataFrame for model breakdown
    model_data = pd.DataFrame(cost_analysis['by_model'])
    if not model_data.empty:
        # Format costs as currency
        for col in ['input_cost', 'output_cost', 'total_cost']:
            model_data[col] = model_data[col].apply(lambda x: f"${x:.4f}")

        # Format tokens with commas
        for col in ['content_tokens', 'prompt_tokens', 'input_tokens', 'output_tokens']:
            model_data[col] = model_data[col].apply(lambda x: f"{x:,}")

        st.dataframe(
            model_data,
            column_config={
                "model_name": "Model",
                "content_tokens": "Content Tokens",
                "prompt_tokens": "Prompt Tokens",
                "input_tokens": "Total Input Tokens",
                "output_tokens": "Output Tokens",
                "input_cost": "Input Cost",
                "output_cost": "Output Cost",
                "total_cost": "Total Cost"
            },
            hide_index=True
        )

    # Create visualizations
    col1, col2 = st.columns(2)

    with col1:
        # Token distribution by model
        token_data = pd.DataFrame(cost_analysis['by_model'])
        if not token_data.empty:
            fig = px.bar(
                token_data,
                x='model_name',
                y=['content_tokens', 'prompt_tokens', 'output_tokens'],
                title='Token Usage by Model',
                labels={'value': 'Number of Tokens', 'model_name': 'Model'},
                barmode='group'
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig)

    with col2:
        # Cost distribution by model
        cost_data = pd.DataFrame(cost_analysis['by_model'])
        if not cost_data.empty:
            fig = px.pie(
                cost_data,
                values='total_cost',
                names='model_name',
                title='Total Cost Distribution by Model'
            )
            st.plotly_chart(fig)

    # Monthly trend
    st.subheader("Cost Trend")
    monthly_data = []
    for article in articles:
        date = article.get('metadata', {}).get('processing_date', '')
        if date:
            analysis = analyzer.analyze_article_tokens_and_costs(article)
            monthly_data.append({
                'date': pd.to_datetime(date).strftime('%Y-%m'),
                'cost': analysis['total_cost']
            })

    if monthly_data:
        df = pd.DataFrame(monthly_data)
        df = df.groupby('date')['cost'].sum().reset_index()
        fig = px.line(
            df,
            x='date',
            y='cost',
            title='Monthly Cost Trend',
            labels={'cost': 'Total Cost ($)', 'date': 'Month'}
        )
        st.plotly_chart(fig)


def main():
    """Main function to run the admin dashboard"""
    st.set_page_config(page_title="Admin Dashboard", page_icon="🔐", layout="wide")

    check_admin_access()

    st.title("🔐 MongoDB Admin Dashboard")

    admin_manager = MongoDBAdminManager()

    # In your main() function, add the cost analysis tab:
    tabs = st.tabs([
        "📊 Overview",
        "👥 User Analysis",
        "📚 Article Analysis",
        "💰 Cost Analysis",  # New tab
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
        show_cost_analysis(admin_manager)

    with tabs[4]:
        show_schema_explorer(admin_manager)

    with tabs[5]:
        show_management_tools(admin_manager)

if __name__ == "__main__":
    main()