
import asyncio
import asyncpg
from typing import List, Optional
import os
# from datetime import datetime
from time import time
# import json
import uuid


from common.postgres import database
from common import message_broker as mb
from common import elan_file_repo

# from .elan_file import elan_annot_repo
from common import elan_file_schema as schema


from common import elan_file_repo
from common import segment_util, file_util

import threading

import logging
logger = logging.getLogger()
logging.basicConfig(
    format="%(threadName)s:%(message)s",
    level=os.environ.get('ANNOT_PROCESSOR_LOGLEVEL', 'INFO').upper()
)

total_file_count=0
total_time=0



async def handle_annot_align(data:dict, loop, executor) :
    global total_time
    global total_file_count
    handler_start=time()
    annotation_record_paths=data['annotation_record_path']
    batch_code=data['batch_code']
    if(annotation_record_paths == None):
        logger.info("___[handle_annot_align] total_time: %s; total_file_count: %s", total_time, total_file_count)
        total_file_count=0
        total_time=0
        return
    annotation_record_path_list = annotation_record_paths.split(",")
    logger.info("[handle_annot_align] len(annotation_record_paths): %s", len(annotation_record_path_list))
    tasks = list(map(lambda record_path:process_annot_align(record_path, loop, executor), annotation_record_path_list))
    align_result:List[schema.ComparisonOperationContainer]= await asyncio.gather(*tasks)
    tasks = list(map(lambda x: persist_annot_align(x, batch_code), align_result))
    insert_counts= await asyncio.gather(*tasks)
    
    total_time=total_time+round(time()-handler_start, 3)
    total_file_count=total_file_count+len(align_result)
    logger.info("[handle_annot_align] first result %s", align_result[0].record_path)
    logger.info("[handle_annot_align] first insert_counts %s", insert_counts[0])
    logger.info("[handle_annot_align] processing time: %s; file_count: %s", total_time, total_file_count)




def mapComparisonOperationWER(op:schema.ComparisonOperation) -> schema.WordOperationStats:
    start=time()
    word_distance=segment_util.levenshtein_distance(hypStr=op.hyp_annotation_value, refStr=op.ref_annotation_value)
    # print(" \t\t\t [mapComparisonOperationWER] levenshtein_distance:",  round(time()-start, 3))
    # start=time()
    stats=segment_util.levenshtein_distance_stats(word_distance=word_distance)
    # print(" \t\t\t [mapComparisonOperationWER] levenshtein_distance:",  round(time()-start, 3))
    # start=time()
    op.word_op_stats=stats
    return op
    



async def process_annot_align(annotation_record_path:str,loop, executor)-> schema.ComparisonOperationContainer:    
    
    # start=time()
    tier_local_id=None
    # logger.info(" \t\t [process_annot_align] record_path: %s", annotation_record_path)
    file_name=file_util.get_file_name(annotation_record_path)
    comparisonDetail=await elan_file_repo.select_annotations_per_file(file_name, tier_local_id) #, "IG005.eaf" tier_local_id="S0000"
    # logger.info(" \t\t [process_annot_align] select_annotations_per_file: %s, %s", file_name ,round(time()-start, 3))
    if(comparisonDetail.hyp == None and comparisonDetail.ref==None):
        val = "comparisonDetail.hyp="+str(comparisonDetail.hyp)+"; comparisonDetail.ref=" + str(comparisonDetail.ref)
        logger.error("[process_annot_align] record_path: %s", annotation_record_path)
        raise Exception("[process_annot_align] Not found:"+val )
    start=time()
    result = await loop.run_in_executor(executor, segment_util.myers_diff_segments, comparisonDetail)
    result_wer = map(mapComparisonOperationWER,result)
    # logger.info(" \t\t [process_annot_align] mapComparisonOperationWER: %s, %s", file_name ,  round(time()-start, 3))
    # logger.info(" \t\t [process_annot_align] %s ; result len:  %s", file_name , len(result))
    conainer = schema.ComparisonOperationContainer(
        record_path=annotation_record_path,
        comparisonOps= list(result_wer))

    return conainer

def map_word_op_stats(word_op_stats:schema.WordOperationStats)-> str:
    if(len(word_op_stats.word_distance)==0):
        return None
    return word_op_stats.model_dump_json()

async def persist_annot_align(opsContainer: schema.ComparisonOperationContainer, batch_code:str)-> int: 
    ops=opsContainer.comparisonOps
    count=0
    if(not opsContainer):
        raise Exception("[map_word_op_stats] opsContainer is null" )
    async with database.pool.acquire() as connection:

        registry_uid = uuid.uuid4()

        mapped_ops=map(lambda op: ([registry_uid, op.operation_id, op.seg_operation, op.hyp_file_id, op.hyp_tier_local_id, op.hyp_annot_local_id, 
                                    op.hyp_time_slot_start, op.hyp_time_slot_end, op.hyp_annotation_value,
                                    op.ref_file_id, op.ref_tier_local_id, op.ref_annot_local_id, op.ref_time_slot_start, op.ref_time_slot_end, 
                                    op.ref_annotation_value, map_word_op_stats(op.word_op_stats)
                                    ]),ops)
        try:
            async with connection.transaction():
                r_id=await connection.execute('''INSERT INTO calc_comparison_operation_registry(record_path, batch_code, registry_uid) VALUES ($1, $2, $3)'''
                                              , opsContainer.record_path, batch_code, registry_uid)
                result = await connection.copy_records_to_table("calc_comparison_operation",records=mapped_ops, columns=[
                    "registry_uid","operation_id", "seg_operation", 
                    "hyp_file_id", "hyp_tier_local_id", "hyp_annot_local_id", "hyp_time_slot_start", "hyp_time_slot_end", "hyp_annotation_value",
                    "ref_file_id", "ref_tier_local_id", "ref_annot_local_id", "ref_time_slot_start", "ref_time_slot_end", "ref_annotation_value",
                    "word_op_stats"])
                count=count+len(ops)
                logger.info("[persist_annot_align] len(ops): %s", len(ops))
        except  asyncpg.PostgresError as pe:
            await log_error(record_path=opsContainer.record_path, batch_code=batch_code, error_message="PG err:"+str(pe))
            # logger.error(e, stack_info=True, exc_info=True)
            logger.error("Postgres error")
            logger.error(pe)
            pass
        except Exception as e:
            logger.error("[persist_annot_align] could not save result for %s", opsContainer.record_path )
            await log_error(record_path=opsContainer.record_path, batch_code=batch_code, error_message="Unkown error:"+str(e) )
            # logger.error(e, stack_info=True, exc_info=True)
            logger.error("Unkown error")
            logger.error(e)
            pass




    # op=ops[0]
    
    # insert=",".join([str(op.operation_id), str(op.seg_operation), str(op.hyp_file_id), str(op.hyp_tier_local_id), str(op.hyp_annot_local_id), str(op.hyp_time_slot_start), 
    #     str(op.hyp_time_slot_end), 
    #     str(op.hyp_annotation_value), str(op.ref_file_id), str(op.ref_tier_local_id), str(op.ref_annot_local_id), str(op.ref_time_slot_start), str(op.ref_time_slot_end), 
    #     str(op.ref_annotation_value), str(op.word_op_stats)])
    # logger.info("[persist_annot_align] insert: %s", insert)
    return count

async def log_error(record_path:str, batch_code:str, error_message:str ):
    with open("/app/logs/handler_annot_align.log", 'a') as logfile:
        logfile.write(",".join([record_path, batch_code, error_message]))
