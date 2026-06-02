from notion_client import Client
import time
import os
import json
import requests
import random

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

SEMANTIC_SCHOLAR_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# Your Notion data source ID
NOTION_DATA_SOURCE_ID = "36ed8c9e-0e36-8021-9ba7-000be4d619dd"

client = OpenAI(api_key=OPENAI_API_KEY)
notion = Client(auth=NOTION_TOKEN)

print("Notion database:", NOTION_DATABASE_ID)
print("Notion data source:", NOTION_DATA_SOURCE_ID)


def safe_text(value, max_len=1900):
    """Convert any value to safe Notion rich_text content."""
    if value is None:
        return ""
    return str(value)[:max_len]


def openalex_abstract_to_text(abstract_inverted_index):
    """
    OpenAlex does not usually return paper['abstract'].
    It returns abstract_inverted_index, which needs to be reconstructed.
    """
    if not abstract_inverted_index:
        return ""

    words = []
    for word, positions in abstract_inverted_index.items():
        for position in positions:
            words.append((position, word))

    words.sort(key=lambda x: x[0])
    return " ".join(word for _, word in words)


def get_openalex_metadata(paper):
    """Extract metadata correctly from an OpenAlex work record."""
    title = paper.get("title") or paper.get("display_name") or "Untitled"

    abstract = openalex_abstract_to_text(paper.get("abstract_inverted_index"))

    journal = (
        (paper.get("primary_location") or {})
        .get("source", {})
        .get("display_name", "")
    )

    year = paper.get("publication_year")
    doi = paper.get("doi") or ""

    # OpenAlex DOI often looks like "https://doi.org/...". Keep it readable.
    doi_clean = doi.replace("https://doi.org/", "") if doi else ""

    url = (
        ((paper.get("primary_location") or {}).get("landing_page_url"))
        or doi
        or paper.get("id")
        or None
    )

    citation_count = paper.get("cited_by_count", 0)
    paper_id = paper.get("id") or doi_clean or title

    return {
        "paper_id": paper_id,
        "title": title,
        "abstract": abstract,
        "journal": journal,
        "year": year,
        "doi": doi_clean,
        "url": url,
        "citation_count": citation_count,
    }


def get_semantic_scholar_abstract(title):
    if not SEMANTIC_SCHOLAR_API_KEY:
        print("Semantic Scholar API key not found in .env; skipping Semantic Scholar fallback.")
        return None

    url = "https://api.semanticscholar.org/graph/v1/paper/search"

    headers = {
        "x-api-key": SEMANTIC_SCHOLAR_API_KEY
    }

    params = {
        "query": title,
        "limit": 1,
        "fields": "title,abstract,year"
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=20)

        if response.status_code == 429:
            print("Semantic Scholar rate limit hit; using title only if no abstract.")
            return None

        response.raise_for_status()
        data = response.json()

        papers = data.get("data", [])

        if papers:
            return papers[0].get("abstract")

    except Exception as e:
        print("Semantic Scholar error:", e)

    return None


RESEARCH_TOPICS = [
    # AI / intelligent materials
    "AI designed biomaterials",
    "machine learning guided biomaterials design",
    "artificial intelligence smart materials biomedical",
    "adaptive intelligent biomaterials",
    "autonomous smart biomaterials",
    "closed-loop responsive drug delivery biomaterials",
    "self-regulating smart hydrogel",

    # Electroactive / electric / ionic / bioelectric
    "electric eel inspired materials",
    "electric eel inspired hydrogel",
    "bioinspired ionic power source",
    "electroactive hydrogel biomedical",
    "ionic conductive hydrogel biomaterials",
    "bioelectric biomaterials tissue engineering",
    "soft bioelectronics biomaterials",
    "conductive polymer biomaterials",
    "piezoelectric biomaterials tissue regeneration",
    "triboelectric biomedical materials",
    "energy harvesting biomaterials",

    # Electrospinning / fibers / nanofibers
    "electrospinning tissue engineering scaffold",
    "electrospun nanofiber biomaterials",
    "aligned nanofiber scaffold tissue engineering",
    "core-shell electrospinning drug delivery",
    "coaxial electrospinning biomedical",
    "nanofiber hydrogel composite biomaterials",
    "electrospun ECM mimetic scaffold",

    # ECM / natural materials / bio-derived materials
    "extracellular matrix biomaterials",
    "ECM mimetic hydrogel",
    "decellularized extracellular matrix hydrogel",
    "collagen bioink tissue engineering",
    "collagen hydrogel biomaterials",
    "gelatin methacrylate biomaterials",
    "natural polymer hydrogel tissue engineering",
    "silk fibroin biomaterials",
    "alginate hydrogel tissue engineering",
    "hyaluronic acid biomaterials",
    "chitosan antibacterial biomaterials",
    "fibrin hydrogel tissue engineering",

    # Smart responsive systems
    "stimuli responsive hydrogel biomedical",
    "shape memory biomaterials",
    "4D printed hydrogel biomedical",
    "self-healing biomaterials",
    "dynamic covalent hydrogel biomaterials",
    "pH responsive drug delivery biomaterial",
    "temperature responsive hydrogel biomedical",
    "light responsive biomaterials",
    "enzyme responsive biomaterials",
    "bacteria responsive biomaterials",

    # Bioinspired / biointerface / adhesion / coatings
    "mussel inspired adhesive biomaterials",
    "bioinspired wet adhesion hydrogel",
    "bioinspired surface engineering biomaterials",
    "microstructured biomaterial interface",
    "slippery liquid infused surface biomedical",
    "bioadhesive hydrogel tissue interface",
    "antifouling biomaterial coating",
    "cell instructive biomaterial interface",

    # Soft robotics / wearable / implantable interfaces
    "soft robotic biomaterials",
    "wearable bioelectronics hydrogel",
    "stretchable conductive hydrogel sensor",
    "implantable soft electronics biomaterials",
    "human machine biointerface biomaterials",
    "soft actuator hydrogel biomedical",

    # Fabrication / manufacturing methods
    "3D bioprinting biomaterials",
    "microfluidic biomaterials fabrication",
    "laser fabricated biomaterials",
    "plasma surface engineering biomaterials",
    "biofabrication tissue engineering",
    "micro nano fabrication biomaterials",
    "photocrosslinked hydrogel biomaterials",
    "injectable hydrogel in situ forming",

    # Living / hybrid / synthetic biology systems
    "engineered living materials biomaterials",
    "living hydrogel systems",
    "cell-laden biofabrication",
    "synthetic biology biomaterials",
    "biohybrid materials biomedical",
    "microbial living materials biomedical",

    # Ocular / translational biointerfaces, still relevant to your PhD
    "smart contact lens drug delivery",
    "ocular biomaterials hydrogel drug delivery",
    "corneal tissue engineering biomaterials",
    "antimicrobial contact lens biomaterials",
]

REVIEW_TOPICS = [
    "review AI smart biomaterials",
    "review machine learning biomaterials design",
    "review bioinspired smart materials",
    "review electroactive hydrogels biomedical",
    "review bioelectric biomaterials",
    "review electrospinning tissue engineering",
    "review extracellular matrix biomaterials",
    "review natural polymer hydrogels biomedical",
    "review adaptive responsive biomaterials",
    "review soft bioelectronics biomaterials",
    "review engineered living materials",
    "review advanced biofabrication biomaterials",
]


def search_openalex():
    # Broad future-materials scout: about 20% review / 80% research.
    review_probability = 0.2

    if random.random() < review_probability:
        query = random.choice(REVIEW_TOPICS)
        paper_mode = "REVIEW"
    else:
        query = random.choice(RESEARCH_TOPICS)
        paper_mode = "RESEARCH"

    # Prefer newer papers. Occasionally include high-citation classics.
    sort_mode = random.choice([
        "publication_date:desc",
        "publication_date:desc",
        "publication_date:desc",
        "cited_by_count:desc"
    ])

    page = random.randint(1, 8)

    url = "https://api.openalex.org/works"

    params = {
        "search": query,
        "per-page": 5,
        "page": page,
        "sort": sort_mode,
        "mailto": "yfan8920@gmail.com",
    }

    headers = {
        "User-Agent": "mailto:yfan8920@gmail.com"
    }

    print("Mode:", paper_mode)
    print("Query:", query)
    print("Sort:", sort_mode)
    print("Page:", page)

    response = requests.get(url, params=params, headers=headers, timeout=30)
    response.raise_for_status()

    return response.json().get("results", []), paper_mode

def analyse_with_gpt(abstract_text, paper_mode):
    prompt = f"""
You are a bioinspired materials research intelligence agent.

This paper was retrieved in {paper_mode} mode.

Your job is not only to summarise the paper, but to make it interesting enough that a biomaterials researcher would want to read it.

Write in a concise, engaging research-scout style.
Every field must contain at least one useful sentence.
Do not leave any field empty.
Do not write "N/A".
If the abstract is limited, infer cautiously from the title and say "Based on the title...".

Focus on:
- bioinspired or biomimetic mechanism
- material design principle
- fabrication strategy
- functional performance
- why this paper may inspire new biomaterials, hydrogels, coatings, bioadhesives, fibers, interfaces, or drug delivery systems

Return ONLY valid JSON.
Do not use markdown.
Do not wrap the JSON in ```json.

Use exactly these fields:
{{
  "title": "",
  "hook": "A curiosity-driven one-sentence hook explaining why this paper is worth opening.",
  "material": "A useful sentence describing the main material system.",
  "fabrication": "A useful sentence describing how the material/system was made or engineered.",
  "mechanism": "A useful sentence describing the core mechanism or design principle.",
  "innovation": "A useful sentence describing what is scientifically exciting or unusual.",
  "application": "A useful sentence describing potential applications.",
  "limitation": "A useful sentence describing a likely limitation, caution, or missing validation.",
  "why_read": "A useful sentence explaining a biomaterials/hydrogel researcher, may want to read it.",
  "relevance_score": 0
}}

Abstract or title:
{abstract_text}
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    text = response.output_text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        print("GPT JSON parsing failed. Raw output:", text[:1000])
        data = {
            "title": "JSON parsing failed",
            "hook": "This paper may be relevant, but the AI output could not be parsed into structured JSON.",
            "material": "Please check the raw AI output saved in Notion.",
            "fabrication": "Please check the raw AI output saved in Notion.",
            "mechanism": "Please check the raw AI output saved in Notion.",
            "innovation": "Please check the raw AI output saved in Notion.",
            "application": "Please check the raw AI output saved in Notion.",
            "limitation": "Please check the raw AI output saved in Notion.",
            "why_read": text[:1000] if text else "The AI returned an empty response.",
            "relevance_score": 0,
            "raw_output": text
        }

    # Guarantee no empty Telegram fields even if GPT returns empty strings.
    defaults = {
        "title": "Untitled",
        "hook": "This paper may contain a useful biomaterials idea worth checking.",
        "material": "The material system was not clearly specified in the available abstract/title.",
        "fabrication": "The fabrication or engineering strategy was not clearly specified in the available abstract/title.",
        "mechanism": "The core mechanism was not clearly specified, so the full paper may be needed.",
        "innovation": "The potential novelty is not fully clear from the available text, but it may still be relevant to biomaterials design.",
        "application": "The application may relate to biomaterials, hydrogels, coatings, drug delivery, or tissue interfaces.",
        "limitation": "A likely limitation is that more experimental validation may be needed to assess real-world performance.",
        "why_read": "It may provide a useful design idea or comparison point for future biomaterials research.",
        "relevance_score": 0
    }

    for key, default_value in defaults.items():
        if key not in data or data.get(key) in [None, "", "N/A", "n/a"]:
            data[key] = default_value

    try:
        data["relevance_score"] = float(data.get("relevance_score", 0) or 0)
    except (TypeError, ValueError):
        data["relevance_score"] = 0

    data["raw_output"] = text
    return data

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
                            "content": safe_text(metadata.get("title") or data.get("title") or "Untitled")
                        }
                    }
                ]
            },

            "Journal": {
                "rich_text": [
                    {
                        "text": {
                            "content": safe_text(metadata.get("journal"))
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
                            "content": safe_text(metadata.get("doi"))
                        }
                    }
                ]
            },

            "PMID": {
                "rich_text": [
                    {
                        "text": {
                            "content": safe_text(paper_id)
                        }
                    }
                ]
            },

            "Material": {
                "rich_text": [
                    {
                        "text": {
                            "content": safe_text(data.get("material"))
                        }
                    }
                ]
            },

            "Fabrication": {
                "rich_text": [
                    {
                        "text": {
                            "content": safe_text(data.get("fabrication"))
                        }
                    }
                ]
            },

            "Mechanism": {
                "rich_text": [
                    {
                        "text": {
                            "content": safe_text(data.get("mechanism"))
                        }
                    }
                ]
            },

            "Innovation": {
                "rich_text": [
                    {
                        "text": {
                            "content": safe_text(data.get("innovation"))
                        }
                    }
                ]
            },

            "Application": {
                "rich_text": [
                    {
                        "text": {
                            "content": safe_text(data.get("application"))
                        }
                    }
                ]
            },

            "Limitation": {
                "rich_text": [
                    {
                        "text": {
                            "content": safe_text(data.get("limitation"))
                        }
                    }
                ]
            },

            "AI Summary": {
                "rich_text": [
                    {
                        "text": {
                            "content": safe_text(
                                data.get("raw_output")
                                or (
                                    f"Hook: {data.get('hook', '')}\n"
                                    f"Innovation: {data.get('innovation', '')}\n"
                                    f"Mechanism: {data.get('mechanism', '')}\n"
                                    f"Why read: {data.get('why_read', '')}"
                                )
                            )
                        }
                    }
                ]
            },

            "Relevance Score": {
                "number": float(data.get("relevance_score", 0) or 0)
            },

            # Notion URL fields must be a real URL or None. Empty string "" causes validation error.
            "Source": {
                "url": metadata.get("url") or None
            }
        }
    )


def send_telegram_message(message):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("Telegram token/chat_id not found; skipped Telegram message.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message[:3900],
        "disable_web_page_preview": True
    }

    response = requests.post(url, data=payload, timeout=20)

    print("Telegram status:", response.status_code)

    response.raise_for_status()


def main():
    papers, paper_mode = search_openalex()

    for paper in papers:
        print("=" * 80)

        try:
            metadata = get_openalex_metadata(paper)

            paper_id = metadata["paper_id"]
            title = metadata["title"]
            abstract = metadata["abstract"]
            journal = metadata["journal"]
            year = metadata["year"]
            doi = metadata["doi"]
            url = metadata["url"]
            citation_count = metadata["citation_count"]

            print("Processing:", title)
            print("Journal:", journal)

            if already_exists_by_title_or_doi(title, doi):
                print("Skipped: already exists")
                continue

            if not abstract:
                print("OpenAlex missing abstract, trying Semantic Scholar...")
                abstract = get_semantic_scholar_abstract(title)
                time.sleep(1)

                if not abstract:
                    print("Still no abstract, using title only")
                    abstract = title

            data = analyse_with_gpt(abstract, paper_mode)

            print("GPT analysed")
            print("GPT data:", json.dumps(data, ensure_ascii=False)[:1200])

            add_to_notion(data, paper_id, metadata)

            print("Added to Notion")

            telegram_message = f"""
🧠 Bioinspired Paper Scout

🎯 Why this may be worth reading:
{data.get("hook", "No hook generated.")}

📌 Paper:
{title}

📚 Journal:
{journal} ({year})

🔥 What is exciting:
{data.get("innovation", "No innovation summary generated.")}

⚙️ Core mechanism:
{data.get("mechanism", "No mechanism summary generated.")}

🧪 Material / strategy:
{data.get("material", "No material summary generated.")}
{data.get("fabrication", "")}

💡 Research inspiration:
{data.get("why_read", data.get("application", "No research inspiration generated."))}

⚠️ Limitation:
{data.get("limitation", "No limitation summary generated.")}

⭐ Relevance score:
{data.get("relevance_score", 0)}

📎 Details:
Mode: {paper_mode}
Citations: {citation_count}
DOI: {doi or "No DOI found"}

🔗 Source:
{url or "No URL found"}
"""

            send_telegram_message(telegram_message)

            print("Telegram sent")

            time.sleep(2)

        except Exception as e:
            print("ERROR")
            print(e)
            continue


if __name__ == "__main__":
    main()
