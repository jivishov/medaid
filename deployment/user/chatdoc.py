import streamlit as st
import requests
from datetime import datetime

# API endpoint
API_ENDPOINT = "http://localhost:5000"

# Function to handle login
def login(username, password):
    response = requests.post(f"{API_ENDPOINT}/login", json={"username": username, "password": password})
    if response.status_code == 200:
        return response.json()['access_token']
    return None

# Function to fetch conversations
def get_conversations(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_ENDPOINT}/conversations", headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

# Function to fetch messages for a conversation
def get_messages(token, conversation_id):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_ENDPOINT}/messages/{conversation_id}", headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

# Function to send a message
def send_message(token, conversation_id, content):
    headers = {"Authorization": f"Bearer {token}"}
    data = {"conversation_id": conversation_id, "content": content}
    response = requests.post(f"{API_ENDPOINT}/messages", headers=headers, json=data)
    return response.status_code == 201

# Function to mark messages as read
def mark_messages_as_read(token, conversation_id):
    headers = {"Authorization": f"Bearer {token}"}
    data = {"conversation_id": conversation_id}
    response = requests.post(f"{API_ENDPOINT}/messages/read", headers=headers, json=data)
    return response.status_code == 200

# Streamlit app
def main():
    st.set_page_config(page_title="Patient-Physician Messaging", layout="wide")
    st.title("Patient-Physician Messaging")

    # Check if user is logged in
    if 'access_token' not in st.session_state:
        st.session_state.access_token = None

    # Login form
    if not st.session_state.access_token:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            token = login(username, password)
            if token:
                st.session_state.access_token = token
                st.experimental_rerun()
            else:
                st.error("Invalid credentials")
    else:
        # Messaging interface
        conversations = get_conversations(st.session_state.access_token)
        
        # Sidebar for conversation selection
        st.sidebar.title("Conversations")
        selected_conversation = st.sidebar.selectbox(
            "Select a conversation", 
            options=[f"{conv['id']} - {'Dr. ' if conv['physician_name'] else ''}{conv['physician_name'] or conv['patient_name']}" for conv in conversations],
            format_func=lambda x: x.split(' - ')[1]
        )
        
        if selected_conversation:
            conversation_id = int(selected_conversation.split(' - ')[0])
            
            # Main messaging area
            st.subheader(f"Conversation with {selected_conversation.split(' - ')[1]}")
            
            # Display messages
            messages = get_messages(st.session_state.access_token, conversation_id)
            for msg in messages:
                with st.chat_message(msg['sender_role']):
                    st.write(f"{msg['sender_name']}: {msg['content']}")
                    st.caption(f"Sent at {msg['created_at']} {'(Unread)' if not msg['is_read'] else ''}")
            
            # Mark messages as read
            mark_messages_as_read(st.session_state.access_token, conversation_id)
            
            # Message input
            user_input = st.text_area("Type your message here...")
            if st.button("Send"):
                if send_message(st.session_state.access_token, conversation_id, user_input):
                    st.success("Message sent successfully!")
                    st.experimental_rerun()
                else:
                    st.error("Failed to send message. Please try again.")

        # Logout button
        if st.sidebar.button("Logout"):
            st.session_state.access_token = None
            st.experimental_rerun()

if __name__ == "__main__":
    main()