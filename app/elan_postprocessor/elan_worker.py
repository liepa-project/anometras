import asyncio
import os
# from datetime import datetime
from time import time
import json
import signal


from common.postgres import database
from common import message_broker as mb
# from common import elan_file_repo

# from .elan_file import elan_annot_repo
from .worker_pool import WorkerPool

from .handler_annot_align import handle_annot_align
from .handler_elan_file import handle_elan_file

import logging
logger = logging.getLogger()
logging.basicConfig(
    level=os.environ.get('ANNOT_PROCESSOR_LOGLEVEL', 'INFO').upper()
)

CHANNEL_HANDLER={
    mb.ELAN_FILE_INPUT_CHANNEL_NAME:handle_elan_file,
    mb.ANNOT_ALIGN_INPUT_CHANNEL_NAME:handle_annot_align

}


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


        


    async def manage(self):
        """
         Manange 
        """
        logger.info('starting')
        await database.connect()
        await mb.broker.connect()
        self.client = await mb.broker.client()
        pong=await self.client.ping()
        logger.info("[manage] Ping: %s", str(pong)) 
        async with self.client.pubsub() as p:
            channels=[mb.ELAN_FILE_INPUT_CHANNEL_NAME, mb.ANNOT_ALIGN_INPUT_CHANNEL_NAME]
            logger.info("[manage] Subscribe: %s", channels)
            await p.subscribe(*channels)
            if p != None:
                while self.keep_running:
                    message = await p.get_message(ignore_subscribe_messages=True)
                    if message != None:                      
                        logger.info("[reader] Recieved: " + str(message))
                        data = json.loads(message['data'])
                        channel = message['channel'].decode("utf-8")
                        logger.info("[reader] Process in channel: %s, data: %s", channel, str(data))
                        try:
                            handler=CHANNEL_HANDLER[channel]
                            # started_time = time()
                            self.workerPool.add_task(handler(data))
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
