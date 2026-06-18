import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def scrape_github_repo(url: str, timeout: int = 10) -> dict:
    """
    Given a github.com URL, attempt to parse the org and repo,
    and fetch the raw README.md from raw.githubusercontent.com.
    """
    try:
        parsed = urlparse(url)
        path = parsed.path.strip("/")
        parts = [p for p in path.split("/") if p]
        
        if len(parts) < 2:
            raise ValueError("Invalid GitHub URL structure")
            
        org = parts[0]
        repo = parts[1]
        if repo.endswith(".git"):
            repo = repo[:-4]
            
        # Try main branch first
        readme_url = f"https://raw.githubusercontent.com/{org}/{repo}/main/README.md"
        resp = requests.get(readme_url, headers=HEADERS, timeout=timeout)
        
        # If 404, try master branch
        if resp.status_code == 404:
            readme_url = f"https://raw.githubusercontent.com/{org}/{repo}/master/README.md"
            resp = requests.get(readme_url, headers=HEADERS, timeout=timeout)
            
        resp.raise_for_status()
        
        # Extract body text from README (first 1500 chars)
        readme_text = resp.text
        body_text = readme_text[:1500]
        
        return {
            "success": True,
            "url_type": "github",
            "title": f"{org}/{repo} GitHub Repository",
            "meta_description": f"GitHub repository for {org}/{repo}",
            "og_description": None,
            "h1_tags": [repo],
            "body_text": body_text,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "url_type": "github",
            "title": None,
            "meta_description": None,
            "og_description": None,
            "h1_tags": [],
            "body_text": "",
            "error": f"Failed to fetch GitHub README: {str(e)}"
        }

def scrape_homepage(url: str, timeout: int = 10) -> dict:
    """
    Fetches startup homepage and extracts key text content.
    If the domain is github.com, routes to scrape_github_repo.
    Never raises an exception — always returns a structured dict.
    """
    if not url:
        return {
            "success": False,
            "url_type": "homepage",
            "title": None,
            "meta_description": None,
            "og_description": None,
            "h1_tags": [],
            "body_text": "",
            "error": "Empty URL"
        }
        
    try:
        domain = urlparse(url).netloc.lower()
        if "github.com" in domain:
            return scrape_github_repo(url, timeout)
            
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
    except Exception as e:
        return {
            "success": False,
            "url_type": "homepage",
            "title": None,
            "meta_description": None,
            "og_description": None,
            "h1_tags": [],
            "body_text": "",
            "error": str(e)
        }
        
    try:
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Remove noise
        for tag in soup(["script", "style", "nav", "footer", "iframe", "noscript"]):
            tag.decompose()
            
        title = soup.title.string.strip() if soup.title and soup.title.string else None
        
        meta_desc_tag = soup.find("meta", attrs={"name": "description"})
        meta_description = meta_desc_tag["content"].strip() if meta_desc_tag and meta_desc_tag.has_attr("content") else None
        
        og_desc_tag = soup.find("meta", attrs={"property": "og:description"})
        og_description = og_desc_tag["content"].strip() if og_desc_tag and og_desc_tag.has_attr("content") else None
        
        h1s = [h.get_text(strip=True) for h in soup.find_all("h1") if h.get_text(strip=True)][:3]
        
        # Extract visible text and normalize spacing
        body_text = " ".join(soup.get_text(separator=" ").split())[:1500]
        
        return {
            "success": True,
            "url_type": "homepage",
            "title": title,
            "meta_description": meta_description,
            "og_description": og_description,
            "h1_tags": h1s,
            "body_text": body_text,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "url_type": "homepage",
            "title": None,
            "meta_description": None,
            "og_description": None,
            "h1_tags": [],
            "body_text": "",
            "error": f"Failed to parse page content: {str(e)}"
        }
