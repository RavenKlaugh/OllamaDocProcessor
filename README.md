# OllamaDocProcessor

A versatile document processing tool that sends text, PDF, and Word documents to Ollama-compatible LLM APIs for analysis, summarization, or transformation.

## Description

OllamaDocProcessor is a command-line utility designed to streamline the processing of multiple document types through large language models. It supports text files, PDFs, and Word documents, automatically handling text extraction and chunking for documents that exceed the model's context window.

The tool is especially useful for:
- Batch processing documents with AI
- Extracting insights from large document collections
- Performing consistent analysis across multiple files
- Working with local LLMs through Ollama

## Features

- Support for multiple document formats (TXT, PDF, DOC, DOCX)
- Automatic text extraction from PDFs and Word documents
- Smart chunking of large documents to fit within model context limits
- Flexible API integration with Ollama-compatible endpoints
- Customizable prompts for different processing tasks
- Consolidated output in a single file

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/OllamaDocProcessor.git
cd OllamaDocProcessor

# Install dependencies
pip install -r requirements.txt
```

## Dependencies

- Python 3.6+
- PyPDF2
- python-docx
- requests

## Usage

```bash
python ollamadocprocessor.py [directory] [prompt] [url] [options]
```

### Required Arguments

- `directory`: Path to the directory containing documents to process
- `prompt`: The prompt to send with each text chunk
- `url`: Ollama API URL (e.g., http://localhost:11434)

### Optional Arguments

- `--api-key`: API key for authentication (if required)
- `--max-words`: Maximum words per chunk (default: 3000)
- `--model`: Ollama model to use (default: deepseek-r1:32b-qwen-distill-q8_0)
- `--temperature`: Temperature for model responses (0.0 to 1.0, default: 0.6)

### Example

```bash
# Process all documents in the "reports" directory
python ollamadocprocessor.py ./reports "Summarize the following text:" http://localhost:11434 --model llama2 --temperature 0.7
```

## Output

All responses are appended to an `out.txt` file in the specified directory, with clear headers indicating which file and chunk each response corresponds to.

## Example Prompts

- **Summarization**: "Summarize the following text in 3-5 bullet points:"
- **Key Insights**: "Extract the key insights from this document:"
- **Translation**: "Translate the following text to Spanish:"
- **Analysis**: "Analyze the sentiment and main themes in this document:"

## Customization

You can modify the `process_text_with_ollama` function to adjust how text is formatted and sent to the API, or extend the program to support additional document types by adding new extraction functions.

## Limitations

- PDF extraction may not preserve complex formatting or tables
- Very large documents may require significant processing time
- Performance depends on the Ollama API endpoint and model used

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
