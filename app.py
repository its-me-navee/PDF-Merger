from flask import Flask, render_template, request, redirect, url_for, send_file
from PyPDF2 import PdfReader, PdfWriter
from azure.storage.blob import BlobServiceClient, ContainerClient
from io import BytesIO
import uuid
import datetime

app = Flask(__name__)
app.config['AZURE_STORAGE_CONNECTION_STRING'] = 'DefaultEndpointsProtocol=https;AccountName=navneetsingh;AccountKey=Fh8xbTgypRGVdD5OKcA2yiYGhZs2Z4e6HmsaJ88ykpXJdL+eX/iwFPOrINCWNDqSnVLPl2hVUHNb+AStSE240w==;EndpointSuffix=core.windows.net'
app.config['AZURE_CONTAINER_NAME'] = 'uploads'
app.config['AZURE_MERGED_FOLDER'] = 'merged'

# Initialize Azure Blob Service
blob_service_client = BlobServiceClient.from_connection_string(app.config['AZURE_STORAGE_CONNECTION_STRING'])
container_client = blob_service_client.get_container_client(app.config['AZURE_CONTAINER_NAME'])

if not container_client.exists():
    container_client.create_container()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/merge', methods=['POST'])
def merge_pdfs():
    # Get uploaded files
    pdf_files = request.files.getlist('pdf_files')

    # Save uploaded files to Azure Blob Storage
    uploaded_paths = []
    for pdf_file in pdf_files:
        blob_name = pdf_file.filename
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.upload_blob(pdf_file, overwrite=True)

        uploaded_paths.append(blob_name)

    # Merge PDFs
    merged_pdf = PdfWriter()
    for blob_name in uploaded_paths:
        blob_client = container_client.get_blob_client(blob_name)
        blob_data = blob_client.download_blob()
        
        # Create a BytesIO object from the downloaded bytes data
        bytes_io = BytesIO(blob_data.readall())

        # Use BytesIO object with PyPDF2
        pdf = PdfReader(bytes_io)
        for page_num in range(len(pdf.pages)):
            page = pdf.pages[page_num]
            merged_pdf.add_page(page)

    # Generate a unique filename for the merged PDF
    merged_blob_name = str(uuid.uuid4()) + '.pdf'
    
    # Save merged PDF to Azure Blob Storage
    merged_blob_client = container_client.get_blob_client(merged_blob_name)
    
    # Create a BytesIO object to store the merged PDF
    merged_pdf_bytes_io = BytesIO()
    merged_pdf.write(merged_pdf_bytes_io)
    
    # Upload the BytesIO object to Azure Blob Storage
    merged_blob_client.upload_blob(merged_pdf_bytes_io.getvalue(), overwrite=True)

    # Delete uploaded files
    for blob_name in uploaded_paths:
        container_client.get_blob_client(blob_name).delete_blob()

    # Provide correct download link
    download_link = url_for('download_merged', filename=merged_blob_name)
    return render_template('index.html', download_link=download_link)

@app.route('/download_merged/<filename>')
def download_merged(filename):
    # Use BytesIO for sending the file
    blob_client = container_client.get_blob_client(filename)
    blob_data = blob_client.download_blob()

    # Generate a timestamp
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

    # Combine the original file name with the timestamp
    download_name = f"{timestamp}.pdf"

    # Set the correct content type
    response = send_file(
        BytesIO(blob_data.readall()),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=download_name  # Set the download name
    )

    return response

if __name__ == '__main__':
    app.run(debug=True)
