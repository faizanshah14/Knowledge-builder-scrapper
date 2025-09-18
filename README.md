# 🍎 Knowledge Builder

A powerful web scraper and knowledge base system that extracts technical content from websites and enables intelligent Q&A using Claude AI. Built with Apple-level quality and designed for scalability.

## ✨ Features

- **🌐 Universal Web Scraping**: Works with any website without custom code
- **🤖 AI-Powered Q&A**: Ask questions about scraped content using Claude 3.5
- **📊 Smart Content Extraction**: Converts HTML to clean markdown
- **🔍 Intelligent URL Discovery**: Finds relevant pages via sitemaps, RSS feeds, and crawling
- **💾 Persistent Storage**: Saves scraped data and builds searchable indices
- **🎨 Beautiful UI**: Clean, Apple-inspired Streamlit interface
- **🐳 Docker Ready**: Easy deployment with Docker Compose
- **⚡ High Performance**: Concurrent processing and efficient indexing

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Claude API key from [Anthropic](https://console.anthropic.com/)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/knowledge-builder.git
   cd knowledge-builder
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env and add your ANTHROPIC_API_KEY
   ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

6. **Open your browser**
   Navigate to `http://localhost:8501`

## 🐳 Docker Deployment

### Quick Start with Docker

```bash
# Set your API key
export ANTHROPIC_API_KEY=your_api_key_here

# Run with Docker Compose
docker compose up --build

# Access at http://localhost:8501
```

### Manual Docker Build

```bash
# Build the image
docker build -t knowledge-builder .

# Run the container
docker run -p 8501:8501 \
  -e ANTHROPIC_API_KEY=your_key_here \
  -v $(pwd)/outputs:/app/outputs \
  -v $(pwd)/.index_cache:/app/.index_cache \
  knowledge-builder
```

## 📖 Usage

### Web Interface

1. **Enter a URL**: Input any website or blog URL
2. **Configure Settings**: Adjust max pages, concurrency, and patterns
3. **Scrape & Index**: Click to extract content and build search index
4. **Ask Questions**: Query the scraped content with natural language
5. **Manage Data**: Download files, view previous searches, rebuild indices

### Command Line Interface

```bash
# Scrape a website
python -m scrapper.cli https://example.com/blog --max-pages 100 --output data.json

# Build search index
python -m scrapper.qa_cli index data.json

# Ask questions
python -m scrapper.qa_cli ask "What are the main topics covered?"
```

## 🏗️ Architecture

### Core Components

- **`scrapper/crawler.py`**: URL discovery and web crawling
- **`scrapper/extractor.py`**: HTML to markdown conversion
- **`scrapper/indexer.py`**: FAISS vector index creation
- **`scrapper/qa_agent.py`**: Claude AI integration for Q&A
- **`app.py`**: Streamlit web interface

### Data Flow

1. **Discovery**: Find URLs via sitemaps, RSS feeds, and BFS crawling
2. **Extraction**: Convert HTML content to clean markdown
3. **Indexing**: Create searchable vector embeddings with FAISS
4. **Querying**: Use Claude AI to answer questions about the content

## 📊 Output Format

The scraper outputs structured JSON data:

```json
{
  "site": "https://example.com/blog",
  "items": [
    {
      "title": "Article Title",
      "content": "# Markdown content...",
      "content_type": "blog",
      "source_url": "https://example.com/blog/article"
    }
  ]
}
```

### Content Types

- `blog`: Blog posts and articles
- `podcast_transcript`: Podcast transcripts
- `call_transcript`: Call recordings
- `linkedin_post`: LinkedIn content
- `reddit_comment`: Reddit discussions
- `book`: Book content
- `other`: Other content types

## ⚙️ Configuration

### Scraping Settings

- **Max Pages**: Maximum number of pages to scrape (default: 200)
- **Concurrency**: Number of concurrent requests (default: 16)
- **Include Patterns**: URL patterns to include (e.g., "blog,guide,learn")
- **Exclude Patterns**: URL patterns to exclude (e.g., "admin,login")

### AI Settings

- **Model**: Choose between Claude 3.5 Sonnet or Haiku
- **Temperature**: Response creativity (0 = focused, 1 = creative)
- **Max Tokens**: Maximum response length

## 🔧 Advanced Usage

### Custom Patterns

```python
# Include only blog posts and guides
include_patterns = ["blog", "guide", "tutorial"]

# Exclude admin and login pages
exclude_patterns = ["admin", "login", "signup"]
```

### Batch Processing

```python
from scrapper.crawler import crawl_site
from scrapper.extractor import extract_markdown_items

# Scrape multiple sites
sites = [
    "https://site1.com/blog",
    "https://site2.com/guides",
    "https://site3.com/docs"
]

for site in sites:
    urls = crawl_site(site, max_pages=100, concurrency=16)
    items = extract_markdown_items(urls)
    # Process items...
```

## 🧪 Testing

The scraper has been tested with various websites:

- ✅ Technical blogs (interviewing.io, quill.co)
- ✅ Documentation sites
- ✅ News websites
- ✅ E-commerce sites
- ✅ Personal blogs

### Test Coverage

```bash
# Run the test suite
python test_coverage.py
```

## 📁 Project Structure

```
knowledge-builder/
├── scrapper/                 # Core scraping modules
│   ├── __init__.py
│   ├── cli.py               # Command-line interface
│   ├── crawler.py           # URL discovery and crawling
│   ├── extractor.py         # Content extraction
│   ├── indexer.py           # FAISS index creation
│   └── qa_agent.py          # Claude AI integration
├── app.py                   # Streamlit web interface
├── requirements.txt         # Python dependencies
├── docker-compose.yml       # Docker configuration
├── Dockerfile              # Docker image definition
├── .gitignore              # Git ignore rules
├── env.example             # Environment variables template
└── README.md               # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Streamlit](https://streamlit.io/) for the beautiful web interface
- [LangChain](https://langchain.com/) for AI integration
- [Anthropic](https://anthropic.com/) for Claude AI
- [Trafilatura](https://trafilatura.readthedocs.io/) for content extraction
- [FAISS](https://faiss.ai/) for vector search

## 📞 Support

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/yourusername/knowledge-builder/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/yourusername/knowledge-builder/discussions)
- 📧 **Email**: your.email@example.com

---

**Built with ❤️ for the developer community**