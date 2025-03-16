from typing import List, Tuple
import unittest
from common.segment_util import levenshtein_distance, levenshtein_distance_stats
#segment_distance,
from common import elan_file_schema as schema
import uuid

class TestSegmentUtil(unittest.TestCase):

    async def test_levenshtein_distance_eql(self):
        """
        Should be eq
        """
        comparisonOperation=schema.ComparisonOperation(operation_id=uuid.uuid4(),seg_operation=schema.ComparisonOperationType.op_eql)
        word_distance=await levenshtein_distance(comparisonOperation.hyp_annotation_value, comparisonOperation.ref_annotation_value)
        stats=await levenshtein_distance_stats(word_distance=word_distance)
        # print(stats)
        self.assertEqual( 0, len(word_distance))
        self.assertEqual( 0, stats.op_total)



    async def test_levenshtein_distance_eq_sub(self):
        """
        Should be sub
        """
        comparisonOperation=schema.ComparisonOperation(operation_id=uuid.uuid4(),seg_operation=schema.ComparisonOperationType.op_eql,
                                                       hyp_annotation_value="Testas testui",
                                                       ref_annotation_value="testis testui")
        word_distance=await levenshtein_distance(comparisonOperation.hyp_annotation_value, 
                                    comparisonOperation.ref_annotation_value)
        stats=await levenshtein_distance_stats(word_distance=word_distance)
        print(stats)
        self.assertEqual( 2, len(word_distance))
        self.assertIsNotNone(word_distance[0].op_sub)
        self.assertIsNotNone(word_distance[1].op_eql)
        self.assertEqual( 2, stats.op_total)
        self.assertEqual( 1, stats.op_sub)
        


    async def test_levenshtein_distance_rem(self):
        """
        Should be sub
        """
        comparisonOperation=schema.ComparisonOperation(operation_id=uuid.uuid4(),seg_operation=schema.ComparisonOperationType.op_eql,
                                                       hyp_annotation_value="Testas mano testui",
                                                       ref_annotation_value="Testas testui")
        word_distance=await levenshtein_distance(comparisonOperation.hyp_annotation_value, 
                                    comparisonOperation.ref_annotation_value)
        stats=await levenshtein_distance_stats(word_distance=word_distance)
        print(word_distance)
        self.assertEqual( 3, len(word_distance))
        self.assertIsNotNone(word_distance[1].op_del)
        self.assertEqual( 3, stats.op_total)
        self.assertEqual( 1, stats.op_del)
