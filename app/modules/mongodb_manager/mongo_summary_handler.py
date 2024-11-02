# #mongo_summary_handler.py
# """
# MongoDB integration for saving article summaries.
# To be imported into the smart_link_summarizer.py file.
# """
# import logging
# from datetime import datetime
# from typing import List, Dict, Any
# from .mongodb_query_manager import MongoDBQueryManager, ArticleStorageManager

# class SummaryMongoHandler:
#     def __init__(self, mongo_uri: str = "mongodb://localhost:27017/"):
#         self.logger = logging.getLogger(__name__)
#         try:
#             self.db_manager =  ArticleStorageManager(mongo_uri)
#         except Exception as e:
#             self.logger.error(f"Failed to initialize MongoDB connection: {str(e)}", exc_info=True)
#             raise

#         self.mongo_query_manager = MongoDBQueryManager()

#     def format_article_for_mongo(self, article: Dict[str, Any]) -> Dict[str, Any]:
#         """
#         Transforms the article data into MongoDB schema format.
#         """
#         try:
#             # Format the current date for processing
#             current_date = datetime.now()
#             processing_date = current_date.strftime("%Y-%m-%d")
#             detailed_processing_date = current_date.strftime("%d%m%Y")

#             # Extract and format metadata
#             metadata = {
#                 "url": article.get("🌐 URL", article.get("url", "")),
#                 "title": article.get("🛣️ Title", article.get("title", "")),
#                 "content": article.get("📝 Summary", article.get("content", "")),
#                 "authors": article.get("authors", []),
#                 "published_date": article.get("📅 Date of Article", article.get("published_date", processing_date)),
#                 "processing_date": processing_date,
#                 "detailed_processing_date": detailed_processing_date,
#                 "keywords": article.get("🏷️ Tags", "").split(", ") if article.get("🏷️ Tags") else []
#             }

#             # Format summary
#             summary = {
#                 "model_used": "gpt-4o",  # Default model
#                 "text": self.mongo_query_manager.format_article_summary(article)
#             }

#             return {
#                 "metadata": metadata,
#                 "summary": summary
#             }
#         except Exception as e:
#             self.logger.error(f"Error formatting article for MongoDB: {str(e)}", exc_info=True)
#             raise

#     def save_summaries_to_mongo(self, articles: List[Dict[str, Any]], user_email: str = None) -> Dict[str, Any]:
#         """
#         Saves the processed articles to MongoDB and associates them with the user if provided.
#         """
#         try:
#             saved_count = 0
#             skipped_count = 0
#             saved_ids = []
#             current_date = datetime.now().strftime("%d%m%Y")

#             # Create or update user document if email is provided
#             if user_email:
#                 user_doc = {
#                     "email": user_email,
#                     "articles": {
#                         current_date: []  # Initialize empty list for current date
#                     }
#                 }
#                 self.db_manager.db.users.update_one(
#                     {"email": user_email},
#                     {"$setOnInsert": user_doc},
#                     upsert=True
#                 )

#             for article in articles:
#                 try:
#                     # Format article for MongoDB
#                     mongo_article = self.format_article_for_mongo(article)

#                     # Check if article already exists by URL
#                     existing_article = self.db_manager.db.articles.find_one({
#                         "metadata.url": mongo_article["metadata"]["url"]
#                     })

#                     if existing_article:
#                         skipped_count += 1
#                         if user_email:
#                             # Add existing article ID to user's articles if not already present
#                             self.db_manager.db.users.update_one(
#                                 {"email": user_email},
#                                 {
#                                     "$addToSet": {
#                                         f"articles.{current_date}": str(existing_article["_id"])
#                                     }
#                                 }
#                             )
#                         continue

#                     # Insert new article
#                     result = self.db_manager.db.articles.insert_one(mongo_article)
#                     article_id = str(result.inserted_id)
#                     saved_ids.append(article_id)
#                     saved_count += 1

#                     # Associate article with user if email provided
#                     if user_email:
#                         self.db_manager.db.users.update_one(
#                             {"email": user_email},
#                             {
#                                 "$addToSet": {
#                                     f"articles.{current_date}": article_id
#                                 }
#                             }
#                         )

#                 except Exception as e:
#                     self.logger.error(f"Error processing article: {str(e)}", exc_info=True)
#                     continue

#             return {
#                 "success": True,
#                 "saved_count": saved_count,
#                 "skipped_count": skipped_count,
#                 "saved_ids": saved_ids
#             }

#         except Exception as e:
#             self.logger.error(f"Error in save_summaries_to_mongo: {str(e)}", exc_info=True)
#             return {
#                 "success": False,
#                 "error": str(e)
#             }

"""
MongoDB integration for saving article summaries with simplified duplicate detection.
"""
import logging
from datetime import datetime
from typing import List, Dict, Any
from .mongodb_query_manager import MongoDBQueryManager, ArticleStorageManager

class SummaryMongoHandler:
    def __init__(self, mongo_uri: str = "mongodb://localhost:27017/"):
        self.logger = logging.getLogger(__name__)
        try:
            self.db_manager = ArticleStorageManager(mongo_uri)
            self.mongo_query_manager = MongoDBQueryManager()
        except Exception as e:
            self.logger.error(f"Failed to initialize MongoDB connection: {str(e)}", exc_info=True)
            raise

    def format_article_for_mongo(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Format article data for MongoDB storage."""
        try:
            # Get current date
            current_date = datetime.now()
            processing_date = current_date.strftime("%Y-%m-%d")

            # Extract basic fields with fallbacks
            url = article.get("URL") or article.get("url", "")
            title = article.get("Title") or article.get("title", "")

            # Process tags
            tags = article.get("Tags", "")
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(",") if tag.strip()]
            elif isinstance(tags, list):
                tags = [tag for tag in tags if tag]
            else:
                tags = []

            # Build metadata
            metadata = {
                "url": url,
                "title": title,
                "date": article.get("Date of Article", processing_date),
                "processing_date": processing_date,
                "keywords": tags
            }

            # Build summary
            summary = {
                "text": article.get("Summary", ""),
                "key_points": article.get("Key Points", []),
                "implications": article.get("Implications and Industry Trends", [])
            }

            return {
                "metadata": metadata,
                "summary": summary
            }

        except Exception as e:
            self.logger.error(f"Error formatting article: {str(e)}", exc_info=True)
            raise

    def save_summaries_to_mongo(self, articles: List[Dict[str, Any]], user_email: str = None) -> Dict[str, Any]:
        """Save articles to MongoDB with basic duplicate checking."""
        try:
            saved_count = 0
            skipped_count = 0
            saved_ids = []
            current_date = datetime.now().strftime("%d%m%Y")

            # Initialize user document if email provided
            if user_email:
                user_doc = {
                    "email": user_email,
                    "articles": {
                        current_date: []
                    }
                }
                self.db_manager.db.users.update_one(
                    {"email": user_email},
                    {"$setOnInsert": user_doc},
                    upsert=True
                )

            for article in articles:
                try:
                    # Format article
                    mongo_article = self.format_article_for_mongo(article)

                    # Check for duplicate using URL
                    existing = self.db_manager.db.articles.find_one({
                        "metadata.url": mongo_article["metadata"]["url"]
                    })

                    if existing:
                        skipped_count += 1
                        # Add to user's articles if not already present
                        if user_email:
                            self.db_manager.db.users.update_one(
                                {"email": user_email},
                                {"$addToSet": {f"articles.{current_date}": str(existing["_id"])}}
                            )
                        continue

                    # Insert new article
                    result = self.db_manager.db.articles.insert_one(mongo_article)
                    article_id = str(result.inserted_id)
                    saved_ids.append(article_id)
                    saved_count += 1

                    # Associate with user if email provided
                    if user_email:
                        self.db_manager.db.users.update_one(
                            {"email": user_email},
                            {"$addToSet": {f"articles.{current_date}": article_id}}
                        )

                except Exception as e:
                    self.logger.error(f"Error processing article: {str(e)}", exc_info=True)
                    continue

            return {
                "success": True,
                "saved_count": saved_count,
                "skipped_count": skipped_count,
                "saved_ids": saved_ids
            }

        except Exception as e:
            self.logger.error(f"Error in save_summaries_to_mongo: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }