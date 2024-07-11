from flask import Flask, request, jsonify
import os
from typing import Optional
from google.api_core.client_options import ClientOptions
from google.cloud import documentai  # type: ignore

app = Flask(__name__)

@app.route('/ping', methods=['GET'])
def ping():
    print("hi")
    return jsonify({'msg': 'pong!'}), 200

mime_type = ["application/pdf", "image/jpeg"]

def process_document_sample(
    file,
    mime_type: str,
    processor_version_id: Optional[str] = None,
):
    project_id = "ace-fa-space-424110"
    location = "us"
    processor_id = "e3e87fb41a83ffb9"
    field_mask = "text,entities,pages.pageNumber"
    opts = ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")

    client = documentai.DocumentProcessorServiceClient(client_options=opts)

    if processor_version_id:
        # The full resource name of the processor version, e.g.:
        # `projects/{project_id}/locations/{location}/processors/{processor_id}/processorVersions/{processor_version_id}`
        name = client.processor_version_path(
            project_id, location, processor_id, processor_version_id
        )
    else:
        # The full resource name of the processor, e.g.:
        # `projects/{project_id}/locations/{location}/processors/{processor_id}`
        name = client.processor_path(project_id, location, processor_id)

    file = file.read()
    # Load binary data
    raw_document = documentai.RawDocument(content=file, mime_type=mime_type)

    # For more information: https://cloud.google.com/document-ai/docs/reference/rest/v1/ProcessOptions
    # Optional: Additional configurations for processing.
    process_options = documentai.ProcessOptions(
        # Process only specific pages
        individual_page_selector=documentai.ProcessOptions.IndividualPageSelector(
            pages=[1,2,3]
        )
    )

    # Configure the process request
    request = documentai.ProcessRequest(
        name=name,
        raw_document=raw_document,
        field_mask=field_mask,
        process_options=process_options,
    )

    result = client.process_document(request=request)

    document = result.document

    structured_json = {}
    for entity in document.entities:
        if not entity.type_ in structured_json.keys():
            structured_json[entity.type_] = [str(entity.mention_text)]
        else:
            structured_json[entity.type_].append(str(entity.mention_text))

    return structured_json


# Endpoint to receive an image
@app.route('/process', methods=['POST'])
def upload_image():
    # Check if a file was uploaded
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    
    file = request.files['file']

    # If user does not select a file, browser also submit an empty part without filename
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        # Determine the content type of the file
        content_type = file.content_type
        print(f'Uploaded file content type: {content_type}')

        respose = process_document_sample(file, content_type)

        return jsonify(respose), 200

    return jsonify({'error': 'Upload failed'}), 500




if __name__ == '__main__':
    app.run(debug=True, port=5001)