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


import logging

logger = logging.getLogger('uvicorn.error')



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
    r= await mb.broker.client()
    await r.publish(mb.INPUT_CHANNEL_NAME, json.dumps(data))
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
    der = elan_file_repo.calc_diarization_error_rate(file_name, tier_local_id)
    return der

@elan_file_router.get("/files/{file_name}/diff", description="Diff annotations org vs annot1 ")
async def diff_document(file_name:str, tier_local_id:Optional[str]=None)-> List[schema.ComparisonOperation]:
    comparisonDetail=await elan_file_repo.compare_annotations_per_file_with_wer(file_name, tier_local_id=tier_local_id) #, "IG005.eaf" tier_local_id="S0000"
    return comparisonDetail
    # return 

def mapComparisonOperation2str(op:schema.ComparisonOperation) -> str:
    return f"{op.operation_id},{op.seg_operation.value},{op.hyp_file_id},{op.hyp_tier_local_id},{op.hyp_annot_local_id},{op.hyp_time_slot_start},{op.hyp_time_slot_end},{op.ref_file_id},{op.ref_tier_local_id},{op.ref_annot_local_id},{op.ref_time_slot_start},{op.ref_time_slot_end}"
    

@elan_file_router.get("/files/{file_name}/diff/csv", description="Diff annotations org vs annot1. Diff format ")
async def diff_document_csv(file_name:str, tier_local_id:Optional[str]=None):
    comparisonDetail=await elan_file_repo.compare_annotations_per_file_with_wer(file_name, tier_local_id=tier_local_id) #, "IG005.eaf" tier_local_id="S0000"
    # result = myers_diff_segments(comparisonDetail)
    result_csv = [mapComparisonOperation2str(x) for x in comparisonDetail]
    
    header_csv="operation_id,seg_operation,hyp_file_id,hyp_tier_local_id,hyp_annot_local_id,hyp_time_slot_start,hyp_time_slot_end,ref_file_id,ref_tier_local_id,ref_annot_local_id,ref_time_slot_start,ref_time_slot_end"
    result_csv.insert(0, header_csv )
    # return 
    return Response("\n".join(result_csv),
                    media_type='text/csv')
    # return 