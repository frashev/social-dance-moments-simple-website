from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from .database import get_db
import sqlite3

router = APIRouter(prefix="/api/dance-sequences", tags=["dance-sequences"])

class DanceSequenceRecord(BaseModel):
    sequence_name: str
    style: str
    completion_time: float  # in seconds with milliseconds
    user_name: Optional[str] = None  # Optional user name

class DanceSequenceResponse(BaseModel):
    id: int
    sequence_name: str
    style: str
    completion_time: float
    user_name: Optional[str] = None
    created_at: str

@router.post("/save", response_model=DanceSequenceResponse)
async def save_dance_sequence(record: DanceSequenceRecord):
    """Save or update the fastest completion time for a dance sequence."""
    try:
        with get_db() as conn:
            c = conn.cursor()
            
            # Check if record exists (select full row so response_model is always satisfiable)
            c.execute(
                "SELECT * FROM dance_sequences WHERE sequence_name = ? AND style = ?",
                (record.sequence_name, record.style)
            )
            existing = c.fetchone()
            
            if existing:
                # Update only if new time is faster
                if record.completion_time < existing["completion_time"]:
                    user_name = record.user_name if record.user_name else existing.get("user_name")
                    c.execute(
                        "UPDATE dance_sequences SET completion_time = ?, user_name = ?, created_at = ? WHERE id = ?",
                        (record.completion_time, user_name, datetime.utcnow().isoformat(), existing["id"])
                    )
                    conn.commit()
                    # Fetch updated record
                    c.execute(
                        "SELECT * FROM dance_sequences WHERE id = ?",
                        (existing["id"],)
                    )
                    updated = c.fetchone()
                    return dict(updated)
                else:
                    # Return existing record (new time is not faster)
                    return dict(existing)
            else:
                # Insert new record
                created_at = datetime.utcnow().isoformat()
                c.execute(
                    "INSERT INTO dance_sequences (sequence_name, style, completion_time, user_name, created_at) VALUES (?, ?, ?, ?, ?)",
                    (record.sequence_name, record.style, record.completion_time, record.user_name, created_at)
                )
                conn.commit()
                # Fetch new record
                c.execute(
                    "SELECT * FROM dance_sequences WHERE id = ?",
                    (c.lastrowid,)
                )
                new_record = c.fetchone()
                return dict(new_record)
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save record: {str(e)}")

@router.get("/records", response_model=list[DanceSequenceResponse])
async def get_dance_sequence_records(style: str = None):
    """Get all dance sequence records, optionally filtered by style."""
    try:
        with get_db() as conn:
            c = conn.cursor()
            
            if style:
                c.execute(
                    "SELECT * FROM dance_sequences WHERE style = ? ORDER BY completion_time ASC",
                    (style,)
                )
            else:
                c.execute(
                    "SELECT * FROM dance_sequences ORDER BY style, completion_time ASC"
                )
            
            records = c.fetchall()
            return [dict(record) for record in records]
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch records: {str(e)}")

@router.get("/record/{sequence_name}/{style}", response_model=DanceSequenceResponse)
async def get_dance_sequence_record(sequence_name: str, style: str):
    """Get the fastest record for a specific sequence and style."""
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT * FROM dance_sequences WHERE sequence_name = ? AND style = ?",
                (sequence_name, style)
            )
            record = c.fetchone()
            
            if not record:
                raise HTTPException(status_code=404, detail="Record not found")
            
            return dict(record)
    except HTTPException:
        raise
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch record: {str(e)}")
