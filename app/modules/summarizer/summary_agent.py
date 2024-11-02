#summary_agent.py


"""
MongoDB Schema Documentation remains for reference:

1. Database: article_db
   Collections:

   a) users:
   {
     "_id": ObjectId,
     "email": String (unique index),
     "articles": {
       "DDMMYYYY": [String]  // Date-based array of article ObjectId references
     }
   }

   b) articles:
   {
     "_id": ObjectId,
     "metadata": {
       "url": String (unique index),
       "title": String,
       "content": String,
       "authors": Array<String>,
       "published_date": String (ISO format),
       "processing_date": String (ISO format),
       "keywords": Array<String>
     },
     "summary": {
       "model_used": String,
       "text": String
     }
   }
"""

import json
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from newspaper import Article
from langchain_openai import ChatOpenAI
from swarm import Swarm, Agent
import time
from scrapegraphai.graphs import SmartScraperGraph
import nltk

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')


class ContentProcessor:
    def __init__(self, summary_prompt_path, model="gpt-4o-mini"):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        self.model = model
        self.summary_prompt_path = summary_prompt_path

    def fetch_article_data(self, link: str) -> Optional[Dict[str, Any]]:
        """Fetch article data using newspaper3k, with a fallback to SmartScraperGraph if the primary method fails."""
        if not isinstance(link, str) or not link.strip():
            self.logger.error(f"Invalid link format: {link}")
            return None

        # Try to fetch using newspaper3k's Article
        try:
            article = Article(link)
            article.download()
            article.parse()
            article.nlp()

            self.logger.info(f"Article parsed successfully:")
            self.logger.info(f"Title: {article.title}")
            self.logger.info(f"Authors: {article.authors}")
            self.logger.info(f"Publish date: {article.publish_date}")
            self.logger.info(f"Text length: {len(article.text)}")

            return {
                "metadata": {
                    "url": article.url,
                    "title": article.title,
                    "content": article.text,
                    "authors": article.authors,
                    "published_date": article.publish_date.isoformat() if article.publish_date else datetime.now().isoformat(),
                    "processing_date": datetime.now().date().isoformat(),
                    "detailed_processing_date": datetime.now().isoformat()
                }
            }

        except Exception as e:
            self.logger.error(f"Error fetching article using Article for {link}: {str(e)}. Falling back to SmartScraperGraph.", exc_info=True)
            return self.scrape_with_smart_scraper(link)

    def scrape_with_smart_scraper(self, url: str) -> Optional[Dict[str, Any]]:
        """Fallback to scraping with SmartScraperGraph if newspaper3k fails."""
        smart_scraper_prompt = (
            "Extract the following metadata from the webpage content at the specified URL. "
            "Ensure the output is in JSON format with the exact keys:\n\n"
            "1. title: The main title or headline of the article.\n"
            "2. content: The full main body text of the article, excluding ads, comments, and unrelated text.\n"
            "3. authors: A list of authors of the article, if available.\n"
            "4. published_date: The publication date of the article in ISO 8601 format (YYYY-MM-DD), if available.\n"
            "If any field is missing or cannot be found, return an empty string or an empty list as appropriate for that field."
        )

        graph_config = {
            "llm": {
                "api_key": os.getenv("OPENAI_API_KEY"),
                "model": "openai/"+self.model
            },
            "verbose": True,
            "headless": False,
        }

        try:
            start_time = time.time()
            self.logger.info(f"Starting SmartScraperGraph for: {url}")

            smart_scraper_graph = SmartScraperGraph(
                prompt=smart_scraper_prompt,
                source=url,
                config=graph_config
            )
            result = smart_scraper_graph.run()

            duration = time.time() - start_time
            self.logger.info(f"SmartScraperGraph finished scraping {url} in {duration:.2f} seconds")

            return self.parse_scraper_result(result, url)

        except Exception as e:
            self.logger.error(f"Error with SmartScraperGraph fallback for {url}: {str(e)}", exc_info=True)
            return None

    def parse_scraper_result(self, result: Any, url: str) -> Optional[Dict[str, Any]]:
        """Parse the result from SmartScraperGraph, ensuring a dictionary format is returned."""
        if isinstance(result, dict):
            return {
                "metadata": {
                    "url": url,
                    "title": result.get("title", ""),
                    "content": result.get("content", ""),
                    "authors": result.get("authors", []),
                    "published_date": result.get("published_date", datetime.now().isoformat()),
                    "keywords": result.get("keywords", []),
                    "processing_date": datetime.now().date().isoformat(),
                    "detailed_processing_date": datetime.now().isoformat()
                }
            }
        elif isinstance(result, str):
            self.logger.warning(f"Result returned as a string for {url}. Using minimal metadata.")
            return {
                "metadata": {
                    "url": url,
                    "title": "Unknown Title",
                    "content": result,
                    "authors": [],
                    "published_date": datetime.now().isoformat(),
                    "keywords": [],
                    "processing_date": datetime.now().date().isoformat(),
                    "detailed_processing_date": datetime.now().isoformat()
                }
            }
        else:
            self.logger.warning(f"Unexpected result type for {url}: {type(result)}")
            return None

    def validate_topic(self, article_content: str, topic: str) -> bool:
        """Validate if the article content is relevant to the topic."""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            self.logger.error("OpenAI API key not found")
            return False
        try:
            llm = ChatOpenAI(model=self.model)
            prompt = f"Is the following article content relevant to the topic '{topic}'? Answer only 'yes' or 'no'."
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": article_content[:3000]}  # Limit content length
            ]
            response = llm.invoke(messages, temperature=0.1, max_tokens=10)
            result = response.content.strip().lower()
            if "yes" in result.lower():
                self.logger.info(f"Topic validation result: {result} for topic: {topic}")
                return True
            else:
                return False
        except Exception as e:
            self.logger.error(f"Topic validation failed: {str(e)}", exc_info=True)
            return False

    def generate_summary(self, article_text: str) -> str:
        """Generate a summary for the article using OpenAI with a prompt from a specified file path."""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            self.logger.error("OpenAI API key not found")
            return ""

        try:
            # Load prompt from the text file specified by self.summary_prompt
            with open(self.summary_prompt_path, 'r') as file:
                prompt = file.read().strip()

            llm = ChatOpenAI(model=self.model)
            messages = [{"role": "system", "content": prompt}, {"role": "user", "content": article_text}]
            response = llm.invoke(messages, temperature=0.1)

            return response.content
        except FileNotFoundError:
            self.logger.error(f"Prompt file not found: {self.summary_prompt_path}")
            return ""
        except Exception as e:
            self.logger.error(f"Summary generation failed: {str(e)}", exc_info=True)
            return ""