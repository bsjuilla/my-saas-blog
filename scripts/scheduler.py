"""
scheduler.py — v3
Fully automated pipeline: generate → draft → publish.
No human steps. Emails are FYI only.
"""

import argparse, json, os, sys, smtplib
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from content_generator import generate_article, load_topics, get_next_topic
from blogger_client    import create_draft, publish_post, get_draft_preview_url

DRAFTS_FILE = "data/drafts.json"
TOPICS_FILE = "data/article_topics.json"


def load_drafts() -> list:
    if not Path(DRAFTS_FILE).exists():
        return []
    with open(DRAFTS_FILE) as f:
        return json.load(f)

def save_drafts(drafts: list) -> None:
    with open(DRAFTS_FILE, "w") as f:
        json.dump(drafts, f, indent=2)
    print(f"  Saved {len(drafts)} drafts.")


def next_publish_date(drafts: list) -> str:
    taken       = {d["publish_date"] for d in drafts if d.get("publish_date")}
    publish_days = {0, 2, 4}   # Mon, Wed, Fri
    check = datetime.now(timezone.utc) + timedelta(days=1)
    for _ in range(30):
        if check.weekday() in publish_days and check.strftime("%Y-%m-%d") not in taken:
            return check.strftime("%Y-%m-%d")
        check += timedelta(days=1)
    raise RuntimeError("No free publish slot in next 30 days")


def send_email(subject: str, body_html: str) -> None:
    gu = os.environ.get("GMAIL_USER")
    gp = os.environ.get("GMAIL_APP_PASSWORD")
    ne = os.environ.get("NOTIFY_EMAIL")
    if not all([gu, gp, ne]):
        print("  Email skipped — env vars not set")
        return
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"Blog System <{gu}>"
    msg["To"]      = ne
    msg.attach(MIMEText(body_html, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(gu, gp)
        s.sendmail(gu, ne, msg.as_string())
    print(f"  Email sent → {ne}")


# ── Actions ───────────────────────────────────────────────────────────────────

def action_generate() -> None:
    print("\n=== GENERATE ===")
    drafts     = load_drafts()
    used_slugs = [d["slug"] for d in drafts]
    topics     = load_topics(TOPICS_FILE)
    topic      = get_next_topic(topics, used_slugs)

    if not topic:
        print("All topics exhausted — add more to article_topics.json")
        return

    print(f"Topic: {topic['title']}")
    article      = generate_article(topic)
    publish_date = next_publish_date(drafts)
    post_id      = create_draft(article)
    preview_url  = get_draft_preview_url(post_id)
    author       = article.get("author", {})

    entry = {
        "id":               post_id,
        "title":            article["title"],
        "slug":             article["slug"],
        "meta_description": article["meta_description"],
        "focus_keyword":    article.get("focus_keyword", ""),
        "author_name":      author.get("name", ""),
        "author_title":     author.get("title", ""),
        "publish_date":     publish_date,
        "status":           "draft",
        "word_count":       article.get("word_count_estimate", 0),
        "visuals_used":     article.get("visuals_used", []),
        "ad_slots_placed":  article.get("ad_slots_placed", 5),
        "affiliate_tools":  article.get("affiliate_tools", []),
        "created_at":       datetime.now(timezone.utc).isoformat(),
        "published_at":     None,
        "published_url":    None,
        "blogger_post_id":  post_id,
        "blogger_preview_url": preview_url,
    }
    drafts.append(entry)
    save_drafts(drafts)

    send_email(
        subject=f"✍️ New article drafted — '{article['title']}'",
        body_html=f"""
        <div style="font-family:Arial;max-width:560px;margin:0 auto;padding:24px">
          <div style="background:#4f46e5;color:#fff;padding:20px;border-radius:8px;margin-bottom:20px">
            <h2 style="margin:0;font-size:18px">New article drafted automatically</h2>
          </div>
          <table style="width:100%;font-size:14px;border-collapse:collapse">
            <tr><td style="padding:8px 0;color:#6b7280;width:130px">Title</td>
                <td style="padding:8px 0;font-weight:600">{article['title']}</td></tr>
            <tr><td style="padding:8px 0;color:#6b7280">Author</td>
                <td style="padding:8px 0">{author.get('name','')} — {author.get('title','')}</td></tr>
            <tr><td style="padding:8px 0;color:#6b7280">Word count</td>
                <td style="padding:8px 0">~{article.get('word_count_estimate','?')} words</td></tr>
            <tr><td style="padding:8px 0;color:#6b7280">Ad slots</td>
                <td style="padding:8px 0">{article.get('ad_slots_placed',5)} placed strategically</td></tr>
            <tr><td style="padding:8px 0;color:#6b7280">Visuals</td>
                <td style="padding:8px 0">{', '.join(article.get('visuals_used',[]))}</td></tr>
            <tr><td style="padding:8px 0;color:#6b7280">Publishes</td>
                <td style="padding:8px 0;font-weight:600;color:#4f46e5">{publish_date} at 10:00 AM UTC</td></tr>
          </table>
          <p style="margin-top:20px">
            <a href="{preview_url}" style="background:#4f46e5;color:#fff;padding:10px 18px;
               border-radius:6px;text-decoration:none;font-size:13px">Preview draft on Blogger →</a>
          </p>
          <p style="font-size:12px;color:#9ca3af;margin-top:16px">No action needed. Publishes automatically.</p>
        </div>"""
    )
    print(f"\n✅ DONE — publishes {publish_date} | preview: {preview_url}")


def action_publish() -> None:
    print("\n=== PUBLISH ===")
    drafts    = load_drafts()
    today     = datetime.now(timezone.utc).date()
    published = 0

    for draft in drafts:
        if draft.get("status") == "published":
            continue
        try:
            pub_date = datetime.strptime(draft["publish_date"], "%Y-%m-%d").date()
        except (ValueError, KeyError):
            continue
        if pub_date != today:
            continue

        print(f"Publishing: {draft['title']}")
        try:
            live_url = publish_post(draft["blogger_post_id"])
            draft.update({
                "status":       "published",
                "published_at": datetime.now(timezone.utc).isoformat(),
                "published_url": live_url,
            })
            published += 1

            send_email(
                subject=f"🚀 Published! '{draft['title']}'",
                body_html=f"""
                <div style="font-family:Arial;max-width:560px;margin:0 auto;padding:24px">
                  <div style="background:#059669;color:#fff;padding:20px;border-radius:8px;margin-bottom:20px;text-align:center">
                    <h2 style="margin:0">🚀 Article is Live!</h2>
                  </div>
                  <p style="font-size:15px;font-weight:600">{draft['title']}</p>
                  <p>Written by: {draft.get('author_name','')}</p>
                  <p>Word count: ~{draft.get('word_count',0):,} words</p>
                  <p>Ad slots active: {draft.get('ad_slots_placed',5)}</p>
                  <p style="margin-top:16px">
                    <a href="{live_url}" style="background:#059669;color:#fff;padding:10px 18px;
                       border-radius:6px;text-decoration:none">View live article →</a>
                  </p>
                  <p style="font-size:12px;color:#9ca3af;margin-top:16px">Next article generates automatically. No action needed.</p>
                </div>"""
            )
            print(f"  ✅ Live: {live_url}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
            send_email(
                subject=f"⚠️ Publish failed — '{draft['title']}'",
                body_html=f"<p style='font-family:Arial'>Error: {e}<br>Post ID: {draft.get('blogger_post_id')}</p>"
            )

    save_drafts(drafts)
    print(f"\n✅ PUBLISH DONE — {published} published today")


def action_status() -> None:
    drafts = load_drafts()
    if not drafts:
        print("No drafts yet.")
        return
    print(f"\n{'Title':<40} {'Author':<18} {'Words':<8} {'Status':<12} {'Publish'}")
    print("-" * 95)
    for d in drafts:
        print(f"{d['title'][:39]:<40} {d.get('author_name','?')[:17]:<18} "
              f"{d.get('word_count',0):<8} {d['status']:<12} {d.get('publish_date','?')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", choices=["generate","publish","status"], required=True)
    args = parser.parse_args()
    {"generate": action_generate, "publish": action_publish, "status": action_status}[args.action]()
