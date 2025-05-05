import os
import PyPDF2
import logging
from tika import parser

class PDFProcessor:
    def __init__(self, pdf_dir='downloads'):
        self.pdf_dir = pdf_dir
        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir)
        
        logging.basicConfig(filename='pdf_processor.log', level=logging.INFO,
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    def download_pdf(self, url, filename):
        """PDF 파일 다운로드"""
        import requests
        
        try:
            response = requests.get(url)
            filepath = os.path.join(self.pdf_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            logging.info(f"Downloaded PDF: {filename}")
            return filepath
        
        except Exception as e:
            logging.error(f"Error downloading PDF: {e}")
            return None
    
    def extract_text_pypdf2(self, filepath):
        """PyPDF2를 사용한 텍스트 추출 (기본)"""
        try:
            with open(filepath, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    text += page.extract_text() + "\n"
                
            return text
        
        except Exception as e:
            logging.error(f"PyPDF2 extraction error: {e}")
            return ""
    
    def extract_text_tika(self, filepath):
        """Apache Tika를 사용한 텍스트 추출 (향상된 추출)"""
        try:
            raw = parser.from_file(filepath)
            return raw['content'] if 'content' in raw else ""
        
        except Exception as e:
            logging.error(f"Tika extraction error: {e}")
            return ""
    
    def extract_best_text(self, filepath):
        """여러 방법을 시도하여 최상의 텍스트 추출"""
        # 첫 번째 방법 시도
        text = self.extract_text_pypdf2(filepath)
        
        # 결과가 불충분하면 다른 방법 시도
        if len(text.strip()) < 100:
            text = self.extract_text_tika(filepath)
        
        return text
    
    def batch_process_pdfs(self, pdf_links, filenames=None):
        """여러 PDF 파일 일괄 처리"""
        results = []
        
        for i, url in enumerate(pdf_links):
            filename = filenames[i] if filenames and i < len(filenames) else f"report_{i}.pdf"
            
            # PDF 다운로드
            filepath = self.download_pdf(url, filename)
            
            if filepath:
                # 텍스트 추출
                text = self.extract_best_text(filepath)
                
                results.append({
                    'filename': filename,
                    'filepath': filepath,
                    'text': text
                })
                
                logging.info(f"Processed PDF: {filename}")
            
        return results