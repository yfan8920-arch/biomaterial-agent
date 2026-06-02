# Biomaterial AI Scout

An autonomous AI-powered scientific discovery engine for biomaterials, smart materials, and interdisciplinary future technologies.

## Why I Built This

As a biomaterials PhD researcher, I found that keeping up with interdisciplinary research across smart materials, biointerfaces, AI-designed systems, electrospinning, ECM, bioelectronics, and adaptive biomaterials became increasingly overwhelming.

Most paper recommendation systems focus on citation metrics rather than scientific curiosity or future-facing innovation.

This project was built to function as an autonomous AI research scout — continuously searching, filtering, analyzing, and delivering potentially exciting scientific ideas directly into a personalized research workflow.


This system automatically:

* searches cutting-edge research papers
* analyzes scientific novelty using GPT
* filters high-interest interdisciplinary topics
* sends engaging Telegram summaries
* archives papers into Notion
* runs fully autonomously in the cloud

## Research Areas

The scout explores topics including:

* Smart biomaterials
* AI-designed materials
* Electrospinning & nanofibers
* ECM & natural biomaterials
* Bioelectric & electroactive systems
* Soft robotics
* Living materials
* Adaptive biointerfaces
* Conductive hydrogels
* 4D printed biomaterials
* Biofabrication
* Tissue engineering

## Tech Stack

* Python
* OpenAI API
* OpenAlex API
* Semantic Scholar API
* Telegram Bot API
* Notion API
* Railway (cloud deployment)
* GitHub Actions / cron automation

## Features

* Autonomous literature scouting
* AI-generated scientific insights
* Multi-disciplinary paper discovery
* Cloud-based scheduled execution
* Telegram push notifications
* Notion knowledge database
* Semantic abstract fallback retrieval
* Research relevance scoring

## Example Workflow

1. Search interdisciplinary scientific papers
2. Retrieve abstract metadata
3. Analyze with GPT
4. Generate engaging research summaries
5. Push to Telegram
6. Archive to Notion database

## Future Directions

* Figure understanding
* AI novelty scoring
* Hidden gem paper detection
* Weekly research digest
* Multi-user topic customization
* Research idea generation
* Citation graph analysis
* Personalized scientific recommendation systems
* ## Screenshots

### Telegram Push Example
![telegram](images/telegram.png)<img width="1179" height="2556" alt="Image_20260529183824_87_7" src="https://github.com/user-attachments/assets/3e6a9e12-c1e3-4eef-8030-0f4ed0bbb3f9" />



### Notion Database
![notion](images/notion.png)<img width="1113" height="667" alt="Screenshot 2026-06-03 at 8 16 26 am" src="https://github.com/user-attachments/assets/c67d20b1-649c-4dc4-960a-465acb020deb" />


### Railway Deployment
![railway](images/railway.png)<img width="1134" height="640" alt="Screenshot 2026-06-03 at 8 17 37 am" src="https://github.com/user-attachments/assets/83726e21-2931-4fe5-bbd8-a205a677389c" />



## Architecture Diagram

```text
OpenAlex / Semantic Scholar
              ↓
          GPT Analysis
              ↓
     Relevance Filtering
          ↙       ↘
    Telegram      Notion
              ↓
        Railway Cloud
````

## Quick Start

Clone the repository:

```bash
git clone https://github.com/yfan8920-arch/biomaterial-agent.git
cd biomaterial-agent
```

Create virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create `.env`:

```env
OPENAI_API_KEY=
SEMANTIC_SCHOLAR_API_KEY=
NOTION_TOKEN=
NOTION_DATABASE_ID=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

Run locally:

```bash
python main.py
```


