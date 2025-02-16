import asyncio
import json
import logging
from common.postgres import database
from common import message_broker as mb
from .elan_file import elan_annot_repo
from common import elan_file_repo
import os
# import uuid
import datetime

logger = logging.getLogger()
logging.basicConfig(
    level=os.environ.get('LOGLEVEL', 'INFO').upper()
)





async def reader():
    await database.connect()
    await mb.broker.connect()
    # logger.info("[reader] 2")
    r= await mb.broker.client()
    pong=await r.ping()
    logger.info("[reader] Ping: " + str(pong)) 
    
    async with r.pubsub() as p:
        logger.info("[reader] Subscribe: " + mb.INPUT_CHANNEL_NAME)
        await p.subscribe(mb.INPUT_CHANNEL_NAME)
        if p != None:
            while True:
                message = await p.get_message(ignore_subscribe_messages=True)
                await asyncio.sleep(0)
                if message != None:
                    logger.info("[reader] Recieved: " + str(message))
                    data = json.loads(message['data'])
                    try:
                        # ep = ElanPostprocess(data)
                        # response_msg = ep.distance_from_velocity()
                        annotation_record_path=data['annotation_record_path']
                        ti_m = os.path.getmtime(annotation_record_path)
                        annotation_upload_date=datetime.datetime.fromtimestamp(ti_m)
                        
                        elan_file = await elan_file_repo.insert_record(annotation_record_path, annotation_upload_date)
                        elan_annot_doc=  await elan_annot_repo.insert_annotations(annotation_record_path, elan_file.file_id, elan_file.annotation_upload_date)
                        calculated_data = json.dumps({'annotation_record_path': annotation_record_path,
                                                       "elan_file":str(elan_file.annotation_upload_date)})#, 'elan_annot_doc': elan_annot_doc.model_dump()
                        logger.info("[reader] calculated_data: " + str(calculated_data))
                        # await pub.publish('elan_postprocessed', calculated_data)
                    except Exception as e:
                        logger.error(str(e))
                        pass
    await r.aclose()
    await database.disconnect()

class ElanPostprocess:
    def __init__(self, data):
        self.msg = data['msg']
    
    def postprocess(self):
        print(self.msg)
        return "done"




if __name__ == '__main__':
    logger.info("Starting")
    asyncio.run(reader())
