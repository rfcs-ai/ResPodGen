# Research Paper Podcast Generator

A streamlined tool to convert academic papers in PDF format into engaging podcast-style audio content using AI-powered text generation and speech synthesis.

## Features

- Extracts and summarizes PDF research papers
- Generates natural dialogue scripts between two hosts
- Converts dialogue into realistic audio using Dia TTS
- Produces ready-to-publish podcast MP3 files
- Supports voice conditioning for consistent speaker identity

## Installation

### Prerequisites

- Python 3.9+
- CUDA-compatible GPU (strongly recommended)
- Ollama (for text generation)
- PyTorch with CUDA support

### Installing from GitHub

```bash
# Clone the repository
git clone https://github.com/yourusername/research-paper-podcast.git
cd research-paper-podcast

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with CUDA support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install -e .
```

### Installing Dependencies

```bash
# Install Dia TTS directly from GitHub
pip install git+https://github.com/nari-labs/dia.git
```

## Usage

### Basic Usage

```bash
python -m research_podcast path/to/paper.pdf
```

### Advanced Options

```bash
python -m research_podcast path/to/paper.pdf \
  --model mistral:latest \
  --temperature 0.7 \
  --output-dir outputs \
  --voice-prompts voice_map.json
```

### Voice Conditioning

Create a JSON file mapping speakers to audio samples:

```json
{
  "Julia": "/path/to/female_voice_sample.wav",
  "Guido": "/path/to/male_voice_sample.wav"
}
```

## Configuration

| Option | Description | Default |
|--------|-------------|---------|
| `--model` | Ollama model to use | `mistral:latest` |
| `--temperature` | Temperature for text generation | `0.7` |
| `--output-dir` | Directory for output files | `outputs` |
| `--voice-prompts` | JSON file mapping speakers to WAV files | `None` |
| `--host` | Ollama server host | `localhost` |
| `--port` | Ollama server port | `11434` |

## How It Works

1. **PDF Processing**: Extracts text from research papers
2. **Summarization**: Generates concise summary via Ollama
3. **Dialogue Generation**: Creates conversational script
4. **TTS Synthesis**: Converts text to speech with Dia TTS
5. **Post-processing**: Normalizes audio levels and exports MP3

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## Acknowledgments

- [Dia TTS](https://github.com/nari-labs/dia) for the speech synthesis
- [Ollama](https://ollama.ai/) for the text generation
- [PyMuPDF](https://github.com/pymupdf/PyMuPDF) for PDF processing