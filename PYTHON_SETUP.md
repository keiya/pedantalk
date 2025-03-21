# Python 3.13 Setup Guide for Pedantalk

This project requires specific package versions that are compatible with Python 3.13. Follow these instructions to set up your environment correctly.

## Prerequisites

- Python 3.13
- pip (latest version recommended)
- ffmpeg installed on your system

## Setup Steps

1. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Update pip to the latest version:

```bash
pip install --upgrade pip
```

3. Install dependencies:

```bash
# Option 1: Using make
make install

# Option 2: Manual installation
pip install -r requirements.txt
```

## Troubleshooting

If you encounter build errors with pydantic-core, you can try installing packages individually:

```bash
pip install openai
pip install ffmpeg-python
pip install python-dotenv
pip install typing-extensions
pip install pydantic
pip install mypy pylint flake8 black isort
```

## Running the Application

After successful installation:

```bash
make run
```

Or with specific parameters:

```bash
python -m pedantalk.main --turns 20 --topic "Artificial Intelligence Ethics"
```
