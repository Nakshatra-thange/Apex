import os
import sys
from datetime import datetime, timedelta, timezone
import asyncio

# Allow script to import from the main app
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

# It's important to import these after setting the path
from app.database import get_db, engine
from app.models import AuditLog


async def generate_daily_security_report():
    """
    Connects to the database and generates a security report from the audit logs
    of the last 24 hours.
    """
    print("--- Generating Daily Security Audit Report ---")
    
    # We need to manage the DB session manually in a script
    db: AsyncSession = await anext(get_db())
    
    try:
        # Define the time window for the report
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=1)
        
        print(f"Report for period: {start_time.isoformat()} to {end_time.isoformat()}\n")
        
        # 1. Count total events
        total_events_query = select(func.count(AuditLog.id)).where(AuditLog.timestamp.between(start_time, end_time))
        total_events = (await db.execute(total_events_query)).scalar_one()
        print(f"Total Security-Related Events Logged: {total_events}")
        
        # 2. Find most common suspicious actions
        action_query = (
            select(AuditLog.action, func.count(AuditLog.action).label("count"))
            .where(AuditLog.timestamp.between(start_time, end_time))
            .where(AuditLog.action.in_(['LOGIN_FAILURE', 'PROJECT_ACCESS_DENIED', 'RATE_LIMIT_EXCEEDED']))
            .group_by(AuditLog.action)
            .order_by(func.count(AuditLog.action).desc())
        )
        print("\n--- Suspicious Activity Breakdown ---")
        suspicious_actions = (await db.execute(action_query)).all()
        if not suspicious_actions:
            print("No suspicious activity detected in the last 24 hours.")
        else:
            for action, count in suspicious_actions:
                print(f"- {action}: {count} occurrences")

        # 3. Identify IPs with the most failed logins (potential brute-force)
        failed_login_ips_query = (
            select(AuditLog.ip_address, func.count(AuditLog.id).label("count"))
            .where(AuditLog.timestamp.between(start_time, end_time))
            .where(AuditLog.action == 'LOGIN_FAILURE')
            .group_by(AuditLog.ip_address)
            .order_by(func.count(AuditLog.id).desc())
            .limit(5)
        )
        print("\n--- Top 5 IPs with Failed Logins ---")
        top_ips = (await db.execute(failed_login_ips_query)).all()
        if not top_ips:
            print("No failed logins recorded.")
        else:
            for ip, count in top_ips:
                print(f"- IP: {ip}, Attempts: {count}")
        
    finally:
        await db.close()
        # It's crucial to dispose of the engine in a standalone script
        await engine.dispose()

if __name__ == "__main__":
    print("Starting security audit report generation...")
    asyncio.run(generate_daily_security_report())
    print("Report generation complete.")