# -*- coding: utf-8 -*-
import heapq
import sys
import timeit

from simulation import util, visualisation
from rra_star import RRAstar

def main(agents):
    world, starts, goals = util.generate_problem(agents, 16, 16, 0.2)

    start_time = timeit.default_timer()
    # Calculate RRAstar
    heuristics = {}
    for agent in range(agents):
        heuristics[goals[agent]] = RRAstar(world, starts[agent], goals[agent])
    # Calculate the initial optimal set of paths
    paths = []
    for agent in range(agents):
        paths.append(astar(world, starts[agent], goals[agent],
                           heuristics[goals[agent]]))

    conflicts = util.paths_conflict(paths)

    end_time = timeit.default_timer()
    print(f'elapsed time: {(end_time - start_time) * 1000:5.3f}ms')

    print('Making visualisation')
    vis = visualisation.Visualisation(world, agents, scale=20)
    #vis.draw_paths('poc.mkv', paths)
    conflict_im = vis.draw_paths_with_conflicts(paths, conflicts)
    conflict_im.save('poc_conflicts.png')

def astar(world, start, goal, h):
    closed_set = set()
    open_set = []
    came_from = {}
    g = {start: 0}
    heapq.heappush(open_set, (0, start))

    while open_set:
        cur = heapq.heappop(open_set)[1]
        if cur == goal:
            return reverse_path(goal, came_from)

        closed_set.add(cur)
        for successor in successors(world, cur):
            # Skip successor in closed list
            if successor in closed_set:
                continue

            score = g[cur] + 1
            # We found a longer path, ignore it
            if successor in g and score >= g[successor]:
                continue
            came_from[successor] = cur
            g[successor] = score
            heapq.heappush(open_set,
                (score + h.dist(successor), successor))
    raise util.NoPathsFoundException()

def successors(world, pos):
    return [pos] + world.neighbours(pos)

def reverse_path(pos, came_from):
    path = [pos]
    while pos in came_from:
        pos = came_from[pos]
        path.append(pos)
    path.reverse()
    return path

if __name__ == '__main__':
    try:
        agents = int(sys.argv[1])
    except IndexError:
        agents = 2
    main(agents)
