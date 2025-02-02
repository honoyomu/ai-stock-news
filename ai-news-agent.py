import streamlit as st
import requests
import uuid
import json
from supabase import create_client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure the page
st.set_page_config(page_title="AI News Agent Chat", page_icon="🤖", layout="wide")

# Constants - Get from environment variables
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def send_message_to_webhook(session_id, user_message, auth_token):
    """Send the user message to the n8n webhook and return the response"""
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "sessionId": session_id,
        "chatInput": user_message
    }
    
    try:
        response = requests.post(WEBHOOK_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["output"]
    except Exception as e:
        st.error(f"Error communicating with the webhook: {str(e)}")
        return None

def initialize_session_state():
    """Initialize session state variables if they don't exist"""
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "auth_token" not in st.session_state:
        st.session_state.auth_token = None
    
    # Add custom CSS
    st.markdown("""
        <style>
        .stButton button {
            background-color: #FF4B4B;
            color: white;
            border-radius: 5px;
            border: none;
            padding: 0.5rem 1rem;
        }
        .stButton button:hover {
            background-color: #FF6B6B;
        }
        .stTextInput input {
            border-radius: 5px;
        }
        .stMarkdown {
            max-width: 100%;
            overflow-wrap: break-word;
        }
        </style>
    """, unsafe_allow_html=True)

def login(email, password):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        st.session_state.authenticated = True
        st.session_state.user = response.user
        st.session_state.auth_token = response.session.access_token
        return True
    except Exception as e:
        st.error(f"Login failed: {str(e)}")
        return False

def signup(email, password):
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        st.success("Signup successful! Please check your email for verification.")
        return True
    except Exception as e:
        st.error(f"Signup failed: {str(e)}")
        return False

def auth_page():
    # Center the auth form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("Welcome to AI News Agent 🤖")
        st.divider()
        
        tab1, tab2 = st.tabs(["🔑 Login", "✨ Sign Up"])
        
        with tab1:
            with st.form("login_form"):
                st.subheader("Login")
                login_email = st.text_input("Email", key="login_email")
                login_password = st.text_input("Password", type="password", key="login_password")
                submit_login = st.form_submit_button("Login", use_container_width=True)
                if submit_login:
                    if login(login_email, login_password):
                        st.rerun()

        with tab2:
            with st.form("signup_form"):
                st.subheader("Create Account")
                signup_email = st.text_input("Email", key="signup_email")
                signup_password = st.text_input("Password", type="password", key="signup_password")
                submit_signup = st.form_submit_button("Sign Up", use_container_width=True)
                if submit_signup:
                    signup(signup_email, signup_password)

def chat_interface():
    # Remove the columns and use a cleaner layout
    st.title("AI News Agent Chat 🤖")
    
    # Create a cleaner sidebar
    with st.sidebar:
        st.subheader("👤 User Profile")
        st.caption(f"📧 {st.session_state.user.email}")
        st.divider()
        
        # Add a collapsible section for session info
        with st.expander("Session Information"):
            st.caption(f"🔑 Session ID: {st.session_state.session_id}")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    # Add minimal CSS just for chat input positioning
    st.markdown("""
        <style>
        .stChatInputContainer {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background-color: white;
            padding: 1rem 5rem;
            z-index: 100;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Add some space before the fixed chat input
    st.markdown("<div style='margin-bottom: 80px'></div>", unsafe_allow_html=True)
    
    # Chat input
    if prompt := st.chat_input("What would you like to know?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = send_message_to_webhook(
                    st.session_state.session_id,
                    prompt,
                    st.session_state.auth_token
                )
                if response:
                    st.write(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})

def main():
    initialize_session_state()
    
    if not st.session_state.authenticated:
        auth_page()
    else:
        chat_interface()

if __name__ == "__main__":
    main()
