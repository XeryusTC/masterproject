# -*- coding: utf-8 -*-
import heapq
from pprint import pprint
import random
import sys
import timeit

from simulation import util, visualisation
from rra_star import RRAstar

class Agent:
    def __init__(self, world, start, goal):
        self.world = world
        self.start = start
        self.goal = goal
        self.h = RRAstar(world, start, goal)
        self.path = []

    def plan(self):
        self.path = self._astar()

    def _astar(self):
        closed_set = set()
        open_set = []
        came_from = {}
        g = {self.start: 0}
        heapq.heappush(open_set, (0, 0, self.start))

        while open_set:
            _, time_step, cur = heapq.heappop(open_set)
            if cur == self.goal:
                return self._reverse_path((time_step, cur), came_from)

            closed_set.add(cur)
            for successor in self._successors(cur):
                # Skip successor in closed list
                if successor in closed_set:
                    continue

                score = g[cur] + 1
                # Ignore a path if it is longer
                if successor in g and score >= g[successor]:
                    continue
                came_from[time_step + 1, successor] = (time_step, cur)
                g[successor] = score
                heapq.heappush(open_set,
                    (score + self.h.dist(successor), time_step + 1, successor))
        raise util.NoPathsFoundException()

    def _successors(self, pos):
        return [pos] + self.world.neighbours(pos)

    def _reverse_path(self, state, came_from):
        path = [state[1]]
        last_time = state[0]
        while state in came_from:
            state = came_from[state]
            # Add the state multiple times if we need to wait
            for i in range(last_time - state[0]):
                path.append(state[1])
            last_time = state[0]
        path.reverse()
        return path

    def __repr__(self):
        return f'{self.start}-{self.goal}'


def main(num_agents):
    world, starts, goals = util.generate_problem(num_agents, 16, 16, 0.2)

    start_time = timeit.default_timer()
    # Create agents
    agents = [Agent(world, starts[i], goals[i]) for i in range(num_agents)]
    # Calculate the initial optimal set of paths
    paths = []
    for agent in agents:
        agent.plan()
        paths.append(agent.path)

    conflicts = util.paths_conflict(paths)
    conflict_sets = {}
    while conflicts:
        print(f'Conflicts found: {len(conflicts)}')
        for conflict in conflicts:
            # Find time and place of conflict
            try:
                place = agents[conflict['path1']].path[conflict['time']]
            except IndexError:
                place = agents[conflict['path2']].path[conflict['time']]
            place_time = (place, conflict['time'])
            if place_time not in conflict_sets:
                conflict_sets[place_time] = set()
            # Add agents to conflict
            conflict_sets[place_time].add(agents[conflict['path1']])
            conflict_sets[place_time].add(agents[conflict['path2']])

        # Randomly get an order for the conflict
        for conflict in conflict_sets:
            conflict_sets[conflict] = list(conflict_sets[conflict])
        pprint(conflict_sets)
        conflicts = False

    end_time = timeit.default_timer()
    print(f'elapsed time: {(end_time - start_time) * 1000:5.3f}ms')

    print('Making visualisation')
    conflicts = util.paths_conflict(paths)
    vis = visualisation.Visualisation(world, num_agents, scale=20)
    #vis.draw_paths('poc.mkv', paths)
    conflict_im = vis.draw_paths_with_conflicts(paths, conflicts)
    conflict_im.save('poc_conflicts.png')

if __name__ == '__main__':
    try:
        agents = int(sys.argv[1])
    except IndexError:
        agents = 2
    main(agents)
