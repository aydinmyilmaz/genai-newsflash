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
from modules.utils.helpers import load_config


class SummaryMongoHandler:
    def __init__(self, mongo_uri: str = "mongodb://localhost:27017/"):
        self.logger = logging.getLogger(__name__)
        try:
            self.db_manager = ArticleStorageManager(mongo_uri)
            self.mongo_query_manager = MongoDBQueryManager()
        except Exception as e:
            self.logger.error(f"Failed to initialize MongoDB connection: {str(e)}", exc_info=True)
            raise

    def check_article_exists(self, url: str) -> bool:
        """Simple check if article exists in MongoDB."""
        try:
            existing = self.db_manager.db.articles.find_one({
                "metadata.url": url
            })
            return bool(existing)
        except Exception as e:
            self.logger.error(f"Error checking article: {e}")
            return False

    def format_article_for_mongo(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Format article data for MongoDB storage with enhanced flexible key matching."""
        try:
            config = load_config()  # Your existing config loading function
            model_name = config.get('openai_model_name', 'gpt-4o-mini')
            current_date = datetime.now()
            processing_date = current_date.strftime("%Y-%m-%d")

            def normalize_key(key: str) -> str:
                """Normalize key by removing emojis and special characters."""
                import re
                key = re.sub(r'[^\w\s]', '', key)
                return ' '.join(key.lower().split())

            def get_value_flexible(data: Dict[str, Any], key_patterns: List[str], default: Any = "") -> Any:
                """
                Get value using flexible key matching with partial matches.
                """
                normalized_keys = {normalize_key(k): k for k in data.keys()}

                # First try exact matches
                for pattern in key_patterns:
                    normalized_pattern = normalize_key(pattern)
                    if normalized_pattern in normalized_keys:
                        return data[normalized_keys[normalized_pattern]]

                # Then try partial matches
                for pattern in key_patterns:
                    normalized_pattern = normalize_key(pattern)
                    for norm_key, original_key in normalized_keys.items():
                        if normalized_pattern in norm_key or norm_key in normalized_pattern:
                            return data[original_key]

                return default

            def format_summary_text(article_data: Dict[str, Any]) -> str:
                """
                Format the complete summary text with emojis and sections based on config.
                """
                sections_config = config.get('article_formatting', {}).get('sections', [])
                if not sections_config:
                    self.logger.warning("No sections configuration found, using default format")
                    return str(article_data)

                formatted_text = []
                for section in sections_config:
                    title = section['title']
                    content = get_value_flexible(article_data, section['keys'])

                    if content:
                        formatted_text.append(f"### {title}")
                        if isinstance(content, list):
                            formatted_text.extend([f"- {item}" for item in content])
                        else:
                            formatted_text.append(str(content))
                        formatted_text.append("")  # Add blank line between sections

                return "\n".join(formatted_text)

            def process_list_field(field_value):
                if isinstance(field_value, str):
                    return [item.strip() for item in field_value.split(',')]
                elif isinstance(field_value, list):
                    return [str(item).strip() for item in field_value]
                return []

            # Extract basic fields for metadata
            url = get_value_flexible(article, ['url', 'URL', 'source']).strip()
            title = get_value_flexible(article, ['title', 'Title']).strip()
            formatted_content = format_summary_text(article)

            # Handle tags/keywords and entities
            tags_raw = get_value_flexible(article, ['tags', 'Tags', 'keywords'], [])
            entities_raw = get_value_flexible(article, ['entities', 'Entities', 'Entity'], [])

            # Process tags and entities
            tags = process_list_field(tags_raw)
            entities = process_list_field(entities_raw)
            combined_tags = list(set(tags + entities))

            # Process other fields
            key_points = process_list_field(get_value_flexible(article, ['key points', 'Key Points'], []))
            implications = process_list_field(get_value_flexible(article, ['implications', 'Implications'], []))
            audience = process_list_field(get_value_flexible(article, ['audience', 'Intended Audience'], []))
            date = get_value_flexible(article, ['date', 'Date of Article'], processing_date)
            score = get_value_flexible(article, ['score', 'Strategic Importance Score'], [])

            # Validate essential fields
            if not url or not title or not formatted_content:
                self.logger.warning(
                    f"Missing essential fields for article - URL: {url}, Title: {title}, Has content: {bool(formatted_content)}")
                return None

            # Build metadata
            metadata = {
                "url": url,
                "title": title,
                "content": formatted_content,
                "published_date": date,
                "processing_date": processing_date,
                "keywords": combined_tags,
                "intended_audience": audience,
                'score': score

            }

            # Build summary
            summary = {
                "model_used": model_name,
                "text": formatted_content,
            }

            return {
                "metadata": metadata,
                "summary": summary
            }

        except Exception as e:
            self.logger.error(f"Error formatting article: {str(e)}", exc_info=True)
            return None

    def is_valid_article(self, article: Dict[str, Any]) -> bool:
        """Check if an article has valid, non-empty content."""
        metadata = article.get("metadata", {})
        summary = article.get("summary", {})

        has_valid_content = all([
            metadata.get("url", "").strip(),
            metadata.get("title", "").strip(),
            metadata.get("content", "").strip() or summary.get("text", "").strip()
        ])

        if not has_valid_content:
            self.logger.debug(f"Invalid article content - URL: {metadata.get('url', '')}, "
                            f"Title: {metadata.get('title', '')}, "
                            f"Has content: {bool(metadata.get('content', '').strip() or summary.get('text', '').strip())}")

        return has_valid_content

    def save_summaries_to_mongo(self, articles: List[Dict[str, Any]], user_email: str = None) -> Dict[str, Any]:
        """Save articles to MongoDB with improved duplicate checking and validation."""
        try:
            saved_count = 0
            skipped_count = 0
            updated_count = 0
            saved_ids = []
            skipped_ids = []  # New list to track skipped article IDs
            invalid_format_urls = []  # Track URLs that failed formatting
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
                    # Format article for MongoDB
                    mongo_article = self.format_article_for_mongo(article)
                    if not mongo_article:
                        url = article.get("URL") or article.get("url", "N/A")
                        invalid_format_urls.append(url)
                        self.logger.warning(f"Skipping invalid article format for URL: {url}")
                        skipped_count += 1
                        continue

                    # Check for existing article
                    existing_article = self.db_manager.db.articles.find_one({
                        "metadata.url": mongo_article["metadata"]["url"]
                    })

                    if existing_article:
                        existing_id = str(existing_article["_id"])
                        # Check if existing article has valid content
                        if self.is_valid_article(existing_article):
                            skipped_count += 1
                            skipped_ids.append(existing_id)
                            self.logger.info(f"Skipping existing valid article - ID: {existing_id}, "
                                           f"URL: {existing_article['metadata']['url']}")

                            if user_email:
                                # Add existing article ID to user's articles
                                self.db_manager.db.users.update_one(
                                    {"email": user_email},
                                    {"$addToSet": {f"articles.{current_date}": existing_id}}
                                )
                            continue
                        else:
                            # Update the existing empty article with new content
                            self.logger.info(f"Updating empty article - ID: {existing_id}, "
                                           f"URL: {existing_article['metadata']['url']}")
                            result = self.db_manager.db.articles.update_one(
                                {"_id": existing_article["_id"]},
                                {"$set": mongo_article}
                            )
                            if result.modified_count > 0:
                                updated_count += 1
                                saved_ids.append(existing_id)
                            continue

                    # Insert new article
                    result = self.db_manager.db.articles.insert_one(mongo_article)
                    article_id = str(result.inserted_id)
                    saved_ids.append(article_id)
                    saved_count += 1
                    self.logger.info(f"Saved new article - ID: {article_id}, "
                                   f"URL: {mongo_article['metadata']['url']}")

                    # Associate with user if email provided
                    if user_email:
                        self.db_manager.db.users.update_one(
                            {"email": user_email},
                            {"$addToSet": {f"articles.{current_date}": article_id}}
                        )

                except Exception as e:
                    self.logger.error(f"Error processing article: {str(e)}", exc_info=True)
                    continue

            # Log summary statistics
            self.logger.info(f"Processing complete - "
                           f"Saved: {saved_count}, "
                           f"Updated: {updated_count}, "
                           f"Skipped: {skipped_count}")
            self.logger.info(f"Saved IDs: {saved_ids}")
            self.logger.info(f"Skipped IDs: {skipped_ids}")
            if invalid_format_urls:
                self.logger.warning(f"Invalid format URLs: {invalid_format_urls}")

            return {
                "success": True,
                "saved_count": saved_count,
                "updated_count": updated_count,
                "skipped_count": skipped_count,
                "saved_ids": saved_ids,
                "skipped_ids": skipped_ids,  # Added to return value
                "invalid_format_urls": invalid_format_urls  # Added to return value
            }

        except Exception as e:
            self.logger.error(f"Error in save_summaries_to_mongo: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }