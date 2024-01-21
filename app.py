from flask import Flask, render_template, request, redirect, url_for
from PyPDF2 import PdfReader, PdfWriter
from azure.storage.blob import BlobServiceClient, ContainerClient
from io import BytesIO

from merge import merge_pdfs, download_pdf
from splitter import split_pdfs, download_pdfs

from dotenv import load_dotenv
import os

load_dotenv()
key_string = os.getenv("key_string")

app = Flask(__name__)
app.config["AZURE_STORAGE_CONNECTION_STRING"] = key_string
app.config["AZURE_CONTAINER_NAME"] = "uploads"
app.config["AZURE_MERGED_FOLDER"] = "merged"

# Initialize Azure Blob Service
blob_service_client = BlobServiceClient.from_connection_string(
    app.config["AZURE_STORAGE_CONNECTION_STRING"]
)
container_client = blob_service_client.get_container_client(
    app.config["AZURE_CONTAINER_NAME"]
)

if not container_client.exists():
    container_client.create_container()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/merge", methods=["GET"])
def merge_page():
    return render_template("mergit.html")


@app.route("/add", methods=["POST"])
def merge():
    merged_blob_name = merge_pdfs(container_client)
    # Provide correct download link
    download_link = url_for("download_merged", filename=merged_blob_name)
    return render_template("mergit.html", download_link=download_link)


@app.route("/download_merged/<filename>")
def download_merged(filename):
    return download_pdf(container_client, filename)


@app.route("/split", methods=["GET"])
def split_page():
    return render_template("split.html")


@app.route("/break", methods=["GET", "POST"])
def split():
    split_blob_name = split_pdfs(container_client)
    # Provide correct download link
    download_link = url_for("download_splitted", filename=split_blob_name)
    return render_template("split.html", download_link=download_link)


@app.route("/download_split/<filename>")
def download_splitted(filename):
    return download_pdfs(container_client, filename)


if __name__ == "__main__":
    app.run(debug=True)
