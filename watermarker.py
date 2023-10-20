from PyPDF4 import PdfFileReader, PdfFileWriter
from PyPDF4.pdf import ContentStream
from PyPDF4.generic import TextStringObject, NameObject
from PyPDF4.utils import b_
import os
import argparse
from io import BytesIO
from typing import Tuple
# Import the reportlab library
from reportlab.pdfgen import canvas
# The size of the page supposedly A4
from reportlab.lib.pagesizes import A4
# The color of the watermark
from reportlab.lib import colors

PAGESIZE = A4
FONTNAME = 'Helvetica-Oblique'
FONTSIZE = 23
COLOR = (247, 247, 247)
X = 100
Y = 10
ROTATION_ANGLE = 90


def get_output_file(input_file: str, output_file: str):
    """
    Check whether a temporary output file is needed or not
    """
    input_path = os.path.dirname(input_file)
    input_filename = os.path.basename(input_file)
    # If output file is empty -> generate a temporary output file
    # If output file is equal to input_file -> generate a temporary output file
    if not output_file or input_file == output_file:
        tmp_file = os.path.join(input_path, 'tmp_' + input_filename)
        return True, tmp_file
    return False, output_file


def create_watermark(wm_text: str):
    """
    Creates a watermark template.
    """
    if wm_text:
        # Generate the output to a memory buffer
        output_buffer = BytesIO()
        # Default Page Size = A4
        c = canvas.Canvas(output_buffer, pagesize=PAGESIZE)
        # Set the size and type of the font
        c.setFont(FONTNAME, FONTSIZE)
        c.setFillColor(COLOR)
        c.rotate(ROTATION_ANGLE)
        c.drawString(X, Y, wm_text)
        c.save()
        return True, output_buffer
    return False, None

def save_watermark(wm_buffer, output_file):
    """
    Saves the generated watermark template to disk
    """
    with open(output_file, mode='wb') as f:
        f.write(wm_buffer.getbuffer())
    f.close()
    return True

def watermark_pdf(input_file: str, wm_text: str, pages: Tuple = None):
    """
    Adds watermark to a pdf file.
    """
    result, wm_buffer = create_watermark(wm_text)
    if result:
        wm_reader = PdfFileReader(wm_buffer)
        pdf_reader = PdfFileReader(open(input_file, 'rb'), strict=False)
        pdf_writer = PdfFileWriter()
        try:
            for page in range(pdf_reader.getNumPages()):
                # If required to watermark specific pages not all the document pages
                if pages:
                    if str(page) not in pages:
                        continue
                page = pdf_reader.getPage(page)
                page.mergePage(wm_reader.getPage(0))
                pdf_writer.addPage(page)
        except Exception as e:
            print("Exception = ", e)
            return False, None, None

        return True, pdf_reader, pdf_writer

def watermark_unwatermark_file(**kwargs):
    input_file = kwargs.get('input_file')
    wm_text = kwargs.get('wm_text')
    action = kwargs.get('action')
    mode = kwargs.get('mode')
    pages = kwargs.get('pages')
    temporary, output_file = get_output_file(
        input_file, kwargs.get('output_file'))
    if action == "watermark":
        result, pdf_reader, pdf_writer = watermark_pdf(
            input_file=input_file, wm_text=wm_text, pages=pages)
    
    # Completed successfully
    if result:
        # Generate to memory
        if mode == "RAM":
            output_buffer = BytesIO()
            pdf_writer.write(output_buffer)
            pdf_reader.stream.close()
            # No need to create a temporary file in RAM Mode
            if temporary:
                output_file = input_file
            with open(output_file, mode='wb') as f:
                f.write(output_buffer.getbuffer())
            f.close()
        elif mode == "HDD":
            # Generate to a new file on the hard disk
            with open(output_file, 'wb') as pdf_output_file:
                pdf_writer.write(pdf_output_file)
            pdf_output_file.close()

            pdf_reader.stream.close()
            if temporary:
                if os.path.isfile(input_file):
                    os.replace(output_file, input_file)
                output_file = input_file
