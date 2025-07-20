from fastapi import APIRouter, Request, HTTPException, status, Depends
import hmac
import hashlib
import os
import httpx
from .task_queue import queue
from .worker_tasks import run_review_and_post_comment

router = APIRouter()

GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

SUPPORTED_LANGUAGES = {".py": "python", ".js": "javascript"}

if not GITHUB_WEBHOOK_SECRET or not GITHUB_TOKEN:
    raise RuntimeError("GITHUB_WEBHOOK_SECRET and GITHUB_TOKEN must be set.")

async def verify_signature(request: Request):
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        raise HTTPException(status_code=403, detail="X-Hub-Signature-256 header is missing!")
    body = await request.body()
    computed_hash = hmac.new(GITHUB_WEBHOOK_SECRET.encode('utf-8'), body, hashlib.sha256).hexdigest()
    expected_signature = f"sha256={computed_hash}"
    if not hmac.compare_digest(expected_signature, signature):
        raise HTTPException(status_code=403, detail="Request signature does not match!")

async def get_pr_files(files_url: str):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(files_url, headers=headers)
        response.raise_for_status()
        return response.json()

async def get_file_content(file_url: str):
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3.raw"}
    async with httpx.AsyncClient() as client:
        response = await client.get(file_url, headers=headers)
        response.raise_for_status()
        return response.text

@router.post("/webhook", summary="GitHub Webhook Endpoint", dependencies=[Depends(verify_signature)])
async def handle_github_webhook(request: Request):
    payload = await request.json()
    
    if "pull_request" in payload and payload.get("action") in ["opened", "synchronize"]:
        pr = payload["pull_request"]
        files_url = pr["url"] + "/files"
        comments_url = pr["comments_url"] # URL for posting general PR comments
        
        try:
            changed_files = await get_pr_files(files_url)
            jobs_queued = 0
            
            for file_info in changed_files:
                filename = file_info["filename"]
                file_extension = os.path.splitext(filename)[1]
                
                if file_extension in SUPPORTED_LANGUAGES:
                    language = SUPPORTED_LANGUAGES[file_extension]
                    file_content = await get_file_content(file_info["contents_url"])
                    
                    # Enqueue the new task with all necessary arguments
                    queue.enqueue(
                        run_review_and_post_comment,
                        file_content,
                        language,
                        comments_url,
                        filename
                    )
                    jobs_queued += 1
            
            return {"status": f"{jobs_queued} review(s) queued"}
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch data from GitHub: {e}")

    return {"status": "event_received_but_not_processed"}

