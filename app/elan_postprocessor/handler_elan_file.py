import asyncio
import os
from datetime import datetime
from time import time
import json


from common.postgres import database
from common import message_broker as mb
from common import elan_file_repo

from .elan_file import elan_annot_repo



import logging
logger = logging.getLogger()
logging.basicConfig(
    level=os.environ.get('ANNOT_PROCESSOR_LOGLEVEL', 'INFO').upper()
)


async def handle_elan_file(data):
    """
    Process
    """
    logger.debug("[process_elan]Task started %s (count: %s)",
                    asyncio.current_task().get_name())
    annotation_record_path=data['annotation_record_path']
    annotation_record_type=data['annotation_record_type']
    batch_code=data['batch_code']
    logger.debug("[process_elan] input - path: %s, type: %s, batch: %s", annotation_record_path, annotation_record_type, batch_code)
    ti_m = os.path.getmtime(annotation_record_path)
    annotation_upload_date=datetime.fromtimestamp(ti_m)
    
    started_time = time()
    elan_file = await elan_file_repo.insert_record(annotation_record_path, annotation_upload_date, annotation_record_type, batch_code)
    logger.debug("[process_elan] Insert record %s", str(round(time()-started_time,3)))
    
    started_time = time()
    await elan_annot_repo.insert_annotations(annotation_record_path, elan_file.file_id, elan_file.annotation_upload_date, annotation_record_type)
    logger.debug("[process_elan] Insert annotation: %s ", str(round(time()-started_time,3)))
    calculated_data = json.dumps({'annotation_record_path': annotation_record_path,
                                "elan_file":str(elan_file.annotation_upload_date)})#, 'elan_annot_doc': elan_annot_doc.model_dump()
    logger.debug("[process_elan] calculated_data: %s", str(calculated_data))