# mongodb_query_manager.py
# from pymongo import MongoClient
# from bson import ObjectId
# import logging
# from datetime import datetime
# from typing import List, Dict, Any, Optional, Tuple

# # Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# class MongoDBQueryManager:
#     def __init__(self, connection_string: str = "mongodb://localhost:27017/", user_email: str = "amrtyilmaz@gmail.com"):
#         """Initialize MongoDB connection"""
#         try:
#             self.client = MongoClient(connection_string)
#             self.db = self.client['article_db']
#             self.user_email = user_email
#         except Exception as e:
#             logger.error(f"Failed to connect to MongoDB: {str(e)}", exc_info=True)
#             raise

#     def get_available_dates(self) -> List[str]:
#         """Fetch available dates for the current user"""
#         try:
#             user = self.db.users.find_one({"email": self.user_email})
#             if user and 'articles' in user:
#                 dates = list(user['articles'].keys())
#                 dates.sort(reverse=True)
#                 return dates
#             return []
#         except Exception as e:
#             logger.error(f"Error fetching available dates: {str(e)}", exc_info=True)
#             return []

#     def get_articles_count_for_date(self, date: str) -> int:
#         """Get number of articles for a specific date for the current user"""
#         try:
#             user = self.db.users.find_one(
#                 {"email": self.user_email},
#                 {f"articles.{date}": 1}
#             )
#             if user and 'articles' in user and date in user['articles']:
#                 return len(user['articles'][date])
#             return 0
#         except Exception as e:
#             logger.error(f"Error counting articles for date {date}: {str(e)}", exc_info=True)
#             return 0

#     def get_article_ids_for_dates(self, selected_dates: List[str]) -> List[ObjectId]:
#         """Get article IDs for selected dates for the current user"""
#         try:
#             if not selected_dates:
#                 return []

#             user = self.db.users.find_one(
#                 {"email": self.user_email},
#                 {f"articles.{date}": 1 for date in selected_dates}
#             )

#             article_ids = []
#             if user and 'articles' in user:
#                 for date in selected_dates:
#                     if date in user['articles']:
#                         article_ids.extend([ObjectId(id_str) for id_str in user['articles'][date]])

#             logger.info(f"Found {len(article_ids)} article IDs for dates")
#             return article_ids
#         except Exception as e:
#             logger.error(f"Error fetching article IDs: {str(e)}", exc_info=True)
#             return []

#     def filter_articles_by_entities(self, articles: List[Dict], search_entities: List[str]) -> List[Dict]:
#         """Filter articles by searching entities in summary text"""
#         if not search_entities:
#             return articles

#         filtered_articles = []
#         # Clean and prepare search entities
#         search_entities = [entity.strip().lower() for entity in search_entities if entity.strip()]

#         for article in articles:
#             # Get summary text and convert to lowercase for case-insensitive search
#             summary_text = article.get('summary', {}).get('text', '').lower()

#             # Check if any entity appears in the summary text
#             if any(entity in summary_text for entity in search_entities):
#                 filtered_articles.append(article)
#                 logger.info(f"Found match in article: {article.get('metadata', {}).get('title', 'No Title')}")

#         logger.info(f"Filtered {len(filtered_articles)} articles from {len(articles)} total")
#         return filtered_articles

#     def fetch_articles_paginated(self, article_ids: List[ObjectId], page: int, articles_per_page: int,
#                                entities: List[str] = None) -> Tuple[List[Dict], int]:
#         """Fetch articles with pagination and entity filtering"""
#         try:
#             if not article_ids:
#                 return [], 0

#             # Fetch all articles for the given IDs
#             articles = list(self.db.articles.find({"_id": {"$in": article_ids}}))

#             # Apply entity filtering if specified
#             if entities:
#                 articles = self.filter_articles_by_entities(articles, entities)

#             # Calculate pagination
#             total_articles = len(articles)
#             total_pages = (total_articles + articles_per_page - 1) // articles_per_page

#             # Calculate start and end indices for the current page
#             start_idx = (page - 1) * articles_per_page
#             end_idx = min(start_idx + articles_per_page, total_articles)

#             # Get articles for the current page
#             page_articles = articles[start_idx:end_idx]

#             logger.info(f"Fetched {len(page_articles)} articles for page {page} out of {total_articles} total")
#             return page_articles, total_pages

#         except Exception as e:
#             logger.error(f"Error fetching articles: {str(e)}", exc_info=True)
#             return [], 0

#     def format_article_summary(self, article: Dict) -> str:
#         """Format article summary with proper date handling"""
#         try:
#             if not article or 'summary' not in article:
#                 return "Summary not available"

#             summary_text = article['summary']['text']

#             if "There is not enough extracted data" in summary_text:
#                 sections = summary_text.split('### ')
#                 formatted_sections = []

#                 for section in sections:
#                     if section:
#                         if section.startswith("Date of Article 📅"):
#                             formatted_sections.append(
#                                 f"Date of Article 📅\n{article['metadata']['processing_date']}"
#                             )
#                         else:
#                             formatted_sections.append(section)

#                 return "### " + "### ".join(formatted_sections)
#             else:
#                 return summary_text.replace(
#                     "### Date of Article 📅",
#                     "\n\n### Date of Article 📅"
#                 )
#         except Exception as e:
#             logger.error(f"Error formatting article summary: {str(e)}", exc_info=True)
#             return "Error formatting summary"

# mongodb_query_manager.py
from pymongo import MongoClient
from bson import ObjectId
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ArticleStorageManager:
    """Manages article and user data storage operations in MongoDB"""
    def __init__(self, uri="mongodb://localhost:27017/"):
        try:
            self.client = MongoClient(uri)
            # Test the connection
            self.client.server_info()
            logger.info("Successfully connected to MongoDB")

            self.db = self.client['article_db']
            # Add direct collection references
            self.article_collection = self.db.articles
            self.user_collection = self.db.users
            self.setup_database_indexes()
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}", exc_info=True)
            raise

    def setup_database_indexes(self):
        """Setup database indexes for unique constraints."""
        self.article_collection.create_index([("metadata.url", 1)], unique=True)
        self.user_collection.create_index([("email", 1)], unique=True)

    def get_article_by_url(self, url: str) -> Optional[Dict]:
        """Check if an article with the given URL already exists in the database."""
        return self.article_collection.find_one({"metadata.url": url})

    def save_article(self, article_data: Dict) -> Optional[str]:
        """Save article data to MongoDB if it doesn't already exist."""
        try:
            logger.info(f"Attempting to save article: {article_data['metadata']['title']}")

            # Check if article is already in the database
            existing_article = self.get_article_by_url(article_data['metadata']['url'])
            if existing_article:
                logger.info(f"Article already exists with ID: {existing_article['_id']}")
                return str(existing_article["_id"])

            # Insert new article
            result = self.article_collection.insert_one(article_data)
            logger.info(f"New article saved with ID: {result.inserted_id}")

            # Verify the insert
            saved_article = self.article_collection.find_one({"_id": result.inserted_id})
            if saved_article:
                logger.info("Article verified in database")
                return str(result.inserted_id)
            else:
                logger.error("Article not found after insert")
                return None

        except Exception as e:
            logger.error(f"Failed to save article: {str(e)}", exc_info=True)
            return None

    def add_article_to_user(self, user_email: str, article_id: str, processing_date: str) -> bool:
        """Associate an article with a user by processing date."""
        try:
            # Save article under user's collection by date
            result = self.user_collection.update_one(
                {"email": user_email},
                {"$addToSet": {f"articles.{processing_date}": article_id}},
                upsert=True
            )
            logger.info(f"Article {article_id} linked to user {user_email} under date {processing_date}")
            return result.modified_count > 0 or result.upserted_id is not None
        except Exception as e:
            logger.error(f"Failed to add article to user: {str(e)}", exc_info=True)
            return False


class MongoDBQueryManager:
    """Manages querying and retrieval of articles and user data from MongoDB"""
    def __init__(self, connection_string: str = "mongodb://localhost:27017/", user_email: str = "amrtyilmaz@gmail.com"):
        try:
            self.client = MongoClient(connection_string)
            self.db = self.client['article_db']
            self.user_collection = self.db.users
            self.article_collection = self.db.articles
            self.user_email = user_email
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}", exc_info=True)
            raise

    def get_available_dates(self) -> List[str]:
        """Fetch available dates for the current user"""
        try:
            user = self.user_collection.find_one({"email": self.user_email})
            if user and 'articles' in user:
                dates = list(user['articles'].keys())
                dates.sort(reverse=True)
                return dates
            return []
        except Exception as e:
            logger.error(f"Error fetching available dates: {str(e)}", exc_info=True)
            return []

    def get_articles_count_for_date(self, date: str) -> int:
        """Get number of articles for a specific date for the current user"""
        try:
            user = self.user_collection.find_one(
                {"email": self.user_email},
                {f"articles.{date}": 1}
            )
            if user and 'articles' in user and date in user['articles']:
                return len(user['articles'][date])
            return 0
        except Exception as e:
            logger.error(f"Error counting articles for date {date}: {str(e)}", exc_info=True)
            return 0

    def get_article_ids_for_dates(self, selected_dates: List[str]) -> List[ObjectId]:
        """Get article IDs for selected dates for the current user"""
        try:
            if not selected_dates:
                return []

            user = self.user_collection.find_one(
                {"email": self.user_email},
                {f"articles.{date}": 1 for date in selected_dates}
            )

            article_ids = []
            if user and 'articles' in user:
                for date in selected_dates:
                    if date in user['articles']:
                        article_ids.extend([ObjectId(id_str) for id_str in user['articles'][date]])

            logger.info(f"Found {len(article_ids)} article IDs for dates")
            return article_ids
        except Exception as e:
            logger.error(f"Error fetching article IDs: {str(e)}", exc_info=True)
            return []

    def filter_articles_by_entities(self, articles: List[Dict], search_entities: List[str]) -> List[Dict]:
        """Filter articles by searching entities in summary text"""
        if not search_entities:
            return articles

        filtered_articles = []
        search_entities = [entity.strip().lower() for entity in search_entities if entity.strip()]

        for article in articles:
            summary_text = article.get('summary', {}).get('text', '').lower()
            if any(entity in summary_text for entity in search_entities):
                filtered_articles.append(article)
                logger.info(f"Found match in article: {article.get('metadata', {}).get('title', 'No Title')}")

        logger.info(f"Filtered {len(filtered_articles)} articles from {len(articles)} total")
        return filtered_articles

    def fetch_articles_paginated(self, article_ids: List[ObjectId], page: int, articles_per_page: int,
                               entities: List[str] = None) -> Tuple[List[Dict], int]:
        """Fetch articles with pagination and entity filtering"""
        try:
            if not article_ids:
                return [], 0

            articles = list(self.article_collection.find({"_id": {"$in": article_ids}}))

            if entities:
                articles = self.filter_articles_by_entities(articles, entities)

            total_articles = len(articles)
            total_pages = (total_articles + articles_per_page - 1) // articles_per_page

            start_idx = (page - 1) * articles_per_page
            end_idx = min(start_idx + articles_per_page, total_articles)

            page_articles = articles[start_idx:end_idx]

            logger.info(f"Fetched {len(page_articles)} articles for page {page} out of {total_articles} total")
            return page_articles, total_pages

        except Exception as e:
            logger.error(f"Error fetching articles: {str(e)}", exc_info=True)
            return [], 0

    def format_article_summary(self, article: Dict) -> str:
        """
        Format article summary with proper date handling for both legacy and new JSON schema formats.
        Uses flexible key matching to handle variations in key names.

        Args:
            article (Dict): Article dictionary in either legacy or new JSON schema format

        Returns:
            str: Formatted article summary
        """
        try:
            if not article:
                return "Summary not available"

            # Helper function to find keys flexibly
            def find_key(search_terms: list, dict_keys: list) -> str:
                """Find the first key that contains any of the search terms"""
                for key in dict_keys:
                    if any(term.lower() in key.lower() for term in search_terms):
                        return key
                return None

            # Check if it's new format by looking for date or emoji indicators
            article_keys = article.keys()
            date_key = find_key(['date', '📅'], article_keys)

            if date_key:  # New JSON schema format
                formatted_sections = []

                # Add Date
                if date_key:
                    formatted_sections.append(f"### Date of Article 📅\n{article[date_key]}")

                # Add Title
                title_key = find_key(['title', '🛣️'], article_keys)
                if title_key:
                    formatted_sections.append(f"### Title 🛣️\n{article[title_key]}")

                # Add Summary
                summary_key = find_key(['summary', '📝'], article_keys)
                if summary_key:
                    formatted_sections.append(f"### Summary 📝\n{article[summary_key]}")

                # Add Key Points
                points_key = find_key(['key points', 'points', '🔑'], article_keys)
                if points_key and article[points_key]:
                    points = article[points_key]
                    if isinstance(points, list):
                        points_text = '\n'.join([f"- {point}" for point in points])
                    else:
                        points_text = points
                    formatted_sections.append(f"### Key Points 🔑\n{points_text}")

                # Add Implications
                implications_key = find_key(['implications', 'trends', '📈'], article_keys)
                if implications_key and article[implications_key]:
                    implications = article[implications_key]
                    if isinstance(implications, list):
                        implications_text = '\n'.join([f"- {imp}" for imp in implications])
                    else:
                        implications_text = implications
                    formatted_sections.append(f"### Implications 📈\n{implications_text}")

                # Add Intended Audience
                audience_key = find_key(['audience', '👥'], article_keys)
                if audience_key and article[audience_key]:
                    audience = article[audience_key]
                    if isinstance(audience, list):
                        audience_text = '\n'.join([f"- {aud}" for aud in audience])
                    else:
                        audience_text = audience
                    formatted_sections.append(f"### Intended Audience 👥\n{audience_text}")

                # Add URL/Source
                url_key = find_key(['url', 'source', '🌐'], article_keys)
                if url_key:
                    formatted_sections.append(f"### Source 🌐\n{article[url_key]}")

                return "\n\n".join(formatted_sections)

            # Handle legacy format
            if 'summary' not in article:
                return "Summary not available"

            summary_text = article['summary']['text']
            if "There is not enough extracted data" in summary_text:
                sections = summary_text.split('### ')
                formatted_sections = []
                for section in sections:
                    if section:
                        if section.startswith("Date of Article 📅"):
                            formatted_sections.append(
                                f"Date of Article 📅\n{article['metadata']['processing_date']}"
                            )
                        else:
                            formatted_sections.append(section)
                return "### " + "### ".join(formatted_sections)
            else:
                return summary_text.replace(
                    "### Date of Article 📅",
                    "\n\n### Date of Article 📅"
                )

        except Exception as e:
            logger.error(f"Error formatting article summary: {str(e)}", exc_info=True)
            return "Error formatting summary"