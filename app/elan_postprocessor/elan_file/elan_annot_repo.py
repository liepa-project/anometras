from typing import List, Optional
from common import elan_file_schema as schema
# from .elan_annot_repo_influxdb import insert_annotations_influxdb 
from common.postgres import database
import datetime

from pathlib import Path
from pympi import Eaf

import logging

logger = logging.getLogger("DEBUG")



def map_annotations(key:str, detail, time_slots:List[schema.TimeSlot]) -> schema.Annotation:
    time_slot_start_id=detail[0]
    time_slot_start = [ts.time_value for ts in time_slots if ts.id == time_slot_start_id][0]
    time_slot_end_id=detail[1]
    time_slot_end = [ts.time_value for ts in time_slots if ts.id == time_slot_end_id][0]
    # logger.debug('[map_annotations] detail', detail)
    return schema.Annotation(id=key,
                            time_slot_start_id=time_slot_start_id,
                            time_slot_start=time_slot_start,
                            time_slot_end_id=time_slot_end_id,
                            time_slot_end=time_slot_end,
                            annotation_value=detail[2])#

def map_tier_detail(key:str, tier_details, time_slots:List[schema.TimeSlot]) -> schema.Tier:
    annotations_dict=tier_details[0]
    annotations=[map_annotations(k,v, time_slots) for k,v in annotations_dict.items()]
    # print(annotations)
    # logger.debug('[map_tier_detail] annotation empty %s', tier_details[1])
    # logger.debug('[map_tier_detail] annotation header %s', tier_details[2])
    # logger.debug('[map_tier_detail] annotation seq %s', tier_details[3])
    if "ANNOTATOR" in tier_details[2]: 
        return schema.Tier(id=key,
                        annotator=tier_details[2]["ANNOTATOR"],
                        participant=tier_details[2].get("PARTICIPANT","NONE"),
                        annotations=annotations)
    else:
        return None
#[schema.Annotation(id=k, time_slot_start="", time_slot_end="", annotation_value="" ) for k,v in annotations.items]

async def parse_document(elan_temp_path:Path, annotation_upload_date:datetime.datetime) ->schema.AnnotationDoc:
    
    eaf = Eaf(elan_temp_path)
    time_slots = [schema.TimeSlot(id=k, time_value=v) for k, v in eaf.timeslots.items()]
    tiers_all = [map_tier_detail(k,v, time_slots) for k, v in eaf.tiers.items()]
    tiers = list(filter(lambda x: x is not None, tiers_all)) 
    logger.debug("[parse_document] %s", eaf.properties[0])


    return schema.AnnotationDoc(doc_urn="",
                                media_url=eaf.media_descriptors[0]["MEDIA_URL"],
                                annotation_upload_date=annotation_upload_date,
                                time_slots=time_slots,
                                 tiers=tiers)




async def insert_annotations ( elan_temp_path:Path, elan_file_file_id:str, annotation_upload_date:datetime.datetime, annotation_record_type:str) -> schema.AnnotationDoc:
    annotationDoc = await parse_document(elan_temp_path, annotation_upload_date)
    # insert_annotations_influxdb(annotationDoc)
    # print("insert_annotations", annotationDoc)
    query = f"""
        INSERT INTO elan_annot_{annotation_record_type} 
            (file_id, tier_local_id, tier_annotator, tier_participant, annot_local_id, annot_time_slot_start, annot_time_slot_end, annot_time_slot_duration, annotation_value, annotation_upload_date) 
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
    """
    # embedding_model = speaker_embedings.create_embedding_model()
    async with database.pool.acquire() as connection:
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
                annot_values.append(annot_record)
                # await connection.execute(query, elan_file_file_id, tier.id, tier.annotator,
                #                         tier.participant,
                #                         annot.id, 
                #                         time_slot_start, time_slot_end,time_slot_duration,
                #                         annot.annotation_value,
                #                         annotation_upload_date)
        logger.debug('[insert_annotations] inserting %s records', len(annot_values))
        await connection.executemany(query, annot_values)
    return annotationDoc

async def select_segments(file_id:str) -> schema.AnnotationDoc:
    query="select annot_time_slot_start, annot_time_slot_end from elan_annot where file_id=$1;"
    async with database.pool.acquire() as connection:
        rows = await connection.fetch(query, 'LA001.eaf', 'a3')
        data = [dict(row) for row in rows]
        schema.AnnotationSegment()
    return None
