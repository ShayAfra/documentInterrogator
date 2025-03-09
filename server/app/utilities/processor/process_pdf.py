from langchain_community.document_loaders.parsers.pdf import PDFPlumberParser
from langchain_community.document_loaders import Blob

class PDFProcessor:
    def __init__(self, file_name, file_contents):
        self.file_name = file_name
        self.file_contents = file_contents
        self.parser = PDFPlumberParser()

    def process(self):
        blob = Blob.from_data(self.file_contents, metadata={"source": self.file_name})
        return self.parser.parse(blob)

    