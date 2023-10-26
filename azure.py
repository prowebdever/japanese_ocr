from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path

import os
import sys
import requests
import shutil
import tempfile

import requests

poppler_path = r"./poppler/Library/bin"  # update this path

def split_pdf_to_pages(pdf_path, output_folder):
    pdf = PdfReader(pdf_path)
    for page in range(len(pdf.pages)):
        pdf_writer = PdfWriter()
        pdf_writer.add_page(pdf.pages[page])

        output_filename = "{}/page_{:03d}.pdf".format(output_folder, page)

        with open(output_filename, 'wb') as out:
            pdf_writer.write(out)

def main():
    args = sys.argv

    args = args[1:]
    if len(args) <= 0:
        print('please execute with parameter(folder path that contains pdf files)')
        sys.exit()

    directory_path = args[0]
    target_path = './ocr'
    
    if os.path.exists(directory_path) == False:
        print('please execute with parameter(folder path that contains pdf files)')
        sys.exit()

    if os.path.exists(target_path):
        shutil.rmtree(target_path)
    os.mkdir(target_path)

    files = os.listdir(directory_path)

    url = "https://portal.vision.cognitive.azure.com/api/demo/analyze?features=read"
    
    for org_file in files:
        try:
            temp_pdf_dir = tempfile.mkdtemp()
            temp_png_dir = tempfile.mkdtemp()

            file_path = os.path.join(directory_path, org_file)

            split_pdf_to_pages(file_path, temp_pdf_dir)

            files = os.listdir(temp_pdf_dir)
            page = 0
            for file in files:
                file_path = os.path.join(temp_pdf_dir, file)
                images = convert_from_path(file_path, dpi=250, poppler_path=poppler_path)
                for i, image in enumerate(images):
                    gray_image = image.convert('L')
                    path = os.path.join(temp_png_dir, 'page{:03d}.png'.format(page))
                    gray_image.save(path, 'PNG')
                    page += 1

            files = os.listdir(temp_png_dir)
            for file in files:
                file_path = os.path.join(temp_png_dir, file)
                with open(file_path, 'rb') as f:
                    post_files=[('file',(file,f,'image/png'))]
                    response = requests.request("POST", url, data={}, files=post_files)
                    if(response.status_code == 200):
                        path = os.path.join(target_path, org_file)
                        with open(path, 'w', encoding='utf-8-sig') as f:
                            f.write(response.text)
                    else:
                        print(response.status_code, org_file)

            shutil.rmtree(temp_pdf_dir)
            shutil.rmtree(temp_png_dir)

        except Exception as err:
            print('Error:', err)

if __name__ == "__main__":
    main()
