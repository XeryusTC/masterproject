# -*- coding: utf-8 -*-
import heapq
from pprint import pprint
import random
import sys

from simulation import util, visualisation
from rra_star import RRAstar

def astar(world, start, goal, window):
    closed_set = set()
    open_set = []
    came_from = {}
    g = {start: 0}
    heapq.heappush(open_set, (0, 0, start))
    h = RRAstar(world, start, goal)

    while open_set:
        f, time_step, cur = heapq.heappop(open_set)
        print('evaluating', f, time_step, cur)
        pprint(open_set)

        if time_step > window:
            return reverse_path((time_step, cur), came_from)

        closed_set.add(cur)
        for successor in (world.neighbours(cur) + [cur]):
            if successor in closed_set and cur != successor:
                continue

            if time_step == window:
                score = g[cur] + h.dist(successor)
            elif cur == goal and successor == goal:
                score = g[cur]
            else:
                score = g[cur] + 1
            # Ignore a path if it is a longer variant
            if successor in g and score >= g[successor] and successor != cur:
                continue

            came_from[time_step + 1, successor] = (time_step, cur)
            g[successor] = score
            if time_step == window:
                heapq.heappush(open_set, (score, time_step + 1, successor))
            else:
                heapq.heappush(open_set, (score + h.dist(successor),
                                          time_step + 1, successor))
    raise util.NoPathsFoundException()

def reverse_path(state, came_from):
    path = [state[1]]
    while state in came_from:
        state = came_from[state]
        path.append(state[1])
    path.reverse()
    return path

def main(window):
    world, *problem = util.generate_problem(1, 16, 16, 0.2)
    start = problem[0][0]
    goal  = problem[1][0]
    print('Navigating from', start, 'to', goal)
    actual_path = []

    while start != goal:
        path = astar(world, start, goal, window_size)
        try:
            start = path[int(window / 2)]
        except IndexError:
            start = path[-1]
        actual_path += path[:int(window / 2) + 1]
        print('Partial path', path)
        print('Path up to now', actual_path)
        print('next start', start, ', going to', goal)
        input()

if __name__ == '__main__':
    try:
        window_size = sys.argv[1]
    except IndexError:
        window_size = 4
    main(window_size)
