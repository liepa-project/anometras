from typing import List, Optional
import src.elan_file.elan_file_schema as schema
from src.commons.postgres import database
import datetime
from pathlib import Path




def parse(record_path:str, annotation_upload_date:datetime.datetime) -> schema.ElanFile:
    annotator=record_path.split("/")[-2]
    # annotation_upload_date = datetime.datetime.fromisoformat(annotation_upload_date_str)
    elan_file = schema.ElanFile(record_path=record_path, annotator=annotator, annotation_upload_date=annotation_upload_date)
    return elan_file


async def insert_record(record_path:str, annotation_upload_date:datetime.datetime) -> schema.ElanFile:
    elan_file = parse(record_path, annotation_upload_date)
    query = "INSERT INTO elan_file (record_path, annotator, annotation_upload_date) VALUES ($1, $2, $3) RETURNING file_id"
    async with database.pool.acquire() as connection:
        elan_file.file_id=await connection.fetchval(query, elan_file.record_path, elan_file.annotator, elan_file.annotation_upload_date)
    return elan_file
