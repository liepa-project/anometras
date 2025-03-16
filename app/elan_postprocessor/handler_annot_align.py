
# import asyncio
from typing import List, Optional
import os
# from datetime import datetime
from time import time
# import json


from common.postgres import database
from common import message_broker as mb
from common import elan_file_repo

# from .elan_file import elan_annot_repo
from common import elan_file_schema as schema


from common import elan_file_repo
from common import segment_util, file_util


import logging
logger = logging.getLogger()
logging.basicConfig(
    level=os.environ.get('ANNOT_PROCESSOR_LOGLEVEL', 'INFO').upper()
)

total_file_count=0
total_time=0



def mapComparisonOperationWER(op:schema.ComparisonOperation) -> schema.WordOperationStats:
    start=time()
    word_distance=segment_util.levenshtein_distance(hypStr=op.hyp_annotation_value, refStr=op.ref_annotation_value)
    # print(" \t\t\t [mapComparisonOperationWER] levenshtein_distance:",  round(time()-start, 3))
    # start=time()
    stats=segment_util.levenshtein_distance_stats(word_distance=word_distance)
    # print(" \t\t\t [mapComparisonOperationWER] levenshtein_distance:",  round(time()-start, 3))
    # start=time()
    op.word_op_stats=stats
    return op
    

async def handle_annot_align(data:dict) -> List[schema.ComparisonOperation]:
    start=time()
    handler_start=time()
    annotation_record_path=data['annotation_record_path']
    tier_local_id=None
    logger.info(" \t\t [handle_annot_align] record_path: %s", annotation_record_path)
    file_name=file_util.get_file_name(annotation_record_path)
    comparisonDetail=await elan_file_repo.select_annotations_per_file(file_name, tier_local_id) #, "IG005.eaf" tier_local_id="S0000"
    logger.info(" \t\t [handle_annot_align] select_annotations_per_file: %s, %s", file_name ,round(time()-start, 3))
    if(comparisonDetail.hyp == None and comparisonDetail.ref==None):
        raise Exception("Not found")
    start=time()
    result = segment_util.myers_diff_segments(comparisonDetail)
    logger.info(" \t\t [handle_annot_align] myers_diff_segments: %s, %s", file_name ,  round(time()-start, 3))
    start=time()
    # result_wer=[]
    # for x in result:
    #     result_wer.append(mapComparisonOperationWER(x))
    result_wer = map(mapComparisonOperationWER,result)
    logger.info(" \t\t [handle_annot_align] mapComparisonOperationWER: %s, %s", file_name ,  round(time()-start, 3))
    logger.info(" \t\t [handle_annot_align] %s ; result len:  %s", file_name , len(result))
    global total_time
    global total_file_count
    total_time=total_time+round(time()-handler_start, 3)
    total_file_count=total_file_count+1
    logger.info("___[handle_annot_align] total_time: %s; total_file_count: %s", total_time, total_file_count)
    return list(result_wer)