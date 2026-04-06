"""
get_refresh_token.py
Run this ONCE on your local machine to get your Blogger OAuth refresh token.
This token is then stored as a GitHub Secret and used for all future automation.

Usage:
  pip install google-auth-oauthlib
  python tools/get_refresh_token.py
"""

import json
import os

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("Run: pip install google-auth-oauthlib")
    exit(1)


SCOPES = ["https://www.googleapis.com/auth/blogger"]


def main():
    print("\n=== BLOGGER OAUTH REFRESH TOKEN SETUP ===\n")
    print("You need your Google OAuth2 credentials.")
    print("Get them from: https://console.cloud.google.com")
    print("(Enable Blogger API → Create OAuth 2.0 Client ID → Desktop App)\n")

    client_id = input("Enter your CLIENT_ID: ").strip()
    client_secret = input("Enter your CLIENT_SECRET: ").strip()

    if not client_id or not client_secret:
        print("ERROR: Client ID and Secret are required.")
        return

    # Build client config
    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
        }
    }

    # Save temp config file
    config_path = "tools/temp_oauth_config.json"
    with open(config_path, "w") as f:
        json.dump(client_config, f)

    print("\nOpening browser for Google login...")
    print("Sign in with the Google account that owns your Blogger blog.\n")

    flow = InstalledAppFlow.from_client_secrets_file(config_path, SCOPES)
    creds = flow.run_local_server(port=0)

    # Clean up temp file
    os.remove(config_path)

    print("\n" + "=" * 50)
    print("✅ SUCCESS! Here are your credentials:")
    print("=" * 50)
    print(f"\nCLIENT_ID:\n  {client_id}")
    print(f"\nCLIENT_SECRET:\n  {client_secret}")
    print(f"\nREFRESH_TOKEN:\n  {creds.refresh_token}")
    print("\n" + "=" * 50)
    print("\nNow add these as GitHub Secrets:")
    print("  BLOGGER_CLIENT_ID     → your client ID above")
    print("  BLOGGER_CLIENT_SECRET → your client secret above")
    print("  BLOGGER_REFRESH_TOKEN → your refresh token above")
    print("\nThe refresh token does NOT expire unless you revoke access.")
    print("Keep it secret — do not commit it to your repository.\n")

    # Get blog ID
    print("\nFINDING YOUR BLOG ID...")
    import requests

    # Get fresh access token
    token_response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "grant_type": "refresh_token",
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": creds.refresh_token,
        },
    )
    access_token = token_response.json().get("access_token")

    if access_token:
        blogs_response = requests.get(
            "https://www.googleapis.com/blogger/v3/users/self/blogs",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if blogs_response.status_code == 200:
            blogs = blogs_response.json().get("items", [])
            if blogs:
                print("\nYour Blogger blogs:")
                for blog in blogs:
                    print(f"  Name: {blog['name']}")
                    print(f"  ID:   {blog['id']}  ← Use this as BLOGGER_BLOG_ID")
                    print(f"  URL:  {blog['url']}\n")
            else:
                print("No blogs found. Create a blog at blogger.com first.")
        else:
            print("Could not fetch blog list. Check your credentials.")


if __name__ == "__main__":
    main()
