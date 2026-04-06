# 🤖 Automated SaaS/AI Blog — v2 (Zero Human Intervention)

Claude writes the article AND generates all visuals. Publishes 3x/week automatically.

## What Claude generates instead of images

Every article gets 5+ of these auto-generated inline visuals:
- Hero Stat Banner — big numbers about the niche
- Tool Comparison Cards — color-coded side-by-side
- SVG Bar Chart — tool scores visualised
- Step-by-Step Process Infographic
- Verdict Winner Banner — dark/gold recommendation
- Feature Checklist Table — ✓/✗ grid
- Highlight Quote Boxes, Pricing Cards, Pros/Cons splits

## Pipeline

Tue/Thu/Sat 2am → Claude writes article + visuals → Blogger draft created → Email (FYI)
Mon/Wed/Fri 10am → Auto-publish → Live URL emailed to you

Your work: zero. Check email to see what went live.

## Setup (one-time, ~45 min)

### 1. GitHub repo — upload all these files

### 2. Blogger blog — blogger.com → Create New Blog

### 3. Google Cloud — enable Blogger API v3, create OAuth Desktop App credentials

### 4. Get refresh token
```bash
pip install google-auth-oauthlib requests
python tools/get_refresh_token.py
```

### 5. Anthropic API key — console.anthropic.com (add $5 credit)

### 6. Gmail App Password — Google Account → Security → App Passwords

### 7. GitHub Secrets (Settings → Secrets → Actions)

| Secret | Value |
|---|---|
| ANTHROPIC_API_KEY | sk-ant-... |
| BLOGGER_BLOG_ID | from step 4 |
| BLOGGER_CLIENT_ID | from Google Cloud |
| BLOGGER_CLIENT_SECRET | from Google Cloud |
| BLOGGER_REFRESH_TOKEN | from step 4 |
| GMAIL_USER | you@gmail.com |
| GMAIL_APP_PASSWORD | 16-char password |
| NOTIFY_EMAIL | you@gmail.com |

### 8. Affiliate links (create data/affiliate_links.json)
```json
{
  "Jasper AI": "https://jasper.ai?fpr=YOUR_ID",
  "GetResponse": "https://app.getresponse.com/affiliate/YOUR_ID",
  "Semrush": "https://semrush.com/your-link",
  "ClickUp": "https://clickup.com/?ref=YOUR_ID",
  "Surfer SEO": "https://surferseo.com/your-id",
  "Hostinger": "https://hostinger.com/your-id"
}
```

### 9. Enable GitHub Actions → test with manual workflow trigger

## Cost
~$19/year total (domain + ~$0.60/month Claude API for 12 articles/month)
