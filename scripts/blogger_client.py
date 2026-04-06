"""
blogger_client.py — v3
Handles Blogger API v3.
Key additions over v2:
  - Injects real AdSense ad units at 5 strategic slot positions
  - Renders a human author byline (name, title, initials avatar)
  - Resolves affiliate link placeholders
  - Adds full SEO meta wrapper
"""

import os, re, json
from pathlib import Path
from datetime import datetime, timezone
import requests

BLOGGER_TOKEN_URL = "https://oauth2.googleapis.com/token"
BLOGGER_API_BASE  = "https://www.googleapis.com/blogger/v3"


# ─── AdSense ad unit HTML ────────────────────────────────────────────────────
# YOUR_ADSENSE_PUBLISHER_ID and YOUR_AD_SLOT_ID are replaced at runtime
# from the ADSENSE_PUBLISHER_ID and ADSENSE_SLOT_ID env vars.
# Sizes used are based on highest-CTR research:
#   Slot 1, 4, 5 → 728×90 leaderboard (best for above/below content)
#   Slot 2, 3    → 336×280 large rectangle (best CTR in-content per Google)

def _ad_unit(position: int, pub_id: str, slot_id: str) -> str:
    """
    Returns the AdSense responsive ad unit HTML for a given position.
    Uses the statistically best-performing format for each position.
    """
    # In-content positions (2 and 3) use large rectangle — highest in-content CTR
    if position in (2, 3):
        return f"""
<div style="text-align:center;margin:28px 0;padding:16px 0;border-top:1px solid #f3f4f6;border-bottom:1px solid #f3f4f6">
  <ins class="adsbygoogle"
       style="display:block"
       data-ad-client="{pub_id}"
       data-ad-slot="{slot_id}"
       data-ad-format="rectangle"
       data-full-width-responsive="true"></ins>
  <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
</div>"""
    # Above-fold, pre-decision, end-of-content → responsive leaderboard
    return f"""
<div style="text-align:center;margin:28px 0;padding:12px 0;border-top:1px solid #f3f4f6;border-bottom:1px solid #f3f4f6">
  <ins class="adsbygoogle"
       style="display:block"
       data-ad-client="{pub_id}"
       data-ad-slot="{slot_id}"
       data-ad-format="auto"
       data-full-width-responsive="true"></ins>
  <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
</div>"""


def _draft_ad_placeholder(position: int) -> str:
    """
    In draft mode (no AdSense credentials), insert a clearly visible
    placeholder so you can visually verify ad positioning.
    """
    labels = {
        1: "After intro — above fold (leaderboard)",
        2: "Post first section — in content (large rectangle, 2× CTR)",
        3: "Inside tool review — in content (large rectangle, 2× CTR)",
        4: "Pre-verdict — peak attention (leaderboard)",
        5: "Post conclusion — end of content (leaderboard)",
    }
    return f"""
<div style="background:#fff8e1;border:2px dashed #f59e0b;border-radius:8px;
     padding:16px;text-align:center;margin:28px 0;font-family:Arial,sans-serif">
  <p style="font-size:12px;color:#92400e;font-weight:600;margin:0 0 4px">
    📢 AD SLOT {position}
  </p>
  <p style="font-size:11px;color:#b45309;margin:0">{labels.get(position,'')}</p>
</div>"""


# ─── Blogger API helpers ──────────────────────────────────────────────────────

def _get_access_token() -> str:
    r = requests.post(BLOGGER_TOKEN_URL, data={
        "grant_type":    "refresh_token",
        "client_id":     os.environ["BLOGGER_CLIENT_ID"],
        "client_secret": os.environ["BLOGGER_CLIENT_SECRET"],
        "refresh_token": os.environ["BLOGGER_REFRESH_TOKEN"],
    })
    if r.status_code != 200:
        raise RuntimeError(f"Token error: {r.status_code} — {r.text}")
    return r.json()["access_token"]


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {_get_access_token()}",
        "Content-Type":  "application/json",
    }


def create_draft(article: dict) -> str:
    blog_id = os.environ["BLOGGER_BLOG_ID"]
    html    = _build_full_post(article, is_draft=True)

    r = requests.post(
        f"{BLOGGER_API_BASE}/blogs/{blog_id}/posts?isDraft=true",
        headers=_headers(),
        json={
            "title":   article["title"],
            "content": html,
            "labels":  article.get("affiliate_tools", [])[:5],
        },
    )
    if r.status_code not in (200, 201):
        raise RuntimeError(f"Draft failed {r.status_code}: {r.text}")

    post_id = r.json()["id"]
    print(f"  Blogger draft created — ID: {post_id}")
    return post_id


def publish_post(post_id: str) -> str:
    """Publishes a draft. Returns live URL."""
    blog_id = os.environ["BLOGGER_BLOG_ID"]

    # Before publishing, update the post with live AdSense code
    # (Draft was created with placeholder ads; now inject real ones)
    pub_id  = os.environ.get("ADSENSE_PUBLISHER_ID", "")
    slot_id = os.environ.get("ADSENSE_SLOT_ID", "")

    if pub_id and slot_id:
        # Fetch current draft content
        get_r = requests.get(
            f"{BLOGGER_API_BASE}/blogs/{blog_id}/posts/{post_id}",
            headers=_headers(),
        )
        if get_r.status_code == 200:
            current_html = get_r.json().get("content", "")
            # Replace placeholder ads with real AdSense units
            for i in range(1, 6):
                placeholder = f'<!-- ADSENSE_PLACEHOLDER_{i} -->'
                real_ad     = _ad_unit(i, pub_id, slot_id)
                current_html = current_html.replace(placeholder, real_ad)
            # Update post with live ads
            requests.patch(
                f"{BLOGGER_API_BASE}/blogs/{blog_id}/posts/{post_id}",
                headers=_headers(),
                json={"content": current_html},
            )
            print("  AdSense units injected for publish")

    r = requests.post(
        f"{BLOGGER_API_BASE}/blogs/{blog_id}/posts/{post_id}/publish",
        headers=_headers(),
    )
    if r.status_code not in (200, 201):
        raise RuntimeError(f"Publish failed {r.status_code}: {r.text}")

    url = r.json().get("url", "")
    print(f"  Published: {url}")
    return url


def get_draft_preview_url(post_id: str) -> str:
    blog_id = os.environ["BLOGGER_BLOG_ID"]
    return f"https://www.blogger.com/blog/post/edit/{blog_id}/{post_id}"


# ─── HTML builder ─────────────────────────────────────────────────────────────

def _build_full_post(article: dict, is_draft: bool = False) -> str:
    content  = article["html_content"]
    author   = article.get("author", {"name": "Sarah Mitchell",
                                      "title": "Senior SaaS Reviewer",
                                      "initials": "SM"})
    pub_id   = os.environ.get("ADSENSE_PUBLISHER_ID", "")
    slot_id  = os.environ.get("ADSENSE_SLOT_ID", "")

    # ── 1. Resolve affiliate links ────────────────────────────────────────────
    aff_file  = Path("data/affiliate_links.json")
    aff_links = json.loads(aff_file.read_text()) if aff_file.exists() else {}

    def replace_affiliate(m):
        tool = m.group(1)
        url  = aff_links.get(tool, f"https://google.com/search?q={tool.replace(' ', '+')}")
        return url

    content = re.sub(r"\[AFFILIATE:([^\]]+)\]", replace_affiliate, content)

    # ── 2. Inject AdSense slots ───────────────────────────────────────────────
    for i in range(1, 6):
        marker = f"<!-- ADSENSE_SLOT_{i} -->"
        if is_draft:
            # Draft: show styled placeholder so you can verify position
            ad_html = _draft_ad_placeholder(i)
        elif pub_id and slot_id:
            # Publish with real AdSense (injected fresh in publish_post)
            # For now insert a placeholder that gets replaced in publish_post
            ad_html = f"<!-- ADSENSE_PLACEHOLDER_{i} -->"
        else:
            # No AdSense configured yet — leave empty
            ad_html = ""
        content = content.replace(marker, ad_html)

    # ── 3. Author byline HTML ─────────────────────────────────────────────────
    today      = datetime.now(timezone.utc).strftime("%B %d, %Y")
    initials   = author["initials"]
    # Pick avatar background colour deterministically from initials
    colours    = ["#4f46e5","#0891b2","#059669","#d97706","#dc2626","#7c3aed"]
    bg_colour  = colours[sum(ord(c) for c in initials) % len(colours)]

    byline_html = f"""
<div style="display:flex;align-items:center;gap:12px;padding:16px 0;
            border-top:1px solid #f3f4f6;border-bottom:1px solid #f3f4f6;
            margin:0 0 24px;font-family:Arial,sans-serif">
  <div style="width:44px;height:44px;border-radius:50%;background:{bg_colour};
              display:flex;align-items:center;justify-content:center;
              color:#fff;font-size:14px;font-weight:700;flex-shrink:0">
    {initials}
  </div>
  <div>
    <div style="font-size:14px;font-weight:700;color:#111">{author["name"]}</div>
    <div style="font-size:12px;color:#6b7280">{author["title"]} · {today}</div>
  </div>
</div>"""

    # ── 4. Affiliate disclaimer ───────────────────────────────────────────────
    disclaimer = """
<hr style="margin:40px 0;border:none;border-top:1px solid #e5e7eb" />
<p style="font-size:12px;color:#9ca3af;text-align:center;font-family:Arial,sans-serif;line-height:1.6">
  Some links in this article are affiliate links. If you purchase through them, 
  we may earn a commission at no extra cost to you. 
  We only recommend tools we have personally tested and genuinely find valuable.
</p>"""

    # ── 5. Assemble final HTML ────────────────────────────────────────────────
    return f"{byline_html}{content}{disclaimer}"
