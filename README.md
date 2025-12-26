# 日本語 Notes

A Japanese learning notes management system, featuring LLM-powered content generation from minimal user input.

Page link: https://sssayon.github.io/nihongo-notes

## Quick Start

### 1. Install Dependencies

```bash
git clone https://github.com/SSSayon/nihongo-notes.git && cd nihongo-notes
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```
Edit `.streamlit/secrets.toml` to add your API Keys.

### 3. Run the Management Interface

```bash
streamlit run app/main.py
```
There, you can interact with LLMs to add or update notes.

Clicking the `🚀 构建网站` button will automatically commit and push changes to GitHub, triggering a workflow that deploys the site to GitHub Pages.

### (Optional) 4. Preview the Website Locally

```bash
# Build the Markdown files
python build.py

# Start the local preview server
mkdocs serve
```


## Project Structure
```
nihonngo/
├── data/                   # data directory
│   ├── verbs.json
│   ├── grammar.json
│   └── vocabulary.json
├── app/                    # Streamlit admin
│   ├── main.py                 # main entry
│   ├── llm_client.py           # unified LLM API calls
│   ├── data_manager.py         # data management utilities
│   ├── prompts.py              # prompt templates
│   └── config.py               # configuration file
├── docs/                   # MkDocs documentation sources
│   ├── index.md
│   ├── verbs.md
│   ├── grammar.md
│   ├── vocabulary.md
│   └── stylesheets/
│       └── extra.css
├── .streamlit/
│   └── secrets.toml        # API keys (do not upload)
├── .github/
│   └── workflows/
│       └── deploy.yml      # automatic deployment
├── build.py                # JSON → Markdown build script
├── mkdocs.yml              # MkDocs configuration
└── requirements.txt
└── README.md
```
