from typing import List, Optional
from common import elan_file_schema as schema
from common.postgres import database
import datetime
from pathlib import Path




def parse(record_path:str, annotation_upload_date:datetime.datetime) -> schema.ElanFile:
    annotator=record_path.split("/")[-3]
    listnumm=record_path.split("/")[-2]
    # annotation_upload_date = datetime.datetime.fromisoformat(annotation_upload_date_str)
    elan_file = schema.ElanFile(record_path=record_path, annotator=annotator, listnumm=listnumm, annotation_upload_date=annotation_upload_date)
    return elan_file


async def insert_record(record_path:str, annotation_upload_date:datetime.datetime) -> schema.ElanFile:
    elan_file = parse(record_path, annotation_upload_date)
    query = "INSERT INTO elan_file (record_path, annotator, listnumm, annotation_upload_date) VALUES ($1, $2, $3, $4) RETURNING file_id"
    async with database.pool.acquire() as connection:
        elan_file.file_id=await connection.fetchval(query, elan_file.record_path, elan_file.annotator, elan_file.listnumm, elan_file.annotation_upload_date)
    return elan_file
