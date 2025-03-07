from typing import List
from common import elan_file_schema as schema
# import Levenshtein 
from pyannote.core import Annotation, Segment
from pyannote.metrics.diarization import DiarizationErrorRate
import uuid

Segment.set_precision(ndigits=4)



# def segment_distance(ref:List[schema.ComparisonSegment], hyp:List[schema.ComparisonSegment]) -> int :
#     return Levenshtein.distance("lewenstein", "levenshtein")

def map_segments_elan( elan_segments:List[schema.ComparisonSegment]) -> Annotation:
    pant_annotation = Annotation()
    for cseg in elan_segments:
        pant_annotation[Segment(cseg.annot_time_slot_start/1000, cseg.annot_time_slot_end/1000)]=cseg.tier_local_id
    return pant_annotation

def diarization_error_rate(ref:List[schema.ComparisonSegment], hyp:List[schema.ComparisonSegment]):
    reference = map_segments_elan(ref)
    hypothesis = map_segments_elan(hyp)
    diarizationErrorRate = DiarizationErrorRate()
    der = diarizationErrorRate(reference, hypothesis, detailed=True)#uem=Segment(0, 40)
    return der


def myers_diff_segments(comparisonDetail: schema.ComparisonDetailPerFile) -> List[schema.ComparisonOperation]:
    """
    Calculates the Myers diff between two lists of ComparisonSegment, comparing 'annot_local_id'.

    Args:
        a: List of ComparisonSegment.
        b: List of ComparisonSegment.

    Returns:
        List of dictionaries representing the diff.
    """
    ref:List[schema.ComparisonSegment]=comparisonDetail.ref_segments
    hyp:List[schema.ComparisonSegment]=comparisonDetail.hyp_segments

    if not ref or not hyp:
        return [schema.ComparisonOperation(operation_id=uuid.uuid4(),
                    seg_operation=schema.ComparisonOperationType.op_noop,
                    ref_file_id=comparisonDetail.ref_file_id,
                    hyp_file_id=comparisonDetail.hyp_file_id,)]

    m, n = len(ref), len(hyp)

    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for j in range(n + 1):
        dp[0][j] = j
    for i in range(m + 1):
        dp[i][0] = i

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if ref[i - 1].annot_local_id == hyp[j - 1].annot_local_id:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])

    i, j = m, n
    diffs:List[schema.ComparisonOperation] = []

    while i > 0 or j > 0:
        ref_val:schema.ComparisonSegment|None = ref[i - 1] if i > 0 else None
        hyp_val:schema.ComparisonSegment|None = hyp[j - 1] if j > 0 else None

        if i > 0 and j > 0 and ref_val.annot_local_id == hyp_val.annot_local_id:
            # start_changed = a_val.annot_time_slot_start - b_val.annot_time_slot_start
            # end_changed = a_val.annot_time_slot_end - b_val.annot_time_slot_end
            
            # ref_val.annot_time_slot_start

            diffs.insert(0, 
                schema.ComparisonOperation(
                    operation_id=uuid.uuid4(),
                    seg_operation=schema.ComparisonOperationType.op_eql,
                    ref_file_id=comparisonDetail.ref_file_id,
                    ref_tier_local_id=ref_val.tier_local_id,
                    ref_annot_local_id=ref_val.annot_local_id,
                    ref_time_slot_start=ref_val.annot_time_slot_start,
                    ref_time_slot_end=ref_val.annot_time_slot_end,
                    hyp_file_id=comparisonDetail.hyp_file_id,
                    hyp_tier_local_id=hyp_val.tier_local_id,
                    hyp_annot_local_id=hyp_val.annot_local_id,
                    hyp_time_slot_start=hyp_val.annot_time_slot_start,
                    hyp_time_slot_end=hyp_val.annot_time_slot_end,
                )
            )


            # diffs.insert(0, {"ref": a_val, "b": b_val, "operation": "EQL", "start_changed": start_changed, "end_changed": end_changed})
            i -= 1
            j -= 1
        elif i > 0 and (j == 0 or dp[i][j] == dp[i - 1][j] + 1):
            # diffs.insert(0, {"ref": a_val, "hyp": None, "operation": "DEL"})
            diffs.insert(0, 
                schema.ComparisonOperation(
                    operation_id=uuid.uuid4(),
                    seg_operation=schema.ComparisonOperationType.op_del,
                    ref_file_id=comparisonDetail.ref_file_id,
                    ref_tier_local_id=ref_val.tier_local_id,
                    ref_annot_local_id=ref_val.annot_local_id,
                    ref_time_slot_start=ref_val.annot_time_slot_start,
                    ref_time_slot_end=ref_val.annot_time_slot_end,
                )
            )
            i -= 1
        else:
            # diffs.insert(0, {"ref": None, "hyp": b_val, "operation": "INS"})
            diffs.insert(0, 
                schema.ComparisonOperation(
                    operation_id=uuid.uuid4(),
                    seg_operation=schema.ComparisonOperationType.op_ins,
                    hyp_file_id=comparisonDetail.hyp_file_id,
                    hyp_tier_local_id=hyp_val.tier_local_id,
                    hyp_annot_local_id=hyp_val.annot_local_id,
                    hyp_time_slot_start=hyp_val.annot_time_slot_start,
                    hyp_time_slot_end=hyp_val.annot_time_slot_end,
                )
            )
            j -= 1

    return diffs