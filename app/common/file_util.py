import datetime
from common import elan_file_schema as schema
import re

VALID_FILE_PATH_REGEX = r"\/([A-Z]{2})\/([\/res\d\-]*)\/([A-Z]{2}\d{3}.*eaf)"

ERR_FILE_FORMAT="ERR_FILE_FORMAT"

def create_file_record(record_path:str, annotation_upload_date:datetime.datetime, batch_code: str) -> schema.ElanFile:

    matches = re.search(VALID_FILE_PATH_REGEX, record_path)

    elan_file = None

    if matches:
        # print(matches.group(1))
        annotator=matches.group(1)
        listnumm=matches.group(2)
        elan_file = schema.ElanFile(record_path=record_path, annotator=annotator, listnumm=listnumm, annotation_upload_date=annotation_upload_date, batch_code=batch_code)
    else:
        elan_file = schema.ElanFile(record_path=record_path, annotation_upload_date=annotation_upload_date, batch_code=batch_code, error_code=ERR_FILE_FORMAT)

    
    return elan_file