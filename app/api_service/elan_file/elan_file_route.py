from fastapi import APIRouter,  BackgroundTasks, UploadFile, HTTPException, Form, Header
from common import elan_file_repo
# from app.elan_postprocessor.elan_file import elan_annot_repo
from common import elan_file_schema as schema
from typing import Optional, List, Annotated
import datetime
import shutil
from tempfile import NamedTemporaryFile
from pathlib import Path
import json
import common.message_broker as mb


#Ploting
from .elan_plot import plot_segments 
from fastapi.responses import Response

import time

import logging
logger = logging.getLogger('uvicorn')



elan_file_router = APIRouter(prefix="/elan-file", tags=["elan"])

    

def save_upload_file_tmp(upload_file: UploadFile) -> Path:
    try:
        suffix = Path(upload_file.filename).suffix
        with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(upload_file.file, tmp)
            tmp_path = Path(tmp.name)
    finally:
        upload_file.file.close()
    return tmp_path


@elan_file_router.post("/files/external", description="Register Elan file by sending full content(when there is no access)")
async def parse_document(uploadFile: UploadFile, 
                         batch_code: Annotated[str, Form()],
                         annotation_record_type: Annotated[str, Form()],
                         annotation_record_path: Annotated[str |None, Header()] ,
                         annotation_upload_date:  Annotated[datetime.datetime |None, Header()] )-> schema.ElanFile:
    
    content_type = uploadFile.content_type
    temp_path=None
    if content_type == 'application/xml' or content_type == 'text/xml':
        temp_path=save_upload_file_tmp(uploadFile)
        logger.debug("[parse_document] temp_path", temp_path)
        #return schema.ElanFile(record_path=str(temp_path))
    else:
        raise HTTPException(status_code=400, detail=f'Content type {content_type} not supported')

    elan_file = await elan_file_repo.insert_record(annotation_record_path, annotation_upload_date, batch_code=batch_code, annotation_record_type=annotation_record_type)
    # elan_annot_doc=  await elan_annot_repo.insert_annotations(temp_path, elan_file)
    # elan_file.annot_doc = elan_annot_doc
    ### delete temp_path
    return elan_file



async def publish_to_redis(data: dict):
    r= mb.broker.client()
    await r.publish(mb.ELAN_FILE_INPUT_CHANNEL_NAME, json.dumps(data))
    await r.aclose()



@elan_file_router.post("/files/local", description="Register Elan file by sending path on mounted volume")
async def create_task(background_tasks: BackgroundTasks, 
                    batch_code: Annotated[str, Form()],
                    annotation_record_type: Annotated[str, Form()],
                    annotation_record_path: Annotated[str, Form()]
                    #annotation_upload_date: Optional[datetime.datetime] = Form(None) #Annotated[Optional[datetime.datetime], Form()]   
                    ) -> str:

    data = {'annotation_record_path': annotation_record_path, 'annotation_record_type':annotation_record_type, 'batch_code': batch_code}
    background_tasks.add_task(publish_to_redis, data)
    return "ok"



@elan_file_router.get("/files/record_types/{annotation_record_type}", description="Select Elan files by record types")
async def select_document(annotation_record_type:schema.RecordType, limit: Optional[int] = 10, offset: Optional[int] = 0)-> List[schema.ElanFile]:
    return await elan_file_repo.select_files(annotation_record_type=annotation_record_type, limit=limit, offset=offset)

@elan_file_router.get("/files/record_types/{annotation_record_type}/paths", description="Select Elan files by record types")
async def select_document_record_paths(annotation_record_type:schema.RecordType)-> List[str]:
    result_csv=await elan_file_repo.select_files_record_paths(annotation_record_type=annotation_record_type)
    return Response("\n".join(result_csv),
                    media_type='text/csv')


@elan_file_router.get("/files/{file_name}", description="Get file annotations")
async def select_annotations(file_name:str, tier_local_id:Optional[str]=None)-> Optional[schema.ComparisonDetailPerFile]:
    result=await elan_file_repo.select_annotations_per_file(file_name, tier_local_id=tier_local_id)
    return result
    # return 


@elan_file_router.get("/files/{file_name}/segment/plot", description="Plot segments")
async def plot_segment(file_name:str, tier_local_id:Optional[str]=None):
    
    
    # annot1_annotation = map_segments_elan(result.ref_segments)
    # org_annotation = map_segments_elan(result.hyp_segments)
    annot1_files=await elan_file_repo.select_files_by_file_name(schema.RecordType.annot1,file_name, 1,0)
    if len(annot1_files)!=1:
        return Response(status_code=500, )
    annot1=annot1_files[0]
    annot1_segments= await elan_file_repo.select_segments_by_file_id(schema.RecordType.annot1, annot1.file_id, tier_local_id=tier_local_id, limit=10000, offset=0)

    img_buf = await plot_segments(annot1_segments)
    headers = {'Content-Disposition': 'inline; filename="out.png"'}
    return Response(img_buf.getvalue(),
                    headers=headers, media_type='image/png')


@elan_file_router.get("/files/{file_name}/segment/diarization_error_rate", description="Diarization Error Rate")
async def calc_diarization_error_rate(file_name:str, tier_local_id:Optional[str]=None):
    der = await elan_file_repo.calc_diarization_error_rate(file_name, tier_local_id)
    return der

@elan_file_router.get("/files/{file_name}/diff", description="Diff annotations org vs annot1 ")
async def diff_document(file_name:str, tier_local_id:Optional[str]=None)-> schema.ComparisonOperationContainer:
    comparisonOperationContainer=await elan_file_repo.comparison_operation_per_file(file_name) #, "IG005.eaf" tier_local_id="S0000"
    return comparisonOperationContainer
    # return 

@elan_file_router.get("/files/{file_name}/diff/csv", description="Diff annotations org vs annot1. Diff format ")
async def diff_document_csv(file_name:str, tier_local_id:Optional[str]=None):
    result_csv=await elan_file_repo.comparison_operation_per_file_csv(file_name)
    return Response("\n".join(result_csv),
                    media_type='text/csv')


@elan_file_router.post("/stats/reindex/wer", description="Reindex elan files that requires: calculate features for each file each anotation ")
async def reindex_all_files_wer()->str:
    start = time.time()
    # result = await elan_file_repo.process_all_files_wer()
    # result = await elan_file_repo.etl()
    result = await elan_file_repo.publish_reindexable_files_wer()
    end = time.time() 
    # logger.error("[process_all_files_wer] total process time: %s", round(end-start, 3))
    print("[router process_all_files_wer] \n\n total process time: ", round(end-start, 3))
    return "OK:" + str(result)


