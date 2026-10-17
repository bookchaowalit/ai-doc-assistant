"""
Document Processor — Extract text from PDFs and DOCX, chunk into segments
"""
import pypdf
from docx import Document
from typing import List, Dict
import re


class DocumentProcessor:
    """Process documents: extract text and chunk into segments"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def process(self, file_path: str, filename: str) -> Dict:
        """Process a document file and return chunks"""
        # Extract text based on file type
        if filename.lower().endswith('.pdf'):
            text = self._extract_pdf(file_path)
        elif filename.lower().endswith('.docx'):
            text = self._extract_docx(file_path)
        elif filename.lower().endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        else:
            raise ValueError(f"Unsupported file type: {filename}")
        
        # Chunk the text
        chunks = self._chunk_text(text, filename)
        
        return {
            "filename": filename,
            "text": text,
            "chunks": chunks,
            "total_chunks": len(chunks)
        }
    
    def _extract_pdf(self, file_path: str) -> str:
        """Extract text from PDF"""
        text = ""
        with open(file_path, 'rb') as f:
            reader = pypdf.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    
    def _extract_docx(self, file_path: str) -> str:
        """Extract text from DOCX"""
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    
    def _chunk_text(self, text: str, filename: str) -> List[Dict]:
        """Split text into overlapping chunks"""
        # Clean text
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Split into chunks
        chunks = []
        start = 0
        chunk_id = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence ending in the last 100 chars
                last_sentence = text[max(start, end-100):end]
                for punct in ['. ', '? ', '! ', '\n']:
                    pos = last_sentence.rfind(punct)
                    if pos > 0:
                        end = max(start, end-100) + pos + 1
                        break
            
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunks.append({
                    "id": f"{filename}_chunk_{chunk_id}",
                    "text": chunk_text,
                    "metadata": {
                        "source": filename,
                        "chunk_id": chunk_id,
                        "start_char": start,
                        "end_char": end
                    }
                })
                chunk_id += 1
            
            # Move to next chunk with overlap
            start = end - self.chunk_overlap
        
        return chunks
