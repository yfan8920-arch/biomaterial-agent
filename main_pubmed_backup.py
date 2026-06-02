from notion_client import Client
import time
import os
import json
import csv

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
notion = Client(auth=os.getenv("NOTION_TOKEN"))


NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
notion = Client(auth=os.getenv("NOTION_TOKEN"))

NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")



print(NOTION_DATABASE_ID)

import requests

def search_pubmed():
    
    query = """
    (
        bioinspired[Title/Abstract]
        OR biomimetic[Title/Abstract]
        OR nature-inspired[Title/Abstract]
        OR smart material[Title/Abstract]
        OR adaptive material[Title/Abstract]
        OR responsive material[Title/Abstract]
        OR self-healing[Title/Abstract]
        OR living material[Title/Abstract]
        OR hydrogel[Title/Abstract]
        OR scaffold[Title/Abstract]
        OR fiber[Title/Abstract]
        OR fibrous[Title/Abstract]
        OR nanofiber[Title/Abstract]
        OR electrospinning[Title/Abstract]
        OR microfiber[Title/Abstract]
        OR bioadhesive[Title/Abstract]
        OR bioglue[Title/Abstract]
        OR adhesive[Title/Abstract]
        OR wet adhesion[Title/Abstract]
        OR interface[Title/Abstract]
        OR surface engineering[Title/Abstract]
        OR coating[Title/Abstract]
        OR antimicrobial surface[Title/Abstract]
        OR biofabrication[Title/Abstract]
        OR tissue engineering[Title/Abstract]
        OR regenerative material[Title/Abstract]
        OR drug delivery[Title/Abstract]
        OR nanoparticle[Title/Abstract]
        OR microparticle[Title/Abstract]
    )
    AND
    (
        fabrication[Title/Abstract]
        OR mechanism[Title/Abstract]
        OR engineering[Title/Abstract]
        OR assembly[Title/Abstract]
        OR self-assembly[Title/Abstract]
        OR plasma[Title/Abstract]
        OR coating[Title/Abstract]
        OR interface[Title/Abstract]
        OR crosslinking[Title/Abstract]
        OR functionalization[Title/Abstract]
    )
    """
    





    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

    params = {
        "db": "pubmed",
        "term": query,
        "retmax": 5,
        "retmode": "json",
        "sort": "pub_date"
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()["esearchresult"]["idlist"]


def fetch_abstract(pmid):
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    params = {
        "db": "pubmed",
        "id": pmid,
        "retmode": "text",
        "rettype": "abstract"
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.text

def fetch_pubmed_metadata(pmid):
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

    params = {
        "db": "pubmed",
        "id": pmid,
        "retmode": "json"
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    record = response.json()["result"][pmid]

    title = record.get("title", "")
    journal = record.get("fulljournalname", "")
    pubdate = record.get("pubdate", "")
    year = int(pubdate[:4]) if pubdate[:4].isdigit() else None

    doi = ""
    for article_id in record.get("articleids", []):
        if article_id.get("idtype") == "doi":
            doi = article_id.get("value", "")

    return {
        "title": title,
        "journal": journal,
        "year": year,
        "doi": doi
    }


def analyse_with_gpt(abstract_text):
    prompt = f"""
You are a biomaterial fabrication and mechanism extraction agent.

Extract the key information from this abstract.

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


def already_exists_in_notion(pmid, doi=""):
    query_filter = {
        "or": [
            {
                "property": "PMID",
                "rich_text": {
                    "equals": str(pmid)
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
    data_source_id="36ed8c9e-0e36-8021-9ba7-000be4d619dd",
    filter=query_filter
    )

    return len(response.get("results", [])) > 0

def add_to_notion(data, pmid, metadata):
    notion.pages.create(
        parent={"database_id": NOTION_DATABASE_ID},
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
                            "content": str(pmid)
                        }
                    }
                ]
            },

            "Material": {
                "rich_text": [{"text": {"content": data.get("material", "")}}]
            },

            "Fabrication": {
                "rich_text": [{"text": {"content": data.get("fabrication", "")}}]
            },

            "Mechanism": {
                "rich_text": [{"text": {"content": data.get("mechanism", "")}}]
            },

            "Innovation": {
                "rich_text": [{"text": {"content": data.get("innovation", "")}}]
            },

            "Application": {
                "rich_text": [{"text": {"content": data.get("application", "")}}]
            },

            "Limitation": {
                "rich_text": [{"text": {"content": data.get("limitation", "")}}]
            },

            "AI Summary": {
                "rich_text": [
                    {
                        "text": {
                            "content": data.get("raw_output", data.get("mechanism", ""))[:1900]
                        }
                    }
                ]
            },

            "Relevance Score": {
                "number": float(data.get("relevance_score", 0))
            },

            "Source": {
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
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


pmids = search_pubmed()


journal_if = load_journal_impact_factors()
MIN_IMPACT_FACTOR = 4.5

for pmid in pmids:

    print("=" * 80)
    print("Processing PMID:", pmid)

    try:
        metadata = fetch_pubmed_metadata(pmid)

        journal = metadata.get("journal", "")
        doi = metadata.get("doi", "")
        impact_factor = get_impact_factor(journal, journal_if)

        print("Journal:", journal)
        print("Impact Factor:", impact_factor)

        if already_exists_in_notion(pmid, doi):
            print("Skipped: already exists in Notion")
            continue

        if impact_factor < MIN_IMPACT_FACTOR:
            print("Skipped: impact factor below 4.5")
            continue

        abstract = fetch_abstract(pmid)
        print("Abstract fetched")

        data = analyse_with_gpt(abstract)
        print("GPT analysed")

        add_to_notion(data, pmid, metadata)
        print("Added to Notion")

        telegram_message = f"""
✅ New high-impact paper added to Notion

Title: {metadata.get("title", "")}

Journal: {journal}
Impact Factor: {impact_factor}
Year: {metadata.get("year", "")}
DOI: {doi}

Relevance Score: {data.get("relevance_score", 0)}

PubMed: https://pubmed.ncbi.nlm.nih.gov/{pmid}/
"""

        send_telegram_message(telegram_message)
        print("Telegram sent")

        time.sleep(2)

    except Exception as e:
        print("ERROR for PMID:", pmid)
        print(e)
        continue



