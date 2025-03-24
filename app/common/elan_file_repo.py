from typing import List, Optional
from common import elan_file_schema as schema

import common.file_util as file_util
#from .segment_util import  myers_diff_segments, async_myers_diff_segments, levenshtein_distance, async_levenshtein_distance, levenshtein_distance_stats, 
from .segment_util import diarization_error_rate
import datetime
# from fastapi.concurrency import run_in_threadpool

import json
from pathlib import Path
import time

import asyncio

import logging
logger = logging.getLogger('uvicorn.error')

import concurrent
import multiprocessing


from common.postgres import database
import common.message_broker as mb


async def insert_record(record_path:str, annotation_upload_date:datetime.datetime, annotation_record_type:str, batch_code:str) -> schema.ElanFile:
    elan_file:schema.ElanFile = file_util.create_file_record(record_path, annotation_upload_date, batch_code=batch_code)
    query = f"INSERT INTO elan_file_{annotation_record_type} (record_path, annotator, listnumm, annotation_upload_date, batch_code, error_code) VALUES ($1, $2, $3, $4, $5, $6) RETURNING file_id"
    async with database.pool.acquire() as connection:
        elan_file.file_id=await connection.fetchval(query, elan_file.record_path, elan_file.annotator, elan_file.listnumm, elan_file.annotation_upload_date, 
                                                    elan_file.batch_code, elan_file.error_code )
    return elan_file


async def select_anotators() -> List[schema.Annotator]:
    query=f"select DISTINCT(tier_annotator) annotator from elan_annot_annot1;"
    # logger.info("[select_anotators] query: %s", query)
    async with database.pool.acquire() as connection:
        rows = await connection.fetch(query)
        return [schema.Annotator(**dict(row)) for row in rows]   


async def select_files(annotation_record_type:schema.RecordType, limit: int, offset:int, annotator:Optional[str]) -> List[schema.ElanFile]:
    query_param = [limit, offset]
    filter=""
    if(annotator):
        filter = "where annotator = $3"
        query_param.append(annotator)
    query=f"""SELECT file_id, record_path, annotator, annotation_upload_date from elan_file_{annotation_record_type.value}
    {filter} 
    ORDER BY annotation_upload_date DESC
    LIMIT $1 OFFSET $2;"""
    # logger.info("[select_files] query: %s", query)
    async with database.pool.acquire() as connection:
        rows = await connection.fetch(query, *tuple(query_param))
        return [schema.ElanFile(**dict(row)) for row in rows]
    

async def select_files_record_paths(annotation_record_type:schema.RecordType) -> List[str]:
    query=f"SELECT record_path from elan_file_{annotation_record_type.value} ORDER BY record_path; "
    async with database.pool.acquire() as connection:
        rows = await connection.fetch(query)
        pathsList=[";".join(row.values()) for row in rows]
        return pathsList
    

    
    
async def select_files_by_file_name(annotation_record_type:schema.RecordType, file_name:str,  limit: int, offset:int) -> List[schema.ElanFile]:
    query=f"SELECT file_id, record_path, annotator, annotation_upload_date from elan_file_{annotation_record_type.value} WHERE record_path like $3 LIMIT $1 OFFSET $2;"
    async with database.pool.acquire() as connection:
        rows = await connection.fetch(query, limit, offset, f"%{file_name}")
        return [schema.ElanFile(**dict(row)) for row in rows]

async def select_segments_by_file_id(annotation_record_type:schema.RecordType, file_id:str, limit: int, offset:int, tier_local_id:Optional[str]=None,) -> List[schema.ComparisonSegment]:
    additional_filtering = ""
    if tier_local_id:
        additional_filtering = additional_filtering + f" and tier_local_id='{tier_local_id}'"

    query=f"""SELECT annot_id,tier_local_id, annot_local_id, annot_time_slot_start, annot_time_slot_end, annotation_value from elan_annot_{annotation_record_type.value} 
        where file_id =$3 
        {additional_filtering}
        ORDER BY annot_time_slot_start 
        LIMIT $1 OFFSET $2;"""
    async with database.pool.acquire() as connection:
        rows = await connection.fetch(query, limit, offset, file_id)
        return [schema.ComparisonSegment(**dict(row)) for row in rows]




async def select_annotations_per_file(file_name:str, tier_local_id:Optional[str]=None) -> schema.ComparisonDetailPerFile:
    annot1_files=await select_files_by_file_name(schema.RecordType.annot1,file_name, 1,0)
    # print("annot1_files", annot1_files)
    org_files=await select_files_by_file_name(schema.RecordType.org,file_name, 1,0)
    # print("org_files", org_files)
    annot1 = None
    annot1_file_id=None
    annot1_segments:List[schema.ComparisonSegment]=[]
    if len(annot1_files)==1:
        annot1=annot1_files[0]
        annot1_file_id = annot1.file_id
        annot1_segments= await select_segments_by_file_id(schema.RecordType.annot1, annot1.file_id, tier_local_id=tier_local_id, limit=10000, offset=0)
    org = None 
    org_file_id = None
    org_segments:List[schema.ComparisonSegment]=[]
    if len(org_files)==1:
        org=org_files[0]
        org_file_id = org.file_id
        org_segments= await select_segments_by_file_id(schema.RecordType.org, org.file_id, tier_local_id=tier_local_id, limit=10000, offset=0)

    return schema.ComparisonDetailPerFile(ref=annot1
                              , ref_file_id=annot1_file_id
                              , ref_segments=annot1_segments
                              , hyp=org
                              , hyp_file_id=org_file_id
                              , hyp_segments=org_segments)



async def calc_diarization_error_rate(file_name:str, tier_local_id:Optional[str]=None):
    # annot1_annotation = map_segments_elan(result.ref_segments)
    # org_annotation = map_segments_elan(result.hyp_segments)
    annot1_files=await select_files_by_file_name(schema.RecordType.annot1,file_name, 1,0)
    if len(annot1_files)==0:
        raise Exception("No annot1 files found")
    if len(annot1_files)!=1:
        raise Exception("Too many annot1 files")
    annot1=annot1_files[0]
    annot1_segments= await select_segments_by_file_id(schema.RecordType.annot1, annot1.file_id, tier_local_id=tier_local_id, limit=10000, offset=0)

    org_files=await select_files_by_file_name(schema.RecordType.org,file_name, 1,0)
    (schema.RecordType.org,file_name, 1,0)
    if len(org_files)==0:
        raise Exception("No org files found")
    if len(org_files)!=1:
        raise Exception("Too many org files")
    org=org_files[0]
    org_segments= await select_segments_by_file_id(schema.RecordType.org, org.file_id, tier_local_id=tier_local_id, limit=10000, offset=0)

    der=diarization_error_rate(annot1_segments, org_segments)
    return der





async def publish_to_redis_annot_align(annotation_record_path: str, batch_code:str):
    r= mb.broker.client()
    data={'annotation_record_path': annotation_record_path, 'batch_code': batch_code}
    await r.publish(mb.ANNOT_ALIGN_INPUT_CHANNEL_NAME, json.dumps(data))
    await r.aclose()

async def publish_reindexable_files_wer() -> int:
    batch_code="batch_wer_"+ datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    # select_query="SELECT record_path from elan_file_annot1"
    select_query="""select anot_registry.record_path from elan_file_annot1 anot_registry
    LEFT OUTER JOIN calc_comparison_operation_registry op_registry
    ON (op_registry.record_path = anot_registry.record_path)
    WHERE op_registry.record_path IS NULL"""
    total_processed:int=0
    start = time.time()
    print(" \t [process_all_files_wer]. start db connection")
    async with database.pool.acquire() as connection:
        print(" \t [process_all_files_wer]. got db connection")
        async with connection.transaction():
            print(" \t [process_all_files_wer]. got transaction")
            prep_select_query = await connection.prepare(select_query)
            cur = await prep_select_query.cursor()
            while True:
                start = time.time()
                NUM_CORES=30
                rows = await cur.fetch(NUM_CORES)
                print(rows)
                if not rows:
                    break
                record_paths = list(map(lambda record: record["record_path"], rows ))
                
                await publish_to_redis_annot_align(",".join(record_paths), batch_code)
                # for record in rows:
                #     await publish_to_redis_annot_align(record["record_path"])
                
                total_processed=total_processed+len(record_paths)
            await publish_to_redis_annot_align(None, batch_code)
    return total_processed

async def comparison_operation_per_file(file_name:str) -> schema.ComparisonOperationContainer:

    query_record="select registry_uid, record_path from calc_comparison_operation_registry where record_path like $1 LIMIT 1"
    query_ops="""select operation_id,     seg_operation,     hyp_file_id,     hyp_tier_local_id,     hyp_annot_local_id,     hyp_time_slot_start,     
    hyp_time_slot_end,     hyp_annotation_value,     ref_file_id,     ref_tier_local_id,     ref_annot_local_id,     ref_time_slot_start,     
    ref_time_slot_end,     ref_annotation_value  
    FROM calc_comparison_operation 
    WHERE registry_uid = $1
    ORDER BY id
    """
    
    async with database.pool.acquire() as connection:
        row = await connection.fetchrow(query_record, f"%{file_name}")
        record_path=row.get("record_path")
        # file_id=row.get("file_id")
        registry_uid=row.get("registry_uid")
        rows = await connection.fetch(query_ops,  registry_uid)
        comparisonOps=[schema.ComparisonOperation(**dict(row)) for row in rows]
        return schema.ComparisonOperationContainer(record_path=record_path, comparisonOps=comparisonOps)

def to_str(value):
    if(value):
       return str(value)
    else:
        return ""

async def comparison_operation_per_file_csv(file_name:str) -> List[str]:

    collumn_names_str="""operation_id,     seg_operation,     hyp_file_id,     hyp_tier_local_id,     hyp_annot_local_id,     hyp_time_slot_start,     
    hyp_time_slot_end,     hyp_annotation_value,     ref_file_id,     ref_tier_local_id,     ref_annot_local_id,     ref_time_slot_start,     
    ref_time_slot_end,     ref_annotation_value, word_op_stats"""
    collumn_names=[x.strip() for x in collumn_names_str.split(',')]
    collumn_names_header=";".join(collumn_names)
    
    query_ops="""select operation_id,     seg_operation,     hyp_file_id,     hyp_tier_local_id,     hyp_annot_local_id,     hyp_time_slot_start,     
    hyp_time_slot_end,     hyp_annotation_value,     ref_file_id,     ref_tier_local_id,     ref_annot_local_id,     ref_time_slot_start,     
    ref_time_slot_end,     ref_annotation_value, word_op_stats  
    FROM calc_comparison_operation where registry_uid = (
        select registry_uid from calc_comparison_operation_registry where record_path like $1 LIMIT 1
    )
    ORDER BY id;
    """
    
    

    async with database.pool.acquire() as connection:
        rows = await connection.fetch(query_ops,  f"%{file_name}")
        comparisonOpsList=[";".join(map(to_str,row.values())) for row in rows]
        comparisonOpsList.insert(0, collumn_names_header)
        return comparisonOpsList