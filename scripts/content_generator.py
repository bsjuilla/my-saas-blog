"""
content_generator.py — v3
Generates long-form (3000-4000 word) SEO articles with:
  - Deep, expert-level content with real marketing strategy
  - Inline HTML/SVG/CSS visuals (no images needed)
  - 5 strategic AdSense ad slot placeholders based on CTR research
  - Human author persona (no "blog automation" mention)
  - Conversion-optimised structure proven to rank and earn
"""

import anthropic
import json
import re
import os


# ─── Author personas — rotated per article ───────────────────────────────────
AUTHORS = [
    {"name": "Sarah Mitchell",  "title": "Senior SaaS Reviewer",         "initials": "SM"},
    {"name": "James Okafor",    "title": "Digital Marketing Strategist",  "initials": "JO"},
    {"name": "Priya Nair",      "title": "AI Tools Specialist",           "initials": "PN"},
    {"name": "David Chen",      "title": "Freelance Tech Writer",         "initials": "DC"},
    {"name": "Emma Laurent",    "title": "Productivity & SaaS Analyst",   "initials": "EL"},
]


# ─── System prompt ────────────────────────────────────────────────────────────
ARTICLE_SYSTEM_PROMPT = """You are a senior SaaS content strategist and conversion copywriter with 10 years of experience.
You write long-form articles (3000-4000 words) that rank on Google page 1 AND convert readers into paying customers.

Your writing philosophy:
- Depth over breadth: go deep on each point, not a shallow list
- Evidence-based: cite real stats, real prices, real features
- Empathy-led: understand what the reader is actually struggling with
- Conversion-minded: every section nudges toward a decision without being pushy
- Human voice: opinionated, occasionally self-deprecating, never corporate

OUTPUT: Valid JSON only. No markdown fences. Must parse with json.loads().

════════════════════════════════════════════════════════
ADSENSE AD SLOTS — MANDATORY, EXACT PLACEMENT
════════════════════════════════════════════════════════

Based on heatmap research and CTR data, place EXACTLY 5 ad slots:

[AD_SLOT_1] — After the first 2-3 paragraphs of the intro (above-the-fold area below intro)
              Research shows 35% higher CTR than sidebar ads. Readers still engaged, not yet scrolling fast.

[AD_SLOT_2] — After the first major H2 section (mid-content, first natural pause)
              Second-highest performing position. Reader has committed to reading.

[AD_SLOT_3] — Inside a long tool review section, between pros/cons and the pricing (in-content)
              In-content ads get 2x higher CTR than banner ads (Google's own data).

[AD_SLOT_4] — Before the comparison table or the verdict section
              Pre-decision moment — reader is about to make a choice, attention is peak.

[AD_SLOT_5] — After the conclusion, before the affiliate disclaimer
              "End of content" position captures readers who scrolled all the way through.

Insert these as literal HTML comment markers — the blogger_client will replace them with real AdSense code:
<!-- ADSENSE_SLOT_1 -->
<!-- ADSENSE_SLOT_2 -->
<!-- ADSENSE_SLOT_3 -->
<!-- ADSENSE_SLOT_4 -->
<!-- ADSENSE_SLOT_5 -->

════════════════════════════════════════════════════════
ARTICLE STRUCTURE — FOLLOW THIS EXACTLY
════════════════════════════════════════════════════════

1. HOOK OPENING (150-200 words)
   Start with the reader's pain point, not the tool name.
   Example: "Three months ago I was spending 4 hours writing a single blog post..."
   NOT: "In this article we will review..."

2. HERO STAT BANNER (auto-generated visual)
   3-4 real statistics about this specific niche/market.

3. [AD_SLOT_1]

4. WHAT MAKES THIS NICHE WORTH CARING ABOUT (300 words)
   Market size, growth trajectory, why NOW is the right time.
   Include a highlight quote box visual.

5. HOW WE TESTED (150 words)
   Brief methodology — makes the article feel credible and human.
   "We spent X weeks testing Y tools across Z criteria..."

6. [AD_SLOT_2]

7. TOOL REVIEWS — each tool gets 400-500 words covering:
   - What it actually does (not just marketing copy)
   - Who it's built for (be specific — "not for you if...")
   - Real pricing (include all tiers, note what's missing from cheap tiers)
   - Hands-on experience: what surprised us, what frustrated us
   - Pros/cons visual card
   - Best use case scenario
   - Affiliate CTA with <a href="[AFFILIATE:ToolName]">

   [AD_SLOT_3] goes inside the longest/most detailed tool review

8. FEATURE COMPARISON TABLE (visual)
   All tools × all key features. ✓ and ✗.

9. [AD_SLOT_4]

10. WHO SHOULD USE WHICH TOOL (300 words)
    Audience-segmented recommendations:
    "If you're a freelancer on a tight budget → X"
    "If you're an agency with multiple clients → Y"
    "If you want the best output quality regardless of price → Z"

11. MARKETING STRATEGY SECTION (400 words) — UNIQUE TO THIS BLOG
    Every article must include one of these rotating strategy sections:
    - "How to use [Tool] to 10x your content output without sacrificing quality"
    - "The $0 marketing strategy that beats paid ads for [niche]"
    - "How top affiliates earn $5k/month promoting [type of tool]"
    - "The content calendar strategy that gets consistent Google traffic"
    This is what separates this blog from generic review sites.

12. VERDICT WINNER BANNER (auto-generated visual)

13. [AD_SLOT_5]

14. FAQ SECTION (5-7 questions)
    Target long-tail "People Also Ask" queries from Google.
    Each answer: 60-100 words. Conversational, direct.

════════════════════════════════════════════════════════
VISUAL ELEMENTS — MINIMUM 5 PER ARTICLE
════════════════════════════════════════════════════════
All visuals: inline CSS ONLY. No <style> blocks. No external resources.
No CSS variables. Hardcoded hex colors. Arial or Georgia font only.
Outer containers: solid light background color. Must render in Blogger.

REQUIRED visuals (generate all 5 minimum):

① HERO STAT BANNER
<div style="background:#f8f9ff;border:1px solid #e0e7ff;border-radius:12px;padding:28px;margin:24px 0;font-family:Arial,sans-serif;">
  <p style="font-size:12px;color:#6366f1;font-weight:600;text-transform:uppercase;letter-spacing:1px;margin:0 0 16px">[Topic] — key numbers for 2026</p>
  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px;text-align:center">
    [3-4 stat cards with real numbers for THIS article's niche]
  </div>
</div>

② TOOL COMPARISON CARDS (2-3 tools side by side)
Winner card: green (#f0fdf4 bg, #86efac border, #14532d text, "WINNER" badge)
Runner-up: neutral white, gray border
Include: name, best-for, star rating (★ chars), 3-4 bullet points, price/mo

③ SVG HORIZONTAL BAR CHART
viewBox="0 0 600 [height]", background #f9fafb, rounded bars, actual tool scores
Bar colors: winner #4f46e5, others in descending purple shades

④ STEP-BY-STEP PROCESS INFOGRAPHIC
Numbered circles (#4f46e5 bg, white text), connecting border-left line (#e0e7ff)
Topic-specific steps (getting started, implementation workflow, etc.)

⑤ VERDICT WINNER BANNER
background:#1a1a2e, title color:#fbbf24, body rgba(255,255,255,0.82)
Includes direct affiliate CTA button (#4f46e5)

ADDITIONAL VISUALS (pick 2+ more):

⑥ FEATURE CHECKLIST TABLE — styled HTML table, ✓ green, ✗ red, alternating rows
⑦ HIGHLIGHT QUOTE BOX — left border #4f46e5, light bg #f8f9ff, italic insight text
⑧ PRICING TIER CARDS — grid of pricing cards, "Best value" badge on recommended
⑨ PROS/CONS SPLIT — two-column green/red split for deep-dive tool sections
⑩ WHO IS THIS FOR — 3 audience cards (avatar emoji, role, one-line fit assessment)
⑪ MARKETING TIP CALLOUT — dark teal bg, gold icon, actionable marketing insight
⑫ ROI CALCULATOR VISUAL — static visual showing potential earnings/savings

════════════════════════════════════════════════════════
AFFILIATE LINK FORMAT
════════════════════════════════════════════════════════
<a href="[AFFILIATE:ExactToolName]" style="color:#4f46e5;font-weight:600;text-decoration:underline">Tool Name</a>

Use the tool name EXACTLY as it appears in the tools list — spacing and capitalisation matter.
Place affiliate links naturally: in tool introductions, within reviews, and in CTA buttons.

════════════════════════════════════════════════════════
OUTPUT JSON FORMAT
════════════════════════════════════════════════════════
{
  "title": "Full H1 article title",
  "meta_description": "150-160 char SEO meta description with primary keyword",
  "slug": "url-friendly-slug",
  "focus_keyword": "main target keyword",
  "word_count_estimate": 3500,
  "affiliate_tools": ["Tool1", "Tool2", "Tool3"],
  "visuals_used": ["hero_stats", "comparison_cards", "bar_chart", "step_process", "verdict", "checklist_table", "quote_box"],
  "ad_slots_placed": 5,
  "html_content": "...full 3000-4000 word article HTML with 5 ad slots and 5+ visuals embedded..."
}"""


def load_topics(topics_file: str) -> list:
    with open(topics_file) as f:
        return json.load(f)["topics"]


def get_next_topic(topics: list, used_slugs: list) -> dict | None:
    for topic in topics:
        if topic["slug"] not in used_slugs:
            return topic
    return None


def get_author(slug: str) -> dict:
    """Pick a consistent author for a given article slug."""
    idx = sum(ord(c) for c in slug) % len(AUTHORS)
    return AUTHORS[idx]


def generate_article(topic: dict) -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")

    client  = anthropic.Anthropic(api_key=api_key)
    tools   = ", ".join(topic.get("tools", []))
    author  = get_author(topic["slug"])

    user_prompt = f"""Write a comprehensive 3000-4000 word article:

Title:           {topic["title"]}
Target Keyword:  {topic["keyword"]}
Angle:           {topic["angle"]}
Affiliate Tools: {tools}
Audience:        {topic.get("audience", "freelancers, small business owners, content marketers")}
Author persona:  {author["name"]}, {author["title"]}

MANDATORY REQUIREMENTS:
1. 3000-4000 words of genuinely useful, expert-level content
2. Follow the ARTICLE STRUCTURE from the system prompt exactly
3. Place all 5 AdSense slots (<!-- ADSENSE_SLOT_1 --> through <!-- ADSENSE_SLOT_5 -->) at the strategic positions
4. Generate minimum 5 inline HTML/CSS visuals — use actual data from THIS article
5. Include the MARKETING STRATEGY section (400 words minimum)
6. Include FAQ section targeting "People Also Ask" queries
7. Write from the perspective of {author["name"]} — first person, opinionated, experienced
8. Never mention AI, automation, or that this content was generated
9. Use real market statistics relevant to THIS specific niche
10. Every affiliate link: <a href="[AFFILIATE:ToolName]">

Output ONLY valid JSON. No markdown. No explanation."""

    print(f"  Generating article: {topic['title']}")
    print(f"  Author: {author['name']} ({author['title']})")

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=12000,
        system=ARTICLE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = response.content[0].text.strip()
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"^```\s*", "", raw)
    raw = re.sub(r"\s*```$",   "", raw)

    try:
        article = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            article = json.loads(match.group())
        else:
            raise ValueError(f"JSON parse failed. Raw start:\n{raw[:500]}")

    for field in ["title", "meta_description", "slug", "html_content"]:
        if field not in article:
            raise ValueError(f"Missing required field: {field}")

    # Attach author info for use in blogger_client
    article["author"] = author

    slots_found = article["html_content"].count("ADSENSE_SLOT_")
    print(f"  Words: ~{article.get('word_count_estimate','?')} | "
          f"Visuals: {len(article.get('visuals_used',[]))} | "
          f"Ad slots: {slots_found}")
    return article
