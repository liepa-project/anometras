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
