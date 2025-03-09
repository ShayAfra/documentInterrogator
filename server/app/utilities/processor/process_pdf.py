from langchain_community.document_loaders.parsers.pdf import PDFPlumberParser
from langchain_community.document_loaders import Blob

class PDFProcessor:
    def __init__(self, file_contents):
        self.file_contents = file_contents
        self.parser = PDFPlumberParser()

    def process(self):
        blob = Blob.from_data(self.file_contents)
        return self.parser.parse(blob)

    