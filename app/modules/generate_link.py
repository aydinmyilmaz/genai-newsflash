import logging
import json
import time
import yaml
from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import RatelimitException
from datetime import datetime

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Create a logger for this module
logger = logging.getLogger(__name__)

# Optionally, you can add a file handler
file_handler = logging.FileHandler('app.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

def search_duckduckgo(query, max_results=20, max_retries=3):
    logger.info(f"Searching DuckDuckGo for query: {query}")
    with DDGS() as ddgs:
        retry_count = 0
        while retry_count < max_retries:
            try:
                results = []
                for r in ddgs.text(query, max_results=max_results):
                    logger.debug(f"Scraped result: {r}")
                    results.append(r)
                    time.sleep(3)
                logger.info(f"Successfully retrieved {len(results)} results for query: {query}")
                return results
            except RatelimitException:
                retry_count += 1
                logger.warning(f"RatelimitException encountered. Retrying in {2 ** retry_count} seconds.")
                time.sleep(2 ** retry_count)
    logger.error(f"Failed to retrieve results for query: {query} after {max_retries} retries")
    return []

def update_json_file(file_path, topic, results, manual_results):
    try:
        logger.info(f"Updating JSON file at: {file_path}")
        with open(file_path, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logger.info(f"File {file_path} does not exist or is corrupted. Creating a new file.")
        data = {}

    if topic and topic not in data:
        data[topic] = []

    if topic:
        data[topic].extend(results)

    counter = 1
    for manual_result in manual_results:
        key = f"Other Important Topics - {counter}"
        while key in data:
            counter += 1
            key = f"Other Important Topics - {counter}"

        data[key] = [manual_result]
        counter += 1

    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Data successfully written to {file_path} with {len(results)} new items under the topic '{topic}' and {len(manual_results)} new manual entries with unique keys.")
    except Exception as e:
        logger.error(f"Failed to write to file {file_path}: {e}")

def read_additional_links(file_path):
    try:
        with open(file_path, 'r') as f:
            return f.read().splitlines()
    except FileNotFoundError:
        logger.warning(f"File {file_path} not found.")
        return []

def load_config(file_name):
    try:
        with open(file_name, 'r') as ymlfile:
            return yaml.safe_load(ymlfile)
    except Exception as e:
        logger.error(f"Failed to load config from {file_name}: {e}")
        return {}

def run_link_update(link_file_path):
    logger.info("Starting link update process")
    config = load_config('config.yml')

    topics_file = config.get('file_paths', {}).get('topic_file')
    results_file = link_file_path #config['file_paths']['link_file']
    manual_links_file = config.get('file_paths', {}).get('manual_link_file')

    logger.info(f"Results file: {results_file}")
    logger.info(f"Topics file: {topics_file}")
    logger.info(f"Manual links file: {manual_links_file}")

    additional_links = read_additional_links(manual_links_file)

    try:
        with open(topics_file, 'r') as f:
            topics = f.read().splitlines()
        logger.info(f"Loaded topics: {topics}")
    except Exception as e:
        logger.error(f"Error reading topics file: {e}")
        topics = []

    if topics:
        for topic in topics:
            logger.info(f"Searching for: {topic}")
            results = search_duckduckgo(topic)
            formatted_results = [{'title': r['title'], 'link': r['href'], 'snippet': r['body'][0:100], 'timestamp': datetime.now().isoformat()} for r in results]

            manual_results = []
            for link in additional_links:
                if topic in link:
                    manual_results.append({
                        'title': f'Manual entry for {topic}',
                        'link': link,
                        'snippet': 'Manually added link',
                        'timestamp': datetime.now().isoformat()
                    })

            update_json_file(results_file, topic, formatted_results, manual_results)
            time.sleep(2)

    if not topics and additional_links:
        manual_results = []
        for link in additional_links:
            manual_results.append({
                'title': 'Manual entry with no specific topic',
                'link': link,
                'snippet': 'Manually added link',
                'timestamp': datetime.now().isoformat()
            })

        update_json_file(results_file, None, [], manual_results)

if __name__ == "__main__":
    run_link_update()