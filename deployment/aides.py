from anthropic import Anthropic
import base64
from streamlit import secrets as my_secrets, spinner as my_spinner, session_state
import streamlit as st
import json
import asyncio
from anthropic import AsyncAnthropic
from anthropic.types import ContentBlockDeltaEvent
import re, random

def claude_model():
    return "claude-3-haiku-20240307" #"claude-3-5-sonnet-20240620"

# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

image_prompt="""You are extremely helpful, knowledgable and skillful medical specialist who is tasked to help a physician to effectively diagnose patient's case. 
            You will be provided maximum of 3 images of a medical lab analysis by a patient and you need to provide the following.
            First task: interpret the lab results' numerical values item by item by comparing them to their reference numerical values specified in the image. Provide lower and upper ranges from the image, compare them with the measured value and write if the measured value is below, above or within of the mentioned limits. You must not do wrong, therefore, double check before providing answer! Start each sentence as numbered item (1. 2. 3. etc.). Style sentences with values out of limits as bold. Include the first task answer between [results] [/results] custom tags.
            Second task: ask best 5 triage questions with respect to the lab results to collect answers from the user for their physician.  Include the triage questions between [triage] [/triage] custom tags.
            This way you will help physician to diagnose the condition, and also improve patient's morale which is essential in patient treatment.
            You respond only and only in Azerbaijani language, but do not translate custom tags!
            """
followup_prompt ="""You are extremely helpful, knowledgable and skillful medical specialist who is tasked to help a human physician to effectively diagnose patient's case. 
                You are provided with lab results and triage questions and their answers from the patient.
                Your task: Based on the provided lab results and triage Q&A, provide 3 best follow-up questions the user patient needs to ask their physician. Do not imply about any diagnosis in the follow up questions! Include the follow up questions between [followup] [/followup] custom tags.     
                This way you will help physician to diagnose the condition, and also improve patient's morale which is essential in patient treatment.
                You respond only and only in Azerbaijani language, but do not translate custom tags! Here's the information for you to process and then generate the follow-up questios:
                """
# Your compassionate and empathetic response will contain: start with greeting the patient (use 'istifadəçi' in a friendly greeting instead of 'xəstə') to comfort them, continue with the interpretation, the triage questions and follow-up questions.
#             Conclude your response with a hope-instilling and empathetic sentence to comfort and relax the patient.
#You respond only and only in Azerbaijani language, but do not translate custom tags!

results_prompt="""You are extremely helpful, knowledgable and skillful medical specialist who is tasked to help a human physician to effectively diagnose patient's case. 
You will be provided following information chunks between custom tags for the evaluation. There are total of 3 custom tags. 
First custom tags: [results] [/results] and they contain details of the lab analysis report. 
Second custom tags: [triage] [/triage] and they contain triage questions based on the lab results with corresponding answers from a patient. 
Third custom tags: [followup] [/followup] and they contain the patient's follow up questions for the physician.
By evaluating results of a lab test and patient answers of triage questions altogether you will do your best to provide a diagnosis answer to help the physician.
Next, in coherence with lab results and patient answers of triage questions, generate best answers for the included follow up questions to save time for the physician.
All of your response will be shown only to a live human physician for further evaluation. 
A human physician will decide which part of your information will be displayed to the patient.
Here's the mentioned information for you to work on:
                """

def clean_followup_output(text):
    # Check if the input is a list, if so convert it to a string
    if isinstance(text, list):
        text = ''.join(text)
    # Replace escaped newline characters with actual newlines and remove backslashes
    text = re.sub(r'\[/?followup.*?\]', '', text.replace('\\n', '\n').replace('\\', ''), flags=re.IGNORECASE)
    # Strip leading/trailing whitespace from each line, remove empty lines, and join them back together
    cleaned_text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())
    cleaned_string = ''.join(cleaned_text)
    return cleaned_string

async def better_call_dr_qaib_claude(image_list, task, info):
    client = AsyncAnthropic(api_key=my_secrets["anthropic_secrets"]["claude_api"],)
   
    if task=="evaluate_lab_images":
        messages_text=[ {"role": "user", "content": [{"type": "text", "text": image_prompt}]}]
        image_count=len(image_list)
        for i in range(image_count):
            image_dict = {"type": "image", "source": {"type": "base64","media_type": "image/jpeg","data": f"{image_list[i]}"}}
            messages_text[0]["content"].append(image_dict)

    elif task=="make_followup_questions":
        messages_text=[ {"role": "user", "content": [{"type": "text", "text": followup_prompt+info}]}]

    claude_response =await client.messages.create(model=claude_model(), max_tokens=3000, temperature=0, messages=messages_text,)

    if task=="make_followup_questions":
        claude_response=clean_followup_output(claude_response.content[0].text)
    else:
        claude_response=claude_response.content[0].text

    return claude_response

    #REMOVE COLUMN DEPENDENCE HERE

    # if column is None:

    # if column is not None:

        # column.subheader(":orange[Below is the response from the Claude Opus for further processing in the background.]", divider="rainbow")
        #     #claude_response =
        # claude_response =await client.messages.create(
        #     model=claude_model(), #"claude-3-haiku-20240307",
        #     max_tokens=2000, temperature=0,
        #     messages=messages_text,
        #     stream=True,)

        # markdown_start="<span style='width:50%'>"
        # markdown_close="</span>"
        # markdown=""
        # final_text=""
        # placeholder = column.empty()
        # async for chunk in claude_response:
        #         # Display the content to the user
        #     if isinstance(chunk, ContentBlockDeltaEvent):
        #         if chunk.delta.text:
        #             placeholder.empty()
        #             markdown+=chunk.delta.text
        #             # with placeholder.container():
        #             placeholder.markdown(markdown_start+markdown+markdown_close, unsafe_allow_html=True)
        #             final_text=markdown_start+markdown+markdown_close
                
    

@st.experimental_fragment
def claude_response_for_physician(full_info):
    client = Anthropic(api_key=my_secrets["anthropic_secrets"]["claude_api"],)
    messages_text=[ {"role": "user", "content": [{"type": "text", "text": results_prompt+full_info}]}]
    claude_response = client.messages.create(model=claude_model(), max_tokens=2000, temperature=0,messages=messages_text)

    return claude_response.content[0].text



def parse_claude_results_triage_response(claude_response):
    # claude_results = re.search(r'\[results\](.*?)\[/results\]', claude_response, re.DOTALL).group(1).strip()
    claude_results = re.search(r'\[results\](.*?)\[/results\]', claude_response.replace('\\n', '\n'), re.DOTALL).group(1).strip()
    claude_triage = re.search(r'\[triage\](.*?)\[/triage\]', claude_response.replace('\\n', '\n'), re.DOTALL).group(1).strip()
    return claude_results, claude_triage

def parse_claude_followup_response(claude_response):
    claude_followup = re.search(r'\[followup\](.*?)\[/followup\]', claude_response.replace('\\n', '\n'), re.DOTALL).group(1).strip()
    return claude_followup

# List of emojis representing physicians
physician_emojis = ["👨‍⚕️", "👩‍⚕️"]
# List of male and female first names
male_names = ["Dr. John", "Dr. David", "Dr. Michael", "Dr. James", "Dr. Robert", "Dr. William", "Dr. Richard", "Dr. Thomas", "Dr. Mark", "Dr. Steven"]
female_names = ["Dr. Emily", "Dr. Emma", "Dr. Madison", "Dr. Abigail", "Dr. Olivia", "Dr. Isabella", "Dr. Hannah", "Dr. Samantha", "Dr. Ava", "Dr. Ashley"]
# List of last names
last_names = ["Smith", "Johnson", "Brown", "Davis", "Miller", "Wilson", "Taylor", "Anderson", "Clark", "Lewis"]
# List of medical specialties
specialties = ["Cardiology", "Dermatology", "Neurology", "Oncology", "Pediatrics", "Psychiatry", "Radiology", "Surgery", "Urology", "Ophthalmology"]

# Function to generate a random physician
def generate_physician():
    gender = random.choice(["Male", "Female"])
    if gender == "Male":
        first_name = random.choice(male_names)
        emoji = physician_emojis[0]
    else:
        first_name = random.choice(female_names)
        emoji = physician_emojis[1]
    last_name = random.choice(last_names)
    specialty = random.choice(specialties)
    return f"<b>Name:</b> {emoji} {first_name} {last_name} <br> <br> <b>Specialty:</b> {specialty}"

import re

def sanitize_and_check_threats(input_text):
    # List of SQL injection keywords
    sql_keywords = ['union', 'select', 'from', 'where', 'insert', 'update', 'delete', 'drop', 'alter', 'truncate',
                    'database', 'table', 'column', 'order by', 'group by', 'having', 'limit', 'offset']

    # List of system prompt and command keywords
    system_keywords = ['system', 'sistem', 'prompt', 'cmd', 'command', 'shell', 'terminal', 'exec', 'execute']

    # List of language model-specific keywords
    lm_keywords = ['settings', 'config', 'api key', 'access token', 'credentials']

    # List of programming language keywords
    code_keywords = ['function', 'import', 'require', 'eval', 'exec', 'os', 'sys', 'process']

    # List of sensitive information keywords
    sensitive_keywords = ['password', 'api key', 'access token', 'personally identifiable information', 'pii']

    # List of file path and URL-related keywords
    file_url_keywords = ['../', '/', '\\', 'file://', 'http://', 'https://']

    # Combine all the keyword lists
    all_keywords = sql_keywords + system_keywords + lm_keywords + code_keywords + sensitive_keywords + file_url_keywords

    # Regex pattern for special characters and encodings
    special_chars_pattern = r'[\'";#@\\%&+%^|]'

    # Convert the input text to lowercase for case-insensitive matching
    input_text = input_text.lower()

    # Initialize an empty list to store the found threats
    found_threats = []

    # Check for SQL injection keywords
    if any(keyword in input_text for keyword in sql_keywords):
        found_threats.append("1") #Potential SQL Injection
    # Check for system prompt and command keywords
    if any(keyword in input_text for keyword in system_keywords):
        found_threats.append("2") #Potential System Prompt or Command
    # Check for language model-specific keywords
    if any(keyword in input_text for keyword in lm_keywords):
        found_threats.append("3") #Potential Language Model-Specific Keyword
    # Check for programming language keywords
    if any(keyword in input_text for keyword in code_keywords):
        found_threats.append("4") #Potential Code Injection
    # Check for sensitive information keywords
    if any(keyword in input_text for keyword in sensitive_keywords):
        found_threats.append("5") #Potential Sensitive Information
    # Check for file path and URL-related keywords
    if any(keyword in input_text for keyword in file_url_keywords):
        found_threats.append("6") #Potential File Path or URL Threat
    # Check for special characters and encodings
    if re.search(special_chars_pattern, input_text):
        found_threats.append("7") #Potential Special Character or Encoding Threat

    # Sanitize the input text by removing any detected keywords and special characters
    sanitized_text = input_text
    for keyword in all_keywords:
        sanitized_text = sanitized_text.replace(keyword, '')
    sanitized_text = re.sub(special_chars_pattern, '', sanitized_text)

    # Return the sanitized text and any found threats
    return sanitized_text, found_threats