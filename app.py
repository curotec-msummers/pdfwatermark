from flask import Flask, request, Response
import io
import PyPDF2
import requests

app = Flask(__name__)

def add_watermark(pdf_bytes, watermark_text):
    pdf = PyPDF2.PdfFileReader(io.BytesIO(pdf_bytes))
    output = PyPDF2.PdfFileWriter()

    for page_num in range(pdf.getNumPages()):
        page = pdf.getPage(page_num)
        page.mergePage(watermark_text)
        output.addPage(page)

    output_pdf_bytes = io.BytesIO()
    output.write(output_pdf_bytes)
    output_pdf_bytes.seek(0)

    return output_pdf_bytes.getvalue()

@app.route('/watermark-pdf', methods=['POST'])
def watermark_pdf():
    try:
        # Get PDF URL and watermark text from the request
        pdf_url = request.form.get('pdf_url')
        watermark_text = request.form.get('watermark_text')

        # Validate inputs
        if not pdf_url or not watermark_text:
            return "Both 'pdf_url' and 'watermark_text' are required.", 400

        # Fetch the PDF file from the provided URL
        response = requests.get(pdf_url)
        if response.status_code != 200:
            return "Failed to fetch the PDF from the provided URL.", 400

        # Create a watermark (as a PyPDF2 object)
        watermark = PyPDF2.PdfFileReader(io.BytesIO(watermark_text.encode()))

        # Add watermark to the PDF
        watermarked_pdf_bytes = add_watermark(response.content, watermark)

        # Create a response with the watermarked PDF
        response = Response(watermarked_pdf_bytes, content_type='application/pdf')
        response.headers['Content-Disposition'] = 'inline; filename=watermarked.pdf'

        return response

    except Exception as e:
        return str(e), 500  # Return an error response if anything goes wrong

if __name__ == '__main__':
    app.run(debug=False)
