"""Contains tests for saving edges to the database with a max stored distance"""

# from python
from unittest import TestCase
from unittest.mock import MagicMock

# from dependencies
import click
from sqlalchemy import select

# from other modules
import big_scape.data as bs_data
import big_scape.comparison as bs_comparison
from big_scape.cli.cli_validations import validate_max_stored_distance


def create_mock_edges(distances: list[float]) -> list:
    """Creates a list of mock edges with the given distances between unique record ids"""
    edges = []
    for idx, distance in enumerate(distances):
        edges.append(
            (
                idx,
                idx + 100,
                distance,
                1 - distance,
                0.0,
                0.0,
                1,
                bs_comparison.ComparableRegion(0, 0, 0, 0, 0, 0, 0, 0, False),
            )
        )
    return edges


class TestSaveEdges(TestCase):
    """Contains tests for saving edges with a max stored distance"""

    def setUp(self):
        bs_data.DB.create_in_mem()

    def tearDown(self):
        bs_data.DB.close_db()

    def get_stored_distances(self) -> list[float]:
        distance_table = bs_data.DB.metadata.tables["distance"]
        select_statement = select(distance_table.c.distance)
        return sorted(row[0] for row in bs_data.DB.execute(select_statement))

    def test_save_edges_no_max_distance(self):
        """Tests that all edges are saved when no max distance is given"""
        edges = create_mock_edges([0.2, 0.5, 0.6, 1.0])

        bs_comparison.save_edges_to_db(edges, commit=True)

        self.assertEqual(self.get_stored_distances(), [0.2, 0.5, 0.6, 1.0])

    def test_save_edges_max_distance_default(self):
        """Tests that the default max stored distance of 1.0 saves all edges"""
        edges = create_mock_edges([0.2, 0.5, 0.6, 1.0])

        bs_comparison.save_edges_to_db(edges, commit=True, max_distance=1.0)

        self.assertEqual(self.get_stored_distances(), [0.2, 0.5, 0.6, 1.0])

    def test_save_edges_max_distance(self):
        """Tests that only edges at or below the max distance are saved"""
        edges = create_mock_edges([0.2, 0.5, 0.6, 1.0])

        bs_comparison.save_edges_to_db(edges, commit=True, max_distance=0.5)

        self.assertEqual(self.get_stored_distances(), [0.2, 0.5])


class TestValidateMaxStoredDistance(TestCase):
    """Contains tests for the max stored distance CLI validation"""

    def test_valid_max_stored_distance(self):
        """Tests that a max stored distance equal to the largest cutoff is accepted"""
        ctx = MagicMock(obj={"gcf_cutoffs": [0.5, 0.3], "max_stored_distance": 0.5})

        validate_max_stored_distance(ctx)

    def test_invalid_max_stored_distance(self):
        """Tests that a max stored distance below the largest cutoff is rejected"""
        ctx = MagicMock(obj={"gcf_cutoffs": [0.5, 0.3], "max_stored_distance": 0.4})

        self.assertRaises(click.BadParameter, validate_max_stored_distance, ctx)
