# -*- coding: utf-8 -*-
import heapq
import sys
import timeit
from pprint import pprint

from rra_star import RRAstar
from simulation import util, visualisation

from id import TimeExceeded
from od import heur_dist

def main(agents):
    world, starts, goals = util.generate_problem(agents, 16, 16, 0.2)
    print(starts, goals)

    start_time = timeit.default_timer()
    paths = standard_algorithm(agents, world, starts, goals,
                               start_time=start_time, max_time=15)
    end_time = timeit.default_timer()
    print(f'elapsed time: {(end_time - start_time) * 1000:5.3f}ms')

    print('Writing visualisations')
    vis = visualisation.Visualisation(world, agents, scale=20)
    frames = vis.draw_paths('sa.mkv', paths)

def standard_algorithm(agents, world, starts, goals, start_time=None,
                      max_time=None):
    starts = tuple(starts)
    goals = tuple(goals)
    closed_set = set()
    open_set = []
    came_from = {}
    g = {starts: 0}
    count = 0
    heapq.heappush(open_set, (0, count, starts))

    # Set up heuristics
    heur = {}
    for i in range(agents):
        heur[goals[i]] = RRAstar(world, starts[i], goals[i])

    # Display predicted cost
    pred_cost = heur_dist(heur, goals, starts)
    print(f'predicted cost: {pred_cost}')

    while open_set:
        time = timeit.default_timer()
        if start_time != None and (time - start_time) > max_time:
            raise TimeExceeded()
        f, _, current = heapq.heappop(open_set)
        #print(f'f: {f:4}, current: {current}')

        if current == goals:
            return reconstruct_path(came_from, current)

        closed_set.add(current)
        for cost, neighbour in successor_states(world, current, goals,
                                                start_time, max_time):
            if neighbour in closed_set:
                continue

            score = g[current] + cost
            # We found a longer path, ignore it
            if neighbour in g and score >= g[neighbour]:
                continue
            came_from[neighbour] = current
            g[neighbour] = score
            count += 1
            heapq.heappush(open_set, (score + heur_dist(heur, goals, current),
                                      count, neighbour))

    return None

def reconstruct_path(came_from, pos):
    path = [pos]
    while pos in came_from:
        pos = came_from[pos]
        path.append(pos)
    path = tuple(zip(*reversed(path)))
    return path

def successor_states(world, current, goals, start_time, max_time):
    for succ in rec_successor_states(world, current, 0):
        time = timeit.default_timer()
        if start_time != None and (time - start_time) > max_time:
            raise TimeExceeded()

        if util.paths_conflict(tuple(zip(current, succ))):
            print('Conflicting paths found', current, succ)
            continue

        score = sum(1 for i in range(len(current)) if goals[i] != succ[i])
        yield score, tuple(succ)

def rec_successor_states(world, current, agent):
    for neighbour in world.neighbours(current[agent]) + [current[agent]]:
        # Base case (final agent)
        if agent == len(current) - 1:
            yield [neighbour]
        # Recursive case
        else:
            for substate in rec_successor_states(world, current, agent+1):
                yield [neighbour] + substate

if __name__ == '__main__':
    try:
        agents = int(sys.argv[1])
    except IndexError:
        agents = 2
    main(agents)
