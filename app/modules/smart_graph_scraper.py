import json
import time
from typing import List, Dict
from scrapegraphai.graphs import SmartScraperGraph
import yaml
import logging
import os
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s')
logger = logging.getLogger(__name__)

def load_config(file_name='config.yml') -> Dict:
    try:
        with open(file_name, 'r') as config_file:
            config = yaml.safe_load(config_file)
        logger.info(f"Config loaded successfully from {file_name}.")
        return config
    except FileNotFoundError:
        logger.error(f"Config file {file_name} not found.")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file {file_name}: {e}")
        raise

def load_prompt(filename: str) -> str:
    try:
        with open(filename, 'r') as f:
            prompt = f.read().strip()
        logger.info(f"Loaded prompt from {filename}: {prompt[:50]}...")
        return prompt
    except FileNotFoundError:
        logger.error(f"Prompt file {filename} not found.")
        raise

def scrape_url(url: str, prompt: str, graph_config: Dict) -> Dict:
    start_time = time.time()
    logger.info(f"Starting to scrape: {url}")

    try:
        smart_scraper_graph = SmartScraperGraph(
            prompt=prompt,
            source=url,
            config=graph_config
        )
        result = smart_scraper_graph.run()
    except Exception as e:
        logger.error(f"Error scraping {url}: {str(e)}", exc_info=True)
        return {"url": url, "error": str(e)}

    duration = time.time() - start_time
    logger.info(f"Finished scraping {url} in {duration:.2f} seconds")

    if isinstance(result, dict):
        return result
    elif isinstance(result, str):
        return {"url": url, "data": result}
    else:
        logger.warning(f"Unexpected result type for {url}: {type(result)}")
        return {"url": url, "error": "Unexpected result type"}

def scrape_urls(urls: List[str], prompt: str, api_key: str, model: str) -> List[Dict]:
    graph_config = {
        "llm": {
            "api_key": api_key,
            "model": model,
        },
        "verbose": True,
        "headless": False,
    }

    results = []
    for url in urls:
        results.append(scrape_url(url, prompt, graph_config))

    logger.info(f"Scraped {len(results)} URLs")
    return results

def smart_graph_scrap(urls: List[str], config_path='config.yml', custom_prompt=None) -> List[Dict]:
    try:
        config = load_config(config_path)
        load_dotenv()  # Load environment variables from .env file
    except Exception as e:
        logger.error(f"Error loading configuration from {config_path}: {e}", exc_info=True)
        raise

    api_key = os.getenv('OPENAI_API_KEY') or config.get('OPENAI_API_KEY')
    model = os.getenv('OPENAI_MODEL_NAME') or config.get('OPENAI_MODEL_NAME')

    if not api_key or not model:
        logger.error(f"API key or model name not found in {config_path}.")
        raise ValueError(f"API key or model name not found in {config_path}.")

    if custom_prompt is None:
        prompt_folder = config['file_paths'].get('prompt_folder')
        if not prompt_folder:
            logger.error("Prompt folder not specified in config.")
            raise ValueError("Prompt folder not specified in config.")

        prompt_files = [f for f in os.listdir(prompt_folder) if f.endswith('.txt')]
        if not prompt_files:
            logger.error("No prompt files found in the specified folder.")
            raise FileNotFoundError("No prompt files found in the specified folder.")

        # Use the first prompt file found
        prompt_file = os.path.join(prompt_folder, prompt_files[0])
        with open(prompt_file, 'r') as f:
            prompt = f.read().strip()
    else:
        prompt = custom_prompt

    try:
        results = scrape_urls(urls, prompt, api_key, model)
    except Exception as e:
        logger.error(f"Error during scraping: {e}", exc_info=True)
        raise

    return results
