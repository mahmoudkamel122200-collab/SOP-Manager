import asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import AsyncSessionFactory
from app.models.models import AuditLog

async def main():
    async with AsyncSessionFactory() as db:
        query = (
            select(AuditLog)
            .options(selectinload(AuditLog.user))
            .order_by(AuditLog.created_at.desc())
            .limit(100)
        )
        result = await db.execute(query)
        logs = result.scalars().all()
        
        data = []
        for log in logs:
            try:
                data.append({
                    "id": str(log.id),
                    "username": log.user.username if log.user else "System",
                    "action": log.action.value if hasattr(log.action, 'value') else log.action,
                    "module": log.module.value if hasattr(log.module, 'value') else log.module,
                    "resource_type": log.module.value if hasattr(log.module, 'value') else log.module,
                    "description": log.description,
                    "ip_address": log.ip_address,
                    "created_at": log.created_at.isoformat(),
                    "timestamp": log.created_at.isoformat(),
                })
            except Exception as e:
                import traceback
                print("Error parsing log:", log.id, e)
                traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
