# -*- coding: utf-8 -*-
from collections import namedtuple
import heapq
import itertools
from pprint import pprint
import random
import sys
import timeit

from simulation import util, visualisation
from sortedcontainers import SortedListWithKey
from rra_star import RRAstar
from id import TimeExceeded
from poc import find_conflicts

TimePlace = namedtuple('TimePlace', ['time', 'place'])

class Agent:
    def __init__(self, world, start, goal):
        self.world = world
        self.start = start
        self.goal = goal
        self.h = RRAstar(world, start, goal)
        self.path = []
        self.conflicts = SortedListWithKey(key=lambda c: c.time)
        self.resolved_conflicts = []
        self.higher_prio = []

    def plan(self, start_time, max_time):
        self.path = self._astar(start_time, max_time)

    def construct_higher_prio(self):
        prio = set()
        for conflict in self.conflicts:
            prio.update(conflict.agents[:conflict.agents.index(self)])
        print(f'Agent {self} prio: {prio}')
        self.higher_prio = prio

    def propose(self, conflict):
        # Return a set order at first
        # TODO: actually propose something good
        return conflict.agents

    def resolved_conflict(self, conflict):
        self.resolved_conflicts.append(conflict)

    def _astar(self, start_time, max_time):
        closed_set = set()
        open_set = []
        came_from = {}
        g = {self.start: 0}
        heapq.heappush(open_set, (0, 0, self.start))
        self.construct_higher_prio()

        while open_set:
            time = timeit.default_timer()
            if start_time != None and (time - start_time) > max_time:
                raise TimeExceeded()
            _, time_step, cur = heapq.heappop(open_set)
            if cur == self.goal:
                return self._reverse_path((time_step, cur), came_from)

            closed_set.add(cur)
            for successor in self._successors(cur, time_step, start_time,
                                              max_time):
                # Skip successor in closed list
                if successor in closed_set and successor != cur:
                    continue

                score = g[cur] + 1
                # Ignore a path if it is a longer variant
                if successor in g and score >= g[successor] \
                        and successor != cur:
                    continue
                came_from[time_step + 1, successor] = (time_step, cur)
                g[successor] = score
                heapq.heappush(open_set,
                               (score + self.h.dist(successor), time_step + 1,
                                successor))
        raise util.NoPathsFoundException()

    def _successors(self, pos, time, start_time, max_time):
        successors = [pos] + self.world.neighbours(pos)
        filtered = []
        for successor in successors:
            for other_agent in self.higher_prio:
                cur_time = timeit.default_timer()
                if start_time != None and (cur_time - start_time) > max_time:
                    raise TimeExceeded()
                path = other_agent.path
                if len(path[time:]) >= 2:
                    if util.moves_conflict(path[time:time + 2],
                        (pos, successor)):
                        break
                else:
                    if util.moves_conflict((path[-1], path[-1]),
                        (pos, successor)):
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


class Conflict:
    def __init__(self, position, time, agents):
        self.position = position
        self.time = time
        self.agents = list(agents)
        self.solution = None

    def __repr__(self):
        return f'<{self.time:2d} {self.position} {self.agents}>'

    def __eq__(self, other):
        return (self.position == other.position
            and self.time == other.time
            and self.agents == other.agents)

    def __hash__(self):
        return hash((self.position, self.time, tuple(self.agents)))

    def add_agent(self, agent):
        if agent not in self.agents:
            self.agents.append(agent)
            # Register self with agent
            agent.conflicts.add(self)

    def resolve(self, start_time, max_time):
        # If this is not the first conflict for an agent then don't bother
        for agent in self.agents:
            if agent.conflicts[0] != self:
                return

        # Let the agents propose priorities
        proposals = (agent.propose(self) for agent in self.agents)
        proposals = tuple(proposals)[:1] # TODO: remove temporary thing

        # Enter voting if there are multiple proposals
        if len(proposals) > 1:
            pass
        else:
            self.solution = proposals[0]

        # Tell the agents that we are done
        for agent in self.agents:
            agent.plan(start_time, max_time)
            agent.resolved_conflict(self)


def version1(agents, start_time, max_time, visualize=False):
    paths = []
    for agent in agents:
        agent.plan(start_time=start_time, max_time=max_time)
        paths.append(agent.path)

    if visualize:
        vis = visualisation.Visualisation(agents[0].world,
                                          len(agents),
                                          scale=20)
        count = 0
    conflicts = util.paths_conflict(paths)
    while conflicts:
        time = timeit.default_timer()
        if start_time != None and (time - start_time) > max_time:
            raise TimeExceeded()
        if visualize:
            print('Exporting conflicts')
            im = vis.draw_paths_with_conflicts(paths, conflicts)
            im.save(f'conflict_{count:05}.png')
            count += 1
        print(f'Conflicts found: {len(conflicts)}')
        pprint(conflicts)
        conflict_objs = convert_conflicts(agents, conflicts)

        # Get the agents to resove the conflicts
        for agent in agents:
            try:
                conflict = agent.conflicts[0]
            except IndexError:
                continue  # Agent has no conflicts
            conflict.resolve(start_time, max_time)

        # Update the list of conflicts
        paths = [agent.path for agent in agents]
        conflicts = util.paths_conflict(paths)
        if count > 5:
            break

    return paths

def convert_conflicts(agents, conflicts):
    conflict_objs = {}
    for conflict in conflicts:
        # Find place and time of conflict
        try:
            place = agents[conflict['path1']].path[conflict['time']]
        except IndexError:
            place = agents[conflict['path2']].path[conflict['time']]
        time_place = TimePlace(conflict['time'], place)
        # Create Conflict if necessary
        if time_place not in conflict_objs:
            conflict_objs[time_place] = Conflict(place, conflict['time'], [])
        # Add agents to conflict
        conflict_objs[time_place].add_agent(agents[conflict['path1']])
        conflict_objs[time_place].add_agent(agents[conflict['path2']])
    return conflict_objs

def main(num_agents):
    world, starts, goals = util.generate_problem(num_agents, 16, 16, 0.2)

    # Create agents
    agents = [Agent(world, starts[i], goals[i]) for i in range(num_agents)]
    start_time = timeit.default_timer()
    paths = version1(agents, None, None, True)
    end_time = timeit.default_timer()
    print(f'elapsed time: {(end_time - start_time) * 1000:5.3f}ms')

    print('Making visualisation')
    vis = visualisation.Visualisation(world, num_agents, scale=20)
    vis.draw_paths('version1.mkv', paths)

if __name__ == '__main__':
    try:
        agents = int(sys.argv[1])
    except IndexError:
        agents = 2
    main(agents)
