import json
import time
import yaml
import httpx
from selectolax.parser import HTMLParser
from bs4 import BeautifulSoup

def scrape_article_with_requests(url, retries=3):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    for attempt in range(retries):
        response = httpx.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            article = soup.find('article')
            if article:
                return article.get_text()
            else:
                return "Article content not found."
        elif response.status_code == 403:
            print(f"Attempt {attempt + 1}: Access forbidden (403) for {url}. Retrying...")
            time.sleep(2)
    return "Failed to retrieve article after 3 attempts."

def scrape_article_with_selectolax(url, retries=3):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    for attempt in range(retries):
        response = httpx.get(url, headers=headers)
        if response.status_code == 200:
            tree = HTMLParser(response.text)
            article = tree.css_first('article')
            if article:
                return article.text()
            else:
                return "Article content not found."
        elif response.status_code == 403:
            print(f"Attempt {attempt + 1}: Access forbidden (403) for {url}. Retrying...")
            time.sleep(2)
    return "Failed to retrieve article after 3 attempts."

def scrape_article(url, use_selectolax=False):
    result = scrape_article_with_requests(url)
    if (result.startswith("Failed") or result == "Article content not found.") and use_selectolax:
        print("Switching to Selectolax for scraping...")
        return scrape_article_with_selectolax(url)
    return result

def load_config(file_name):
    with open(file_name, 'r') as ymlfile:
        cfg = yaml.safe_load(ymlfile)
    return cfg

def read_json(file_path):
    with open(file_path, 'r') as json_file:
        return json.load(json_file)

def write_json(file_path, data):
    with open(file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def count_words_and_characters(text):
    word_count = len(text.split())
    char_count = len(text)
    return word_count, char_count

def count_tokens(text):
    """Returns the number of tokens (words) in the text."""
    return len(text.split())

def clean_text(text):
    """Cleans the text by removing empty strings and unnecessary lines."""
    # Split the text into lines
    lines = text.splitlines()
    # Filter out empty lines and strip leading/trailing whitespace
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    # Join cleaned lines back into a single string with a single newline between them
    return "\n".join(cleaned_lines)

def run_scrape():
    config = load_config('config.yml')
    input_json_path = config['file_paths']['link_result_file']
    output_json_path = config['file_paths']['scrapped_result_file']

    # Use .get() method with a default value
    use_selectolax = config.get('use_selectolax', False)

    original_data = read_json(input_json_path)
    enhanced_data = {}

    for title, items in original_data.items():
        enhanced_items = []
        for item in items:
            if 'link' in item:
                print(f"Scraping content for: {item['link']}")
                scraped_text = scrape_article(item['link'], use_selectolax)
                cleaned_text = clean_text(scraped_text)

                # Count tokens after cleaning the text
                token_count = count_tokens(cleaned_text)

                if token_count < 300:
                    print(f"Skipping article {item['link']} due to insufficient token count ({token_count} tokens).")
                    continue  # Skip articles with fewer than 300 tokens

                item['text'] = cleaned_text
                word_count, char_count = count_words_and_characters(cleaned_text)
                item['word_count'] = word_count
                item['char_count'] = char_count
            enhanced_items.append(item)
        enhanced_data[title] = enhanced_items

    write_json(output_json_path, enhanced_data)

if __name__ == "__main__":
    run_scrape()
