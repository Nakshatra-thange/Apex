import time
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

# Import our logic
from . import crud, models
from .database import get_db
from .websocket_manager import manager
from .code_processor import process_code_snippet
from .security_analyzer import run_security_analysis
from .performance_analyzer import run_performance_analysis
from .code_quality_analyzer import run_code_quality_analysis
from .openai_client import get_ai_analysis # <-- IMPORT THE NEW CLIENT


async def analyze_code_task(ctx, review_id: uuid.UUID):
    """
    The main background job, now using the real OpenAI client with fallbacks.
    """
    print(f"-> Starting full analysis pipeline for review: {review_id}...")
    db: AsyncSession = await anext(get_db())
    
    try:
        # Stage 1: Fetching Data
        await manager.broadcast_update(review_id, {"status": "processing", "progress": 10, "stage": "Fetching code..."})
        review = await crud.get_review_by_id(db, review_id=review_id)
        if not review or not review.code_snippet:
            raise ValueError(f"Review or snippet not found for ID {review_id}")
        
        snippet = review.code_snippet
        print(f"   -> (1/6) Fetched snippet '{snippet.filename}' for analysis.")
        
        # Stage 2: Preprocessing
        await manager.broadcast_update(review_id, {"status": "processing", "progress": 20, "stage": "Preprocessing code..."})
        metrics = process_code_snippet(snippet.content, snippet.filename)
        await crud.update_snippet_metrics(db, snippet, metrics)
        print(f"   -> (2/6) Preprocessing complete.")

        # Stage 3: Security Analysis
        await manager.broadcast_update(review_id, {"status": "processing", "progress": 35, "stage": "Scanning for security vulnerabilities..."})
        security_report = run_security_analysis(snippet.content)
        print(f"   -> (3/6) Security scan complete.")

        # Stage 4: Performance Analysis
        await manager.broadcast_update(review_id, {"status": "processing", "progress": 50, "stage": "Analyzing performance patterns..."})
        performance_report = run_performance_analysis(snippet.content)
        print(f"   -> (4/6) Performance analysis complete.")

        # Stage 5: Code Quality Analysis
        await manager.broadcast_update(review_id, {"status": "processing", "progress": 65, "stage": "Checking code quality..."})
        quality_report = run_code_quality_analysis(snippet.content, metrics)
        print(f"   -> (5/6) Code quality analysis complete.")

        # --- Stage 6: AI Analysis (THIS IS THE ONLY PART THAT CHANGED) ---
        await manager.broadcast_update(review_id, {"status": "processing", "progress": 80, "stage": "Generating AI summary..."})
        
        # We now call our new, intelligent client function.
        ai_summary = await get_ai_analysis(
            code_content=snippet.content, language=metrics['detected_language']
        )
        
        print("   -> (6/6) Received summary from AI.")

        # Stage 7: Saving
        final_results = {
            "ai_summary": ai_summary,
            "security_report": security_report,
            "performance_report": performance_report,
            "quality_report": quality_report,
            "code_metrics": metrics
        }
        
        await crud.update_review_status_and_results(
            db=db, review=review, new_status="completed", results=final_results
        )
        print(f"   -> (7/7) Saved all analysis results to the database.")

        await manager.broadcast_update(review_id, {"status": "completed", "progress": 100, "stage": "Done!", "results": final_results})
        print(f"-> ✅ Analysis pipeline complete for review: {review_id}.")

    except Exception as e:
        await manager.broadcast_update(review_id, {"status": "failed", "progress": 100, "stage": "An error occurred.", "error": str(e)})
        if 'review' in locals() and review:
            await crud.update_review_status_and_results(db=db, review=review, new_status="failed", error_message=str(e))
    finally:
        await db.close()