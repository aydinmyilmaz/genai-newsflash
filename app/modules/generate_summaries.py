import json
import yaml
import os
import asyncio
import logging
from datetime import datetime
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
# from langchain.callbacks import get_openai_callback
from langchain_community.callbacks.manager import get_openai_callback

from tiktoken import encoding_for_model

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load the config file
with open('./config.yml', 'r') as config_file:
    config = yaml.safe_load(config_file)
    logger.info("Config loaded successfully.")

# Set the environment variable for the API key
os.environ['OPENAI_API_KEY'] = config['OPENAI_API_KEY']
model_name = config['openai_model_name']
max_tokens_per_request = config['max_tokens_per_request']
max_input_tokens = config['max_input_tokens']
logger.info(f"Environment variable for API key set. Max tokens per request: {max_tokens_per_request}, Max input tokens: {max_input_tokens}")

# Load file paths from the config
prompt_file_path = config['file_paths']['prompt_file']
topic_file_path = config['file_paths']['topic_file']
manual_link_file_path = config['file_paths']['manual_link_file']
link_result_file_path = config['file_paths']['link_result_file']
scrapped_result_file_path = config['file_paths']['scrapped_result_file']

# Initialize the ChatOpenAI model
chat = ChatOpenAI(model_name=model_name, temperature=0, max_tokens=max_tokens_per_request)
logger.info("ChatOpenAI model initialized.")

# Load the prompt from file
with open(prompt_file_path, 'r') as prompt_file:
    prompt = prompt_file.read().strip()
logger.info(f"Prompt loaded from file: {topic_file_path}")

# Load the scrapped results
with open(scrapped_result_file_path, 'r') as json_file:
    data = json.load(json_file)
    logger.info(f"Scrapped data loaded from file: {scrapped_result_file_path}")

# Create a ChatPromptTemplate and chain for summarization
summary_template = ChatPromptTemplate.from_template(
    prompt + "\n\nInput of Multiple Article on this Topic to Summarize in Requested Format:\n{text}\n\n"
)
summary_chain = summary_template | chat | StrOutputParser()

# Initialize tokenizer
enc = encoding_for_model(model_name)

def num_tokens_from_string(string: str) -> int:
    """Returns the number of tokens in a text string."""
    return len(enc.encode(string))

async def process_category(category, items):
    merged_text = ""
    total_tokens = num_tokens_from_string(prompt)
    retries = 2

    logger.info(f"Processing category: {category}")  # Log the category being processed

    for item in items:
        text = item.get('text', '')
        text_tokens = num_tokens_from_string(text)
        logger.info(f"Text tokens for current item in {category}: {text_tokens}")  # Log token count for each item

        # Stop adding text when the total token count reaches the max_input_tokens threshold
        if total_tokens + text_tokens > max_input_tokens:
            logger.info(f"Reached token limit for {category}. Stopping text addition.")
            break

        merged_text += "\n\n" + text
        total_tokens += text_tokens

    logger.info(f"Total tokens for {category} after merging: {total_tokens}")  # Log final token count after merging

    for attempt in range(retries + 1):  # Try up to 3 times
        try:
            with get_openai_callback() as cb:
                summary = await summary_chain.ainvoke({"text": merged_text})
            if summary.strip() == "":
                raise ValueError("Empty response from API")

            success_message = (f"Processed {category} successfully. Input tokens used: {total_tokens}. "
                               f"Tokens generated: {cb.completion_tokens}.")
            logger.info(success_message)
            return category, {
                "summary": summary,
                "input_tokens": total_tokens,
                "output_tokens": cb.completion_tokens,
                "total_tokens": cb.total_tokens,
            }, success_message
        except Exception as e:
            error_message = f"Attempt {attempt + 1} failed for {category}: {str(e)}"
            logger.error(error_message)  # Log any errors
            if attempt == retries:
                return category, {
                    "summary": None,
                    "message": f"Unable to generate summary after {retries + 1} attempts."
                }, error_message

async def process_all_categories():
    results = {}
    for category, items in data.items():
        category_result = await process_category(category, items)
        if category_result[1] is not None:
            results[category_result[0]] = category_result[1]
    return results

async def main():
    logger.info("Starting processing...")
    results = await process_all_categories()

    # Generate filename with timestamp
    timestamp = datetime.now().isoformat().replace(':', '-')
    filename = f"./data/openai_results_{timestamp}.json"

    # Write the results to a new JSON file
    with open(filename, 'w') as output_file:
        json.dump(results, output_file, indent=4)
    logger.info(f"Results have been written to {filename}.")

if __name__ == "__main__":
    asyncio.run(main())
