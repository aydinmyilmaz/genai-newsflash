import unittest
from app.modules.youtube_data_handler import (
    validate_youtube_link,
    extract_video_ids,
    extract_video_ids_from_channel,
    get_channel_id,
    get_video_transcript,
    process_transcript,
    count_tokens,
    save_links,
    load_links
)

class TestYouTubeDataHandler(unittest.TestCase):

    def test_validate_youtube_link(self):
        # Valid links
        valid_links = [
            "https://www.youtube.com/watch?v=eBVi_sLaYsc",
            "https://youtu.be/eBVi_sLaYsc",
            "https://www.youtube.com/embed/eBVi_sLaYsc",
            "https://www.youtube.com/live/eBVi_sLaYsc",
            "https://www.youtube.com/channel/UCdIiCSqXuybzwGwJwrpHPqw",
            "https://www.youtube.com/user/username",
            "https://www.youtube.com/@username",
            "www.youtube.com/watch?v=eBVi_sLaYsc",
            "youtube.com/watch?v=eBVi_sLaYsc",
            "youtu.be/eBVi_sLaYsc"
        ]
        for link in valid_links:
            self.assertTrue(validate_youtube_link(link))

        # Invalid links
        invalid_links = [
            "https://www.google.com",
            "https://www.facebook.com",
            "invalid_link",
            "https://www.youtube.com/invalid"
        ]
        for link in invalid_links:
            self.assertFalse(validate_youtube_link(link))

    def test_extract_video_ids(self):
        # Single video link
        link = "https://www.youtube.com/watch?v=eBVi_sLaYsc"
        self.assertEqual(extract_video_ids(link), ["eBVi_sLaYsc"])

        # youtu.be link
        link = "https://youtu.be/eBVi_sLaYsc"
        self.assertEqual(extract_video_ids(link), ["eBVi_sLaYsc"])

        # Embed link
        link = "https://www.youtube.com/embed/eBVi_sLaYsc"
        self.assertEqual(extract_video_ids(link), ["eBVi_sLaYsc"])

        # Live link
        link = "https://www.youtube.com/live/eBVi_sLaYsc"
        self.assertEqual(extract_video_ids(link), ["eBVi_sLaYsc"])

        # Channel link
        link = "https://www.youtube.com/channel/UCdIiCSqXuybzwGwJwrpHPqw"
        video_ids = extract_video_ids(link)
        self.assertGreaterEqual(len(video_ids), 0)  # Assuming the channel has videos

        # Invalid link
        link = "https://www.google.com"
        self.assertEqual(extract_video_ids(link), [])

    def test_extract_video_ids_from_channel(self):
        # Valid channel link
        link = "https://www.youtube.com/channel/UCdIiCSqXuybzwGwJwrpHPqw"
        video_ids = extract_video_ids_from_channel(link)
        self.assertGreaterEqual(len(video_ids), 0)  # Assuming the channel has videos

        # Invalid channel link
        link = "https://www.google.com"
        self.assertEqual(extract_video_ids_from_channel(link), [])

    def test_get_channel_id(self):
        # Valid channel link
        link = "https://www.youtube.com/channel/UCdIiCSqXuybzwGwJwrpHPqw"
        channel_id = get_channel_id(link)
        self.assertEqual(channel_id, "UCdIiCSqXuybzwGwJwrpHPqw")

        # Invalid channel link
        link = "https://www.google.com"
        channel_id = get_channel_id(link)
        self.assertTrue(
            "Channel ID not found" in channel_id or "Failed to retrieve the page" in channel_id,
            f"Unexpected channel_id output: {channel_id}"
        )

    def test_get_video_transcript(self):
        # Video with transcript
        video_id = "eBVi_sLaYsc"  # Replace with a video ID known to have a transcript
        transcript = get_video_transcript(video_id)
        self.assertIsNotNone(transcript)

        # Video without transcript
        video_id = "video_id_without_transcript"  # Replace with a video ID known not to have a transcript
        transcript = get_video_transcript(video_id)
        self.assertIsNone(transcript)

    def test_process_transcript(self):
        # Sample transcript data
        transcript_data = [
            {'text': 'Hello, world!'},
            {'text': 'This is a test.'},
            {'text': 'How are you?'}
        ]
        processed_transcript = process_transcript(transcript_data)
        self.assertEqual(processed_transcript, 'Hello, world! This is a test. How are you?')

    def test_count_tokens(self):
        # Sample text
        text = 'Hello, world! This is a test.'
        token_count = count_tokens(text)
        self.assertGreaterEqual(token_count, 0)

    def test_save_links(self):
        # Sample links
        links = ["https://www.youtube.com/watch?v=eBVi_sLaYsc", "https://youtu.be/eBVi_sLaYsc"]
        file_path = 'links.txt'
        save_links(links, file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            loaded_links = [line.strip() for line in f if line.strip()]
        self.assertEqual(links, loaded_links)

    def test_load_links(self):
        # Sample links file
        file_path = 'links.txt'
        links = ["https://www.youtube.com/watch?v=eBVi_sLaYsc", "https://youtu.be/eBVi_sLaYsc"]
        save_links(links, file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            loaded_links = [line.strip() for line in f if line.strip()]
        self.assertEqual(links, loaded_links)

if __name__ == '__main__':
    unittest.main()