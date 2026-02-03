from google.cloud import vision
from google.oauth2 import service_account
import os
import base64
import json

def extract_text_from_image(image_file):
    
    # Instantiates a client
    google_client = vision.ImageAnnotatorClient(credentials=get_google_api_credentials())
    
    content = image_file.read()
    image = vision.Image(content=content)

    # Performs text detection on the image
    response = google_client.text_detection(image=image)
    texts = response.text_annotations

    if not texts:
        print("ERROR :: No text detected for image")
        return None

    if response.error.message:
        raise Exception(
            f'{response.error.message}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'
        )
    else:
        return texts[0].description
    
# NOTE:: THE CREDENTIAL IN THE ENV VARIABLE IS ACTUALLY FROM THE CONTENT OF API-KEY JSON FILE ENCODED IN BASE64
def get_google_api_credentials():
    base64_encoded_key = os.environ.get('GOOGLE_VISION_CREDENTIALS_JSON_BASE64')

    if base64_encoded_key:
        json_data = base64.b64decode(base64_encoded_key)
        service_account_info = json.loads(json_data)

        return service_account.Credentials.from_service_account_info(service_account_info)
    else:
        return None
