from PyPDF2 import PdfReader, PdfWriter
from azure.storage.blob import BlobServiceClient, ContainerClient
from io import BytesIO
from flask import request, send_file


def merge_pdfs(container_client):
    # Get uploaded files
    pdf_files = request.files.getlist("pdf_files")
    mergedFileName = request.form.get("fileName")

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
    merged_blob_name = mergedFileName + ".pdf"


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


def download_pdf(container_client, merged_blob_name):
    # Use BytesIO for sending the file
    blob_client = container_client.get_blob_client(merged_blob_name)
    blob_data = blob_client.download_blob()

    # Set the correct content type
    response = send_file(
        BytesIO(blob_data.readall()),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=merged_blob_name,  # Set the download name
    )

    return response
