import base64
import io
from io import BytesIO
from pathlib import Path
from typing import Iterator, Dict, Union, List, Any

from PIL import Image

from service.ragfusion.core.document.document import Document
from service.ragfusion.core.loader.unstructured import UnstructuredFileLoader


class PyPDFLoader(UnstructuredFileLoader):
    """Load `PDF` files using `pypdf`.

    You can run the loader in one of two modes: "single" and "elements" and "paged".
    If you use "single" mode, the document will be returned as a single
    ragfusion Document object. If you use "elements" mode, the unstructured
    library will split the document into elements such as Title and NarrativeText.
    You can pass in additional unstructured kwargs after mode to apply
    different unstructured settings.

    Examples
    --------
    from ragfusion.document_loaders import PyPDFLoader

    loader = PyPDFLoader(
        "example.pdf", mode="elements", strategy="fast",
    )
    docs = loader.load()

    References
    ----------
    https://unstructured-io.github.io/unstructured/bricks.html#partition-pdf
    """

    def __init__(
        self,
        file_or_buffer: Union[str, List[str], Path, List[Path], None, BytesIO],
        mode: str = "single",
        extract_img_flag: bool = True,
        **unstructured_kwargs: Any,
    ):
        self.extract_img_flag = extract_img_flag
        super().__init__(file_or_buffer, mode, **unstructured_kwargs)

    def _get_elements(self) -> Dict:
        import pypdf
        reader = pypdf.PdfReader(self.file_or_buffer)
        ret = dict()
        for ind, page in enumerate(reader.pages):
            ret[ind] = page.extract_text()
        return ret

    def _get_images(self) -> Dict:
        """
        Extract images from page

        :return:
            `Dict`, {page_num: [Image]}
        """
        def _extract_images_from_page(page):
            images = []
            if '/XObject' not in page['/Resources']: return images
            xobjects = page['/Resources']['/XObject'].get_object()
            for obj_name in xobjects:
                xobj = xobjects[obj_name]
                if xobj['/Subtype'] != '/Image': continue

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
                        images.append(img_str)

                    except Exception as e:
                        print(f"An error occurred while processing image {obj_name}: {e}")
                        continue
                else:
                    print("No filter found, unable to process image")
                    continue
            return images

        import pypdf
        reader = pypdf.PdfReader(self.file_or_buffer)
        ret = {
            ind: _extract_images_from_page(page)
            for ind, page in enumerate(reader.pages)
        }
        return ret

    def lazy_load(self) -> Iterator[Document]:
        """Load file."""
        elements = self._get_elements()
        if self.mode == "elements":
            for k, element in elements.items():
                metadata = self._get_metadata()
                # NOTE(MthwRobinson) - the attribute check is for backward compatibility
                # with unstructured<0.4.9. The metadata attributed was added in 0.4.9.
                if hasattr(element, "metadata"):
                    metadata.update(element.metadata.to_dict())
                if hasattr(element, "category"):
                    metadata["category"] = element.category
                yield Document(page_content=str(element), metadata=metadata)

        elif self.mode == "paged":
            images = {}
            # Extract image by page
            if self.extract_img_flag:
                images = self._get_images()

            # Convert the dict to a list of Document objects
            for k, element in elements.items():
                metadata = self._get_metadata()
                metadata.update({"page_num": k+1, "images": images.get(k, [])})
                yield Document(page_content=element, metadata=metadata)

        elif self.mode == "single":
            metadata = self._get_metadata()
            text = "\n\n".join([str(content) for k, content in elements.items()])
            yield Document(page_content=text, metadata=metadata)

        else:
            raise ValueError(f"mode of {self.mode} not supported.")
