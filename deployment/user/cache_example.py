import streamlit as st
import random
import string
from io import BytesIO
from PIL import Image

def main():
    st.set_page_config(page_title="Multi-Tab Streamlit App", layout="wide")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Tab 1", "Tab 2", "Tab 3", "Tab 4"])
    
    with tab1:
        st.header("Image Upload")
        uploaded_file = st.file_uploader("Choose a JPEG file", type="jpg")
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.session_state.image = image
            st.image(image, caption="Uploaded Image", use_column_width=True)

    with tab2:
        st.header("Image and Text Processing")
        
        if 'image' in st.session_state:
            if st.button("Process Image"):
                st.session_state.processed_text = process_image(st.session_state.image)
            
            if 'processed_text' in st.session_state:
                st.subheader("Processed Text")
                text_area_content = st.text_area("Edit text if needed:", value=st.session_state.processed_text, height=150)
                
                process_button = st.button("Process")
                if process_button:
                    st.session_state.further_processed_text = process_text(text_area_content)
                
                if 'further_processed_text' in st.session_state:
                    st.subheader("Further Processed Text")
                    further_text_area_content = st.text_area("Edit further processed text if needed:", value=st.session_state.further_processed_text, height=150, key="further_text_area")
                    
                    next_process_button = st.button("Next Process")
                    if next_process_button:
                        final_text = final_process(further_text_area_content)
                        st.subheader("Final Processed Text")
                        st.write(final_text)
        else:
            st.warning("Please upload an image in Tab 1 first.")

    with tab3:
        st.header("Tab 3")
        st.write("This is Tab 3. Content to be added.")

    with tab4:
        st.header("Tab 4")
        st.write("This is Tab 4. Content to be added.")

@st.cache_data
def process_image(_image):
    # Simulating LLM processing with Lorem Ipsum
    st.success("Image processed successfully!")  # This will be replayed on subsequent runs
    lorem_ipsum = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur."
    return lorem_ipsum[:200]

@st.cache_data
def process_text(text):
    # Simulating text processing
    st.info("Text processing completed")  # This will be replayed on subsequent runs
    return f"Processed: {text[:100]}..."

@st.cache_data
def final_process(text):
    # Appending random string
    st.success("Final processing done!")  # This will be replayed on subsequent runs
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
    return f"{text}\n\nAppended random string: {random_string}"

if __name__ == "__main__":
    main()