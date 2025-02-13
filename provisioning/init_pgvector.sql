
-- Install the extension we just compiled

CREATE EXTENSION IF NOT EXISTS vector;

-- DROP TABLE elan_file;
CREATE TABLE IF NOT EXISTS elan_file (
    file_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    record_path text,
    annotator text,
    source_code text,
    annotation_upload_date timestamp with time zone,
    last_modification_date timestamp with time zone
);


CREATE TABLE IF NOT EXISTS elan_annot (
   annot_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
   file_id uuid,
   tier_local_id text,
   tier_annotator text,
   tier_participant text,
   annot_local_id text,
   annot_time_slot_start int,
   annot_time_slot_end int,
   annotation_value text,
   speaker_code text,
   speaker_embedding vector(192)
);


