THESIS = (
    "B2B software that uses LLMs to fully automate a single, previously human-executed "
    "operational workflow for businesses with 10–200 employees, in markets where the "
    "incumbent is either spreadsheets or legacy SaaS priced above $100/seat/month. "
    "At least one technical co-founder required. Excludes: consumer apps, AI copilots "
    "that assist but still need a human in the loop, horizontal platforms, and pure "
    "infrastructure plays."
)

SCORE_THRESHOLDS = {
    "take_a_meeting": 66,
    "watch": 41,
    "pass": 0,
}

GEMINI_RPM_SLEEP = 4   # seconds between calls to stay under 15 RPM
MAX_HOMEPAGE_CHARS = 1500
MIN_HN_POINTS_DEFAULT = 10
DEFAULT_COUNT = 15
