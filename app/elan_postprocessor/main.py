# import asyncio
import logging
import os
# import signal
# from time import time
# from datetime import datetime
# import json

# from common.postgres import database
# from common import message_broker as mb

# from .elan_file import elan_annot_repo
# from common import elan_file_repo


from collections import deque
from .elan_worker import ElanWorker


logger = logging.getLogger()
logging.basicConfig(
    level=os.environ.get('ANNOT_PROCESSOR_LOGLEVEL', 'INFO').upper()
)



if __name__ == '__main__':
    print("to stop run:\nkill -TERM {}".format(os.getpid()))
    ew = ElanWorker()

    ew.run()
    
    # asyncio.run(reader())
    

    
