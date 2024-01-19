from PyPDF2 import PdfReader, PdfWriter
from azure.storage.blob import BlobServiceClient, ContainerClient
from io import BytesIO
import uuid
import datetime
from flask import request, send_file


def split_pdfs(container_client):
    # Get uploaded files and splittig range
    pdf_file = request.files.get("pdf_file")
    upper_val = request.form.get("upper")
    lower_val = request.form.get("lower")
    # Save uploaded files to Azure Blob Storage
    uploaded_paths = []

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
        while upper_val <= lower_val:
            page = pdf.pages[upper_val]
            merged_pdf.add_page(page)
            upper_val += 1

    # Generate a unique filename for the merged PDF
    merged_blob_name = str(uuid.uuid4()) + ".pdf"

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

    return merged_blob_name


def download_pdfs(container_client, filename):
    # Use BytesIO for sending the file
    blob_client = container_client.get_blob_client(filename)
    blob_data = blob_client.download_blob()

    # Generate a timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    # Combine the original file name with the timestamp
    download_name = f"{timestamp}.pdf"

    # Set the correct content type
    response = send_file(
        BytesIO(blob_data.readall()),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=download_name,  # Set the download name
    )

    return response
