#db_query_maker.py
"""
This module provides a MongoDB interface for retrieving and managing article data. It enables querying
articles by topic and date range, with functionality for counting articles and determining the overall
date range of the collection. The module includes methods for displaying article information including
titles, URLs, publication dates, and summaries.
"""


from pymongo import MongoClient
import logging
from datetime import datetime

class ArticleDataRetriever:
    def __init__(self, mongodb_uri: str = "mongodb://localhost:27017/"):
        """Initialize the data retriever with database connection."""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Initialize MongoDB
        self.client = MongoClient(mongodb_uri)
        self.db = self.client['article_db']
        self.article_collection = self.db['articles']

    def retrieve_articles_by_topic(self, topic: str):
        """Retrieve articles by topic."""
        query = {"results.metadata.keywords": {"$in": [topic.lower()]}}  # Assume keywords are stored in lowercase
        articles = self.article_collection.find(query)
        return list(articles)

    def retrieve_articles_by_date(self, start_date: str, end_date: str):
        """Retrieve articles published within a specific date range."""
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        query = {"results.metadata.published_date": {"$gte": start, "$lte": end}}
        articles = self.article_collection.find(query)
        return list(articles)

    def count_articles(self):
        """Count the total number of articles in the database."""
        count = self.article_collection.count_documents({})
        return count

    def date_range_of_articles(self):
        """Find the earliest and latest publication date in the collection."""
        earliest = self.article_collection.find_one(sort=[("results.metadata.published_date", 1)])
        latest = self.article_collection.find_one(sort=[("results.metadata.published_date", -1)])
        if earliest and latest:
            earliest_date = earliest['results'][0]['metadata']['published_date']
            latest_date = latest['results'][0]['metadata']['published_date']
            return (earliest_date, latest_date)
        else:
            return None

    def display_articles(self, articles):
        """Display articles information."""
        for article in articles:
            for result in article['results']:
                print(f"Title: {result['metadata']['title']}")
                print(f"URL: {result['metadata']['url']}")
                print(f"Published Date: {result['metadata']['published_date']}")
                print(f"Summary: {result['summary']}")
                print("-----------------------------------------------------")

if __name__ == "__main__":
    retriever = ArticleDataRetriever()
    topic = "ai"  # Example topic
    start_date = "2024-10-01"  # Example start date
    end_date = "2024-10-31"  # Example end date

    print("Total Number of Articles in Database:")
    print(retriever.count_articles())

    date_range = retriever.date_range_of_articles()
    if date_range:
        print(f"Date Range of Articles from {date_range[0]} to {date_range[1]}")
    else:
        print("No articles found to determine the date range.")

    print("\nArticles by Topic:")
    articles_by_topic = retriever.retrieve_articles_by_topic(topic)
    retriever.display_articles(articles_by_topic)

    print("\nArticles by Date Range:")
    articles_by_date = retriever.retrieve_articles_by_date(start_date, end_date)
    retriever.display_articles(articles_by_date)
