# This file handles all communication with the GitHub API.
import httpx
import os

# It's crucial to load the token from environment variables
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def post_comment(comment_url: str, body: str):
    """
    Posts a comment to a specified GitHub URL (e.g., a pull request's comment thread).

    Args:
        comment_url (str): The API URL for posting comments.
        body (str): The Markdown content of the comment.
    """
    if not GITHUB_TOKEN:
        print("Error: GITHUB_TOKEN is not set. Cannot post comment.")
        return

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"body": body}
    
    try:
        # Using a synchronous client as RQ workers are synchronous
        with httpx.Client() as client:
            response = client.post(comment_url, headers=headers, json=data)
            response.raise_for_status() # Raises an exception for non-2xx responses
            print(f"Successfully posted comment to {comment_url}")
            return response.json()
    except httpx.HTTPStatusError as e:
        print(f"Error posting comment to GitHub: {e.response.status_code} - {e.response.text}")
        raise