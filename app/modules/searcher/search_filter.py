#search_filter.py
"""
This module provides an intelligent search functionality that combines DuckDuckGo search with LLM-based
relevance filtering. It searches for web content based on keywords, evaluates the relevance of results
using OpenAI's language models, and filters out low-quality matches. The module includes comprehensive
logging and metrics tracking for search performance and result quality.
"""

import logging
import time
from typing import List, Dict
from datetime import datetime
from pydantic import BaseModel, Field
from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import RatelimitException
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain

from modules.utils.helpers import load_config


# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Add file handler for logging
file_handler = logging.FileHandler('app.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

class SearchResult(BaseModel):
    """Schema for a single search result evaluation"""
    url: str = Field(description="The URL of the search result")
    score: int = Field(description="Relevance score from 0-10")

class SearchEvaluations(BaseModel):
    """Schema for all search result evaluations"""
    results: List[SearchResult] = Field(description="List of evaluated search results")

class SearchMetrics:
    """Class to track search and filtering metrics"""
    def __init__(self):
        self.search_start_time = None
        self.search_end_time = None
        self.filter_start_time = None
        self.filter_end_time = None
        self.total_links_found = 0
        self.relevant_links_count = 0
        self.score_distribution = {i: 0 for i in range(11)}  # 0-10 scores

    def get_search_duration(self):
        if self.search_start_time and self.search_end_time:
            return round(self.search_end_time - self.search_start_time, 2)
        return 0

    def get_filter_duration(self):
        if self.filter_start_time and self.filter_end_time:
            return round(self.filter_end_time - self.filter_start_time, 2)
        return 0

class SearchModule:
    def __init__(self):
        config = load_config()
        self.model_name = config.get("openai_model_name")
        self.api_key = config.get("OPENAI_API_KEY")
        self.metrics = SearchMetrics()
        self._initialize_llm()
        logger.info(f"SearchModule initialized with model: {self.model_name}")

    def _initialize_llm(self):
        """Initialize LangChain components"""
        if self.api_key:
            self.llm = ChatOpenAI(
                api_key=self.api_key,
                model_name=self.model_name,
                temperature=0.1
            )
            self.parser = PydanticOutputParser(pydantic_object=SearchEvaluations)
            logger.info("LLM and parser initialized successfully")
        else:
            logger.error("OpenAI API key not found")
            self.llm = None
            self.parser = None

    def _create_evaluation_chain(self) -> LLMChain:
        """Create the evaluation chain with prompt and output parser"""
        template = """You are evaluating search results for relevance to these keywords: {keywords}

For each result, rate its relevance from 0-10 based on:
1. Direct mention or discussion of the keywords
2. Recency and relevance of the content
3. Authority and reliability of the source

Consider the context and provide accurate numerical scores.

Search Results:
{search_results}

{format_instructions}

Important: Focus on results with clear relevance to the keywords and current context."""

        prompt = ChatPromptTemplate.from_template(
            template=template,
            partial_variables={
                "format_instructions": self.parser.get_format_instructions()
            }
        )

        return LLMChain(
            llm=self.llm,
            prompt=prompt
        )

    def search_duckduckgo(self, keywords: str, timelimit: str = 'w', max_results: int = 20) -> List[Dict]:
        """
        Perform a DuckDuckGo search for the specified keywords.

        Args:
            keywords (str): Search query
            timelimit (str): Time limit for search results (e.g., 'd' for day, 'w' for week)
            max_results (int): Maximum number of results to return

        Returns:
            List[Dict]: List of search results
        """
        try:
            self.metrics.search_start_time = time.time()

            with DDGS() as ddgs:
                results = list(ddgs.text(
                    keywords,
                    timelimit=timelimit,
                    max_results=max_results,
                    region="de-de"
                ))

            self.metrics.search_end_time = time.time()
            self.metrics.total_links_found = len(results)

            logger.info(f"Retrieved {len(results)} results for query: {keywords}")
            return results

        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def save_links_to_file(self, links: List[str], filename: str = "sources/article_links.txt"):
        """Save links to a file, avoiding duplicates."""
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            # Read existing links
            existing_links = set()
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    existing_links = set(f.read().splitlines())

            # Add new links
            with open(filename, 'a') as f:
                for link in links:
                    if link not in existing_links:
                        f.write(f"{link}\n")
                        existing_links.add(link)

            return True
        except Exception as e:
            logger.error(f"Error saving links to file: {e}")
            return False

    def _format_search_results(self, search_results: List[Dict]) -> str:
        """Format search results for the prompt"""
        formatted_results = []
        for i, item in enumerate(search_results, 1):
            result = (
                f"Result {i}:\n"
                f"Title: {item['title']}\n"
                f"URL: {item['href']}\n"
                f"Description: {item.get('body', '')[:300]}\n"
            )
            formatted_results.append(result)
        return "\n\n".join(formatted_results)

    def filter_relevant_links(self, search_results: List[Dict], keywords: List[str], min_score: int = 6) -> List[str]:
        """Filter search results for relevance to provided keywords."""
        if not self.api_key or not self.llm:
            logger.error("OpenAI API key not found or LLM not initialized")
            return []

        try:
            logger.info(f"Starting relevance filtering for {len(search_results)} results")
            self.metrics.filter_start_time = time.time()

            # Create and run the evaluation chain
            chain = self._create_evaluation_chain()

            response = chain.run({
                "keywords": ", ".join(keywords),
                "search_results": self._format_search_results(search_results)
            })

            # Parse response and extract relevant links
            evaluations = self.parser.parse(response)
            relevant_links = []

            # Reset score distribution
            self.metrics.score_distribution = {i: 0 for i in range(11)}

            # Process results and collect metrics
            for result in evaluations.results:
                self.metrics.score_distribution[result.score] += 1

                if result.score >= min_score:
                    relevant_links.append(result.url)
                    logger.info(f"High relevance (score {result.score}): {result.url}")
                else:
                    logger.debug(f"Low relevance (score {result.score}): {result.url}")

            self.metrics.filter_end_time = time.time()
            self.metrics.relevant_links_count = len(relevant_links)

            # Log comprehensive metrics
            filter_duration = self.metrics.get_filter_duration()
            logger.info(f"Filtering completed in {filter_duration} seconds")
            logger.info(f"Found {len(relevant_links)} relevant links (score ≥ {min_score}) out of {len(search_results)} total")
            logger.info("Score distribution:")
            for score, count in self.metrics.score_distribution.items():
                if count > 0:
                    logger.info(f"Score {score}: {count} results")

            logger.info(f"Relevance rate: {round(len(relevant_links)/len(search_results) * 100, 2)}%")

            return relevant_links

        except Exception as e:
            logger.error(f"Filtering error: {str(e)}", exc_info=True)
            return []

    def get_performance_metrics(self) -> dict:
        """Get all performance metrics for the current search session"""
        return {
            "search_duration": self.metrics.get_search_duration(),
            "filter_duration": self.metrics.get_filter_duration(),
            "total_links_found": self.metrics.total_links_found,
            "relevant_links_count": self.metrics.relevant_links_count,
            "relevance_rate": round(self.metrics.relevant_links_count / max(self.metrics.total_links_found, 1) * 100, 2),
            "score_distribution": self.metrics.score_distribution
        }

# Example usage
if __name__ == "__main__":
    search_module = SearchModule()

    # Example search and filter
    keywords = ["cloud computing", "digital transformation"]
    search_results = search_module.search_duckduckgo(" ".join(keywords))

    if search_results:
        relevant_links = search_module.filter_relevant_links(
            search_results=search_results,
            keywords=keywords
        )

        # Get and print all metrics
        metrics = search_module.get_performance_metrics()
        print("\nPerformance Metrics:")
        print(f"Search Duration: {metrics['search_duration']} seconds")
        print(f"Filter Duration: {metrics['filter_duration']} seconds")
        print(f"Total Links: {metrics['total_links_found']}")
        print(f"Relevant Links: {metrics['relevant_links_count']}")
        print(f"Relevance Rate: {metrics['relevance_rate']}%")