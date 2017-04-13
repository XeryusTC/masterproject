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
        self.prio = set()

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
            for successor in self._successors(cur, time_step):
                # Skip successor in closed list
                if successor in closed_set and successor != cur:
                    continue

                score = g[cur] + 1
                # Ignore a path if it is longer
                if successor in g and score >= g[successor] \
                    and successor != cur:
                    continue
                came_from[time_step + 1, successor] = (time_step, cur)
                g[successor] = score
                heapq.heappush(open_set,
                    (score + self.h.dist(successor), time_step + 1, successor))
        raise util.NoPathsFoundException()

    def _successors(self, pos, time):
        successors = [pos] + self.world.neighbours(pos)
        filtered = []
        for successor in successors:
            for other_agent in self.prio:
                path = other_agent.path
                if len(path[time:]) >= 2:
                    paths = [path[time:time + 2], (pos, successor)]
                else:
                    paths = [[path[-1]], (pos, successor)]
                if util.paths_conflict(paths):
                    break
            else:
                filtered.append(successor)

        return filtered

    def _reverse_path(self, state, came_from):
        path = [state[1]]
        while state in came_from:
            state = came_from[state]
            path.append(state[1])
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
    print(conflicts)
    while conflicts:
        print(f'Conflicts found: {len(conflicts)}')
        conflict_sets = {}
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
            for agent in range(len(conflict_sets[conflict])):
                conflict_sets[conflict][agent].prio.update(
                    conflict_sets[conflict][:agent])

        # Replan for all agents
        for agent in agents:
            agent.plan()
        paths = [agent.path for agent in agents]
        conflicts = util.paths_conflict(paths)

    # Get final paths
    paths = list(agent.path for agent in agents)
    conflicts = util.paths_conflict(paths)
    print(f'Final conflicts found: {len(conflicts)}')
    end_time = timeit.default_timer()
    print(f'elapsed time: {(end_time - start_time) * 1000:5.3f}ms')

    print('Making visualisation')
    conflicts = util.paths_conflict(paths)
    vis = visualisation.Visualisation(world, num_agents, scale=20)
    vis.draw_paths('poc.mkv', paths)

if __name__ == '__main__':
    try:
        agents = int(sys.argv[1])
    except IndexError:
        agents = 2
    main(agents)
