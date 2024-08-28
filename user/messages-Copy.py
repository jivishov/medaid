import streamlit as st
import psycopg2
from datetime import datetime

# Database connection function
def connect_to_db():
    return psycopg2.connect(
        dbname="your_database_name",
        user="your_username",
        password="your_password",
        host="your_host",
        port="your_port"
    )

# Function to fetch sent messages
def fetch_sent_messages(patient_id):
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT m.id, d.name AS doctor_name, m.subject, m.content, m.timestamp
        FROM messages m
        JOIN doctors d ON m.doctor_id = d.id
        WHERE m.patient_id = %s AND m.is_from_patient = TRUE
        ORDER BY m.timestamp DESC
    """, (patient_id,))
    messages = cur.fetchall()
    cur.close()
    conn.close()
    return messages

# Function to fetch received messages
def fetch_received_messages(patient_id):
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT m.id, d.name AS doctor_name, m.subject, m.content, m.timestamp
        FROM messages m
        JOIN doctors d ON m.doctor_id = d.id
        WHERE m.patient_id = %s AND m.is_from_patient = FALSE
        ORDER BY m.timestamp DESC
    """, (patient_id,))
    messages = cur.fetchall()
    cur.close()
    conn.close()
    return messages

# Function to send a message
def send_message(patient_id, doctor_id, subject, content):
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO messages (patient_id, doctor_id, subject, content, is_from_patient, timestamp)
        VALUES (%s, %s, %s, %s, TRUE, %s)
    """, (patient_id, doctor_id, subject, content, datetime.now()))
    conn.commit()
    cur.close()
    conn.close()

# Function to get list of doctors
def get_doctors():
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM doctors ORDER BY name")
    doctors = cur.fetchall()
    cur.close()
    conn.close()
    return doctors

# Streamlit app
# def main():
st.set_page_config(page_title="Patient Messaging System", layout="wide")
st.title("Patient Messaging System")

# Sidebar for navigation
# page = st.sidebar.radio("Navigate", ["Inbox", "Outbox", "New Message"])

# Mock patient ID (replace with actual authentication)
patient_id = 1

if page == "Inbox":
    st.header("Inbox")
    messages = fetch_received_messages(patient_id)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Messages")
        for i, msg in enumerate(messages):
            if st.button(f"{msg[1]} - {msg[2]}", key=f"inbox_{i}"):
                st.session_state.selected_inbox_message = msg

    with col2:
        st.subheader("Message Content")
        if "selected_inbox_message" in st.session_state:
            msg = st.session_state.selected_inbox_message
            st.write(f"From: Dr. {msg[1]}")
            st.write(f"Subject: {msg[2]}")
            st.write(f"Received: {msg[4]}")
            st.write("Message:")
            st.write(msg[3])

elif page == "Outbox":
    st.header("Outbox")
    messages = fetch_sent_messages(patient_id)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Sent Messages")
        for i, msg in enumerate(messages):
            if st.button(f"To: {msg[1]} - {msg[2]}", key=f"outbox_{i}"):
                st.session_state.selected_outbox_message = msg

    with col2:
        st.subheader("Message Content")
        if "selected_outbox_message" in st.session_state:
            msg = st.session_state.selected_outbox_message
            st.write(f"To: Dr. {msg[1]}")
            st.write(f"Subject: {msg[2]}")
            st.write(f"Sent: {msg[4]}")
            st.write("Message:")
            st.write(msg[3])

elif page == "New Message":
    st.header("Compose New Message")
    doctors = get_doctors()
    doctor_id = st.selectbox("Select Physician", options=[d[0] for d in doctors], format_func=lambda x: next(d[1] for d in doctors if d[0] == x))
    subject = st.text_input("Subject")
    content = st.text_area("Message")
    
    if st.button("Send"):
        send_message(patient_id, doctor_id, subject, content)
        st.success("Message sent successfully!")

# Display any important notifications or alerts
st.sidebar.markdown("---")
st.sidebar.subheader("Notifications")
# You can add logic here to display important alerts or reminders

# if __name__ == "__main__":
#     main()