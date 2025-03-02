from typing import List, Tuple
import unittest
from api_service.elan_file.segment_util import  diarization_error_rate, myers_diff_segments
#segment_distance,
from common import elan_file_schema as schema
import uuid

def create_segement_arr(segment_list:List[tuple[int,int, str]]) -> List[schema.ComparisonSegment]:
    return [create_segement_tuple(x) for x in segment_list]

def create_segement_tuple(segment:tuple[int,int, str]) -> schema.ComparisonSegment:
    (start, end, code)=segment
    return create_segement(start, end, code)

def create_segement(start:int, end:int, code:str) -> schema.ComparisonSegment:
    return schema.ComparisonSegment(
        annot_id= uuid.uuid4(),
        participant=code,
        annot_local_id="l"+str(start),
        tier_local_id="t1",
        annot_time_slot_start=start,
        annot_time_slot_end=end
    )

class TestSegmentUtil(unittest.TestCase):

    # def test_segment_distance_mising(self):
    #     ref=[create_segement(0, 10, "A"),  create_segement(21, 30, "A")]
    #     hyp=[create_segement(0, 10, "A"), create_segement(11, 20, "A"), create_segement(21, 30, "A")]
    #     result=segment_distance(ref=ref, hyp=hyp)
    #     self.assertEqual( 2, result)

    
    def test_der(self):
        ref=create_segement_arr([(0, 10,"A"),(12, 20,"B"), (24, 27, "A"), (30, 40, "C")])
        hyp=create_segement_arr([(2, 13,"a"),(13, 14,"D"), (14, 20, "b"), (22, 38, "c"), (38, 40, "d")])
        result=diarization_error_rate(ref=ref, hyp=hyp)
        # print("result", result)
        self.assertEqual( 0.516, round(result["diarization error rate"],3))

    def test_myers_diff_segments_noop(self):
        """
        Should be noop
        """
        comparisonDetail=schema.ComparisonDetailPerFile()
        result=myers_diff_segments(comparisonDetail)
        self.assertEqual( 1, len(result))
        self.assertEqual( schema.ComparisonOperationType.op_noop, result[0].seg_operation)

        comparisonDetail=schema.ComparisonDetailPerFile(
            ref=schema.ElanFile(record_path="path"),
            ref_file_id=uuid.uuid4(),
            ref_segments=[schema.ComparisonSegment(
                annot_id=uuid.uuid4(),
                tier_local_id="tid1",
                annot_local_id="aid1",
                annot_time_slot_start=10,
                annot_time_slot_end=20
            )]
        )
        result=myers_diff_segments(comparisonDetail)

        self.assertEqual( 1, len(result))
        self.assertEqual( schema.ComparisonOperationType.op_noop, result[0].seg_operation)


    def test_myers_diff_segments_eq(self):
        """
        should be equal
        """
        ref_segments=create_segement_arr([(0, 10,"A"),(12, 20,"B"), (24, 27, "A"), (30, 40, "C")])
        hyp_segments=create_segement_arr([(0, 10,"A"),(12, 20,"B"), (24, 27, "A"), (30, 40, "C")])
        comparisonDetail=schema.ComparisonDetailPerFile(
            ref=schema.ElanFile(record_path="ref_path"),
            ref_segments=ref_segments,
            ref_file_id=uuid.uuid4(),
            hyp=schema.ElanFile(record_path="hyp_path"),
            hyp_segments=hyp_segments,
            hyp_file_id=uuid.uuid4(),
        )
        result=myers_diff_segments(comparisonDetail)
        self.assertEqual( 4, len(result))
        # print(result[2])
        self.assertEqual( schema.ComparisonOperationType.op_eql, result[2].seg_operation)


    def test_myers_diff_segments_ins(self):
        """
        should be equal
        """
        ref_segments=create_segement_arr([(0, 10,"A"), (24, 27, "A"), (30, 40, "C")])
        hyp_segments=create_segement_arr([(0, 10,"A"),(12, 20,"B"), (24, 27, "A"), (30, 40, "C")])
        comparisonDetail=schema.ComparisonDetailPerFile(
            ref=schema.ElanFile(record_path="ref_path"),
            ref_segments=ref_segments,
            ref_file_id=uuid.uuid4(),
            hyp=schema.ElanFile(record_path="hyp_path"),
            hyp_segments=hyp_segments,
            hyp_file_id=uuid.uuid4(),
        )
        result=myers_diff_segments(comparisonDetail)
        self.assertEqual( 4, len(result))
        # print(result[2])
        self.assertEqual( schema.ComparisonOperationType.op_ins, result[1].seg_operation)


    def test_myers_diff_segments_del(self):
        """
        should be equal
        """
        ref_segments=create_segement_arr([(0, 10,"A"),(12, 20,"B"), (24, 27, "A"), (30, 40, "C")])
        hyp_segments=create_segement_arr([(0, 10,"A"),(12, 20,"B"), (24, 27, "A")])
        comparisonDetail=schema.ComparisonDetailPerFile(
            ref=schema.ElanFile(record_path="ref_path"),
            ref_segments=ref_segments,
            ref_file_id=uuid.uuid4(),
            hyp=schema.ElanFile(record_path="hyp_path"),
            hyp_segments=hyp_segments,
            hyp_file_id=uuid.uuid4(),
        )
        result=myers_diff_segments(comparisonDetail)
        self.assertEqual( 4, len(result))
        # print(result[2])
        self.assertEqual( schema.ComparisonOperationType.op_del, result[3].seg_operation)