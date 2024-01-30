import subprocess

def reduce_pdf_size(input_path, output_path):

    # Ghostscript command
    gs_command = [
        "gs",
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        "-dPDFSETTINGS=/screen",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-sOutputFile={output_path}",
        input_path
    ]

    # Run the Ghostscript command
    subprocess.run(gs_command, check=True)

if __name__ == "__main__":
    input_pdf_path = "test/Y19-2-merged.pdf"  # Replace with the path to your input PDF file
    output_pdf_path = "test/output_reduced_ghostscript.pdf"  # Replace with the desired output path

    reduce_pdf_size(input_pdf_path, output_pdf_path)
