import streamlit as st
import yaml
from modules.utils.helpers import update_config
from modules.utils.user_auth import UserAuth
from modules.utils.helpers import auth_check

# Set the page title and icon
st.set_page_config(page_title="Smart Newsflash", page_icon="📰")

# Initialize and render authentication
auth = UserAuth()
auth.render_auth_ui(location="sidebar")


# Main heading
st.title("Welcome to Smart Newsflash 📰")

auth_check()

# Call the update_config function
update_config()
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

