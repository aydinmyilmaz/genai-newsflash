#youtube_summmary_manager.py
import streamlit as st
import os
import json
from datetime import datetime
import matplotlib.pyplot as plt

from modules.youtube_data_handler import (
    validate_youtube_link,
    extract_video_ids,
    get_video_transcript,
    save_links,
    load_links,
    get_channel_id
)

# Ensure the necessary directories exist
if not os.path.exists('./sources'):
    os.makedirs('./sources')
if not os.path.exists('./data/transcripts'):
    os.makedirs('./data/transcripts')

# Set the path for the links file
LINKS_FILE_PATH = './sources/youtube_links.txt'

def youtube_summary_manager():

    tabs = st.tabs(["Manage Links", "Retrieve Transcripts"])

    with tabs[0]:
        # Load existing links
        existing_links = load_links(LINKS_FILE_PATH)

        # Text area for entering links
        link_input = st.text_area(
            "Paste YouTube links here (one per line):",
            value="\n".join(existing_links),
            key='link_input'
        )

        # Validate links in real-time
        input_links = [link.strip() for link in link_input.split('\n') if link.strip()]
        channel_links = []
        video_links = []
        invalid_links = []

        for link in input_links:
            if validate_youtube_link(link):
                if "channel" in link or "user" in link or "@" in link:
                    # Convert channel/user link or handle link to channel ID
                    channel_id = get_channel_id(link)
                    if channel_id:
                        corrected_link = f"https://www.youtube.com/channel/{channel_id}"
                        channel_links.append(corrected_link)
                    else:
                        invalid_links.append(link)
                elif "watch?v=" in link:
                    video_links.append(link)
                else:
                    invalid_links.append(link)
            else:
                invalid_links.append(link)

        if invalid_links:
            st.error("The following links are invalid YouTube URLs:")
            for link in invalid_links:
                st.write(f"- {link}")

        # Buttons to Save/Update links and Display Saved Links
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Update Links"):
                if invalid_links:
                    st.error("Cannot save. Please fix invalid links.")
                else:
                    save_links(channel_links, LINKS_FILE_PATH)
                    st.success("Links saved successfully.")
        with col2:
            if st.button("📜 Display Links"):
                st.subheader("Saved YouTube Links")
                for link in existing_links:
                    st.write(f"- {link}")

    with tabs[1]:
        # Number of videos to retrieve and Get Transcripts button
        if channel_links:
            col1, col2 = st.columns([1, 2])  # Adjust column widths for better alignment
            with col1:
                num_videos = st.number_input("Select number of videos to retrieve from each channel:", min_value=1, max_value=10, value=2, step=1)
            with col2:
                # Add explanatory text next to the button
                st.markdown("Click the button to retrieve transcripts of videos.")
                if st.button("Get Transcripts"):
                    transcripts_data = {}
                    token_counts = []
                    video_titles = []
                    video_links = []

                    progress_bar = st.progress(0)
                    total_links = len(channel_links)

                    for idx, channel_id in enumerate(channel_links):
                        st.write(f"Processing channel link {idx+1}/{len(channel_links)}: {channel_id}")

                        video_ids = extract_video_ids(channel_id, max_results=num_videos)
                        st.write(f"Video IDs: {video_ids}")
                        for vid_idx, video_id in enumerate(video_ids):
                            progress = (idx * num_videos + vid_idx + 1) / (total_links * num_videos)
                            progress_bar.progress(min(progress, 1.0))

                            video_link = f"https://www.youtube.com/watch?v={video_id}"
                            transcript_data = get_video_transcript(video_id)
                            if transcript_data:
                                # Only add to transcripts_data if token count is greater than 1000
                                if transcript_data['token_count'] > 1000:
                                    transcripts_data[video_id] = {
                                        'transcript': transcript_data['transcript'],
                                        'token_count': transcript_data['token_count'],
                                        'link': video_link
                                    }
                                    token_counts.append(transcript_data['token_count'])
                                    video_titles.append(f"Video {vid_idx+1} (from channel link {idx+1})")
                                    video_links.append(video_link)
                                else:
                                    st.warning(f"Transcript for video {video_id} has a token count of {transcript_data['token_count']}, which is less than 1000 and will not be saved.")
                            else:
                                transcripts_data[video_id] = {
                                    'transcript': None,
                                    'token_count': 0,
                                    'link': video_link
                                }
                                token_counts.append(0)
                                video_titles.append(f"Video {vid_idx+1} (from channel link {idx+1})")
                                video_links.append(video_link)

                    # Store transcripts data in session state to persist between reruns
                    st.session_state.transcripts_data = transcripts_data
                    st.session_state.video_titles = video_titles

                    # Save transcripts data to JSON only if there are valid entries
                    if transcripts_data:
                        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
                        output_file_path = f"./data/transcripts/transcripts_{current_time}.json"
                        with open(output_file_path, 'w', encoding='utf-8') as f:
                            json.dump(transcripts_data, f, ensure_ascii=False, indent=4)

                        st.success(f"Transcript retrieval completed. Results saved to '{output_file_path}'.")
                    else:
                        st.warning("No transcripts with token counts greater than 1000 were found.")

        # Display Transcripts using a Dropdown Selection (fixed expander issue)
        if "transcripts_data" in st.session_state and st.session_state.transcripts_data and st.checkbox("Display Transcript"):
            dropdown_options = [
                f"{st.session_state.video_titles[idx]} - Preview: {data['transcript'][:100] if data['transcript'] else 'Transcript not available'}"
                for idx, data in enumerate(st.session_state.transcripts_data.values())
            ]

            selected_option = st.selectbox("Select a transcript to view:", dropdown_options)
            selected_idx = dropdown_options.index(selected_option)
            selected_video_id = list(st.session_state.transcripts_data.keys())[selected_idx]
            selected_data = st.session_state.transcripts_data[selected_video_id]

            st.subheader(f"{st.session_state.video_titles[selected_idx]} - Token Count: {selected_data['token_count']}")
            st.write(f"Video Link: {selected_data['link']}")
            if selected_data['transcript']:
                st.write(selected_data['transcript'][:1000])
            else:
                st.warning("Transcript not available.")

if __name__ == "__main__":
    youtube_summary_manager()
