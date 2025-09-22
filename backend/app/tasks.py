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
from .openai_client import get_ai_analysis

async def analyze_code_task(ctx, review_id: uuid.UUID):
    """
    The main background job, now using the specific broadcast_to_review method.
    """
    print(f"-> Starting full analysis pipeline for review: {review_id}...")
    db: AsyncSession = await anext(get_db())
    
    try:
        # All calls now use `manager.broadcast_to_review`
        await manager.broadcast_to_review(review_id, {"status": "processing", "progress": 15, "stage": "Preprocessing code..."})
        review = await crud.get_review_by_id(db, review_id=review_id)
        if not review or not review.code_snippet:
            raise ValueError(f"Review or snippet not found for ID {review_id}")
        
        snippet = review.code_snippet
        metrics = process_code_snippet(snippet.content, snippet.filename)
        await crud.update_snippet_metrics(db, snippet, metrics)
        print("   -> (1/5) Preprocessing complete.")

        await manager.broadcast_to_review(review_id, {"status": "processing", "progress": 30, "stage": "Scanning for security vulnerabilities..."})
        security_report = run_security_analysis(snippet.content)
        print("   -> (2/5) Security scan complete.")

        await manager.broadcast_to_review(review_id, {"status": "processing", "progress": 45, "stage": "Analyzing performance patterns..."})
        performance_report = run_performance_analysis(snippet.content)
        print("   -> (3/5) Performance analysis complete.")
        
        await manager.broadcast_to_review(review_id, {"status": "processing", "progress": 60, "stage": "Checking code quality..."})
        quality_report = run_code_quality_analysis(snippet.content, metrics)
        print("   -> (4/5) Code quality analysis complete.")

        await manager.broadcast_to_review(review_id, {"status": "processing", "progress": 80, "stage": "Generating AI summary..."})
        static_analysis_results = {
            "security_report": security_report, "performance_report": performance_report,
            "quality_report": quality_report, "code_metrics": metrics
        }
        ai_summary = await get_ai_analysis(
            code_content=snippet.content, language=metrics['detected_language'], analysis_results=static_analysis_results
        )
        print("   -> (5/5) Received summary from AI.")

        final_results = {**static_analysis_results, "ai_summary": ai_summary}
        await crud.update_review_status_and_results(db=db, review=review, new_status="completed", results=final_results)
        print(f"   -> (6/6) Saved all analysis results to the database.")

        await manager.broadcast_to_review(review_id, {"status": "completed", "progress": 100, "stage": "Done!", "results": final_results})
        print(f"-> ✅ Analysis pipeline complete for review: {review_id}.")

    except Exception as e:
        print(f"   -> ❌ CRITICAL ERROR during analysis for review {review_id}: {e}")
        await manager.broadcast_to_review(review_id, {"status": "failed", "progress": 100, "stage": "An error occurred.", "error": str(e)})
        if 'review' in locals() and review:
            await crud.update_review_status_and_results(db=db, review=review, new_status="failed", error_message=str(e))
    finally:
        await db.close()