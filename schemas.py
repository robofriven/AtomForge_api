# schemas.py
from typing import List, Optional
from pydantic import BaseModel


class ChatInput(BaseModel):
    message: str
    personality: dict


class MemoryWriteRequest(BaseModel):
    # Each entry: [PredicateName, ArgLabel1, ArgLabel2, ...]
    writes: List[List[str]]
    source: Optional[str] = None
    session_id: Optional[str] = None
