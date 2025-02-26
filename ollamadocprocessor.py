import os
import argparse
import requests
import json
from pathlib import Path
from typing import List, Iterator
import PyPDF2
import docx
import re

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a PDF file."""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error extracting text from PDF {pdf_path}: {str(e)}")
        return ""
    return text

def extract_text_from_docx(docx_path: str) -> str:
    """Extract text from a Word document."""
    text = ""
    try:
        doc = docx.Document(docx_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        print(f"Error extracting text from Word document {docx_path}: {str(e)}")
        return ""
    return text

def chunk_text(text: str, max_words: int) -> Iterator[str]:
    """Split text into chunks of maximum word count."""
    words = text.split()
    current_chunk = []
    current_count = 0
    
    for word in words:
        current_chunk.append(word)
        current_count += 1
        
        if current_count >= max_words:
            yield ' '.join(current_chunk)
            current_chunk = []
            current_count = 0
    
    if current_chunk:
        yield ' '.join(current_chunk)

def process_text_with_ollama(text: str, prompt: str, url: str, model: str, temperature: float, api_key: str = None) -> str:
    """Submit text to Ollama API and return the response."""
    headers = {
        'Content-Type': 'application/json'
    }
    
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'
    
    data = {
        'model': model,
        'prompt': f"{prompt}\n\nText: {text}",
        'stream': False,
        'temperature': temperature,
        'options': {
            "num_ctx": 20480
        }
    }
    
    try:
        response = requests.post(f"{url}/api/generate", headers=headers, json=data)
        response.raise_for_status()
        return response.json()['response']
    except requests.exceptions.RequestException as e:
        return f"Error processing chunk: {str(e)}"

def extract_text_from_file(file_path: Path) -> str:
    """Extract text from different file types based on extension."""
    file_extension = file_path.suffix.lower()
    
    if file_extension == '.txt':
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try another encoding if UTF-8 fails
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception as e:
                print(f"Error reading text file {file_path}: {str(e)}")
                return ""
    elif file_extension == '.pdf':
        return extract_text_from_pdf(str(file_path))
    elif file_extension in ['.docx', '.doc']:
        return extract_text_from_docx(str(file_path))
    else:
        print(f"Unsupported file type: {file_extension}")
        return ""
    
def main():
    parser = argparse.ArgumentParser(description='Process text, PDF, and Word files with Ollama')
    parser.add_argument('directory', help='Directory containing document files')
    parser.add_argument('prompt', help='Prompt to send with each text chunk')
    parser.add_argument('url', help='Ollama API URL')
    parser.add_argument('--api-key', help='API key for authentication')
    parser.add_argument('--max-words', type=int, default=3000,
                       help='Maximum words per chunk (default: 3000)')
    parser.add_argument('--model', default='deepseek-r1:32b-qwen-distill-q8_0',
                       help='Ollama model to use (default: deepseek-r1:32b-qwen-distill-q8_0)')
    parser.add_argument('--temperature', type=float, default=0.6,
                       help='Temperature for model responses (0.0 to 1.0, default: 0.6)')
    
    args = parser.parse_args()
    
    # Ensure output file exists
    output_file = Path(args.directory) / 'out.txt'
    output_file.touch(exist_ok=True)
    
    # Process each supported file in the directory
    for file_path in Path(args.directory).glob('*.*'):
        # Check if file is of supported type and not the output file
        if (file_path.suffix.lower() in ['.txt', '.pdf', '.doc', '.docx'] and 
            file_path.name != 'out.txt'):
                
            print(f"\nProcessing file: {file_path}")
            
            try:
                # Extract text based on file type
                text = extract_text_from_file(file_path)
                
                if not text:
                    print(f"No text extracted from {file_path}. Skipping.")
                    continue
                
                # Clean and normalize whitespace
                text = re.sub(r'\s+', ' ', text).strip()
                
                # If file is smaller than max_words, process it as a single chunk
                word_count = len(text.split())
                if word_count <= args.max_words:
                    response = process_text_with_ollama(
                        text, args.prompt, args.url, args.model, args.temperature, args.api_key
                    )
                    
                    print(f"\nResponse for {file_path.name}:")
                    print(response)
                    
                    with open(output_file, 'a', encoding='utf-8') as f:
                        f.write(f"\n\n=== Response for {file_path.name} ===\n")
                        f.write(response)
                        
                else:
                    # Process file in chunks
                    for i, chunk in enumerate(chunk_text(text, args.max_words), 1):
                        response = process_text_with_ollama(
                            chunk, args.prompt, args.url, args.model, args.temperature, args.api_key
                        )
                        
                        print(f"\nResponse for {file_path.name} (chunk {i}):")
                        print(response)
                        
                        with open(output_file, 'a', encoding='utf-8') as f:
                            f.write(f"\n\n=== Response for {file_path.name} (chunk {i}) ===\n")
                            f.write(response)
                            
            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")

if __name__ == "__main__":
    main()
