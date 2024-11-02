# modules/mongodb_manager/mongo_admin_manager.py

from pymongo import MongoClient
from typing import Dict, List, Any, Tuple
import logging
from datetime import datetime
from collections import defaultdict
from bson import ObjectId

class MongoDBAdminManager:
    def __init__(self, mongo_uri: str = "mongodb://localhost:27017/"):
        self.logger = logging.getLogger(__name__)
        try:
            self.client = MongoClient(mongo_uri)
            self.db = self.client['article_db']
            self.logger.info("Successfully connected to MongoDB")
        except Exception as e:
            self.logger.error(f"Failed to connect to MongoDB: {str(e)}", exc_info=True)
            raise

    def get_schema_analysis(self) -> Dict[str, Any]:
        """Analyze schema structure of collections"""
        try:
            pipeline = [
                {"$project": {"arrayOfKeyValue": {"$objectToArray": "$$ROOT"}}},
                {"$unwind": "$arrayOfKeyValue"},
                {"$group": {"_id": None, "allKeys": {"$addToSet": "$arrayOfKeyValue.k"}}}
            ]

            # Get collection schemas
            users_schema = list(self.db.users.aggregate(pipeline))
            articles_schema = list(self.db.articles.aggregate(pipeline))

            # Get nested schemas
            articles_nested_pipeline = [
                {"$match": {"articles": {"$exists": True}}},
                {"$project": {"articles": {"$objectToArray": "$articles"}}},
                {"$unwind": "$articles"},
                {"$group": {"_id": None, "allKeys": {"$addToSet": "$articles.k"}}}
            ]
            articles_in_users = list(self.db.users.aggregate(articles_nested_pipeline))

            metadata_pipeline = [
                {"$match": {"metadata": {"$exists": True}}},
                {"$project": {"metadata": {"$objectToArray": "$metadata"}}},
                {"$unwind": "$metadata"},
                {"$group": {"_id": None, "allKeys": {"$addToSet": "$metadata.k"}}}
            ]
            metadata_schema = list(self.db.articles.aggregate(metadata_pipeline))

            summary_pipeline = [
                {"$match": {"summary": {"$exists": True}}},
                {"$project": {"summary": {"$objectToArray": "$summary"}}},
                {"$unwind": "$summary"},
                {"$group": {"_id": None, "allKeys": {"$addToSet": "$summary.k"}}}
            ]
            summary_schema = list(self.db.articles.aggregate(summary_pipeline))

            return {
                "users_schema": users_schema[0]['allKeys'] if users_schema else [],
                "articles_schema": articles_schema[0]['allKeys'] if articles_schema else [],
                "articles_in_users": articles_in_users[0]['allKeys'] if articles_in_users else [],
                "metadata_schema": metadata_schema[0]['allKeys'] if metadata_schema else [],
                "summary_schema": summary_schema[0]['allKeys'] if summary_schema else []
            }
        except Exception as e:
            self.logger.error(f"Error analyzing schema: {str(e)}")
            return {}

    def get_user_analysis(self) -> Dict[str, Any]:
        """Get detailed user analysis"""
        try:
            users = list(self.db.users.find())
            analysis = {
                "total_users": len(users),
                "users_with_articles": 0,
                "user_details": [],
                "article_counts_by_date": defaultdict(lambda: defaultdict(int))
            }

            for user in users:
                user_details = {
                    "email": user.get('email', 'Unknown'),
                    "dates": [],
                    "total_articles": 0
                }

                if 'articles' in user and user['articles']:
                    analysis["users_with_articles"] += 1
                    for date, articles in user['articles'].items():
                        article_count = len(articles)
                        user_details["total_articles"] += article_count
                        user_details["dates"].append({
                            "date": date,
                            "article_count": article_count
                        })
                        analysis["article_counts_by_date"][date][user['email']] = article_count

                analysis["user_details"].append(user_details)

            # Calculate averages
            total_articles = sum(u["total_articles"] for u in analysis["user_details"])
            analysis["average_articles_per_user"] = total_articles / len(users) if users else 0
            analysis["max_articles_per_user"] = max((u["total_articles"] for u in analysis["user_details"]), default=0)
            analysis["min_articles_per_user"] = min((u["total_articles"] for u in analysis["user_details"]), default=0)

            return analysis
        except Exception as e:
            self.logger.error(f"Error analyzing users: {str(e)}")
            return {}

    def get_article_analysis(self) -> Dict[str, Any]:
        """Get detailed article analysis with proper date handling"""
        try:
            articles = list(self.db.articles.find())
            analysis = {
                "total_articles": len(articles),
                "sources": defaultdict(int),
                "dates": defaultdict(int),
                "keywords": defaultdict(int),
                "authors": defaultdict(int),
                "model_distribution": defaultdict(int)
            }

            for article in articles:
                metadata = article.get('metadata', {})
                summary = article.get('summary', {})

                # Handle URLs/sources
                url = metadata.get('url', '')
                if url:
                    domain = url.split("//")[-1].split("/")[0]
                    analysis["sources"][domain] += 1

                # Handle dates - ensure consistent format
                try:
                    date_str = metadata.get('processing_date', '')
                    if date_str:
                        # Convert to datetime and back to string for consistency
                        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        formatted_date = date_obj.strftime('%Y-%m-%d')
                        analysis["dates"][formatted_date] += 1
                except (ValueError, TypeError):
                    # Fallback for invalid dates
                    analysis["dates"]["unknown"] += 1

                # Handle keywords
                for keyword in metadata.get('keywords', []):
                    analysis["keywords"][keyword] += 1

                # Handle authors
                for author in metadata.get('authors', []):
                    analysis["authors"][author] += 1

                # Handle models
                model = summary.get('model_used', 'unknown')
                analysis["model_distribution"][model] += 1

            return analysis
        except Exception as e:
            self.logger.error(f"Error analyzing articles: {str(e)}")
            return {
                "total_articles": 0,
                "sources": {},
                "dates": {},
                "keywords": {},
                "authors": {},
                "model_distribution": {}
            }

    def get_article_by_id(self, article_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific article"""
        try:
            return self.db.articles.find_one({"_id": ObjectId(article_id)})
        except Exception as e:
            self.logger.error(f"Error fetching article {article_id}: {str(e)}")
            return {}

    def get_articles_by_date(self, date: str) -> List[Dict[str, Any]]:
        """Get all articles from a specific date"""
        try:
            return list(self.db.articles.find({"metadata.processing_date": date}))
        except Exception as e:
            self.logger.error(f"Error fetching articles for date {date}: {str(e)}")
            return []

    def delete_user_data(self, user_email: str, delete_articles: bool = False) -> Dict[str, Any]:
        """Delete user and optionally their articles"""
        try:
            # Get user's articles before deletion
            user = self.db.users.find_one({"email": user_email})
            if not user:
                return {"success": False, "error": "User not found"}

            article_ids = []
            if 'articles' in user:
                for date_articles in user['articles'].values():
                    article_ids.extend([ObjectId(aid) for aid in date_articles])

            # Delete user
            user_result = self.db.users.delete_one({"email": user_email})

            result = {
                "success": True,
                "user_deleted": user_result.deleted_count > 0,
                "articles_deleted": 0
            }

            # Optionally delete articles
            if delete_articles and article_ids:
                articles_result = self.db.articles.delete_many({"_id": {"$in": article_ids}})
                result["articles_deleted"] = articles_result.deleted_count

            self.logger.info(f"Deleted user {user_email} with {result['articles_deleted']} articles")
            return result

        except Exception as e:
            self.logger.error(f"Error deleting user {user_email}: {str(e)}")
            return {"success": False, "error": str(e)}

    def cleanup_database(self) -> Dict[str, Any]:
        """Perform database cleanup operations"""
        try:
            # Find orphaned articles
            all_user_articles = set()
            for user in self.db.users.find():
                for date_articles in user.get('articles', {}).values():
                    all_user_articles.update(date_articles)

            orphaned_result = self.db.articles.delete_many({
                "_id": {"$nin": [ObjectId(aid) for aid in all_user_articles]}
            })

            # Find users with no articles
            empty_users_result = self.db.users.delete_many({
                "$or": [
                    {"articles": {"$exists": False}},
                    {"articles": {}}
                ]
            })

            return {
                "success": True,
                "orphaned_articles_removed": orphaned_result.deleted_count,
                "empty_users_removed": empty_users_result.deleted_count
            }
        except Exception as e:
            self.logger.error(f"Error during database cleanup: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_database_stats(self) -> Dict[str, Any]:
        """Get general database statistics"""
        try:
            # Get database command stats
            db_stats = self.db.command("dbStats")

            # Get collection stats
            users_stats = self.db.command("collStats", "users")
            articles_stats = self.db.command("collStats", "articles")

            # Calculate storage sizes in MB
            total_storage_size = db_stats["storageSize"] / (1024 * 1024)
            users_storage = users_stats["storageSize"] / (1024 * 1024)
            articles_storage = articles_stats["storageSize"] / (1024 * 1024)

            # Get collection counts
            total_users = self.db.users.count_documents({})
            total_articles = self.db.articles.count_documents({})

            stats = {
                "total_storage_size": total_storage_size,
                "users_storage_size": users_storage,
                "articles_storage_size": articles_storage,
                "total_users": total_users,
                "total_articles": total_articles,
                "avg_article_size": articles_storage / (total_articles or 1),
                "avg_user_size": users_storage / (total_users or 1),
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "database_name": self.db.name,
                "collections": list(self.db.list_collection_names())
            }

            return stats
        except Exception as e:
            self.logger.error(f"Error getting database stats: {str(e)}")
            return {
                "total_storage_size": 0,
                "users_storage_size": 0,
                "articles_storage_size": 0,
                "total_users": 0,
                "total_articles": 0,
                "avg_article_size": 0,
                "avg_user_size": 0,
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "database_name": self.db.name,
                "collections": []
            }