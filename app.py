from flask import Flask, request
from flask_restful import Api, Resource, reqparse, abort
import io
import PyPDF2
import requests

app = Flask(__name__)
api = Api(app)

# Define a dictionary to store valid API keys (you should securely manage these keys)
api_keys = {"f5762a00-1a5c-4ac2-aa97-2447492b05cf": "d0cb8e72-88c5-4c11-a074-443761fcb51a"}

def create_watermark_file(watermark_text):
    # Create a PDF object
    pdf = PyPDF2.PdfFileWriter()

    # Create a new page
    page = PyPDF2.pdf.PageObject.createBlankPage()

    # Create a PDF font
    font = PyPDF2.pdf.ContentStream()
    font.add(PyPDF2.pdf.Tj(watermark_text))

    # Add the font to the page
    page._pushObject(font)
    page._compressContentStreams()

    # Add the page to the PDF
    pdf.addPage(page)

    # Save the PDF to the in-memory buffer
    pdf.write(output_pdf)

    # Reset the buffer pointer to the beginning
    output_pdf.seek(0)
    
    return output_pdf

def validate_api_key(api_key):
    return api_keys.get(api_key) is not None

def add_watermark(pdf_bytes, watermark_text):
    pdf = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
    output = PyPDF2.PdfWriter()

    for page_num in range(pdf.getNumPages()):
        page = pdf.getPage(page_num)
        page.mergePage(create_watermark_file(watermark_text))
        output.addPage(page)

    output_pdf_bytes = io.BytesIO()
    output.write(output_pdf_bytes)
    output_pdf_bytes.seek(0)

    return output_pdf_bytes.getvalue()

class WatermarkPDFResource(Resource):
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('api_key', type=str, required=True, help='API Key is required')
            parser.add_argument('pdf_url', type=str, required=True, help='PDF URL is required')
            parser.add_argument('watermark_text', type=str, required=True, help='Watermark text is required')
            args = parser.parse_args()

            # Validate the API key
            if not validate_api_key(args['api_key']):
                abort(401, message='Invalid API Key')

            # Fetch the PDF file from the provided URL
            response = requests.get(args['pdf_url'])
            if response.status_code != 200:
                abort(400, message='Failed to fetch the PDF from the provided URL')

            # Create a watermark (as a PyPDF2 object)
            watermark = PyPDF2.PdfFileReader(io.BytesIO(args['watermark_text'].encode()))

            # Add watermark to the PDF
            watermarked_pdf_bytes = add_watermark(response.content, watermark)

            return {'watermarked_pdf': watermarked_pdf_bytes.decode('latin1')}

        except Exception as e:
            abort(500, message=str(e))

api.add_resource(WatermarkPDFResource, '/watermark-pdf')

if __name__ == '__main__':
    app.run(debug=False)
