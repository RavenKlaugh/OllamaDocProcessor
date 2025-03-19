import os
import re
import requests
import json
from pathlib import Path
from typing import Iterator
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import PyPDF2
import docx

# --------------------------
# Document Processing Functions
# --------------------------
def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a PDF file."""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
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

def extract_text_from_file(file_path: Path) -> str:
    """Extract text from different file types based on extension."""
    file_extension = file_path.suffix.lower()
    
    if file_extension == '.txt':
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
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

# --------------------------
# Tkinter GUI and Integration
# --------------------------
class DocumentProcessorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Document Chunk & Inference Processor")
        
        # Interrupt flag and thread
        self.stop_processing = False
        self.processing_thread = None
        
        # Directory selection
        self.dir_label = tk.Label(root, text="Select Directory:")
        self.dir_label.pack(pady=(10, 0))
        self.dir_frame = tk.Frame(root)
        self.dir_frame.pack(pady=5)
        self.directory_var = tk.StringVar()
        self.dir_entry = tk.Entry(self.dir_frame, textvariable=self.directory_var, width=50)
        self.dir_entry.pack(side=tk.LEFT, padx=5)
        self.browse_button = tk.Button(self.dir_frame, text="Browse...", command=self.select_directory)
        self.browse_button.pack(side=tk.LEFT)
        
        # Prompt input
        self.prompt_label = tk.Label(root, text="Enter Prompt:")
        self.prompt_label.pack(pady=(10, 0))
        self.prompt_text = tk.Text(root, height=4, width=60)
        self.prompt_text.pack(pady=5)
        
        # Additional parameters frame
        self.params_frame = tk.Frame(root)
        self.params_frame.pack(pady=5)
        
        # Max words
        tk.Label(self.params_frame, text="Max Words:").grid(row=0, column=0, sticky="e")
        self.max_words_var = tk.StringVar(value="3000")
        self.max_words_entry = tk.Entry(self.params_frame, textvariable=self.max_words_var, width=10)
        self.max_words_entry.grid(row=0, column=1, padx=5)
        
        # Model
        tk.Label(self.params_frame, text="Model:").grid(row=0, column=2, sticky="e")
        self.model_var = tk.StringVar(value="gemma3:27b-it-q8_0")
        self.model_entry = tk.Entry(self.params_frame, textvariable=self.model_var, width=20)
        self.model_entry.grid(row=0, column=3, padx=5)
        
        # API URL
        tk.Label(self.params_frame, text="API URL:").grid(row=1, column=0, sticky="e")
        self.api_url_var = tk.StringVar(value="http://10.0.128.168:11434")
        self.api_url_entry = tk.Entry(self.params_frame, textvariable=self.api_url_var, width=30)
        self.api_url_entry.grid(row=1, column=1, columnspan=3, padx=5, pady=5)
        
        # Start and Stop buttons frame
        self.buttons_frame = tk.Frame(root)
        self.buttons_frame.pack(pady=10)
        self.start_button = tk.Button(self.buttons_frame, text="Start Processing", command=self.start_processing)
        self.start_button.pack(side=tk.LEFT, padx=5)
        self.stop_button = tk.Button(self.buttons_frame, text="Stop Processing", command=self.stop_processing_func, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Output display
        self.output_label = tk.Label(root, text="Output:")
        self.output_label.pack(pady=(10, 0))
        self.output_text = scrolledtext.ScrolledText(root, height=15, width=60)
        self.output_text.pack(pady=5)
        
        # Parameters for processing
        self.temperature = 0.6
        self.api_key = None  # Add support for an API key if needed
        
    def select_directory(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.directory_var.set(folder_selected)
    
    def start_processing(self):
        target_dir = self.directory_var.get()
        prompt = self.prompt_text.get("1.0", tk.END).strip()
        try:
            max_words = int(self.max_words_var.get())
        except ValueError:
            messagebox.showerror("Input Error", "Max Words must be an integer.")
            return
        
        model = self.model_var.get()
        api_url = self.api_url_var.get()
        
        if not target_dir or not prompt or not model or not api_url:
            messagebox.showerror("Input Error", "Please fill in all required fields.")
            return
        
        # Reset interrupt flag
        self.stop_processing = False
        
        # Disable start button and enable stop button
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # Clear output
        self.output_text.delete("1.0", tk.END)
        
        # Create or clear output file
        output_file = Path(target_dir) / 'out.txt'
        output_file.touch(exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("")
        
        # Run processing in a separate thread to keep the GUI responsive
        self.processing_thread = threading.Thread(target=self.process_documents, args=(target_dir, prompt, max_words, model, api_url))
        self.processing_thread.start()
    
    def stop_processing_func(self):
        self.stop_processing = True
        self.output_text.insert(tk.END, "\nStop requested. Finishing current task...\n")
    
    def process_documents(self, target_dir, prompt, max_words, model, api_url):
        output_file = Path(target_dir) / 'out.txt'
        for file_path in Path(target_dir).glob('*.*'):
            # Check if process was interrupted
            if self.stop_processing:
                self.output_text.insert(tk.END, "Processing interrupted by user.\n")
                break
            
            if (file_path.suffix.lower() in ['.txt', '.pdf', '.doc', '.docx'] and 
                file_path.name != 'out.txt'):
                self.output_text.insert(tk.END, f"\nProcessing file: {file_path}\n")
                self.output_text.see(tk.END)
                
                try:
                    text = extract_text_from_file(file_path)
                    if not text:
                        self.output_text.insert(tk.END, f"No text extracted from {file_path}. Skipping.\n")
                        continue
                    
                    # Clean and normalize whitespace
                    text = re.sub(r'\s+', ' ', text).strip()
                    
                    word_count = len(text.split())
                    if word_count <= max_words:
                        response = process_text_with_ollama(
                            text, prompt, api_url, model, self.temperature, self.api_key
                        )
                        self.output_text.insert(tk.END, f"Response for {file_path.name}:\n{response}\n")
                        with open(output_file, 'a', encoding='utf-8') as f:
                            f.write(f"\n\n=== Response for {file_path.name} ===\n")
                            f.write(response)
                    else:
                        for i, chunk in enumerate(chunk_text(text, max_words), 1):
                            if self.stop_processing:
                                self.output_text.insert(tk.END, "Processing interrupted by user.\n")
                                break
                            response = process_text_with_ollama(
                                chunk, prompt, api_url, model, self.temperature, self.api_key
                            )
                            self.output_text.insert(tk.END, f"Response for {file_path.name} (chunk {i}):\n{response}\n")
                            with open(output_file, 'a', encoding='utf-8') as f:
                                f.write(f"\n\n=== Response for {file_path.name} (chunk {i}) ===\n")
                                f.write(response)
                except Exception as e:
                    error_msg = f"Error processing {file_path}: {str(e)}\n"
                    self.output_text.insert(tk.END, error_msg)
                    print(error_msg)
                    
        self.output_text.insert(tk.END, "\nProcessing complete.\n")
        # Re-enable start button and disable stop button after processing is done
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = DocumentProcessorGUI(root)
    root.mainloop()
