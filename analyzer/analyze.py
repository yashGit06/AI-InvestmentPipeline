import os
import re
import json
import google.generativeai as genai
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential
import config

load_dotenv()

# Configure Gemini if key is present
gemini_key = os.getenv("GEMINI_API_KEY")
if gemini_key:
    genai.configure(api_key=gemini_key)

def load_prompt_template(filename: str) -> str:
    """Reads a prompt template file."""
    with open(filename, "r", encoding="utf-8") as f:
        return f.read()

def build_prompt(candidate: dict, homepage: dict) -> str:
    """Combines prompt template with thesis, rubric, and startup context."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_path = os.path.join(base_dir, "prompts", "analysis_v2.txt")
    rubric_path = os.path.join(base_dir, "prompts", "scoring_rubric.md")
    
    template = load_prompt_template(template_path)
    rubric = load_prompt_template(rubric_path)
    
    prompt_base = template.replace("{thesis}", config.THESIS).replace("{scoring_rubric}", rubric)
    
    h1s = " | ".join(homepage.get("h1_tags", [])) if homepage.get("h1_tags") else "Not available"
    homepage_status = "Success" if homepage.get("success") else f"Failed - {homepage.get('error')}"
    
    context = f"""
STARTUP DATA
------------
HN Title: {candidate.get('description') or ''}
HN Points: {candidate.get('hn_points', 0)} | Comments: {candidate.get('hn_comments', 0)}
Posted by: {candidate.get('hn_author') or 'Unknown'} on {candidate.get('posted_at') or ''}
Website: {candidate.get('url') or ''}
HN Post: {candidate.get('hn_url') or ''}

HOMEPAGE CONTENT
----------------
Page Title: {homepage.get('title') or 'Not available'}
Meta Description: {homepage.get('meta_description') or 'Not available'}
OG Description: {homepage.get('og_description') or 'Not available'}
H1 Tags: {h1s}
Body Text: {homepage.get('body_text') or 'Not available'}
Homepage Status: {homepage_status}
"""
    return f"{prompt_base}\n\n{context}"

def parse_analysis(raw: str) -> dict | None:
    """Parses JSON content returned by LLM, sanitizes markdown block fences, and validates keys."""
    if not raw:
        return None
        
    clean = raw.strip()
    clean = re.sub(r'^```json\s*', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'```$', '', clean)
    clean = clean.strip()
    
    match = re.search(r'(\{.*\})', clean, re.DOTALL)
    if match:
        clean = match.group(1)
        
    try:
        data = json.loads(clean)
        
        required_keys = [
            "name", "website", "one_liner", "team", "product", "market",
            "risks", "score", "score_breakdown", "recommendation", "rationale",
            "mind_changers", "data_gaps"
        ]
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Missing required key: {key}")
                
        if not isinstance(data["team"], dict) or "technical_depth" not in data["team"] or "data_quality" not in data["team"]:
            raise ValueError("Invalid team structure")
        if not isinstance(data["product"], dict) or "workflow_automated" not in data["product"] or "ai_role" not in data["product"]:
            raise ValueError("Invalid product structure")
        if not isinstance(data["market"], dict) or "tam_estimate" not in data["market"] or "incumbents" not in data["market"]:
            raise ValueError("Invalid market structure")
        if not isinstance(data["score_breakdown"], dict):
            raise ValueError("Invalid score_breakdown structure")
            
        # Ensure score equals sum of breakdown scores
        breakdown = data["score_breakdown"]
        sum_breakdown = sum(
            breakdown.get(k, 0)
            for k in ["team", "product", "market", "moat", "traction"]
        )
        if data["score"] != sum_breakdown:
            data["score"] = sum_breakdown
            
        return data
    except (json.JSONDecodeError, ValueError) as e:
        print(f"JSON Parsing/Validation error: {e}")
        return None

def analyze_startup_openai(candidate: dict, homepage: dict) -> dict | None:
    """Primary method using OpenAI's gpt-4o-mini."""
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("OpenAI key not found.")
        return None
        
    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)
        
        prompt = build_prompt(candidate, homepage)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        raw = response.choices[0].message.content
        return parse_analysis(raw)
    except Exception as e:
        print(f"OpenAI analysis failed: {e}")
        return None

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, max=60), reraise=True)
def analyze_startup_gemini_with_retry(prompt: str) -> str:
    """Attempts to generate content with Gemini 2.0 Flash."""
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            temperature=0.3,
            response_mime_type="application/json",
        )
    )
    return response.text

def analyze_startup_gemini(candidate: dict, homepage: dict) -> dict | None:
    """Fallback method using Gemini 2.0 Flash."""
    if not os.getenv("GEMINI_API_KEY"):
        print("Gemini API key not found. Skipping fallback.")
        return None
        
    print(f"Falling back to Gemini for: {candidate['name']}")
    try:
        prompt = build_prompt(candidate, homepage)
        raw = analyze_startup_gemini_with_retry(prompt)
        return parse_analysis(raw)
    except Exception as e:
        print(f"Gemini fallback failed: {e}")
        return None

def analyze_startup(candidate: dict, homepage: dict) -> dict | None:
    """
    Builds context, sends to OpenAI (Primary) and falls back to Gemini if OpenAI fails.
    """
    if os.getenv("OPENAI_API_KEY"):
        analysis = analyze_startup_openai(candidate, homepage)
        if analysis is not None:
            return analysis
            
    # Try Gemini if OpenAI key is missing or failed
    return analyze_startup_gemini(candidate, homepage)
