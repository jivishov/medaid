import streamlit as st
import psycopg2
import json
from PIL import Image
import os

# Database connection parameters
DB_PARAMS = {
    'dbname': 'your_database_name',
    'user': 'your_username',
    'password': 'your_password',
    'host': 'your_host',
    'port': 'your_port'
}

def save_profile_picture(file):
    if file:
        os.makedirs('profile_pictures', exist_ok=True)
        file_path = os.path.join('profile_pictures', file.name)
        Image.open(file).save(file_path)
        return file_path
    return None

def save_to_database(data):
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    try:
        cur.execute('''
            INSERT INTO doc_table 
            (full_name, specialty, profile_picture_path, current_workplace, 
            workplace_address, workplace_website, cell_phone, whatsapp_number, 
            education_history, work_history, procedures, certifications)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            data['full_name'], data['specialty'], data['profile_picture_path'],
            data['current_workplace'], data['workplace_address'], data['workplace_website'],
            data['cell_phone'], data['whatsapp_number'], 
            '\n'.join(data['education_history']),
            '\n'.join(data['work_history']), 
            data['procedures'], 
            '\n'.join(data['certifications'])
        ))
        conn.commit()
        st.success("Profile saved successfully!")
    except Exception as e:
        conn.rollback()
        st.error(f"An error occurred: {str(e)}")
    finally:
        cur.close()
        conn.close()

def input_page():
    st.title("Physician Profile Input")
    
    col1, col2 = st.columns(2)
    
    with col1:
        full_name = st.text_input("Full Name")
        specialty = st.text_input("Specialty")
        profile_picture = st.file_uploader("Profile Picture", type=['png', 'jpg', 'jpeg'])
        current_workplace = st.text_input("Current Workplace")
        workplace_address = st.text_area("Workplace Address")
        workplace_website = st.text_input("Workplace Website")
    
    with col2:
        cell_phone = st.text_input("Cell Phone Number")
        whatsapp_number = st.text_input("WhatsApp Number")
        procedures = st.text_area("Procedures")
    
    education_history = st.text_area("Education History (One entry per line)")
    work_history = st.text_area("Work History (One entry per line)")
    certifications = st.text_area("Certifications (One entry per line)")
    
    if st.button("Submit Profile"):
        profile_picture_path = save_profile_picture(profile_picture) if profile_picture else None
        
        data = {
            'full_name': full_name,
            'specialty': specialty,
            'profile_picture_path': profile_picture_path,
            'current_workplace': current_workplace,
            'workplace_address': workplace_address,
            'workplace_website': workplace_website,
            'cell_phone': cell_phone,
            'whatsapp_number': whatsapp_number,
            'education_history': education_history.split('\n'),
            'work_history': work_history.split('\n'),
            'procedures': procedures,
            'certifications': certifications.split('\n')
        }
        
        save_to_database(data)

def display_page():
    st.title("Physician Profile Display")
    
    # Fetch profiles from database
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    cur.execute("SELECT id, full_name FROM doc_table")
    profiles = cur.fetchall()
    cur.close()
    conn.close()
    
    selected_profile = st.selectbox("Select a physician", profiles, format_func=lambda x: x[1])
    
    if selected_profile:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        cur.execute("SELECT * FROM doc_table WHERE id = %s", (selected_profile[0],))
        profile = cur.fetchone()
        cur.close()
        conn.close()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if profile[3]:  # profile_picture_path
                st.image(profile[3], width=300)
            st.header(profile[1])  # full_name
            st.subheader(profile[2])  # specialty
            st.write(f"**Current Workplace:** {profile[4]}")
            st.write(f"**Address:** {profile[5]}")
            st.write(f"**Website:** {profile[6]}")
        
        with col2:
            st.write(f"**Phone:** {profile[7]}")
            st.write(f"**WhatsApp:** {profile[8]}")
            st.write("**Procedures:**")
            st.write(profile[11])
        
        st.subheader("Education History")
        for edu in profile[9].split('\n'):  # Assuming education_history is the 10th column
            st.write(f"- {edu}")

        st.subheader("Work History")
        for work in profile[10].split('\n'):  # Assuming work_history is the 11th column
            st.write(f"- {work}")

        st.subheader("Certifications")
        for cert in profile[12].split('\n'):  # Assuming certifications is the 13th column
            st.write(f"- {cert}")

# def main():
input_page()
    # st.sidebar.title("Navigation")
    # page = st.sidebar.radio("Go to", ["Input Profile", "Display Profile"])
    
    # if page == "Input Profile":
    #     input_page()
    # else:
    #     display_page()

# if __name__ == "__main__":
#     main()