from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid


class TimeSlot(BaseModel):
    id: str
    time_value: int


class Annotation(BaseModel):
    id:str
    time_slot_start_id: str
    time_slot_start: int
    time_slot_end_id: str
    time_slot_end: int
    annotation_value: str

class AnnotationSegment(BaseModel):
    time_slot_start: int
    time_slot_end: int

class Tier(BaseModel):
    id: str
    annotator: str
    participant: str
    # time_value: int
    annotations: List[Annotation]


class AnnotationDoc(BaseModel):
    doc_urn:str
    media_url:str
    tiers: List[Tier]
    time_slots: List[TimeSlot]


class ElanFile(BaseModel):
    file_id: Optional[uuid.UUID] = None
    record_path: str
    annotator:  Optional[str] = None
    source_code:  Optional[str] = None
    annotation_upload_date:  datetime = None
    annot_doc: Optional[AnnotationDoc] = None
    #last_modification_date:  Optional[datetime] = None