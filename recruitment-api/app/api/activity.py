import json
import asyncio
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db, SessionLocal
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.candidate import Candidate
from app.models.activity_event import ActivityEvent

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("/stream")
def stream_activity(
    request: Request,
    last_event_id: int = 0,
    current_user: User = Depends(get_current_user),
):
    async def event_generator():
        last_seen_id = last_event_id
        yield ": keepalive\n\n"
        
        # We can implement a loop counter to send heartbeat/ping every 15 seconds
        loop_counter = 0
        
        while True:
            db = SessionLocal()
            try:
                # Query logic with user-role filtering
                query = db.query(ActivityEvent).filter(ActivityEvent.id > last_seen_id)
                
                if current_user.role == "candidate":
                    candidate = db.query(Candidate).filter(Candidate.user_id == current_user.id).first()
                    candidate_id = candidate.id if candidate else -1
                    query = query.filter(
                        (ActivityEvent.candidate_id == candidate_id) |
                        (ActivityEvent.user_id == current_user.id)
                    )
                # HR sees all events, so no filtering if role is HR.
                
                events = query.order_by(ActivityEvent.id.asc()).all()
                for e in events:
                    last_seen_id = e.id
                    try:
                        details = json.loads(e.details_json or "{}") if e.details_json else {}
                    except Exception:
                        details = {}
                    payload = {
                        "id": e.id,
                        "event_type": e.event_type,
                        "candidate_id": e.candidate_id,
                        "user_id": e.user_id,
                        "details": details,
                        "created_at": e.created_at.isoformat()
                    }
                    yield f"data: {json.dumps(payload)}\n\n"
                    loop_counter = 0 # reset on active data
            except Exception as ex:
                pass
            finally:
                db.close()
                
            if await request.is_disconnected() or request.headers.get("x-test-single-run") == "true":
                break
                
            await asyncio.sleep(0.5)
            loop_counter += 1
            if loop_counter >= 30: # 30 * 0.5s = 15 seconds
                yield ": ping\n\n"
                loop_counter = 0
                
    return StreamingResponse(event_generator(), media_type="text/event-stream")
