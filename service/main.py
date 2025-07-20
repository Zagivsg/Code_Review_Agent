from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from prometheus_fastapi_instrumentator import Instrumentator
from agent.agent import CodeReviewAgent
from service.webhook_handler import router as webhook_router
from service.task_queue import queue
import uvicorn

app = FastAPI(title="Code Review Agent API")
agent = CodeReviewAgent()

# CORS Middleware Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production environments
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Prometheus Monitoring
Instrumentator().instrument(app).expose(app)

@app.get("/health", summary="Health Check")
@limiter.limit("10/minute")
async def health_check(request: Request):
    """Provides a simple health check endpoint."""
    return {"status": "healthy"}

@app.post("/review", summary="Submit Code for Review")
@limiter.limit("5/minute")
async def review_code(request: Request):
    """Endpoint for manually submitting code for an asynchronous review."""
    data = await request.json()
    code = data.get("code")
    language = data.get("language")
    if not code or not language:
        raise HTTPException(status_code=400, detail="'code' and 'language' are required fields.")
    
    job = queue.enqueue(agent.run, code, language)
    return {"job_id": job.id, "status": "queued"}

# Include the GitHub webhook router
app.include_router(webhook_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
