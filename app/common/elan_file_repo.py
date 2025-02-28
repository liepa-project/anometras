from typing import List, Optional
from common import elan_file_schema as schema
from common.postgres import database
import common.file_util as file_util
import datetime

from pathlib import Path




async def insert_record(record_path:str, annotation_upload_date:datetime.datetime, annotation_record_type:str, batch_code:str) -> schema.ElanFile:
    elan_file:schema.ElanFile = file_util.create_file_record(record_path, annotation_upload_date, batch_code=batch_code)
    query = f"INSERT INTO elan_file_{annotation_record_type} (record_path, annotator, listnumm, annotation_upload_date, batch_code, error_code) VALUES ($1, $2, $3, $4, $5, $6) RETURNING file_id"
    async with database.pool.acquire() as connection:
        elan_file.file_id=await connection.fetchval(query, elan_file.record_path, elan_file.annotator, elan_file.listnumm, elan_file.annotation_upload_date, 
                                                    elan_file.batch_code, elan_file.error_code )
    return elan_file


async def select_files(annotation_record_type:schema.RecordType, limit: int, offset:int) -> List[schema.ElanFile]:
    query=f"SELECT file_id, record_path, annotator, annotation_upload_date from elan_file_{annotation_record_type.value} LIMIT $1 OFFSET $2;"
    async with database.pool.acquire() as connection:
        rows = await connection.fetch(query, limit, offset)
        return [schema.ElanFile(**dict(row)) for row in rows]
    
async def select_files_by_file_name(annotation_record_type:schema.RecordType, file_name:str,  limit: int, offset:int) -> List[schema.ElanFile]:
    query=f"SELECT file_id, record_path, annotator, annotation_upload_date from elan_file_{annotation_record_type.value} WHERE record_path like $3 LIMIT $1 OFFSET $2;"
    async with database.pool.acquire() as connection:
        rows = await connection.fetch(query, limit, offset, f"%{file_name}")
        return [schema.ElanFile(**dict(row)) for row in rows]

async def select_segments_by_file_id(annotation_record_type:schema.RecordType, file_id:str,  limit: int, offset:int) -> List[schema.ComparisonSegment]:
    query=f"SELECT annot_id,tier_local_id, annot_local_id, annot_time_slot_start, annot_time_slot_end from elan_annot_{annotation_record_type.value} where file_id =$3 order by tier_local_id, annot_time_slot_start LIMIT $1 OFFSET $2;"
    async with database.pool.acquire() as connection:
        rows = await connection.fetch(query, limit, offset, file_id)
        return [schema.ComparisonSegment(**dict(row)) for row in rows]




async def select_annotations_per_file(file_name:str) -> schema.ComparisonDetailPerFile:
    annot1_files=await select_files_by_file_name(schema.RecordType.annot1,file_name, 1,0)
    org_files=await select_files_by_file_name(schema.RecordType.org,file_name, 1,0)
    annot1 = None
    annot1_segments:List[schema.ComparisonSegment]=[]
    if annot1_files:
        annot1=annot1_files[0]
        annot1_segments= await select_segments_by_file_id(schema.RecordType.annot1, annot1.file_id, limit=10000, offset=0)
    org = None 
    org_segments:List[schema.ComparisonSegment]=[]
    if org_files:
        org=org_files[0]
        org_segments= await select_segments_by_file_id(schema.RecordType.org, org.file_id, limit=10000, offset=0)

    return schema.ComparisonDetailPerFile(annot1=annot1
                              , annot1_segments=annot1_segments
                              , org=org
                              , org_segments=org_segments)
