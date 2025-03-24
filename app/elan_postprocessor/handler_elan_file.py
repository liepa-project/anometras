import asyncio

import asyncpg
import os
import datetime
import time
import json


from common.postgres import database
from common import message_broker as mb
from common import elan_file_repo

from .elan_file import elan_annot_repo

from common import elan_file_schema as schema

import common.file_util as file_util

import logging
logger = logging.getLogger()
logging.basicConfig(
    level=os.environ.get('ANNOT_PROCESSOR_LOGLEVEL', 'INFO').upper()
)

total_file_count=0
total_time=0

async def handle_elan_file(data:dict, loop, executor):
    """
    Process
    """
    logger.debug("[handle_elan_file]Task started %s",
                    asyncio.current_task().get_name())
    annotation_record_path=data['annotation_record_path']
    annotation_record_type=data['annotation_record_type']
    batch_code=data['batch_code']
    logger.debug("[handle_elan_file] input - path: %s, type: %s, batch: %s", annotation_record_path, annotation_record_type, batch_code)
    if(annotation_record_path == "STOP"):
        logger.info("[handle_elan_file] STOP")
        await log_finished_stats(annotation_record_path, batch_code)
        return 
    
    ti_m = os.path.getmtime(annotation_record_path)
    annotation_upload_date=datetime.datetime.fromtimestamp(ti_m)
    
    started_time = time.time()
    async with database.pool.acquire() as connection:
        try:
            async with connection.transaction():
                
                ########### elan_file_
                
                # elan_file = await elan_file_repo.insert_record(annotation_record_path, annotation_upload_date, annotation_record_type, batch_code)
                elan_file:schema.ElanFile = file_util.create_file_record(annotation_record_path, annotation_upload_date, batch_code=batch_code)
                query = f"INSERT INTO elan_file_{annotation_record_type} (record_path, annotator, listnumm, annotation_upload_date, batch_code, error_code) VALUES ($1, $2, $3, $4, $5, $6) RETURNING file_id"
                
                elan_file.file_id=await connection.fetchval(query, elan_file.record_path, elan_file.annotator, elan_file.listnumm, elan_file.annotation_upload_date, 
                                                                elan_file.batch_code, elan_file.error_code )
                
                logger.error("[handle_elan_file] Insert record %s", str(round(time.time()-started_time,3)))
                
                started_time = time.time()

                ########### /elan_file_

                ########### elan_annot_
                # await elan_annot_repo.insert_annotations(annotation_record_path, elan_file.file_id, elan_file.annotation_upload_date, annotation_record_type)
                
                
                elan_file_file_id=elan_file.file_id
                annotationDoc = await elan_annot_repo.parse_document(annotation_record_path, annotation_upload_date)
                # insert_annotations_influxdb(annotationDoc)
                # print("insert_annotations", annotationDoc)
                query = f"""
                    INSERT INTO elan_annot_{annotation_record_type} 
                        (file_id, tier_local_id, tier_annotator, tier_participant, annot_local_id, annot_time_slot_start, annot_time_slot_end, annot_time_slot_duration, annotation_value, annotation_upload_date) 
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """
                # embedding_model = speaker_embedings.create_embedding_model()
                
                annot_values = []
                for tier in annotationDoc.tiers:
                    for annot in tier.annotations:
                        time_slot_start = annot.time_slot_start
                        time_slot_end = annot.time_slot_end
                        time_slot_duration = time_slot_end - time_slot_start
                        annot_record = (elan_file_file_id, tier.id, tier.annotator,
                                                tier.participant,
                                                annot.id, 
                                                time_slot_start, time_slot_end,time_slot_duration,
                                                annot.annotation_value,
                                                annotation_upload_date)
                        # annot_record ={"file_id":elan_file_file_id, 
                        # "tier_local_id":tier.id, 
                        # "tier_annotator":tier.annotator,
                        # "tier_participant":tier.participant,
                        # "annot_local_id":annot.id,
                        # "annot_time_slot_start":time_slot_start,
                        # "annot_time_slot_end":time_slot_end,
                        # "annot_time_slot_duration":time_slot_duration,
                        # "annotation_value":annot.annotation_value,
                        # "annotation_upload_date":annotation_upload_date}
                        annot_values.append(annot_record)
                # await connection.executemany(query, annot_values)

                result = await connection.copy_records_to_table(f"elan_annot_{annotation_record_type}",
                                                                records=annot_values, columns=[
                    "file_id", "tier_local_id", "tier_annotator", "tier_participant", "annot_local_id", 
                    "annot_time_slot_start", "annot_time_slot_end", "annot_time_slot_duration", "annotation_value", "annotation_upload_date"])

                await record_stats(str(len(annot_values)) , str(round(time.time()-started_time,3)))
                #logger.debug("[handle_elan_file]  Insert annotation: %s in %s sec ", str(len(annot_values)) , str(round(time.time()-started_time,3)))
                
                ### /elan_annot_
                
                
                calculated_data = json.dumps({'annotation_record_path': annotation_record_path,
                                            "elan_file":str(elan_file.annotation_upload_date)})#, 'elan_annot_doc': elan_annot_doc.model_dump()
                logger.debug("[handle_elan_file] calculated_data: %s", str(calculated_data))
                await log_finished_stats(annotation_record_path, batch_code)
        except  asyncpg.PostgresError as pe:
            await log_error(record_path=annotation_record_path, batch_code=batch_code, error_message="PG err:"+str(pe))
            logger.error(pe, stack_info=True, exc_info=True)
            logger.error("[handle_elan_file]Postgres error")
            logger.error(pe)
            pass
        except Exception as e:
            logger.error("[handle_elan_file] could not save result for %s", annotation_record_path )
            await log_error(record_path=annotation_record_path, batch_code=batch_code, error_message="Unkown error:"+str(e) )
            logger.error(e, stack_info=True, exc_info=True)
            logger.error("[handle_elan_file]Unkown error")
            logger.error(e)
            pass


# async def schedule_task(task_id, delay):
#     score = time.time() + delay
#     r= mb.broker.client()
#     await r.close()

async def log_finished_stats(record_path:str, batch_code:str):
    time_finished=datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    data={"last_record":record_path, "time_finished":time_finished}
    logger.info("[log_finished_stats] %s", json.dumps(data) )
    r= mb.broker.client()
    score = time.time() + 10
    await r.set("handle_elan_file_"+batch_code, json.dumps(data))
    await r.zadd('scheduled_tasks', {batch_code: score})
    current_time = time.time()
    tasks=await r.zrangebyscore('scheduled_tasks', 0, current_time)
    for task_id in tasks:
        logger.info("[log_finished_stats]+++ task_id %s", task_id)
        await r.zrem('scheduled_tasks', task_id)
    r.aclose()

async def log_error(record_path:str, batch_code:str, error_message:str ):
    with open("/app/logs/handler_elan_file.log", 'a') as logfile:
        logfile.write(",".join([record_path, batch_code, error_message]))

async def record_stats(num_rec, total_time ):
    with open("/app/logs/record_stats.csv", 'a') as logfile:
        logfile.write(",".join([num_rec, total_time]))
        logfile.write("\n")