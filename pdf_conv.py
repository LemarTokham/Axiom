from docling.document_converter import DocumentConverter

class PdfParser:
    def __init__(self):
        self.converter = DocumentConverter()

    def parse_pdf(self, source):
        source = source
        res = self.converter.convert(source) 

        return(res.document.export_to_markdown())