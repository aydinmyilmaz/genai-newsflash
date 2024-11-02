"""
MongoDB Schema and Data Viewer
Analyzes collection schema and displays user data
"""
from pymongo import MongoClient
import pprint
from datetime import datetime

# Initialize MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client['article_db']
users_collection = db['users']
articles_collection = db['articles']

def aggregate_schema(collection):
    """Analyze schema structure of a collection."""
    pipeline = [
        {"$project": {"arrayOfKeyValue": {"$objectToArray": "$$ROOT"}}},
        {"$unwind": "$arrayOfKeyValue"},
        {"$group": {"_id": None, "allKeys": {"$addToSet": "$arrayOfKeyValue.k"}}}
    ]
    results = collection.aggregate(pipeline)
    for result in results:
        print(f"\nKeys found in {collection.name}:")
        pprint.pprint(result['allKeys'])

def aggregate_nested_schema(collection_name, sub_document):
    """Analyze nested document schema structure."""
    collection = db[collection_name]
    pipeline = [
        {"$match": {sub_document: {"$exists": True}}},
        {"$project": {sub_document: {"$objectToArray": f"${sub_document}"}}},
        {"$unwind": f"${sub_document}"},
        {"$group": {"_id": None, "allKeys": {"$addToSet": f"${sub_document}.k"}}}
    ]
    results = collection.aggregate(pipeline)
    for result in results:
        print(f"\nAll keys in {sub_document} of collection {collection_name}:")
        pprint.pprint(result['allKeys'])

def display_user_data():
    """Display all users and their associated data."""
    users = users_collection.find()

    print("\n=== User Data Analysis ===")
    for user in users:
        print("\nUser:", user['email'])

        # Display article dates for this user
        if 'articles' in user and user['articles']:
            print("  Article Dates:")
            for date, article_ids in user['articles'].items():
                print(f"    {date}: {len(article_ids)} articles")

                # Fetch and display article details
                print("    Articles:")
                for article_id in article_ids:
                    article = articles_collection.find_one({"_id": article_id})
                    if article:
                        print(f"      - Title: {article['metadata']['title']}")
                        print(f"        URL: {article['metadata']['url']}")
                        print(f"        Processing Date: {article['metadata']['processing_date']}")
        else:
            print("  No articles found")

def analyze_user_statistics():
    """Analyze and display user statistics."""
    total_users = users_collection.count_documents({})
    users_with_articles = users_collection.count_documents({"articles": {"$ne": {}}})

    print("\n=== User Statistics ===")
    print(f"Total Users: {total_users}")
    print(f"Users with Articles: {users_with_articles}")

    # Analyze article distribution
    pipeline = [
        {"$project": {
            "email": 1,
            "articleCount": {"$size": {"$objectToArray": "$articles"}}
        }},
        {"$group": {
            "_id": None,
            "avgArticlesPerUser": {"$avg": "$articleCount"},
            "maxArticlesPerUser": {"$max": "$articleCount"},
            "minArticlesPerUser": {"$min": "$articleCount"}
        }}
    ]

    stats = list(users_collection.aggregate(pipeline))
    if stats:
        stats = stats[0]
        print(f"Average Articles per User: {stats['avgArticlesPerUser']:.2f}")
        print(f"Maximum Articles per User: {stats['maxArticlesPerUser']}")
        print(f"Minimum Articles per User: {stats['minArticlesPerUser']}")

def find_user_by_email(email):
    """Find and display specific user data."""
    user = users_collection.find_one({"email": email})
    if user:
        print(f"\n=== Data for User: {email} ===")
        if 'articles' in user and user['articles']:
            article_count = sum(len(articles) for articles in user['articles'].values())
            print(f"Total Articles: {article_count}")

            for date, article_ids in user['articles'].items():
                print(f"\nDate: {date}")
                print(f"Articles count: {len(article_ids)}")
                for article_id in article_ids:
                    article = articles_collection.find_one({"_id": article_id})
                    if article:
                        print(f"  - {article['metadata']['title']}")
        else:
            print("No articles found for this user")
    else:
        print(f"No user found with email: {email}")

def main():
    """Main function to run all analyses."""
    print("\n=== MongoDB Schema Analysis ===")

    # Analyze collection schemas
    aggregate_schema(users_collection)
    aggregate_schema(articles_collection)

    # Analyze nested schemas
    aggregate_nested_schema('users', 'articles')
    aggregate_nested_schema('articles', 'metadata')
    aggregate_nested_schema('articles', 'summary')

    # Display user data and statistics
    display_user_data()
    analyze_user_statistics()

    # Optional: Find specific user
    # find_user_by_email("example@email.com")

if __name__ == "__main__":
    main()