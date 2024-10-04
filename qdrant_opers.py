import streamlit as st
from streamlit import secrets as my_secrets
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.models import PointStruct
import cohere
import os, uuid
from openai import OpenAI
import openai
import pandas as pd
from io import StringIO
from anthropic import Anthropic
import asyncio
from anthropic import AsyncAnthropic
from anthropic.types import ContentBlockDeltaEvent
from datetime import datetime
from github import Github, GithubException
# ----------------------------
# Configuration and API Keys
# ----------------------------
st.set_page_config(page_icon=None, layout="wide", initial_sidebar_state="collapsed")
# Function to load API keys from environment variables or Streamlit secrets
def load_api_keys():
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY') or st.secrets.get("OPENAI_API_KEY")
    COHERE_API_KEY =os.getenv('COHERE_API_KEY') #"KWTDJc494M5NKqbMIs1vEYDGP1lKc3JRVEr9Rb7V" #os.getenv('COHERE_API_KEY') or st.secrets.get("COHERE_API_KEY")
    QDRANT_HOST = os.getenv('QDRANT_HOST') or st.secrets.get("QDRANT_HOST", "localhost")
    QDRANT_PORT = 6333# int(os.getenv('QDRANT_PORT') or st.secrets.get("QDRANT_PORT", 6333))
    QDRANT_API_KEY =os.getenv('QDRANT_API_KEY') #"KDSwKtqXOgNPTHhLC7OcWtc3XiebzEeIJgFt2kQxCSDm_kX4vRooiA" #st.secrets["local_qdrant_secrets"]["QDRANT_API_KEY"]
    return OPENAI_API_KEY, COHERE_API_KEY, QDRANT_HOST, QDRANT_PORT, QDRANT_API_KEY


OPENAI_API_KEY, COHERE_API_KEY, QDRANT_HOST, QDRANT_PORT, QDRANT_API_KEY= load_api_keys()

# Validate API keys
if not OPENAI_API_KEY:
    st.error("OpenAI API key not found. Please set it in environment variables or Streamlit secrets.")
if not COHERE_API_KEY:
    st.error("Cohere API key not found. Please set it in environment variables or Streamlit secrets.")

# Initialize clients if API keys are available
if OPENAI_API_KEY and COHERE_API_KEY:
    openai.api_key = OPENAI_API_KEY
    co = cohere.Client(COHERE_API_KEY)
    try:
        qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    except Exception as e:
        st.error(f"Failed to connect to Qdrant: {e}")


def save_to_github(user_input, search_query, llm_output, github_token):
    try:
        # Create a Github instance using the provided token
        g = Github(github_token)

        # Get the repository
        repo = g.get_repo("jivishov/medaid")

        # Create a unique filename based on timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"logs/interaction_{timestamp}.txt"

        # Prepare the content
        content = f"User Input:\n{user_input}\n\n"
        content += f"LLM Generated Search Query:\n{search_query}\n\n"
        content += f"LLM Generated Output:\n{llm_output}\n"

        # Create the file in the repository
        repo.create_file(
            path=filename,
            message=f"Add interaction log: {filename}",
            content=content
        )

        return f"Interaction saved to {filename} and pushed to GitHub repo."
    except Exception as e:
        return f"Error saving to GitHub: {str(e)}"

# ----------------------------
# Utility Functions
# ----------------------------

def create_collection(qdr_collection, embedding_size, qdr_distance=models.Distance.COSINE):
    """
    Create a collection in Qdrant.
    """
    qdrant_client =QdrantClient(QDRANT_HOST, api_key=QDRANT_API_KEY)
    try:
        if qdr_collection in qdrant_client.get_collections().collections:
            st.warning(f"Collection '{qdr_collection}' already exists.")
            return
        # qdrant_client.create_collection(
        #     collection_name=qdr_collection,
        #     vectors_config=models.VectorParams(
        #         size=embedding_size,
        #         distance=distance
        #     )
        # )
        
        collection_config = models.VectorParams(
              size=embedding_size, # 768 for instructor-xl, 1536 for OpenAI, embed-multilingual-v2.0=768
            distance=qdr_distance)
    
        qdrant_client.recreate_collection(
        collection_name=qdr_collection,
        vectors_config=collection_config,
        ) 
        st.success(f"Collection '{qdr_collection}' created successfully.")
        return qdrant_client
    except Exception as e:
        st.error(f"Error creating collection '{qdr_collection}': {e}")



def delete_collection(collection_name):
    """
    Delete a collection in Qdrant.
    """
    try:
        if collection_name not in [col.name for col in qdrant_client.get_collections().collections]:
            st.warning(f"Collection '{collection_name}' does not exist.")
            return
        confirmation = st.warning(f"Are you sure you want to delete the collection '{collection_name}'? This action cannot be undone.", icon="⚠️")
        if st.button(f"Confirm Delete '{collection_name}'"):
            qdrant_client.delete_collection(collection_name=collection_name)
            st.success(f"Collection '{collection_name}' deleted successfully.")
    except Exception as e:
        st.error(f"Error deleting collection '{collection_name}': {e}")

def embed_text_openai(text):
    """
    Generate embeddings using OpenAI's embedding model.
    """
    client = OpenAI()
    try:
        response = client.embeddings.create(
            input=text,
            model="text-embedding-3-large"
        )
        return response.data[0].embedding
    except Exception as e:
        st.error(f"Error generating OpenAI embedding: {e}")
        return None

def embed_text_cohere(text):
    """
    Generate embeddings using Cohere's embedding model.
    """
    co = cohere.Client(COHERE_API_KEY) # This is your trial API ke
    try:
        response = co.embed(
            texts=[text],
            model="embed-multilingual-v3.0",
            input_type='classification',
            truncate='NONE'
        )
        return response.embeddings[0]
    except Exception as e:
        st.error(f"Error generating Cohere embedding: {e}")
        return None

def process_user_input(user_text):
    """
    Use OpenAI's GPT model to process user text into a search query.
    """
    try:
        system_prompt=" "
        user_prompt = (
            "Extract the key entities, keywords, and suggest a search query that can be used to find matching ICD codes and descriptions."
            f"\n\nUser Description: {user_text}\n\nSuggested Search Query:"
        )
        client = OpenAI(api_key=OPENAI_API_KEY)
        completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Error processing user input: {e}", icon=':material/sentiment_dissatisfied:')
        return ""
    
def claude_model():
    return "claude-3-5-sonnet-20240620" #claude-3-haiku-20240307

@st.fragment
def claude_process_user_input(user_search_query):
    client = Anthropic(api_key=my_secrets["anthropic_secrets"]["claude_api"],)
    #include mention of surgical proceduras
    system_prompt=("You are a medical assistant very knowledgeable in a collection of medical services provided to the insured in appropriate type, volume, and conditions, funded by the financial sources of mandatory health insurance. " 
                   f"The collection is similar to the ICD codes with their descriptions. You help patients with finding relevant medical service codes and desciptions based on a patient's description of health conditions and symptoms. " 
                   f"You respond in clear Azerbaijani language only.")
    user_prompt = ("Extract the key entities, keywords, and suggest a search query that can be used to find matching medical service (surgical procedures specifically) codes and their descriptions."
            f"\n\nUser Description: {user_search_query}\n\nSuggested Search Query in Azerbaijani language:")
    
    messages_text=[ {"role": "user", "content": [{"type": "text", "text": user_prompt}]}]
    claude_response = client.messages.create(model=claude_model(), max_tokens=8000, temperature=0, system=system_prompt, messages=messages_text)
    return claude_response.content[0].text

def search_collections(query_vector, collection_name, top_k=5):
    """
    Search a Qdrant collection using the provided query vector.
    """
    qdrant_client =QdrantClient(QDRANT_HOST, api_key=QDRANT_API_KEY)
    try:
        results = qdrant_client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=top_k,
            with_payload=True  # Ensure payload is returned
        )
        return results
    except Exception as e:
        st.error(f"Error searching collection '{collection_name}': {e}", icon=':material/sentiment_dissatisfied:')
        return []

def generate_user_friendly_output(results, collection_name):
    """
    Use OpenAI's GPT model to generate user-friendly summaries from search results.
    """
    try:
        if not results:
            return "No results to summarize."
        combined_results = "\n".join([f"{idx+1}. {res.payload.get('description', 'No description available.')}" for idx, res in enumerate(results)])
        system_prompt="You are an assistant that summarizes medical information in a user-friendly manner."
        user_prompt = (
            "Summarize provided medical information in a user-friendly manner.\n\n"
            f"Collection: {collection_name}\n"
            f"Search Results:\n{combined_results}\n\n"
            "Please provide a concise and easy-to-understand summary of the above information."
        )
        client = OpenAI(api_key=OPENAI_API_KEY)
        completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Error generating user-friendly output: {e}", icon=':material/sentiment_dissatisfied:')
        return "Could not generate summary."

def insert_data(collection_name, data, embedding, metadata=None):
    """
    Insert data into a Qdrant collection.
    """
    qdrant_client =QdrantClient(QDRANT_HOST, api_key=QDRANT_API_KEY)

    try:
        qdrant_client.upsert(
            collection_name=collection_name,
            points=[
                PointStruct(
                    id=data.get('id'),
                    vector=embedding,
                    payload=metadata # or data
                )
            ]
        )
        st.success(f"Data inserted into '{collection_name}' successfully.")
    except Exception as e:
        st.error(f"Error inserting data into '{collection_name}': {e}")

def generate_valid_id(original_id):
    # Remove periods and concatenate all digits
    digits_only = ''.join(char for char in str(original_id) if char.isdigit())
    if not digits_only:
        # If there are no digits, generate a hash-based integer
        return abs(hash(str(original_id)))
    # Convert to integer, ensuring it's positive and within a reasonable range
    return int(digits_only) % (2**63 - 1)  # Max value for signed 64-bit integer
    
def insert_data_from_csv(collection1_name, collection2_name):
    st.subheader("Insert Data from CSV")
    
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    if uploaded_file is not None:
        # Read the CSV file
        csv_data = pd.read_csv(StringIO(uploaded_file.getvalue().decode('utf-8')))
        
        if st.button("Insert Data"):
            for _, row in csv_data.iterrows():
                data_id = row['Sifaris_No']
                data_description = row['Təsvir']
                metadata_entities = row['Əlaqəli_adlar']
                metadata_keywords = row['Açar_sözlər']
                
                if data_id and data_description:
                    # Generate embeddings for both collections
                    embedding1 = embed_text_openai(data_description)
                    embedding2 = embed_text_cohere(data_description)
                    
                    if embedding1 and embedding2:
                        metadata = {
                            "order_no": data_id,
                            "description": data_description,
                            "entities": [entity.strip() for entity in metadata_entities.split(",") if entity.strip()],
                            "keywords": [keyword.strip() for keyword in metadata_keywords.split(",") if keyword.strip()],
                            "metada_xidmet": "cərrahi tibbi xidmətlər",
                            "kod": row['Kod'],
                            "ad": row['Ad']
                        }
                        data = {"id": generate_valid_id(data_id)}
                        
                        # Insert into collection1
                        insert_data(collection1_name, data, embedding1, metadata=metadata)
                        
                        # Insert into collection2
                        insert_data(collection2_name, data, embedding2, metadata=metadata)
                    
                    st.success(f"Inserted data for ID: {data_id}")
                else:
                    st.warning(f"Skipped row with missing Data ID or Description: {data_id}")
            
            st.success("All data inserted successfully!")
    else:
        st.info("Please upload a CSV file to proceed.")




# ----------------------------
# Streamlit Layout
# ----------------------------

st.title("Simptom və şikayətlərə görə xidmətin təklif edilməsi")

st.sidebar.header("Konfiqurasiya")

# Qdrant Configuration Inputs
with st.sidebar.expander("Qdrant Configuration"):
    QDRANT_HOST_INPUT = st.text_input("Qdrant Host", value=QDRANT_HOST)
    QDRANT_PORT_INPUT = st.number_input("Qdrant Port", value=QDRANT_PORT, min_value=1, max_value=65535)
    # Optionally, allow users to specify API key or other Qdrant settings

# Update Qdrant client if user changes host or port
if 'qdrant_client' in locals():
    try:
        # qdrant_client = QdrantClient(host=QDRANT_HOST_INPUT, port=int(QDRANT_PORT_INPUT))
        qdr_client =QdrantClient(QDRANT_HOST, api_key=QDRANT_API_KEY)
    except Exception as e:
        st.error(f"Failed to connect to Qdrant with provided settings: {e}")

# Collection Management
st.sidebar.subheader("Manage Collections")

# Collection Names Configuration
collection1_name = st.sidebar.text_input("OpenAI Embeddings Collection Name", value="openai_embeddings_collection")
collection2_name = st.sidebar.text_input("Cohere Embeddings Collection Name", value="cohere_embeddings_collection")

# Embedding Size Configuration
embedding_size_openai = 3072  # As per OpenAI's text-embedding-ada-002
embedding_size_cohere = 1024    # Assuming Cohere's embed-multilang-v2.0 returns 768-dimension embeddings

# Distance Metric Selection
distance_metric = st.sidebar.selectbox("Vector Distance Metric", options=["COSINE", "EUCLID", "DOT"])

# Convert string to Qdrant distance enum
distance_mapping = {
    "COSINE": models.Distance.COSINE,
    "EUCLID": models.Distance.EUCLID,
    "DOT": models.Distance.DOT
}
selected_distance = distance_mapping.get(distance_metric, models.Distance.COSINE)

# Create Collections
if st.sidebar.button("Create Collections"):
    with st.spinner("Creating collections..."):
        create_collection(collection1_name, embedding_size=embedding_size_openai, qdr_distance=selected_distance)
        create_collection(collection2_name, embedding_size=embedding_size_cohere, qdr_distance=selected_distance)

# Delete Collections
if st.sidebar.button("Delete Collections"):
    with st.spinner("Deleting collections..."):
        delete_collection(collection1_name)
        delete_collection(collection2_name)

#********************NEW CODE **************************
import re
from typing import List, Dict


def process_qdrant_results(results: List[Dict]) -> List[Dict]:
    processed_results = []
    for result in results:
        payload = result.payload
        processed_result = {
            "Sifariş No.": payload.get("order_no", "N/A"),
            "Kod": payload.get("kod", "N/A"),
            "Ad": payload.get("ad", "N/A"),
            "Təsvir": payload.get("description", "N/A"),
            "Açar sözlər": payload.get("keywords", []),
            "Uyğunluq": result.score
        }
        processed_results.append(processed_result)
    return processed_results

def format_results_for_display(processed_results: List[Dict], search_query: str) -> str:
    if not processed_results:
        return "Heç bir nəticə tapılmadı."

    formatted_output = "**AXTARIŞ NƏTİCƏLƏRİ:**\n\n"
    for idx, result in enumerate(processed_results, 1):
        formatted_output += f"\nNəticə {idx}:\n"
        formatted_output += f"\n**Sifariş No.**: {result['Sifariş No.']}\n"
        formatted_output += f"\n**Kod**: {result['Kod']}\n"
        formatted_output += f"\n**Ad**: {result['Ad']}\n"
        formatted_output += f"\n**Uyğunluq**: {result['Uyğunluq']:.2%}\n"
        formatted_output += f"\n**Əsaslandırma**: {generate_justification(result, search_query)}\n"
        formatted_output +=f"\n----------------------------------------------------------------"
    return formatted_output

# Update the generate_justification function to use English prompts but output in Azerbaijani
def generate_justification(result: Dict, search_query: str) -> str:
    system_prompt = "You are an assistant that explains medical information in simple terms. Always respond in Azerbaijani language."
    user_prompt = f"""
    Consider the following medical procedure information and search query, 
    and explain in simple terms why this procedure was selected. Your explanation should be brief and easy to understand.

    Procedure: {result['Ad']}
    Description: {result['Təsvir']}
    Keywords: {', '.join(result['Açar sözlər'])}
    Search query: {search_query}

    Provide your explanation in Azerbaijani language.
    """

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return f"Əsaslandırma yaradılarkən xəta baş verdi: {e}"


def calculate_medical_relevance(result: Dict, search_query: str) -> float:
    # Bu funksiya sadə bir alqoritm istifadə edir. Daha mürəkkəb bir alqoritm tətbiq edilə bilər.
    relevance_score = 0
    query_words = re.findall(r'\w+', search_query.lower())
    
    # Açar sözləri yoxlayın
    for keyword in result['Açar sözlər']:
        if any(word in keyword.lower() for word in query_words):
            relevance_score += 0.2  # Hər uyğun açar söz üçün 20% əlavə edin

    # Adı yoxlayın
    if any(word in result['Ad'].lower() for word in query_words):
        relevance_score += 0.3  # Ad uyğunluğu üçün 30% əlavə edin

    # Təsviri yoxlayın
    if any(word in result['Təsvir'].lower() for word in query_words):
        relevance_score += 0.3  # Təsvir uyğunluğu üçün 30% əlavə edin

    # Qdrant-ın verdiyi uyğunluq dərəcəsini də nəzərə alın
    relevance_score += result['Uyğunluq'] * 0.2  # Qdrant skorunu 20% çəki ilə əlavə edin

    return min(relevance_score, 1.0)  # Maksimum 100% qaytarın

st.header("Pasientin vəziyyətini daxil edin")

user_text = st.text_area("Pasientin sağlamlıq vəziyyətini və simptomları daxil edin:", height=150)

# # Optional: Data Ingestion Section
# st.subheader("Data Ingestion (Optional)")
# with st.expander("Insert Data into Collections"):
#     # Call this function in your main Streamlit app
#     insert_data_from_csv(collection1_name, collection2_name)

if st.button("Analiz et"):
    qdrant_client = QdrantClient(QDRANT_HOST, api_key=QDRANT_API_KEY)
    if not user_text.strip():
        st.warning("Please enter a description of your health condition and symptoms.")
    elif not (collection1_name in [col.name for col in qdrant_client.get_collections().collections] and
              collection2_name in [col.name for col in qdrant_client.get_collections().collections]):
        st.warning("Please ensure both collections exist before performing analysis.")
    else:
        with st.spinner("Bircə dəqiqə fikrimi cəmləyirəm..."):
            # Step 1: Process user input to generate search query
            search_query = claude_process_user_input(user_text)
            if search_query:
                st.write(f"**Тəklif olunan axtarış sorğusu:** {search_query}")
            else:
                st.error("İstifadəçi məlumatı axtarış sorğusuna keçirilə bilmədi.")
                st.stop()

            # Step 2: Generate embeddings for the search query
            openai_embedding = embed_text_openai(search_query)
            cohere_embedding = embed_text_cohere(search_query)

            if not openai_embedding or not cohere_embedding:
                st.error("Failed to generate embeddings for the search query.")
                st.stop()

            # Step 3: Search both collections
            results_openai = search_collections(openai_embedding, collection1_name)
            results_cohere = search_collections(cohere_embedding, collection2_name)
            
            # st.write("RESULTS WITH PAYLOAD:")
            # st.write(results_openai)
            # st.divider()

        # Step 4: Process and display results using new functions
        col1, col2 = st.columns(2)
        with st.spinner("Cavab hazırlanır..."):
            with col1:
                st.subheader("1-Cİ VARİANT")
                if results_openai:
                    processed_results_openai = process_qdrant_results(results_openai)
                    formatted_output_openai = format_results_for_display(processed_results_openai, search_query)
                    st.markdown(formatted_output_openai)
                else:
                    st.write("1-Cİ VARİANT Kolleksiyasında heç bir nəticə tapılmadı.")

            with col2:
                st.subheader("2-Cİ VARİANT")
                if results_cohere:
                    processed_results_cohere = process_qdrant_results(results_cohere)
                    formatted_output_cohere = format_results_for_display(processed_results_cohere, search_query)
                    st.markdown(formatted_output_cohere)
                else:
                    st.write("1-Cİ VARİANT Kolleksiyasında heç bir nəticə tapılmadı.")

        # Optional: Add a horizontal line to separate the results from other content
        st.markdown("---")
                # After analysis is complete

        llm_output = formatted_output_openai + "\n\n" + formatted_output_cohere
        github_token=st.secrets["medaid_streamlit"]
        if github_token:
            save_result = save_to_github(user_text, search_query, llm_output, github_token)
            st.success(save_result)
        else:
            st.warning("GitHub token or repository not provided. Results not saved to GitHub.")

# st.header("Enter Your Health Description")

# user_text = st.text_area("Describe your health condition and symptoms here:", height=150)

# # Optional: Data Ingestion Section
# st.subheader("Data Ingestion (Optional)")
# with st.expander("Insert Data into Collections"):
# # Call this function in your main Streamlit app
#     insert_data_from_csv(collection1_name, collection2_name)

# if st.button("Analyze"):
#     qdrant_client =QdrantClient(QDRANT_HOST, api_key=QDRANT_API_KEY)
#     if not user_text.strip():
#         st.warning("Please enter a description of your health condition and symptoms.")
#     elif not (collection1_name in [col.name for col in qdrant_client.get_collections().collections] and
#           collection2_name in [col.name for col in qdrant_client.get_collections().collections]):
#         st.warning("Please ensure both collections exist before performing analysis.")
#     else:
#         with st.spinner("Processing your input..."):
#             # Step 1: Process user input to generate search query
#             search_query = process_user_input(user_text)
#             if search_query:
#                 st.write(f"**Suggested Search Query:** {search_query}")
#             else:
#                 st.error("Failed to generate a search query from the input.")
#                 st.stop()

#             # Step 2: Generate embeddings for the search query
#             openai_embedding = embed_text_openai(search_query)
#             cohere_embedding = embed_text_cohere(search_query)

#             if not openai_embedding or not cohere_embedding:
#                 st.error("Failed to generate embeddings for the search query.")
#                 st.stop()

#             # Step 3: Search both collections
#             results_openai = search_collections(openai_embedding, collection1_name)
#             results_cohere = search_collections(cohere_embedding, collection2_name)
            
#             st.write("RESULTS WITH PAYLOAD:")
#             st.write(results_openai)
#             st.divider()
#             # Step 4: Generate user-friendly outputs
#             if results_openai:
#                 summary_openai = generate_user_friendly_output(results_openai, collection1_name)
#                 st.subheader("Top 5 Results from OpenAI Embeddings Collection")
#                 st.write(summary_openai)
#             else:
#                 st.write("No results found in OpenAI Embeddings Collection.")

#             if results_cohere:
#                 summary_cohere = generate_user_friendly_output(results_cohere, collection2_name)
#                 st.subheader("Top 5 Results from Cohere Embeddings Collection")
#                 st.write(summary_cohere)
#             else:
#                 st.write("No results found in Cohere Embeddings Collection.")
