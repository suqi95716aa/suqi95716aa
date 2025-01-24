import pypdf
from PIL import Image
import io
import base64

def extract_images_from_page(page):
    """Extract images from a PDF page and return them as a list of base64-encoded strings with data URI prefix."""
    images = []
    if '/XObject' in page['/Resources']:
        xobjects = page['/Resources']['/XObject'].get_object()
        for obj_name in xobjects:
            xobj = xobjects[obj_name]
            if xobj['/Subtype'] == '/Image':
                # Extract image size
                size = (xobj['/Width'], xobj['/Height'])
                data = xobj.get_data()

                # Check the filter type to determine how to decode the data
                if '/Filter' in xobj:
                    filter_type = xobj['/Filter']

                    try:
                        if filter_type == '/DCTDecode':
                            # JPEG
                            img = Image.open(io.BytesIO(data))
                            format = 'JPEG'
                            mime_type = 'image/jpeg'
                        elif filter_type == '/JPXDecode':
                            # JPEG 2000
                            img = Image.open(io.BytesIO(data))
                            format = 'JPEG'
                            mime_type = 'image/jpeg'
                        elif filter_type == '/FlateDecode':
                            # Usually PNG
                            if xobj['/ColorSpace'] == '/DeviceRGB':
                                mode = "RGB"
                            elif xobj['/ColorSpace'] == '/DeviceCMYK':
                                mode = "CMYK"
                            elif xobj['/ColorSpace'] == '/DeviceGray':
                                mode = "L"
                            else:
                                mode = "P"
                            img = Image.frombytes(mode, size, data)
                            format = 'PNG'
                            mime_type = 'image/png'
                        else:
                            print(f"Unsupported filter {filter_type}")
                            continue

                        # Convert the image to a base64 string with data URI prefix
                        buffered = io.BytesIO()
                        img.save(buffered, format=format)
                        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
                        img_str_with_prefix = f"data:{mime_type};base64,{img_str}"
                        images.append(img_str_with_prefix)

                    except Exception as e:
                        print(f"An error occurred while processing image {obj_name}: {e}")
                        continue
                else:
                    print("No filter found, unable to process image")
                    continue
    return images

def extract_images_from_pdf(pdf_path):
    """Extract images from each page of a PDF and return them in a dictionary."""
    reader = pypdf.PdfReader(pdf_path)
    images_dict = {}
    for page_number, page in enumerate(reader.pages):
        images = extract_images_from_page(page)
        images_dict[page_number + 1] = images
    return images_dict

# Example usage
pdf_path = r'C:\Users\Administrator\Desktop\output.pdf'
images_dict = extract_images_from_pdf(pdf_path)

print(images_dict)
# Print the dictionary to see the results
for page, images in images_dict.items():
    print(f"Page {page}: {len(images)} images")
