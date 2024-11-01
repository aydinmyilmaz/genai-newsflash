"""
MongoDB integration for saving article summaries.
To be imported into the smart_link_summarizer.py file.
"""
import logging
from datetime import datetime
from typing import List, Dict, Any
from modules.summary_agent import MongoDBManager

class SummaryMongoHandler:
    def __init__(self, mongo_uri: str = "mongodb://localhost:27017/"):
        self.logger = logging.getLogger(__name__)
        self.db_manager = MongoDBManager(mongo_uri)

    def format_article_for_mongo(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforms the article data into MongoDB schema format.
        """
        try:
            # Extract core fields with fallbacks
            metadata = {
                "url": article.get("url", ""),
                "title": article.get("title", ""),
                "content": article.get("content", ""),
                "authors": article.get("authors", []),
                "published_date": article.get("published_date", datetime.now().isoformat()),
                "processing_date": datetime.now().strftime("%Y-%m-%d"),
                "keywords": article.get("keywords", [])
            }

            summary = {
                "model_used": article.get("model_used", "gpt-4"),
                "text": article.get("summary_text", article.get("content", ""))
            }

            return {
                "metadata": metadata,
                "summary": summary
            }

    def save_summaries_to_mongo(self, articles: List[Dict[str, Any]], user_email: str = None) -> Dict[str, Any]:
        """
        Saves the processed articles to MongoDB and associates them with the user if provided.

        Returns:
            Dict containing success status and statistics
        """
        try:
            saved_count = 0
            skipped_count = 0
            saved_ids = []

            for article in articles:
                # Format article for MongoDB
                mongo_article = self.format_article_for_mongo(article)

                # Check if article already exists
                existing_article = self.db_manager.get_article_by_url(mongo_article["metadata"]["url"])
                if existing_article:
                    skipped_count += 1
                    continue

                # Save article
                article_id = self.db_manager.save_article(mongo_article)
                if article_id:
                    saved_count += 1
                    saved_ids.append(article_id)

                    # Associate with user if email provided
                    if user_email:
                        self.db_manager.add_article_to_user(
                            user_email=user_email,
                            article_id=article_id,
                            processing_date=datetime.now().strftime("%d%m%Y")
                        )

            return {
                "success": True,
                "saved_count": saved_count,
                "skipped_count": skipped_count,
                "saved_ids": saved_ids
            }

        except Exception as e:
            self.logger.error(f"Error saving to MongoDB: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }