from agent.agent import CodeReviewAgent
from service.github_client import post_comment
from service.training_data_logger import log_interaction
from service.code_normalizer import get_semantic_hash # Import the new function
from service.task_queue import conn as redis_conn # Import redis connection
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ... (format_review_as_comment function remains the same) ...
def format_review_as_comment(result: dict, filename: str) -> str:
    plan = result.get("plan", "No improvement plan was generated.")
    suggestion = result.get("improved_code", "No code suggestion was generated.")
    notes = result.get("notes", "No reflection notes available.")
    comment_body = f"""
### 🤖 AI Code Review for `{filename}`
**Summary:** {notes}
<details>
<summary><strong>💡 Improvement Plan</strong></summary>

{plan}
</details>

---
**Suggested Code:**
```{result.get('language', '')}
{suggestion}
```
"""
    return comment_body.strip()


def run_review_and_post_comment(file_content: str, language: str, comments_url: str, filename: str):
    """
    The main worker task, now with semantic caching.
    """
    try:
        # --- New Step: Semantic Caching Logic ---
        code_hash = get_semantic_hash(file_content, language)
        cache_key = f"review_cache:{code_hash}"
        
        cached_result = redis_conn.get(cache_key)
        if cached_result:
            logger.info(f"Cache HIT for {filename} (hash: {code_hash[:10]}...). Using cached result.")
            review_result = json.loads(cached_result)
        else:
            logger.info(f"Cache MISS for {filename} (hash: {code_hash[:10]}...). Running agent.")
            agent = CodeReviewAgent()
            review_result = agent.run(file_content, language)
            
            # Save the new result to the cache with a 24-hour expiration
            redis_conn.set(cache_key, json.dumps(review_result), ex=86400)
        # --- End of Caching Logic ---

        review_result['language'] = language
        
        logger.info(f"Logging interaction for {filename}...")
        training_data = {
            "original_code": file_content,
            "improved_code": review_result.get("improved_code"),
            "language": language,
            "reward": review_result.get("reward"),
            "notes": review_result.get("notes"),
            "plan": review_result.get("plan")
        }
        log_interaction(training_data)

        logger.info(f"Formatting and posting comment for {filename}...")
        comment_body = format_review_as_comment(review_result, filename)
        post_comment(comments_url, comment_body)
        
        logger.info(f"Successfully processed review for {filename}.")
    except Exception as e:
        logger.error(f"Failed to process review for {filename}: {e}", exc_info=True)
        try:
            error_body = f"🤖 Could not complete review for `{filename}`. An internal error occurred."
            post_comment(comments_url, error_body)
        except Exception as post_e:
            logger.error(f"Failed to post error comment for {filename}: {post_e}")
