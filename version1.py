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
Weights = namedtuple('Weights', ['path_len', 'conflict_count'])

class Agent:
    def __init__(self, world, start, goal, weights=Weights(1, 3)):
        self.world = world
        self.start = start
        self.goal = goal
        self.h = RRAstar(world, start, goal)
        self.path = []
        self.conflicts = SortedListWithKey(key=lambda c: c.time)
        self.resolved_conflicts = []
        self.current_conflict = None
        self.higher_prio = []
        self.weights = weights

    def plan(self, start_time, max_time):
        print(f'Planning for agent {self}')
        self.old_path = self.path
        self.construct_higher_prio()
        self.path = self._astar(start_time, max_time)

    def construct_higher_prio(self):
        prio = set()
        # Construct priorities from the conflict solutions
        for conflict in self.resolved_conflicts:
            idx = conflict.solution.index(self)
            prio.update(conflict.solution[:idx])
        # Update with the current proposed solution
        if self.current_conflict != None:
            idx = self.current_conflict.proposal.index(self)
            prio.update(self.current_conflict.proposal[:idx])
        print(f'  Agent {self} final prio: {prio}')
        self.higher_prio = prio

    def propose(self, conflict):
        # If there are only two agents, propose to go first
        if len(conflict.agents) == 2:
            if conflict.agents[0] == self:
                print(f'{self} proposing to go first')
                return conflict.agents
            else:
                print(f'{self} proposing to go first, with reversal')
                return reversed(conflict.agents)
        # Return a set order at first
        # TODO: actually propose something good
        return conflict.agents

    def resolved_conflict(self, conflict):
        self.resolved_conflicts.append(conflict)

    def evaluate(self, conflicts):
        score = 0
        # Change in path length
        score += (len(self.old_path) - len(self.path)) * self.weights.path_len
        # Change in conflicts
        filtered = list(filter(lambda c: self in c.agents, conflicts.values()))
        print(f'{self} {len(self.conflicts)} {len(filtered)}')
        score += (len(self.conflicts) - len(filtered)) * \
                 self.weights.conflict_count

        print(f'Agent score {self}: {score}')
        return score

    def _astar(self, start_time, max_time):
        closed_set = set()
        open_set = []
        came_from = {}
        g = {self.start: 0}
        heapq.heappush(open_set, (0, 0, self.start))

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
        return (isinstance(other, Conflict)
                and self.position == other.position
                and self.time == other.time
                and self.agents == other.agents)

    def __hash__(self):
        return hash((self.position, self.time, tuple(self.agents)))

    def add_agent(self, agent):
        if agent not in self.agents:
            self.agents.append(agent)

    def resolve(self, agents, start_time, max_time):
        # Don't try to solve a conflict after having already done so
        if self.solution:
            return
        # If this is not the first conflict for an agent then don't bother
        for agent in self.agents:
            if agent.conflicts[0] != self:
                return
            agent.current_conflict = self

        print(f'Resolving conflict {self}')

        # Let the agents propose priorities
        proposals = tuple(tuple(agent.propose(self)) for agent in self.agents)

        # Enter voting if there are multiple proposals
        votes = {}
        if len(proposals) > 1:
            for proposal in proposals:
                print('Evaluation proposal', proposal)
                self.proposal = proposal
                votes[proposal] = 0
                for agent in proposal:
                    agent.plan(start_time, max_time)
                    # Get updated list of conflicts to evaluate
                    paths = tuple(a.path for a in agents)
                    conflicts = util.paths_conflict(paths)
                    conflicts = convert_conflicts(agents, conflicts)
                    votes[proposal] += agent.evaluate(conflicts)
            # Pick the proposal with the highest sum of votes
            pprint(votes)
            self.solution = max(votes, key=votes.get)
        else:
            self.solution = proposals[0]

        self.proposal = None
        print('SOLUTION', self.solution)
        # Tell the agents that we are done
        for agent in self.solution:
            agent.current_conflict = None
            agent.resolved_conflict(self)
            agent.plan(start_time, max_time)


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
        pprint(conflict_objs)
        # Add conflicts to agents
        for agent in agents:
            agent.conflicts.clear()
        for conflict in conflict_objs.values():
            for agent in conflict.agents:
                agent.conflicts.add(conflict)

        # Get the agents to resove the conflicts
        for agent in agents:
            try:
                conflict = agent.conflicts[0]
            except IndexError:
                continue  # Agent has no conflicts
            conflict.resolve(agents, start_time, max_time)

        # Update the list of conflicts
        paths = [agent.path for agent in agents]
        conflicts = util.paths_conflict(paths)
        if count > 3:
            print('Quiting early')
            break
        print() # Just a new line to break up iterations

    # Final visualisation
    if visualize:
        print('Exporting final conflicts')
        im = vis.draw_paths_with_conflicts(paths, conflicts)
        im.save(f'conflict_{count:05}.png')
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
