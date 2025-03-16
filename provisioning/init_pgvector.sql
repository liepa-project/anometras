
-- Install the extension we just compiled

CREATE EXTENSION IF NOT EXISTS vector;

-- DROP TABLE elan_file;
CREATE TABLE IF NOT EXISTS elan_file_annot1 (
    file_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    record_path text,
    annotator text,
    listnumm text,
    source_code text,
    annotation_upload_date date,
    -- last_modification_date date,
    error_code text,
    batch_code text
);


CREATE TABLE IF NOT EXISTS elan_annot_annot1 (
   annot_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
   file_id uuid,
   tier_local_id text,
   tier_annotator text,
   tier_participant text,
   annot_local_id text,
   annot_time_slot_start int,
   annot_time_slot_end int,
   annot_time_slot_duration int,
   annotation_value text,
   annotation_upload_date date,
   speaker_code text
);


-- DROP TABLE elan_file;
CREATE TABLE IF NOT EXISTS elan_file_org (
    file_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    record_path text,
    annotator text,
    listnumm text,
    source_code text,
    annotation_upload_date date,
    -- last_modification_date date,
    error_code text,
    batch_code text
);


CREATE TABLE IF NOT EXISTS elan_annot_org (
   annot_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
   file_id uuid,
   tier_local_id text,
   tier_annotator text,
   tier_participant text,
   annot_local_id text,
   annot_time_slot_start int,
   annot_time_slot_end int,
   annot_time_slot_duration int,
   annotation_value text,
   annotation_upload_date date,
   speaker_code text
);


--    , speaker_embedding vector(192)



-- DROP TABLE calc_comparison_operation_registry;
CREATE TABLE IF NOT EXISTS calc_comparison_operation_registry (
    id serial primary key,
    record_path text,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(record_path)
);

-- DROP TABLE calc_comparison_operation;
CREATE TABLE IF NOT EXISTS calc_comparison_operation (
    id serial primary key,
    operation_id uuid,
    seg_operation text,
    hyp_file_id uuid,
    hyp_tier_local_id text,
    hyp_annot_local_id text,
    hyp_time_slot_start int,
    hyp_time_slot_end int,
    hyp_annotation_value text,
    ref_file_id uuid,
    ref_tier_local_id text,
    ref_annot_local_id text,
    ref_time_slot_start int,
    ref_time_slot_end int,
    ref_annotation_value text,
    word_op_stats JSONB
);

