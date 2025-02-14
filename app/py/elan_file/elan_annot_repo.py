from typing import List, Optional
import py.elan_file.elan_file_schema as schema
from py.commons.postgres import database

from pathlib import Path
from pympi import Eaf


def map_annotations(key:str, detail, time_slots:List[schema.TimeSlot]) -> schema.Annotation:
    time_slot_start_id=detail[0]
    time_slot_start = [ts.time_value for ts in time_slots if ts.id == time_slot_start_id][0]
    time_slot_end_id=detail[1]
    time_slot_end = [ts.time_value for ts in time_slots if ts.id == time_slot_end_id][0]
    # print(detail)
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
    print("annotation empty:", tier_details[1])
    print("annotation header:", tier_details[2])
    print("annotations seq:", tier_details[3])
    if "ANNOTATOR" in tier_details[2]: 
        return schema.Tier(id=key,
                        annotator=tier_details[2]["ANNOTATOR"],
                        participant=tier_details[2].get("PARTICIPANT","NONE"),
                        annotations=annotations)
    else:
        return None
#[schema.Annotation(id=k, time_slot_start="", time_slot_end="", annotation_value="" ) for k,v in annotations.items]

async def parse_document(elan_temp_path:Path) ->schema.AnnotationDoc:
    
    eaf = Eaf(elan_temp_path)
    time_slots = [schema.TimeSlot(id=k, time_value=v) for k, v in eaf.timeslots.items()]
    tiers_all = [map_tier_detail(k,v, time_slots) for k, v in eaf.tiers.items()]
    tiers = list(filter(lambda x: x is not None, tiers_all)) 
    print("properties", eaf.properties[0])
    print("MEDIA_URL", )

    return schema.AnnotationDoc(doc_urn="",
                                media_url=eaf.media_descriptors[0]["MEDIA_URL"],
                                time_slots=time_slots,
                                 tiers=tiers)




async def insert_annotations ( elan_temp_path:Path, elan_file:schema.ElanFile) -> schema.AnnotationDoc:
    annotationDoc = await parse_document(elan_temp_path)
    # print("insert_annotations", annotationDoc)
    query = """
        INSERT INTO elan_annot 
            (file_id, tier_local_id, tier_annotator, tier_participant, annot_local_id, annot_time_slot_start, annot_time_slot_end, annotation_value) 
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    """
    # embedding_model = speaker_embedings.create_embedding_model()
    async with database.pool.acquire() as connection:
        for tier in annotationDoc.tiers:
            for annot in tier.annotations:
                time_slot_start = annot.time_slot_start
                time_slot_end = annot.time_slot_end
                # speaker_embedding = speaker_embedings.segment_embedding_ms(
                #     audio_path=file_dir+"/LA001.wav",
                #     start_ms=time_slot_start,
                #     end_ms=time_slot_end,
                #     embedding_model=embedding_model)
                await connection.execute(query, elan_file.file_id, tier.id, tier.annotator,
                                        tier.participant,
                                        annot.id, time_slot_start, time_slot_end,
                                        annot.annotation_value)
    return annotationDoc

async def select_segments(file_id:str) -> schema.AnnotationDoc:
    query="select annot_time_slot_start, annot_time_slot_end from elan_annot where file_id=$1;"
    async with database.pool.acquire() as connection:
        rows = await connection.fetch(query, 'LA001.eaf', 'a3')
        data = [dict(row) for row in rows]
        schema.AnnotationSegment()
    return None
