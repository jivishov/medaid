import streamlit as st
import psycopg2
from PIL import Image
import base64

# Database connection parameters
DB_PARAMS = {
    'dbname': 'your_database_name',
    'user': 'your_username',
    'password': 'your_password',
    'host': 'your_host',
    'port': 'your_port'
}

def get_profile_image(profile_picture_path):
    if profile_picture_path:
        try:
            return Image.open(profile_picture_path)
        except FileNotFoundError:
            return None
    return None

def load_css():
    with open("style.css") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def display_profile(profile):
    col1, col2 = st.columns([1, 2])
    
    with col1:
        image = get_profile_image(profile[3])
        if image:
            st.image(image, width=300)
        else:
            st.image("placeholder.png", width=300)
        
        st.markdown(f"<h1 class='doctor-name'>{profile[1]}</h1>", unsafe_allow_html=True)
        st.markdown(f"<h2 class='doctor-specialty'>{profile[2]}</h2>", unsafe_allow_html=True)
        
        with st.expander("Contact Information"):
            st.markdown(f"**Phone:** {profile[7]}")
            st.markdown(f"**WhatsApp:** {profile[8]}")
            st.markdown(f"**Workplace:** {profile[4]}")
            st.markdown(f"**Address:** {profile[5]}")
            if profile[6]:
                st.markdown(f"[Website]({profile[6]})")
    
    with col2:
        st.markdown("## About")
        st.markdown("### Education")
        for edu in profile[9].split('\n'):
            st.markdown(f"- {edu}")
        
        st.markdown("### Work History")
        for work in profile[10].split('\n'):
            st.markdown(f"- {work}")
        
        st.markdown("### Certifications")
        for cert in profile[12].split('\n'):
            st.markdown(f"- {cert}")
        
        st.markdown("### Procedures")
        st.markdown(profile[11])

def main():
    st.set_page_config(page_title="Physician Directory", layout="wide")
    load_css()
    
    st.markdown("<h1 class='main-title'>Physician Directory</h1>", unsafe_allow_html=True)
    
    # Connect to the database
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    
    # Fetch all physicians
    cur.execute("SELECT id, full_name, specialty FROM doc_table ORDER BY full_name")
    physicians = cur.fetchall()
    
    # Create a search box
    search_term = st.text_input("Search physicians by name or specialty")
    
    # Filter physicians based on search term
    filtered_physicians = [
        doc for doc in physicians 
        if search_term.lower() in doc[1].lower() or search_term.lower() in doc[2].lower()
    ]
    
    # Display physicians in a grid
    cols = st.columns(3)
    for idx, doc in enumerate(filtered_physicians):
        with cols[idx % 3]:
            st.markdown(f"<div class='doctor-card'>", unsafe_allow_html=True)
            st.markdown(f"<h3>{doc[1]}</h3>", unsafe_allow_html=True)
            st.markdown(f"<p>{doc[2]}</p>", unsafe_allow_html=True)
            if st.button(f"View Profile", key=doc[0]):
                cur.execute("SELECT * FROM doc_table WHERE id = %s", (doc[0],))
                profile = cur.fetchone()
                display_profile(profile)
            st.markdown("</div>", unsafe_allow_html=True)
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()