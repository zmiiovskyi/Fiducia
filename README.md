# Fiducia

A Flask-based web application for audio analysis and processing.

## Features

- Audio file upload and processing
- Audio transcription using OpenAI Whisper
- Text analysis capabilities
- Web-based user interface

## Requirements

- Python 3.7+
- Flask
- OpenAI Whisper
- PyTorch
- Gunicorn

## Installation

1. Clone the repository:
```bash
git clone https://github.com/zmiiovskyi/Fiducia.git
cd Fiducia
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Development
Run the application in development mode:
```bash
python app.py
```

## Project Structure

```
Fiducia/
├── analysis/          # Analysis modules
├── static/           # Static files (CSS, JS, images)
├── templates/        # HTML templates
├── uploads/          # Uploaded files directory
├── app.py           # Main application file
├── config.py        # Configuration settings
└── requirements.txt # Python dependencies
```
