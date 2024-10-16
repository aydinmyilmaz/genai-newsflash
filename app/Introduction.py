import streamlit as st
import yaml
from modules.helpers import update_config

# Set the page title and icon
st.set_page_config(page_title="GenAI Newsflash", page_icon="📰")

# Main heading
st.title("Welcome to GenAI Newsflash 📰")

# Introduction text
st.markdown("""
### Your AI-Powered News Summarizer 🧠

**GenAI Newsflash** is a revolutionary tool tailored to keep you informed about the latest developments in your chosen fields of interest. Utilizing the power of Generative AI, it transforms the way you access news on technology, business, science, and more, by delivering precise, AI-generated summaries of the latest articles and data.

---

### How It Works:

1. **Input Your Link**: 📝 Simply enter the URL of the news article you wish to summarize.
2. **Advanced Summarization**: 🧠 Employing sophisticated OpenAI models, **GenAI Newsflash** processes and analyzes your content, then crafts a succinct, informative summary.
3. **Interactive Results**: 📊 Easily review and interact with your summaries within the app, and if needed, download them in DOCX format for convenience.

---

### Why Use GenAI Newsflash?

- **Save Time**: ⏳ Avoid the tedium of scrolling through endless news articles. Let our AI efficiently gather and distill key information, freeing up your time for other pursuits.
- **Stay Informed**: 📚 Receive clear and comprehensive summaries that keep you abreast of significant updates and trends.
- **Cutting-Edge Technology**: 🤖 Benefit from the latest advancements in natural language processing to obtain summaries that are not only quick but also strikingly human-like.

---


### Get Started 🚀

Simply input your links and let **GenAI Newsflash** do the rest!
""")

# Checkbox for playing music
st.sidebar.audio("Good_for_All.mp3", format="audio/mp3")

# Checkbox for showing lyrics
if st.sidebar.checkbox("Show Lyrics"):
    st.sidebar.markdown("""
    **Lyrics**

    *(Verse 1)*\n\n
    Every aisle, a promise kept, trust in every step,\n
    Efficiency and warmth in every corner we prep.\n
    Streamlined paths, our vision’s clear,\n
    Gutes für Alle, friendly smiles here to cheer.\n\n

    *(Chorus)*\n\n
    Good for All, that’s our creed,\n
    Trust and friendliness in every deed.\n
    Consistent quality, unbeatable price,\n
    Aldi Süd’s promise, precise and nice.\n\n

    *(Verse 2)*\n
    Choices made with care, for you, for all,\n
    Sustainable and trustworthy, we answer the call.\n
    Quick decisions, efficient lines,\n
    Clarity and warmth in our signs.\n\n

    *(Chorus)*\n
    Good for All, that’s our creed,\n
    Trust and friendliness in every deed.\n
    Consistent quality, unbeatable price,\n
    Aldi Süd’s promise, precise and nice.\n\n

    *(Bridge)*\n
    Honest deals, open doors,\n
    Fair to all, on all our floors.\n
    Duty to planet and every guest,\n
    In responsibility, we invest.\n\n

    *(Verse 3)*\n
    A welcoming space where values meet grace,\n
    In every product, a friendly face.\n
    Commitment deep, in every way,\n
    For every customer, every day.\n\n

    *(Chorus)*\n
    Good for All, that’s our creed,\n
    Trust and friendliness in every deed.\n
    Consistent quality, unbeatable price,\n
    Aldi Süd’s promise, precise and nice.\n\n

    *(Outro)*\n
    Come join us, feel the community call,\n
    At Aldi Süd, it’s Good for All.\n
    Embrace our mission, join the stride,\n
    Together, with trust and pride.\n\n
    """)


# Call the update_config function
update_config()
