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
from app.core.dependencies import require_password_changed
from app.services.activity_visibility import visible_events, serialize_event, stream_session_valid

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("/stream")
def stream_activity(
    request: Request,
    last_event_id: int = 0,
    current_user: User = Depends(require_password_changed),
):
    async def event_generator():
        last_seen_id = last_event_id
        yield ": keepalive\n\n"
        
        # We can implement a loop counter to send heartbeat/ping every 15 seconds
        loop_counter = 0
        
        while True:
            db = SessionLocal()
            try:
                if not stream_session_valid(db, current_user, request):
                    break
                # Query logic with user-role filtering
                query = visible_events(db, current_user).filter(ActivityEvent.id > last_seen_id)
                
                events = query.order_by(ActivityEvent.id.asc()).limit(100).all()
                for e in events:
                    last_seen_id = e.id
                    yield f"data: {json.dumps(serialize_event(db, e, current_user, request))}\n\n"
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


from pydantic import BaseModel
from app.core.dependencies import require_hr
from app.utils.activity_logger import publish_event


class BlindScreeningTogglePayload(BaseModel):
    enabled: bool


@router.post("/blind-screening-toggle")
def toggle_blind_screening_audit(
    payload: BlindScreeningTogglePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr),
):
    event_type = "blind_screening_enabled" if payload.enabled else "blind_screening_disabled"
    publish_event(
        db=db,
        event_type=event_type,
        candidate_id=None,
        user_id=current_user.id,
        details={"enabled": payload.enabled, "actor": "hr_user"}
    )
    db.commit()
    return {"message": f"Blind screening {event_type} recorded successfully.", "enabled": payload.enabled}
