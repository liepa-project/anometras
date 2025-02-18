from influxdb_client import InfluxDBClient, Point
from common import elan_file_schema as schema
import os

import logging

logger = logging.getLogger("DEBUG")

BUCKET = os.getenv('INFLUXDB_BUCKET')
client = InfluxDBClient(url=os.getenv('INFLUXDB_URL'),
                token=os.getenv('INFLUXDB_TOKEN'), org=os.getenv('INFLUXDB_ORG'))
write_api = client.write_api()

TOPIC="anotavimo_valandos"

def insert_annotations_influxdb(annotationDoc:schema.AnnotationDoc):
    """ The callback for when a PUBLISH message is received from the server."""
    logger.error('[insert_annotations_influxdb]annotationDoc' )
    # # We recived bytes we need to converts into something usable
    # measurement = int(msg.payload)
    measurement=0
    logger.error('[insert_annotations_influxdb]' )
    upload_time=annotationDoc.annotation_upload_date
    ## InfluxDB logic
    for tier in annotationDoc.tiers:
        for annot in tier.annotations:
            time_slot_start = annot.time_slot_start
            time_slot_end = annot.time_slot_end
            measurement=measurement + (time_slot_end-time_slot_start)
        
        logger.error('[insert_annotations_influxdb]measurement' + str(measurement) )
        logger.error('[insert_annotations_influxdb]upload_time' + str(upload_time) )
        point = Point(TOPIC).tag(
                "annotator", tier.annotator).tag(
                "tier_local_id", tier.id
            ).field(
            "duration_h", measurement).time(
            time=upload_time, write_precision="s")
        write_api.write(bucket=BUCKET, record=point)
