
from notion_client import Client
import time
import os
import json
import csv
import requests

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
notion = Client(auth=os.getenv("NOTION_TOKEN"))

NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
NOTION_DATA_SOURCE_ID = "36ed8c9e-0e36-8021-9ba7-000be4d619dd"

print("Notion database:", NOTION_DATABASE_ID)

def search_semantic_scholar():
    query = "bioinspired materials biomimetic nature-inspired hydrogel bioadhesive nanofiber self-healing"

    url = "https://api.semanticscholar.org/graph/v1/paper/search"

    params = {
        "query": query,
        "limit": 5,
        "fields": "paperId,title,abstract,year,venue,url,citationCount,externalIds"
    }

    headers = {
        "User-Agent": "biomaterial-agent/1.0"
    }

    for attempt in range(5):
        response = requests.get(url, params=params, headers=headers)

        if response.status_code == 200:
            return response.json().get("data", [])

        if response.status_code == 429:
            print("Semantic Scholar rate limited. Waiting 60 seconds...")
            time.sleep(60)
            continue

        response.raise_for_status()

    print("Semantic Scholar still rate limited. Try again later.")
    return []


def analyse_with_gpt(abstract_text):
    prompt = f"""
You are a bioinspired materials research intelligence agent.

Extract the key information from this abstract.

Focus on:
- bioinspired or biomimetic mechanism
- material design principle
- fabrication strategy
- functional performance
- why this paper may inspire new biomaterials, hydrogels, coatings, bioadhesives, fibers, or drug delivery systems

Return ONLY valid JSON.
Do not include markdown.
Do not include ```json.
Do not include explanation.

Use exactly these fields:
{{
  "title": "",
  "material": "",
  "fabrication": "",
  "mechanism": "",
  "innovation": "",
  "application": "",
  "limitation": "",
  "relevance_score": 0
}}

Abstract:
{abstract_text}
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    text = response.output_text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "title": "JSON parsing failed",
            "material": "",
            "fabrication": "",
            "mechanism": "",
            "innovation": "",
            "application": "",
            "limitation": "",
            "relevance_score": 0,
            "raw_output": text
        }


def load_journal_impact_factors():
    journal_if = {}

    with open("journal_if.csv", "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            journal = row["journal"].strip().lower()
            impact_factor = float(row["impact_factor"])
            journal_if[journal] = impact_factor

    return journal_if


def get_impact_factor(journal_name, journal_if):
    return journal_if.get(journal_name.strip().lower(), 0)


def already_exists_by_title_or_doi(title, doi=""):
    query_filter = {
        "or": [
            {
                "property": "Title",
                "title": {
                    "equals": title
                }
            }
        ]
    }

    if doi:
        query_filter["or"].append(
            {
                "property": "DOI",
                "rich_text": {
                    "equals": doi
                }
            }
        )

    response = notion.data_sources.query(
        data_source_id=NOTION_DATA_SOURCE_ID,
        filter=query_filter
    )

    return len(response.get("results", [])) > 0


def add_to_notion(data, paper_id, metadata):
    notion.pages.create(
        parent={"data_source_id": NOTION_DATA_SOURCE_ID},
        properties={
            "Title": {
                "title": [
                    {
                        "text": {
                            "content": metadata.get("title") or data.get("title", "")
                        }
                    }
                ]
            },

            "Journal": {
                "rich_text": [
                    {
                        "text": {
                            "content": metadata.get("journal", "")
                        }
                    }
                ]
            },

            "Year": {
                "number": metadata.get("year")
            },

            "DOI": {
                "rich_text": [
                    {
                        "text": {
                            "content": metadata.get("doi", "")
                        }
                    }
                ]
            },

            "PMID": {
                "rich_text": [
                    {
                        "text": {
                            "content": str(paper_id)
                        }
                    }
                ]
            },

            "Material": {
                "rich_text": [{"text": {"content": data.get("material", "")[:1900]}}]
            },

            "Fabrication": {
                "rich_text": [{"text": {"content": data.get("fabrication", "")[:1900]}}]
            },

            "Mechanism": {
                "rich_text": [{"text": {"content": data.get("mechanism", "")[:1900]}}]
            },

            "Innovation": {
                "rich_text": [{"text": {"content": data.get("innovation", "")[:1900]}}]
            },

            "Application": {
                "rich_text": [{"text": {"content": data.get("application", "")[:1900]}}]
            },

            "Limitation": {
                "rich_text": [{"text": {"content": data.get("limitation", "")[:1900]}}]
            },

            "AI Summary": {
                "rich_text": [
                    {
                        "text": {
                            "content": data.get("raw_output", data.get("innovation", ""))[:1900]
                        }
                    }
                ]
            },

            "Relevance Score": {
                "number": float(data.get("relevance_score", 0))
            },

            "Source": {
                "url": metadata.get("url", "")
            }
        }
    )


def send_telegram_message(message):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message[:3900],
        "disable_web_page_preview": True
    }

    response = requests.post(url, data=payload)

    print("Telegram status:", response.status_code)
    print("Telegram response:", response.text)

    response.raise_for_status()


journal_if = load_journal_impact_factors()
MIN_IMPACT_FACTOR = 4.5

papers = search_semantic_scholar()

for paper in papers:

    print("=" * 80)

    try:
        paper_id = paper.get("paperId", "")
        title = paper.get("title", "")
        abstract = paper.get("abstract", "")
        journal = paper.get("venue", "")
        year = paper.get("year", None)
        url = paper.get("url", "")
        citation_count = paper.get("citationCount", 0)

        external_ids = paper.get("externalIds", {}) or {}
        doi = external_ids.get("DOI", "")

        print("Processing:", title)
        print("Journal:", journal)

        impact_factor = get_impact_factor(journal, journal_if)
        print("Impact Factor:", impact_factor)

        if already_exists_by_title_or_doi(title, doi):
            print("Skipped: already exists in Notion")
            continue

        if impact_factor < MIN_IMPACT_FACTOR:
            print("Skipped: impact factor below threshold")
            continue

        if not abstract:
            print("Skipped: no abstract")
            continue

        data = analyse_with_gpt(abstract)
        print("GPT analysed")

        metadata = {
            "title": title,
            "journal": journal,
            "year": year,
            "doi": doi,
            "url": url
        }

        add_to_notion(data, paper_id, metadata)
        print("Added to Notion")

        telegram_message = f"""
🔥 New bioinspired material paper added to Notion

Title: {title}

Journal: {journal}
Impact Factor: {impact_factor}
Year: {year}
DOI: {doi}
Citations: {citation_count}

Relevance Score: {data.get("relevance_score", 0)}

Source: {url}
"""

        send_telegram_message(telegram_message)
        print("Telegram sent")

        time.sleep(2)

    except Exception as e:
        print("ERROR")
        print(e)
        continue

