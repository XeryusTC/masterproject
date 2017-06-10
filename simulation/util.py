# -*- coding: utf-8 -*-
from pprint import pprint
import random

from .world import World

class NoPathsFoundException(Exception):
    pass


def generate_problem(agents, width, height, obstacles=0.2):
    world = World(width, height, obstacles)
    starts = random.sample(world.passable, agents)
    goals  = random.sample(world.passable, agents)
    return world, starts, goals

def paths_conflict(paths):
    agents = len(paths)
    conflicts = []

    for i in range(agents):
        for j in range(i+1, agents):
            min_length = min(len(paths[i]), len(paths[j]))
            max_length = max(len(paths[i]), len(paths[j]))
            for time in range(min_length - 1):
                if moves_conflict(paths[i][time:time+2],
                                  paths[j][time:time+2]):
                    conflicts.append({'path1': i, 'path2': j, 'time': time})
            # Check if one agent goes through the endpoint of the other
            if min_length != max_length:
                if len(paths[i]) < len(paths[j]):
                    shortest = paths[i]
                    longest  = paths[j]
                else:
                    shortest = paths[j]
                    longest  = paths[i]
                for time in range(min_length, max_length):
                    if shortest[-1] == longest[time]:
                        conflicts.append({'path1': i, 'path2': j,
                            'time': time})
    return conflicts

def moves_conflict(move1, move2):
    """Returns True if moves conflict, False otherwise"""
    ox0 = move1[0][0]
    oy0 = move1[0][1]
    ox1 = move2[0][0]
    oy1 = move2[0][1]
    nx0 = move1[1][0]
    ny0 = move1[1][1]
    nx1 = move2[1][0]
    ny1 = move2[1][1]

    # If agents are not near each other they can not conflict
    if abs(ox0 - ox1) > 2 or abs(oy0 - oy1) > 2:
        return False
    # Same position
    if nx0 == nx1 and ny0 == ny1:
        return True
    # Swapping position
    elif ox0 == nx1 and oy0 == ny1 and ox1 == nx0 and oy1 == ny0:
        return True
    # Crossing edge
    elif ox0 == ox1 and nx0 == nx1 and ny0 == oy1 and oy0 == ny1:
        return True
    elif oy0 == oy1 and ny0 == ny1 and nx0 == ox1 and ox0 == nx1:
        return True
    return False
