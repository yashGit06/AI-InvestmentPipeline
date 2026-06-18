import json
from unittest.mock import patch, MagicMock
from analyzer.analyze import parse_analysis
from memo.generator import render_memo

MOCK_GEMINI_RESPONSE = json.dumps({
    "name": "TestCo", 
    "website": "https://testco.com",
    "one_liner": "Automates invoice processing for SMBs",
    "team": {
        "summary": "Co-founders have deep industry expertise.",
        "technical_depth": 3,
        "prior_exit": False,
        "founder_names": ["Alice"],
        "data_quality": "medium"
    },
    "product": {
        "summary": "Uses LLMs to extract fields from PDF invoices.",
        "category": "B2B SaaS",
        "workflow_automated": "Invoice processing",
        "ai_role": "LLM extracts fields"
    },
    "market": {
        "summary": "Large market with legacy incumbents.",
        "tam_estimate": "$12B",
        "incumbents": ["QuickBooks"],
        "why_now": "LLMs can now read unstructured invoices reliably"
    },
    "risks": ["Risk 1", "Risk 2", "Risk 3"],
    "score": 68,
    "score_breakdown": {
        "team": 15,
        "product": 16,
        "market": 14,
        "moat": 14,
        "traction": 9
    },
    "recommendation": "Take a Meeting",
    "rationale": "Strong thesis alignment.",
    "mind_changers": ["MC1", "MC2", "MC3"],
    "data_gaps": []
})

def test_parse_analysis_valid():
    result = parse_analysis(MOCK_GEMINI_RESPONSE)
    assert result is not None
    assert result["score"] == 68
    assert result["recommendation"] == "Take a Meeting"
    assert result["team"]["founder_names"] == ["Alice"]

def test_parse_analysis_strips_fences():
    fenced = f"```json\n{MOCK_GEMINI_RESPONSE}\n```"
    result = parse_analysis(fenced)
    assert result is not None
    assert result["score"] == 68

def test_parse_analysis_adjusts_inconsistent_score():
    # Sum is 15+16+14+14+9 = 68. If score is reported as 75, it should be adjusted to 68.
    modified_response = json.loads(MOCK_GEMINI_RESPONSE)
    modified_response["score"] = 75
    result = parse_analysis(json.dumps(modified_response))
    assert result is not None
    assert result["score"] == 68

def test_memo_renders_without_missing_keys():
    analysis = json.loads(MOCK_GEMINI_RESPONSE)
    candidate = {
        "hn_points": 142,
        "hn_comments": 47,
        "hn_url": "https://news.ycombinator.com/item?id=123",
        "posted_at": "2025-01-15T10:00:00Z"
    }
    memo = render_memo(analysis, candidate)
    assert "TestCo — Take a Meeting" in memo
    assert "Score: 68/100" in memo
    assert "Invoice processing" in memo
    assert "Alice" in memo
    assert "QuickBooks" in memo
