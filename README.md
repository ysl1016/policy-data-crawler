# Policy Research Institution Data Crawler and Analysis System

A system for crawling and analyzing research reports from South Korean national research institutions such as KDI (Korea Development Institute) and BOK (Bank of Korea).

## Features

- Web crawling of national research institutions
- PDF file download and text extraction
- Text analysis and keyword extraction
- Topic modeling
- Search engine construction
- Policy analysis report generation

## Installation

1. Install required packages:
```bash
pip install -r requirements.txt
```

2. Install Java JDK (required for KoNLPy)

## Usage

### Run the entire system:
```bash
python main.py --run_all
```

### Run specific features:
```bash
# Crawl KDI materials only
python main.py --crawl_kdi --start_page 1 --end_page 10

# Process PDFs
python main.py --process_all

# Text analysis
python main.py --analyze --top_keywords 30 --num_topics 8

# Build search index
python main.py --build_index

# Generate reports
python main.py --generate_reports
```

### Run web interface:
```bash
python webapp.py
```
Access http://localhost:5000 in your web browser

## Notes

- Respect the terms of use and robots.txt of each institution's website
- Limit crawling speed to prevent server overload
- Text extraction quality may vary depending on PDF format