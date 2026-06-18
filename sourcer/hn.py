import re
import requests
from urllib.parse import urlparse

SKIP_DOMAINS = [
    "news.ycombinator.com",
    "twitter.com",
    "x.com",
    "youtube.com",
    "medium.com",
    "substack.com",
    "producthunt.com",
    "crunchbase.com"
]

def extract_name(title: str) -> str:
    """
    Remove "Show HN: " prefix and extract company name before first dash/colon separator.
    Handles internal hyphens (e.g., buildless-api) by only splitting on dashes with surrounding spaces.
    """
    title_clean = re.sub(r'^Show HN:\s*', '', title, flags=re.IGNORECASE).strip()
    
    # Split by colon, or by any dash (hyphen, en-dash, em-dash) with surrounding whitespace
    parts = re.split(r'\s+[\-–—]\s+|:', title_clean, maxsplit=1)
    if parts:
        name = parts[0].strip()
        if name:
            return name
            
    return title_clean[:40].strip()

def is_valid_startup_url(url: str) -> bool:
    """
    Checks if url is valid startup homepage.
    Allows github.com (flagged as github type later) but skips other non-startup domains.
    """
    if not url or not url.startswith("http"):
        return False
    try:
        domain = urlparse(url).netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        
        # Keep github.com but skip others in SKIP_DOMAINS
        if domain == "github.com":
            return True
            
        return domain not in SKIP_DOMAINS
    except Exception:
        return False

def get_domain(url: str) -> str:
    """Extract domain from URL for deduplication."""
    try:
        domain = urlparse(url).netloc.lower()
        if domain.startswith("www."):
            return domain[4:]
        return domain
    except Exception:
        return ""

def fetch_hn_startups(topic: str, count: int, min_points: int) -> list[dict]:
    """
    Returns list of candidate startups from HN.
    
    Strategy:
      Pass 1: Search "Show HN: {topic}"
      Pass 2: If results < count, broaden to "{topic} launch" (in stories)
      Dedup by domain. Sort by points DESC. Return top `count`.
    """
    candidates = {}
    
    # Pass 1: Search tags=show_hn with query=topic
    try:
        r1 = requests.get(
            "https://hn.algolia.com/api/v1/search",
            params={"query": topic, "tags": "show_hn", "hitsPerPage": 100},
            timeout=15
        )
        r1.raise_for_status()
        hits = r1.json().get("hits", [])
        process_hits(hits, candidates, min_points)
    except Exception as e:
        print(f"Error in Pass 1: {e}")
        
    # Pass 2: If we have fewer than count candidates, broaden search to "{topic} launch"
    if len(candidates) < count:
        try:
            r2 = requests.get(
                "https://hn.algolia.com/api/v1/search",
                params={"query": f"{topic} launch", "tags": "story", "hitsPerPage": 100},
                timeout=15
            )
            r2.raise_for_status()
            hits = r2.json().get("hits", [])
            process_hits(hits, candidates, min_points)
        except Exception as e:
            print(f"Error in Pass 2: {e}")

    # Convert to list and sort by points DESC
    sorted_candidates = sorted(
        candidates.values(),
        key=lambda x: x["hn_points"],
        reverse=True
    )
    
    return sorted_candidates[:count]

def process_hits(hits: list, candidates: dict, min_points: int):
    """Processes search hits, applies filters, and deduplicates by domain."""
    for hit in hits:
        url = hit.get("url")
        if not is_valid_startup_url(url):
            continue
            
        points = hit.get("points") or 0
        if points < min_points:
            continue
            
        title = hit.get("title") or ""
        author = hit.get("author") or "Unknown"
        created_at = hit.get("created_at") or ""
        object_id = hit.get("objectID") or ""
        comments = hit.get("num_comments") or 0
        
        name = extract_name(title)
        domain = get_domain(url)
        
        # Clean title for description
        desc = re.sub(r'^Show HN:\s*', '', title, flags=re.IGNORECASE).strip()
        
        url_type = "github" if domain == "github.com" else "homepage"
        
        candidate = {
            "name": name,
            "url": url,
            "hn_url": f"https://news.ycombinator.com/item?id={object_id}",
            "hn_points": points,
            "hn_comments": comments,
            "hn_author": author,
            "posted_at": created_at,
            "description": desc,
            "url_type": url_type
        }
        
        # Deduplicate by domain, keeping the one with higher points
        if domain not in candidates or candidates[domain]["hn_points"] < points:
            candidates[domain] = candidate
