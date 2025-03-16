from typing import List, Optional
from common import elan_file_schema as schema

import common.file_util as file_util
#from .segment_util import  myers_diff_segments, async_myers_diff_segments, levenshtein_distance, async_levenshtein_distance, levenshtein_distance_stats, diarization_error_rate
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


# def mapComparisonOperationWER(op:schema.ComparisonOperation) -> schema.WordOperationStats:
#     start=time.time()
#     word_distance=levenshtein_distance(hypStr=op.hyp_annotation_value, refStr=op.ref_annotation_value)
#     # print(" \t\t\t [mapComparisonOperationWER] levenshtein_distance:",  round(time.time()-start, 3))
#     # start=time.time()
#     stats=levenshtein_distance_stats(word_distance=word_distance)
#     # print(" \t\t\t [mapComparisonOperationWER] levenshtein_distance:",  round(time.time()-start, 3))
#     # start=time.time()
#     op.word_op_stats=stats
#     return op
    

# async def compare_annotations_per_file_with_wer(file_name:str, tier_local_id:Optional[str]=None) -> List[schema.ComparisonOperation]:
#     start=time.time()
#     comparisonDetail=await select_annotations_per_file(file_name, tier_local_id) #, "IG005.eaf" tier_local_id="S0000"
#     print(" \t\t [compare_annotations_per_file_with_wer] select_annotations_per_file:", file_name ,round(time.time()-start, 3))
#     start=time.time()
#     result = myers_diff_segments(comparisonDetail)
#     print(" \t\t [compare_annotations_per_file_with_wer] myers_diff_segments:", file_name ,  round(time.time()-start, 3))
#     start=time.time()
#     # result_wer=[]
#     # for x in result:
#     #     result_wer.append(mapComparisonOperationWER(x))
#     result_wer = map(mapComparisonOperationWER,result)
#     print(" \t\t [compare_annotations_per_file_with_wer] mapComparisonOperationWER:", file_name ,  round(time.time()-start, 3))
#     print(" \t\t [compare_annotations_per_file_with_wer]", file_name , "; result len: ", len(result))
    
#     return list(result_wer)


async def calc_diarization_error_rate(file_name:str, tier_local_id:Optional[str]=None):
    # annot1_annotation = map_segments_elan(result.ref_segments)
    # org_annotation = map_segments_elan(result.hyp_segments)
    annot1_files=await select_files_by_file_name(schema.RecordType.annot1,file_name, 1,0)
    if len(annot1_files)!=1:
        raise Exception("Too many annot1 files")
    annot1=annot1_files[0]
    annot1_segments= await select_segments_by_file_id(schema.RecordType.annot1, annot1.file_id, tier_local_id=tier_local_id, limit=10000, offset=0)

    org_files=await select_files_by_file_name(schema.RecordType.org,file_name, 1,0)
    if len(org_files)!=1:
        raise Exception("Too many org files")
    org=org_files[0]
    org_segments= await select_segments_by_file_id(schema.RecordType.org, org.file_id, tier_local_id=tier_local_id, limit=10000, offset=0)

    der =await diarization_error_rate(annot1_segments, org_segments)
    return der





async def publish_to_redis_annot_align(annotation_record_path: str):
    r= await mb.broker.client()
    data={'annotation_record_path': annotation_record_path}
    await r.publish(mb.ANNOT_ALIGN_INPUT_CHANNEL_NAME, json.dumps(data))
    await r.aclose()

async def publish_all_files_wer() -> int:
    select_query="SELECT record_path from elan_file_annot1"
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
                NUM_CORES=1
                rows = await cur.fetch(NUM_CORES)
                print(rows)
                if not rows:
                    break
                for record in rows:
                    await publish_to_redis_annot_align(record["record_path"])
                
                total_processed=total_processed+len(record)
    return total_processed

# async def process_all_files_wer() -> int:
#     count_query="SELECT count(*) as num_files from elan_file_annot1"
#     select_query="SELECT file_id, record_path, annotator, annotation_upload_date from elan_file_annot1"
#     total_processed:int=0
#     start = time.time()
#     print(" \t [process_all_files_wer]. start db connection")
#     async with database.pool.acquire() as connection:
#         print(" \t [process_all_files_wer]. got db connection", round (time.time() - start, 3))
#         start = time.time()
#         counting_rows = await connection.fetchrow(count_query)
#         print(" \t [process_all_files_wer]. got count", round (time.time() - start, 3))
#         start = time.time()
#         print("count_rows", counting_rows)
#         num_file = counting_rows.get("num_files", 0)
#         async with connection.transaction():
#             print(" \t [process_all_files_wer]. got transaction", round (time.time() - start, 3))
#             start = time.time()
#             prep_select_query = await connection.prepare(select_query)
#             cur = await prep_select_query.cursor()
#             while True:
#                 start = time.time()
#                 NUM_CORES=1
#                 rows = await cur.fetch(NUM_CORES)
#                 print(rows)
#                 if not rows:
#                     break
#                 # tasks=map(lambda record:  asyncio.create_task(compare_annotations_per_file_with_wer(file_util.get_file_name(record["record_path"]))), rows)
#                 # batch = await asyncio.gather(*tasks)

#                 file_names = map(lambda record:  file_util.get_file_name(record["record_path"]), rows)
                
                
                

#                 # with concurrent.futures.ProcessPoolExecutor(NUM_CORES) as executor:
#                 #     results = executor.map(start_compare_annotations, file_names)
#                 #     total_processed=total_processed+len(list(results))

#                     # batch = executor.map(compare_annotations_per_file_with_wer, inputs)
#                     # futures = [executor.submit(start_compare_annotations, file_name) for file_name in file_names]

#                     # for future in concurrent.futures.as_completed(futures):
#                     #     print(future.result())
#                     #     total_processed=total_processed+1

#                     # for file_name in file_names:
#                     #     new_future = executor.submit(
#                     #         start_compare_annotations, # Function to perform
#                     #         # v Arguments v
#                     #         file_name=file_name
#                     #     )
#                     #     futures.append(new_future)

#                 # concurrent.futures.wait(futures)
                    
#                 # total_processed=total_processed+len(rows)

#                 print(" \t [process_all_files_wer] compare_annotations_per_file_with_wer", "rows", len(rows), "Files:", total_processed , "of", num_file, "processed: ", round(time.time() - start, 3))

#             # async for record in prep_select_query.cursor():
#             #     start = time.time()
#             #     record_path = record["record_path"]
#             #     file_name=file_util.get_file_name(record_path)
#             #     print(" \t [process_all_files_wer] +++++ file_name:", file_name)
#             #     if(file_name):
#             #         start = time.time()
#             #         # print("file_name", file_name, "start", start)
#             #         comparisonDetail=await compare_annotations_per_file_with_wer(file_name) 
#             #         total_processed=total_processed+1
#             #         print(" \t [process_all_files_wer] len", len(comparisonDetail))
#             #     print(" \t [process_all_files_wer] compare_annotations_per_file_with_wer", "record_path", record_path, "Files:", total_processed , "of", num_file, "processed: ", round(time.time() - start, 3))
                
                
#     return total_processed

# async def producer(queue): 
#     select_query="SELECT file_id, record_path from elan_file_annot1"
#     print(" \t [producer]. start db connection")
#     async with database.pool.acquire() as connection:
#         async with connection.transaction():
#             prep_select_query = await connection.prepare(select_query)
#             cur = await prep_select_query.cursor()
#             while True:
#                 start = time.time()
#                 NUM_CORES=1
#                 rows = await cur.fetch(NUM_CORES)
#                 for record in rows:
#                     record_path = record["record_path"]
#                     # print("[producer] record_path", record_path)
#                     await queue.put(record_path)
#                 # print(rows)
#                 if not rows:
#                     await queue.put(None) 
#                     break

# def transform(batch_record_path:List[str]):
#     transformed_batch = [] 
#     for record_path in batch_record_path:
#         file_name=file_util.get_file_name(record_path)
#         transformed_batch.append(file_name)
#         # print("[transform]", record_path, "=>", file_name)
#     return transformed_batch
#     # file_name=file_util.get_file_name(record_path)
#     # """ Starts an async process for comparison """
#     # print(f"Process {file_name} starting...")
#     # asyncio.run(compare_annotations_per_file_with_wer(file_name))
#     # loop = asyncio.get_event_loop()
#     # result = loop.run_until_complete(compare_annotations_per_file_with_wer(file_name))
#     # print(f"Process {file_name} finished. {result}")
# #     return result

# async def process_compare_annotation (batch_file_namer:List[str]): 
#     result_bulk=[]
#     for file_name in batch_file_namer:
#         result = await compare_annotations_per_file_with_wer(file_name)
#         print("[process_compare_annotation]", len(result))
#         result_bulk.append(file_name)
#     return "AAAA: " + str(result_bulk) 
#         # result = await compare_annotations_per_file_with_wer(file_name)
# 	# async with connection.transaction(): 
# 	# 	columns = ("first_name", "last_name", "age") 
# 	# 	await connection.copy_records_to_table( "output_table", records=batch, columns=columns ) 

# async def task_set_load_helper(task_set): 
#     result_bulk=[]
#     for future in task_set: 
#         result=await process_compare_annotation(await future) 
#         result_bulk.append(result)
#     print("[task_set_load_helper]", result_bulk)
#     return result_bulk
        

# async def consumer(loop, pool, queue): 
#     task_set = set() 
#     batch = [] 
#     while True: 
#         record_path = await queue.get() 
#         if record_path is not None: 			 
#             batch.append(record_path) 
#             # print("[consumer] add to patch", record_path)
#             if queue.empty(): 
#                 # print("[consumer]", batch)
#                 task = loop.run_in_executor(pool, transform, batch) 
#                 task_set.add(task) 
#                 if len(task_set) >= pool._max_workers: 
#                     print("[consumer] 1 len(task_set): ", record_path, len(task_set), ">=", pool._max_workers )
#                     done_set, task_set = await asyncio.wait( task_set, return_when=asyncio.FIRST_COMPLETED ) 
#                     result_batch=await task_set_load_helper(done_set)
#                     print("[consumer] result_batch: ", result_batch ) 
#                     batch = [] 
#         if record_path is None: 
#             break 
#     print("[consumer] 2 len(task_set): ", record_path, len(task_set), ">=", pool._max_workers )
#     if task_set: 
#         await task_set_load_helper( asyncio.as_completed(task_set) ) 



# async def etl(): 
#     with concurrent.futures.ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as pool: 
#         print("[etl] start")
#         loop = asyncio.get_running_loop() 
#         queue = asyncio.Queue(maxsize=1000) 
#         await asyncio.gather( 
#             asyncio.create_task(producer(queue)), 
#             asyncio.create_task(consumer(loop, pool, queue)), 
#             return_exceptions=False, ) 
#         print("[etl] done", multiprocessing.cpu_count())