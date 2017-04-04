# -*- coding: utf-8 -*-
from unittest import TestCase
from simulation import util

class SimulationTests(TestCase):
    def test_paths_conflict(self):
        paths = (((0,0), (1,1), (2,2), (3,3), (4,4)),
                 ((2,2), (1,1), (1,2), (1,3), (2,4)),
                 ((2,5), (1,4), (1,3), (1,2), (0,2)),
                 ((1,2), (2,3), (3,3), (3,4), (4,3)))
        conflicts = util.paths_conflict(paths)
        self.assertCountEqual(conflicts, [
            {'path1': 0, 'path2': 1, 'time': 0},
            {'path1': 1, 'path2': 2, 'time': 2},
            {'path1': 0, 'path2': 3, 'time': 3},
        ])

    def test_paths_conflict_swap(self):
        paths = (((0,0), (1,1)), ((1,1), (0,0)))
        conflicts = util.paths_conflict(paths)
        self.assertEqual(conflicts, [{'path1': 0, 'path2': 1, 'time': 0}])

    def test_paths_conflict_same_position(self):
        paths = (((0,0), (1,1)), ((2,2), (1,1)))
        conflicts = util.paths_conflict(paths)
        self.assertEqual(conflicts, [{'path1': 0, 'path2': 1, 'time': 0}])

    def test_paths_conflict_cross_north_to_south(self):
        paths = (((0,0), (1,1)), ((1,0), (0,1)))
        conflicts = util.paths_conflict(paths)
        self.assertEqual(conflicts, [{'path1': 0, 'path2': 1, 'time': 0}])

    def test_paths_conflict_cross_south_to_north(self):
        paths = (((1,1), (0,0)), ((0,1), (1,0)))
        conflicts = util.paths_conflict(paths)
        self.assertEqual(conflicts, [{'path1': 0, 'path2': 1, 'time': 0}])

    def test_paths_conflict_cross_west_to_east(self):
        paths = (((0,0), (1,1)), ((0,1), (1,0)))
        conflicts = util.paths_conflict(paths)
        self.assertEqual(conflicts, [{'path1': 0, 'path2': 1, 'time': 0}])

    def test_paths_conflict_cross_east_to_west(self):
        paths = (((1,1), (0,0)), ((1,0), (0,1)))
        conflicts = util.paths_conflict(paths)
        self.assertEqual(conflicts, [{'path1': 0, 'path2': 1, 'time': 0}])
