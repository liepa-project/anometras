from fastapi import APIRouter, Header, Request, UploadFile, HTTPException
import src.elan_file.elan_file_schema as schema
from src.elan_file import elan_file_repo
from src.elan_file import elan_annot_repo
from typing import Optional, List, Annotated
import datetime
import shutil
from tempfile import NamedTemporaryFile
from pathlib import Path



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


@elan_file_router.post("/files", description="Register Elan file")
async def parse_document(uploadFile: UploadFile, 
                         annotation_record_path: Annotated[str |None, Header()] ,
                         annotation_upload_date:  Annotated[datetime.datetime |None, Header()] )-> schema.ElanFile:
    
    content_type = uploadFile.content_type
    temp_path=None
    if content_type == 'application/xml' or content_type == 'text/xml':
        temp_path=save_upload_file_tmp(uploadFile)
        print("temp_path", temp_path)
        #return schema.ElanFile(record_path=str(temp_path))
    else:
        raise HTTPException(status_code=400, detail=f'Content type {content_type} not supported')

    elan_annot_doc=  await elan_annot_repo.insert_annotations(temp_path, elan_file)
    elan_file = await elan_file_repo.insert_record(annotation_record_path, annotation_upload_date)
    elan_file.annot_doc = elan_annot_doc
    ### delete temp_path
    return elan_file


@elan_file_router.get("/files/{file_id}/segments", description="Select Elan DB")
async def select_document(file_id:str)-> schema.AnnotationSegment:
    return await elan_annot_repo.select_segments(file_id)