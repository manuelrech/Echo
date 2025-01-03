# Echo 🐦

A tool that reads your newsletter subscriptions through Gmail, extracts the key concepts, and helps you generate Twitter content from them.

![Demo Video](media/demo720.gif)

## What is Echo?

Echo connects to your Gmail account to process newsletter emails. It:

1. Fetches newsletters and extracts meaningful concepts using LLMs
2. Stores and organizes these concepts, removing duplicates
3. Generates tweets or threads based on the extracted content

## Features

- 📧 **Smart Email Processing**
  - Gmail API integration for newsletter fetching
  - Automatic concept extraction using gpt-4o or deepseek-v3
  - Duplicate detection with semantic similarity checking

- 🧠 **Advanced Content Generation**
  - Support for multiple LLM models (OpenAI, DeepSeek)
  - Single tweet and thread generation
  - Context enhancement with similar concepts (using semantic similarity)
  - Custom instruction support

- 💫 **Modern Web Interface**
  - Built with Streamlit
  - Real-time content preview
  - Responsive design
  - Easy-to-use concept management

## Getting Started

### Prerequisites

1. Python 3.8 or higher
2. Google Cloud Platform account
3. OpenAI API key (or DeepSeek API key)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Echo.git
cd Echo
```

2. Create and activate a virtual environment:
```bash
python3 -m venv .venv_echo
source .venv_echo/bin/activate  # On Windows use: .venv_echo\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up Google Cloud Platform:
   - Create a new project in [Google Cloud Console](https://console.cloud.google.com)
   - Enable the Gmail API
   - Create OAuth 2.0 credentials
   - Download the credentials and save as `credentials.json` in the root directory

### Running the App

```bash
streamlit run Echo.py
```

Visit `http://localhost:8501` in your browser to start using Echo!

## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Connect & Support

- Follow me on Twitter/X: [@RechManuel](https://x.com/RechManuel)
- ⭐ Star this repo if you find it helpful!
- 🐛 Report bugs by opening an issue
- 💡 Request features through issues
- 🤝 Contribute to make Echo even better
