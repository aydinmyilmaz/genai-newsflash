# youtube_data_handler.py

import re
import logging
import feedparser
from typing import List, Dict, Optional
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import tiktoken
import requests
from bs4 import BeautifulSoup
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_youtube_link(link):
    # Regex pattern to match standard YouTube video links, channel links, user links, and new handle format
    pattern = r'^(https?://)?(www\.)?(youtube\.com/(watch\?v=|channel/|user/|@)|youtu\.be/)[\w-]{11}$|^https?://www\.youtube\.com/@[\w-]+$'

    # Check for channel links specifically
    channel_pattern = r'^(https?://)?(www\.)?youtube\.com/channel/[\w-]+$'

    return re.match(pattern, link) is not None or re.match(channel_pattern, link) is not None

def extract_video_ids_from_channel(channel_url: str, max_results: int = 5) -> List[str]:
    """
    Extracts the latest video IDs from a YouTube channel using the RSS feed.
    """
    channel_id_match = re.search(r'channel/([0-9A-Za-z_-]+)', channel_url)
    if not channel_id_match:
        logger.error("Invalid channel URL format")
        return []

    channel_id = channel_id_match.group(1)
    rss_url = f'https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}'
    feed = feedparser.parse(rss_url)
    video_ids = []

    for entry in feed.entries[:max_results]:
        video_url = entry.link
        video_id_match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', video_url)
        if video_id_match:
            video_id = video_id_match.group(1)
            video_ids.append(video_id)

    return video_ids

def extract_video_ids(link: str, max_results: int = 5) -> List[str]:
    """
    Extracts the video IDs from a YouTube link.
    If the link is a channel URL, extract the latest video IDs.
    """
    if "channel/" in link:
        return extract_video_ids_from_channel(link, max_results)

    # If it's a single video link, extract the video ID
    youtube_regex = re.compile(
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    )
    match = re.search(youtube_regex, link)
    if match:
        return [match.group(1)]
    else:
        return []


def get_channel_id(channel_url):
    try:
        response = requests.get(channel_url)
        if response.status_code == 200:
            content = response.text

            # Pattern 1: Look for "channelId"
            channel_id_match = re.search(r'"channelId":"(UC[\w-]+)"', content)
            if channel_id_match:
                return channel_id_match.group(1)

            # Pattern 2: Look for "externalId"
            external_id_match = re.search(r'"externalId":"(UC[\w-]+)"', content)
            if external_id_match:
                return external_id_match.group(1)

            # Pattern 3: Look for "channelIds" in array
            channel_ids_match = re.search(r'"channelIds":\s*\[\s*"(UC[\w-]+)"\s*\]', content)
            if channel_ids_match:
                return channel_ids_match.group(1)

            # Pattern 4: Try to find and parse JSON-like structures
            json_like_matches = re.findall(r'\{[^{}]+\}', content)
            for match in json_like_matches:
                try:
                    data = json.loads(match)
                    if 'channelId' in data:
                        return data['channelId']
                    if 'externalId' in data:
                        return data['externalId']
                    if 'channelIds' in data and isinstance(data['channelIds'], list) and data['channelIds']:
                        return data['channelIds'][0]
                except json.JSONDecodeError:
                    continue

            return "Channel ID not found"
        else:
            return f"Failed to retrieve the page. Status code: {response.status_code}"
    except Exception as e:
        return f"An error occurred: {str(e)}"

def get_video_transcript(video_id: str) -> Optional[Dict[str, any]]:
    """
    Retrieves and processes the transcript for a given YouTube video ID.
    Returns a dictionary with the transcript and token count.
    """
    try:
        logger.info(f"Attempting to fetch transcript for video ID: {video_id}")
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        processed_transcript = process_transcript(transcript_list)
        token_count = count_tokens(processed_transcript)
        logger.info(f"Successfully retrieved transcript for video ID: {video_id}")
        return {
            'transcript': processed_transcript,
            'token_count': token_count
        }
    except TranscriptsDisabled:
        logger.warning(f"Transcripts are disabled for video ID: {video_id}")
    except NoTranscriptFound:
        logger.warning(f"No transcript found for video ID: {video_id}")
    except Exception as e:
        logger.error(f"An error occurred while fetching transcript for video ID: {video_id}. Error: {str(e)}")
    return None

def process_transcript(transcript: List[Dict[str, str]]) -> str:
    """
    Processes the transcript to create more readable sentences.
    """
    processed_text = ""
    current_sentence = ""

    for item in transcript:
        text = item['text'].strip().replace('\n', ' ')
        if text.endswith(('.', '!', '?')):
            current_sentence += text + " "
            processed_text += current_sentence.capitalize()
            current_sentence = ""
        else:
            current_sentence += text + " "

    if current_sentence:
        processed_text += current_sentence.capitalize()

    return processed_text.strip()

def count_tokens(text: str) -> int:
    """
    Counts the number of tokens in the given text using tiktoken.
    """
    encoding = tiktoken.get_encoding('cl100k_base')  # Adjust the encoding if needed
    tokens = encoding.encode(text)
    return len(tokens)

def save_links(links: List[str], file_path: str) -> None:
    """
    Saves the list of YouTube links to a text file.
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        for link in links:
            f.write(f"{link}\n")

def load_links(file_path: str) -> List[str]:
    """
    Loads the list of YouTube links from a text file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            links = [line.strip() for line in f if line.strip()]
        return links
    except FileNotFoundError:
        return []
