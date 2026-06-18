import os
import re
from datetime import datetime

def slugify(name: str) -> str:
    """Converts a company name to a safe filename slug."""
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

def render_memo(analysis: dict, candidate: dict) -> str:
    """Renders the analyzed startup data and HN candidate details into markdown."""
    # Handle nested dictionaries with safe defaults
    team = analysis.get("team", {})
    product = analysis.get("product", {})
    market = analysis.get("market", {})
    score_breakdown = analysis.get("score_breakdown", {})
    
    # Process risks list
    risks = analysis.get("risks", [])
    if risks:
        risks_str = "\n".join(f"{i+1}. {r}" for i, r in enumerate(risks))
    else:
        risks_str = "None identified."
        
    # Process mind changers list
    mind_changers = analysis.get("mind_changers", [])
    if mind_changers:
        mind_changers_str = "\n".join(f"{i+1}. {mc}" for i, mc in enumerate(mind_changers))
    else:
        mind_changers_str = "None identified."
        
    # Format data gaps
    data_gaps = analysis.get("data_gaps", [])
    data_gaps_str = ""
    if data_gaps:
        data_gaps_str = f"\n**Data gaps:** {'; '.join(data_gaps)}\n"
        
    # Format incumbents
    incumbents = market.get("incumbents", [])
    if isinstance(incumbents, list):
        incumbents_str = ", ".join(incumbents)
    else:
        incumbents_str = str(incumbents)
        
    # Format founders
    founders = team.get("founder_names", [])
    if isinstance(founders, list):
        founders_str = ", ".join(founders)
    else:
        founders_str = str(founders)
        
    posted_date = candidate.get("posted_at", "")[:10] if candidate.get("posted_at") else "Unknown date"
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    memo_template = f"""# {analysis.get('name')} — {analysis.get('recommendation')}

**Score: {analysis.get('score')}/100** | HN: {candidate.get('hn_points', 0)} pts / {candidate.get('hn_comments', 0)} comments | {posted_date}

---

_The footer includes exact source attribution and traction metrics for traceability._

## One-liner

{analysis.get('one_liner', 'Not available.')}

## Team

{team.get('summary', 'Not available.')}

**Founders:** {founders_str or 'Unknown'}

_Technical depth: {team.get('technical_depth', 0)}/5 | Prior exit: {team.get('prior_exit', False)} | Data confidence: {team.get('data_quality', 'low')}_

## Product

{product.get('summary', 'Not available.')}

**Workflow automated:** {product.get('workflow_automated', 'Not available.')}  
**How AI is used:** {product.get('ai_role', 'Not available.')}

## Market

{market.get('summary', 'Not available.')}

**TAM estimate:** {market.get('tam_estimate', 'Unknown')}  
**Incumbents:** {incumbents_str or 'None listed'}  
**Why now:** {market.get('why_now', 'Not available.')}

## Risks & Open Questions

{risks_str}

## Scoring

| Dimension | Score                      | Max     |
| --------- | -------------------------- | ------- |
| Team      | {score_breakdown.get('team', 0)}     | 25      |
| Product   | {score_breakdown.get('product', 0)}  | 20      |
| Market    | {score_breakdown.get('market', 0)}   | 20      |
| Moat      | {score_breakdown.get('moat', 0)}     | 20      |
| Traction  | {score_breakdown.get('traction', 0)} | 15      |
| **Total** | **{analysis.get('score', 0)}**                | **100** |

---

## Call: {analysis.get('recommendation')}

{analysis.get('rationale', 'No rationale provided.')}

**What would change our mind:**

{mind_changers_str}
{data_gaps_str}
---

_Sources: [HN Post]({candidate.get('hn_url', '#')}) · [Homepage]({analysis.get('website', '#')}) · Analyzed: {today_str}_
"""
    return memo_template

def generate_memo(analysis: dict, candidate: dict, output_dir: str) -> str:
    """
    Renders analysis + HN data into a markdown memo.
    Saves to output_dir/{slug}_memo.md.
    Returns file path.
    """
    os.makedirs(output_dir, exist_ok=True)
    filename = slugify(analysis["name"]) + "_memo.md"
    path = os.path.join(output_dir, filename)
    
    content = render_memo(analysis, candidate)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
        
    return path
