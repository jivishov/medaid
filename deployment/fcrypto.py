import io, os, uuid
import base64
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
import requests, datetime
from typing import Dict, List, Any, Union, Tuple

url = 'http://medaid.bx5nfnnj.a2hosted.com/fapp'
# file_name="file"+str(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))+".pdf"
# local_pdf_path=os.curdir+"/pdfs/"+file_name


def submit_patient_question(patient_id: int, lab_results: str, LLM_triage: str, 
                            ptnt_triage_answ: str, LLM_followup_quest: str, 
                            ptnt_followup_quest: str, lab_photo: str, llm_type: str) -> Union[int, Tuple[int, str]]:
    payload = {
        "patient_id": patient_id,
        "lab_results": lab_results,
        "LLM_triage": LLM_triage,
        "ptnt_triage_answ": ptnt_triage_answ,
        "LLM_followup_quest": LLM_followup_quest,
        "ptnt_followup_quest": ptnt_followup_quest,
        "lab_photo": lab_photo,
        "llm_type": llm_type
    }
    response = requests.post(f"{url}/insert_patient_question", json=payload)
    if response.status_code == 200:
        return response.json()["question_id"]
    else:
       return 0, response.text

def assign_question_to_doctors(ptnt_quest_id: int, patient_id: int, doc_ids: List[int]) -> Dict[str, Any]:
    payload = {
        "ptnt_quest_id": ptnt_quest_id,
        "patient_id": patient_id,
        "doc_ids": doc_ids
    }
    response = requests.post(f"{url}/insert_doc_question", json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to assign question to doctors: {response.text}")


def submit_responses_rating(gpt_response, claude_response, gpt_rating, claude_rating, file_name):
    payload = {
        "gpt_response":gpt_response,
        "claude_response":	 claude_response,
        "gpt_rating":gpt_rating,
        "claude_rating": claude_rating,
        "file_name":file_name}

    response = requests.post(f"{url}/submit_rating", json=payload)
    if response.status_code == 200:
        # Successful response
        print(response.json())
    else:
        # Try to extract and print the detailed error message from the response
        try:
            error_response = response.json()
            error_message = error_response.get('error', 'Unknown error')  # Default to 'Unknown error' if not found
            return f'Failed to send data. Status code: {response.status_code}, Error: {error_message}'
        except Exception as parse_error:
            # If there's an error parsing the error message, print a generic error
            return f'Failed to send data, and could not parse error message. Status code: {response.status_code}'


def combine_and_send_images(image_list):
    if len(image_list) > 3:
        raise ValueError("Maximum of 3 images allowed in the list.")

    # Create a bytes buffer for the PDF
    pdf_buffer = io.BytesIO()

    # Create a new PDF with letter size pages
    pdf = canvas.Canvas(pdf_buffer, pagesize=letter)

    for image_base64 in image_list:
        # Decode the base64 image
        if "," in image_base64:
            image_data = base64.b64decode(image_base64.split(",")[1])
        else:
            image_data = base64.b64decode(image_base64)
        
    # Create a bytes buffer for the PDF
    pdf_buffer = io.BytesIO()

    # Create a new PDF with letter size pages
    pdf = canvas.Canvas(pdf_buffer, pagesize=letter)

    for image_base64 in image_list:
        # Decode the base64 image
        if "," in image_base64:
            image_data = base64.b64decode(image_base64.split(",")[1])
        else:
            image_data = base64.b64decode(image_base64)
        
        # Create an ImageReader object from the image data
        image = ImageReader(io.BytesIO(image_data))

        # Get the image width and height
        image_width, image_height = image.getSize()

        # Calculate the scaling factor to fit the image within the page
        page_width, page_height = letter
        scale_factor = min(page_width / image_width, page_height / image_height)

        # Calculate the scaled image dimensions
        scaled_width = image_width * scale_factor
        scaled_height = image_height * scale_factor

        # Calculate the position to place the image at the top-left corner
        x = 0
        y = page_height - scaled_height

        # Draw the image on the PDF canvas with scaling
        pdf.drawImage(image, x, y, width=scaled_width, height=scaled_height)
        pdf.showPage()

    # Save the PDF and move to the beginning of the buffer
    pdf.save()
    pdf_buffer.seek(0)

    # Save the PDF file locally
    file_name=f"file{uuid.uuid4().hex}.pdf"
    local_pdf_path=os.curdir+"/pdfs/"+file_name
    with open(local_pdf_path, "wb") as file:
        file.write(pdf_buffer.getvalue())

    # return "pdf saved"
    # Prepare the file for sending
    files = {"file": (file_name, pdf_buffer, "application/pdf")}

    # Send the PDF to the Flask endpoint
    response = requests.post(f"{url}/upload", files=files, verify=True)

    if response.status_code == 200:
        return "SUCCESS", file_name
    else:
        return "FAILED", 'none'