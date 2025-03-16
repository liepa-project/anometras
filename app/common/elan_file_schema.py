from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
from enum import Enum


class RecordType(str, Enum):
    annot1 = "annot1"
    org = "org"

class ComparisonOperationType(str, Enum):
    op_eql = "eql" # Equals
    op_ins = "ins" # Insert
    op_del = "del" # Delete
    op_noop = "noop" # No Operation - nothing to compare

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
    annotation_upload_date:  datetime = None
    tiers: List[Tier]
    time_slots: List[TimeSlot]


class ElanFile(BaseModel):
    file_id: Optional[uuid.UUID] = None
    record_path: str
    annotator:  Optional[str] = None
    listnumm:  Optional[str] = None
    source_code:  Optional[str] = None
    annotation_upload_date:  datetime = None
    annot_doc: Optional[AnnotationDoc] = None
    error_code: Optional[str] = None
    batch_code: Optional[str] = None
    #last_modification_date:  Optional[datetime] = None


class ComparisonSegment(BaseModel):
    annot_id: uuid.UUID
    tier_local_id: str
    annot_local_id: str
    annot_time_slot_start: int
    annot_time_slot_end: int
    participant: Optional[str] = None
    annotation_value: Optional[str] = None


class WordOperation(BaseModel):
    op_eql: Optional[str] = None
    op_ins: Optional[str] = None
    op_del: Optional[str] = None
    op_sub: Optional[str] = None
    by: Optional[str] = None

class WordOperationStats(BaseModel):
    op_sub: int
    op_ins: int
    op_del: int
    op_total: int
    word_distance: List[WordOperation]



class ComparisonOperation(BaseModel):
    operation_id: uuid.UUID
    seg_operation:ComparisonOperationType
    hyp_file_id: Optional[uuid.UUID] = None
    hyp_tier_local_id: Optional[str] = None
    hyp_annot_local_id: Optional[str] = None
    hyp_time_slot_start: Optional[int] = None
    hyp_time_slot_end: Optional[int] = None
    hyp_annotation_value: Optional[str] = None
    ref_file_id: Optional[uuid.UUID] = None
    ref_tier_local_id: Optional[str] = None
    ref_annot_local_id: Optional[str] = None
    ref_time_slot_start: Optional[int] = None
    ref_time_slot_end: Optional[int] = None
    ref_annotation_value: Optional[str] = None
    word_op_stats: Optional[WordOperationStats] = None

class ComparisonOperationContainer(BaseModel):
    record_path: str
    comparisonOps: List[ComparisonOperation]

class ComparisonDetailPerFile(BaseModel):
    hyp: Optional[ElanFile] = None #org
    hyp_file_id:Optional[uuid.UUID] = None #org
    hyp_segments: Optional[List[ComparisonSegment]] = None #org
    ref: Optional[ElanFile] = None #annot1
    ref_file_id:Optional[uuid.UUID] = None #annot1
    ref_segments: Optional[List[ComparisonSegment]]=None #annot1


