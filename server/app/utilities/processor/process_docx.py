#! /usr/bin/env python

import re
import xml.etree.ElementTree as ET
import zipfile
import os
import io

class DocxProcessor:
    def __init__(self, file_contents, img_dir=None):
        self.file_contents = file_contents
        self.img_dir = img_dir

        self.nsmap = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}


    def qn(self, tag):
        """
        Stands for 'qualified name', a utility function to turn a namespace
        prefixed tag name into a Clark-notation qualified tag name for lxml. For
        example, ``qn('p:cSld')`` returns ``'{http://schemas.../main}cSld'``.
        Source: https://github.com/python-openxml/python-docx/
        """
        prefix, tagroot = tag.split(':')
        uri = self.nsmap[prefix]
        return '{{{}}}{}'.format(uri, tagroot)


    def xml2text(self, xml):
        """
        A string representing the textual content of this run, with content
        child elements like ``<w:tab/>`` translated to their Python
        equivalent.
        Adapted from: https://github.com/python-openxml/python-docx/
        """
        text = u''
        root = ET.fromstring(xml)
        for child in root.iter():
            if child.tag == self.qn('w:t'):
                t_text = child.text
                text += t_text if t_text is not None else ''
            elif child.tag == self.qn('w:tab'):
                text += '\t'
            elif child.tag in (self.qn('w:br'), self.qn('w:cr')):
                text += '\n'
            elif child.tag == self.qn("w:p"):
                text += '\n\n'
        return text


    def process(self):
        text = u''
        docx = io.BytesIO(self.file_contents)

        # Now, whether docx is a file path or a file-like object, it works.
        zipf = zipfile.ZipFile(docx)
        filelist = zipf.namelist()

        # Process headers
        header_xmls = 'word/header[0-9]*.xml'
        for fname in filelist:
            if re.match(header_xmls, fname):
                text += self.xml2text(zipf.read(fname))

        # Process main document
        doc_xml = 'word/document.xml'
        text += self.xml2text(zipf.read(doc_xml))

        # Process footers
        footer_xmls = 'word/footer[0-9]*.xml'
        for fname in filelist:
            if re.match(footer_xmls, fname):
                text += self.xml2text(zipf.read(fname))

        zipf.close()
        return text.strip()
