# user_auth.py
"""
User authentication module for Smart Newsflash application.
Place this file in the modules directory: modules/user_auth.py
"""
import streamlit as st
import yaml
import re
import logging
from typing import Tuple, Optional
from modules.mongodb_manager.mongodb_query_manager import MongoDBQueryManager

logger = logging.getLogger(__name__)

class UserAuth:
    def __init__(self, config_path: str = "./config.yml"):
        """Initialize UserAuth with configuration."""
        self.load_config(config_path)
        self.db_manager = MongoDBQueryManager()

    def load_config(self, config_path: str) -> None:
        """Load configuration from YAML file."""
        try:
            with open(config_path, "r") as file:
                self.config = yaml.safe_load(file)
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validate email format."""
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        return bool(re.match(email_regex, email))

    def initialize_session_state(self) -> None:
        """Initialize session state variables."""
        if 'user_email' not in st.session_state:
            st.session_state.user_email = None

    def verify_auth(self, email: str, auth_key: str) -> bool:
        """Verify authentication key."""
        return auth_key == self.config['USER_AUTH_KEY']

    def handle_signup(self, email: str, auth_key: str) -> Tuple[bool, str]:
        """Handle user signup process."""
        try:
            if not self.is_valid_email(email):
                return False, "Invalid email format"

            user_exists = self.db_manager.user_collection.find_one({"email": email})
            if user_exists:
                return False, "User already exists"

            if not self.verify_auth(email, auth_key):
                return False, "Invalid authentication key"

            # Create new user
            self.db_manager.user_collection.insert_one({
                "email": email,
                "articles": {}
            })
            st.session_state.user_email = email
            return True, "Signup successful"

        except Exception as e:
            logger.error(f"Signup error: {str(e)}", exc_info=True)
            return False, f"Signup error: {str(e)}"

    def handle_login(self, email: str, auth_key: str) -> Tuple[bool, str]:
        """Handle user login process."""
        try:
            if not self.is_valid_email(email):
                return False, "Invalid email format"

            user_exists = self.db_manager.user_collection.find_one({"email": email})
            if not user_exists:
                return False, "User does not exist"

            if not self.verify_auth(email, auth_key):
                return False, "Invalid authentication key"

            st.session_state.user_email = email
            return True, "Login successful"

        except Exception as e:
            logger.error(f"Login error: {str(e)}", exc_info=True)
            return False, f"Login error: {str(e)}"

    def get_current_user(self) -> Optional[str]:
        """Get current user's email from session state."""
        return st.session_state.get('user_email')

    def logout(self) -> None:
        """Log out current user."""
        st.session_state.user_email = None

    def render_auth_ui(self, location="sidebar") -> None:
        """Render authentication UI in specified location."""
        self.initialize_session_state()

        # Determine where to place the auth UI
        container = st.sidebar if location == "sidebar" else st

        with container.expander("User Authentication", expanded=True):
            user_email = st.text_input(
                "Email Address:",
                value=st.session_state.user_email if st.session_state.user_email else "",
                placeholder="example@gmail.com"
            )
            auth_key = st.text_input("Authentication Key:", type="password")

            # Create columns for buttons
            col1, col2, col3 = st.columns([1, 1, 1])

            with col1:
                if st.button("Sign Up"):
                    success, message = self.handle_signup(user_email, auth_key)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)

            with col2:
                if st.button("Log In"):
                    success, message = self.handle_login(user_email, auth_key)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)

            with col3:
                if st.button("Log Out"):
                    self.logout()
                    st.success("Logged out successfully")
                    st.rerun()

            # Display current user
            if self.get_current_user():
                st.info(f"Current user: {self.get_current_user()}")