import os
import sys
import json
import argparse
import time
from datetime import datetime
from rich.console import Console
from rich.table import Table

from sourcer.hn import fetch_hn_startups
from scraper.homepage import scrape_homepage
from analyzer.analyze import analyze_startup
from memo.generator import generate_memo
import config

console = Console()

def parse_args():
    parser = argparse.ArgumentParser(description="AI-Augmented Investment Pipeline")
    parser.add_argument("--topic", type=str, required=True, help="Topic or query string to search on HN")
    parser.add_argument("--count", type=int, default=config.DEFAULT_COUNT, help="Number of startups to analyze (default: 15)")
    parser.add_argument("--min-pts", type=int, default=config.MIN_HN_POINTS_DEFAULT, help="Minimum HN upvotes to include (default: 10)")
    parser.add_argument("--output", type=str, default="./outputs", help="Output directory for memos (default: ./outputs)")
    parser.add_argument("--dry-run", action="store_true", help="Source only — no AI calls, prints candidates to terminal")
    return parser.parse_args()

def save_json(path: str, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_json(path: str):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def log_error(name: str, message: str):
    os.makedirs("data", exist_ok=True)
    with open("errors.log", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} | {name} | {message}\n")

def print_candidates_table(candidates):
    table = Table(title=f"Sourced Candidates ({len(candidates)})")
    table.add_column("Startup", style="cyan")
    table.add_column("HN Points", style="green")
    table.add_column("HN Comments", style="magenta")
    table.add_column("HN Author", style="yellow")
    table.add_column("Website", style="blue")
    
    for c in candidates:
        table.add_row(
            c["name"],
            str(c["hn_points"]),
            str(c["hn_comments"]),
            c["hn_author"],
            c["url"]
        )
    console.print(table)

def print_summary_table(results):
    table = Table(title="Pipeline Summary")
    table.add_column("Startup", style="cyan")
    table.add_column("Score", style="green")
    table.add_column("Recommendation", style="bold")
    table.add_column("Memo Path", style="blue")
    
    for r in results:
        rec_color = "red"
        if r["rec"].lower() == "take a meeting":
            rec_color = "green"
        elif r["rec"].lower() == "watch":
            rec_color = "yellow"
            
        table.add_row(
            r["name"],
            str(r["score"]),
            f"[{rec_color}]{r['rec']}[/{rec_color}]",
            r["path"]
        )
    console.print(table)

def main():
    args = parse_args()
    
    console.print(f"[bold blue]Starting Sourcing Layer for topic: '{args.topic}'[/bold blue]")
    candidates = fetch_hn_startups(
        topic=args.topic,
        count=args.count,
        min_points=args.min_pts
    )
    
    if not candidates:
        console.print("[yellow]No candidates found matching the criteria.[/yellow]")
        return
        
    save_json("data/1_sourced.json", candidates)
    console.print(f"[green]Sourced {len(candidates)} candidates from HN[/green]")
    console.print("[blue]Saved raw sourced data to data/1_sourced.json[/blue]")
    
    if args.dry_run:
        print_candidates_table(candidates)
        return
        
    # Load analysis cache to avoid unnecessary calls during prompt tuning / retries
    analysis_cache = load_json("data/2_analyzed.json")
    if not isinstance(analysis_cache, dict):
        analysis_cache = {}
        
    results = []
    
    for i, candidate in enumerate(candidates, 1):
        name = candidate["name"]
        url = candidate["url"]
        console.print(f"\n[bold][{i}/{len(candidates)}] Processing: {name}[/bold]")
        
        # Check cache (match by url or name)
        cached_analysis = analysis_cache.get(url) or analysis_cache.get(name)
        
        if cached_analysis:
            console.print(f"[green]Found cached analysis for {name}[/green]")
            try:
                memo_path = generate_memo(cached_analysis, candidate, args.output)
                results.append({
                    "name": name,
                    "score": cached_analysis["score"],
                    "rec": cached_analysis["recommendation"],
                    "path": memo_path
                })
                continue
            except Exception as e:
                console.print(f"[red]Failed to render cached memo for {name}: {e}[/red]")
                # fall through to fresh analysis if cache is corrupt or template rendering fails
        
        console.print(f"Scraping homepage: {url}")
        homepage = scrape_homepage(url)
        if not homepage["success"]:
            console.print(f"[yellow]Scrape failed: {homepage['error']}[/yellow]")
            
        console.print(f"Analyzing {name} with LLM...")
        analysis = analyze_startup(candidate, homepage)
        
        if analysis is None:
            console.print(f"[red]Failed to analyze {name}[/red]")
            log_error(name, "Analysis returned None")
            continue
            
        console.print(f"[green]Analysis complete. Score: {analysis['score']} -> Recommendation: {analysis['recommendation']}[/green]")
        
        # Update cache (use both name and url as keys for flexible lookup)
        analysis_cache[name] = analysis
        analysis_cache[url] = analysis
        save_json("data/2_analyzed.json", analysis_cache)
        
        try:
            memo_path = generate_memo(analysis, candidate, args.output)
            results.append({
                "name": name,
                "score": analysis["score"],
                "rec": analysis["recommendation"],
                "path": memo_path
            })
            console.print(f"Memo generated at: {memo_path}")
        except Exception as e:
            console.print(f"[red]Failed to generate memo for {name}: {e}[/red]")
            log_error(name, f"Memo generation exception: {str(e)}")
            
        # Enforce rate-limit sleep to stay under Gemini RPM limit (15 RPM)
        time.sleep(config.GEMINI_RPM_SLEEP)
        
    console.print("\n[bold green]Pipeline Run Completed[/bold green]")
    if results:
        print_summary_table(results)
    else:
        console.print("[red]No successful memos generated.[/red]")

if __name__ == "__main__":
    main()
