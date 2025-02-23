import asyncio
import logging
import os
import signal
from time import time
from datetime import datetime
import json

from common.postgres import database
from common import message_broker as mb

from .elan_file import elan_annot_repo
from common import elan_file_repo

from collections import deque


logger = logging.getLogger()
logging.basicConfig(
    level=os.environ.get('ANNOT_PROCESSOR_LOGLEVEL', 'INFO').upper()
    
)

class WorkerPool:
    def __init__(self, task_count=5):
        self.task_count = task_count
        self.running = set()
        self.waiting = deque()
        
    @property
    def running_task_count(self):
        return len(self.running)
        
    def add_task(self, coro):
        if len(self.running) >= self.task_count:
            self.waiting.append(coro)
        else:
            self._start_task(coro)
        
    def _start_task(self, coro):
        self.running.add(coro)
        asyncio.create_task(self._task(coro))
        
    async def _task(self, coro):
        try:
            return await coro
        finally:
            self.running.remove(coro)
            if self.waiting:
                coro2 = self.waiting.popleft()
                self._start_task(coro2)



class ElanWorker:
    def __init__(self):
        self.keep_running = True
        self.workerPool = WorkerPool()

        self.loop = asyncio.new_event_loop()
        # self.loop.add_signal_handler(signal.SIGTERM, self.stop)
        for signame in ('SIGINT', 'SIGTERM'):
            self.loop.add_signal_handler(getattr(signal, signame),
                            lambda signame=signame: 
                            asyncio.create_task(self.stop(signame)))

    async def process_elan(self, data):
        """
        Process
        """
        logger.debug("[process_elan]Task started %s (count: %s)",
                      asyncio.current_task().get_name(),
              self.workerPool.running_task_count)
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
        


    async def manage(self):
        """
         Manange 
        """
        logger.info('starting')
        await database.connect()
        await mb.broker.connect()
        self.client = await mb.broker.client()
        pong=await self.client.ping()
        logger.debug("[manage] Ping: %s", str(pong)) 
        async with self.client.pubsub() as p:
            logger.debug("[manage] Subscribe: %s", mb.INPUT_CHANNEL_NAME)
            await p.subscribe(mb.INPUT_CHANNEL_NAME)
            if p != None:
                while self.keep_running:
                    message = await p.get_message(ignore_subscribe_messages=True)
                    if message != None:                      
                        logger.info("[reader] Recieved: " + str(message))
                        data = json.loads(message['data'])
                        try:
                            # started_time = time()
                            self.workerPool.add_task(self.process_elan(data))
                            # await self.process_elan(data)
                            # logger.info("[manage] process elan: %s ", str(round(time()-started_time,3)))
                        except Exception as e:
                            logger.error(str(e))
                            pass
                    await asyncio.sleep(0.1)
                    
        

    async def stop(self, signame):
        """
        Stop
        """
        self.keep_running=False
        logger.info('[stop]stopping')
        logger.debug("[stop]got signal %s: exit", signame)

        await self.client.aclose()
        logger.debug("[stop] db close")
        await database.disconnect()
        logger.debug("[stop] all closed")
        # self.loop.stop()
        

    def run(self, close=True):
        """
        Run
        """
        logger.info('[run]starting loop')
        try:
            self.loop.run_until_complete(self.manage())
            logger.info('[run]loop stopped')
        finally:
            logger.info("[run] done")
            # if close:
            #     self.loop.close()


if __name__ == '__main__':
    print("to stop run:\nkill -TERM {}".format(os.getpid()))
    ew = ElanWorker()

    ew.run()
    
    # asyncio.run(reader())
    

    
