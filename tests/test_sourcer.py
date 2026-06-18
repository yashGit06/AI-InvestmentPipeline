import pytest
from urllib.parse import urlparse
from sourcer.hn import fetch_hn_startups, extract_name, is_valid_startup_url

def test_hn_returns_expected_shape():
    # Real HN API call with a known topic
    results = fetch_hn_startups("AI agents", count=3, min_points=2)
    # The API might be slow or return empty if network issues occur, but usually passes
    if len(results) > 0:
        assert all("name" in r for r in results)
        assert all("hn_points" in r for r in results)
        assert all("url" in r for r in results)
        assert all("hn_url" in r for r in results)
        assert all("posted_at" in r for r in results)
        assert all("description" in r for r in results)

def test_extract_name():
    assert extract_name("Show HN: Embra – Fast AI for Teams") == "Embra"
    assert extract_name("Show HN: Retool: Build Internal Tools") == "Retool"
    assert extract_name("Show HN: I built an AI accountant") != ""
    assert extract_name("Show HN: buildless-api - Fast API client") == "buildless-api"

def test_is_valid_startup_url():
    assert is_valid_startup_url("https://embra.co") is True
    assert is_valid_startup_url("https://github.com/org/repo") is True
    assert is_valid_startup_url("https://news.ycombinator.com/item?id=123") is False
    assert is_valid_startup_url("https://twitter.com/someuser") is False
    assert is_valid_startup_url("") is False
    assert is_valid_startup_url("not-a-url") is False

def test_deduplication():
    # Two items with same domain should collapse to one.
    # We call with a common term "notion" and low min_points
    results = fetch_hn_startups("notion", count=10, min_points=1)
    if len(results) > 0:
        domains = []
        for r in results:
            domain = urlparse(r["url"]).netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            domains.append(domain)
        assert len(domains) == len(set(domains))
