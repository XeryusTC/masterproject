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

Weights = namedtuple('Weights', ['path_len',
                                 'conflict_count',
                                 'partial_solved',
                                ])

class TimePlace(namedtuple('TimePlace', ['time', 'place'])):
    def __eq__(self, other):
        return self.time == other.time and self.place == other.place

    def __hash__(self):
        return hash((self.time, self.place))


class ConflictNotSolved(Exception):
    pass


class ConflictPartiallySolved(Exception):
    pass


class Agent:
    def __init__(self, world, start, goal,
                 weights=Weights(1, 3, 3), caching=True):
        self.world = world
        self.start = start
        self.goal = goal
        self.h = RRAstar(world, start, goal)
        self.path = []
        self.path_cache = {}
        self.conflicts = SortedListWithKey(key=lambda conflict: conflict.time)
        self.resolved_conflicts = []
        self.current_conflict = None
        self.higher_prio = frozenset()
        self.weights = weights
        self.caching = caching

    def plan(self, start_time, max_time):
        #print(f'Planning for agent {self}')
        self.old_path = self.path
        self.construct_higher_prio()
        # Check if there is a path in the cache for this prio set up
        if self.caching and self.higher_prio in self.path_cache:
            # Check if the cached path conflicts with those of higher prio
            paths = [agent.path for agent in self.higher_prio]
            conflicts = util.paths_conflict(paths)
            if not conflicts:
                #print('Using cached path')
                self.path = self.path_cache[self.higher_prio]
                return
        self.path = self._astar(start_time, max_time)
        # Update the cache
        self.path_cache[self.higher_prio] = self.path

    def construct_higher_prio(self):
        prio = []
        # Construct priorities from the conflict solutions
        for conflict in self.resolved_conflicts:
            for i in range(conflict.solution['level']):
                if conflict.solution[i] == self:
                    continue
                prio.append(conflict.solution[i])
        # Update with the current proposed solution
        if self.current_conflict != None:
            for i in range(self.current_conflict.proposal['level']):
                if self.current_conflict.proposal[i] == self:
                    continue
                prio.append(self.current_conflict.proposal[i])
        self.higher_prio = frozenset(prio)
        #print(f'  Agent {self} final prio: {self.higher_prio}')

    def propose(self, conflict):
        # If there are no proposals yet, propose to go first
        if len(conflict.proposals) == 0:
            return {'score': None, 'level': 1, 0: self, 'children': []}

        #print('Making complicated proposal')
        # Take the highest rated proposal without any children
        for proposal in conflict.leaf_proposals:
            if len(conflict.agents) == proposal['level']:
                continue  # Skip if all agents have a priority assigned
            # Skip this proposal if agent already has a priority assigned
            skip = False
            for i in range(proposal['level']):
                if proposal[i] == self:
                    skip = True
                    break
            if skip:
                continue

            # Propose to go next
            new_proposal = {
                'score': None,
                'level': proposal['level'] + 1,
                proposal['level']: self,
                'children': []
            }
            for i in range(proposal['level']):
                new_proposal[i] = proposal[i]

            #print(f'Complicated proposal {new_proposal}')
            proposal['children'].append(new_proposal)
            return new_proposal
        return None

    def resolved_conflict(self, conflict):
        self.resolved_conflicts.append(conflict)

    def evaluate(self, conflicts):
        # Current conflict solved
        if self.current_conflict in conflicts.values():
            #print('Conflict not solved')
            raise ConflictNotSolved()
        score = 0
        # Change in path length
        score += (len(self.old_path) - len(self.path)) * self.weights.path_len
        # Change in conflicts
        filtered = list(filter(lambda c: self in c.agents, conflicts.values()))
        #print(f'{self} {len(self.conflicts)} {len(filtered)}')
        score += (len(self.conflicts) - len(filtered)) * \
                 self.weights.conflict_count

        # In a multi agent conflict, check if not conflicting with other
        # agents any more
        partially_solved = False
        if len(self.current_conflict.agents) > 2:
            for timeplace, conflict in conflicts.items():
                intersection = [agent for agent in conflict.agents
                                      if agent in self.current_conflict.agents]
                if len(intersection) >= 2 and self in intersection:
                    #print('  Conflict only partially solved!')
                    partially_solved = True
                    score -= self.weights.partial_solved

        #print(f'Agent score {self}: {score}')
        if partially_solved:
            raise ConflictPartiallySolved(score)
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
        self.proposals = []
        self.leaf_proposals = []

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

        #print(f'Resolving conflict {self}')

        best_score = -float('inf')
        partially_solved = False
        while best_score == -float('inf') or partially_solved:
            time = timeit.default_timer()
            if start_time != None and (time - start_time) > max_time:
                raise TimeExceeded()

            partially_solved = True
            proposals = tuple(filter(lambda p: p != None,
                               (agent.propose(self) for agent in self.agents)))
            self.proposals += proposals

            # If no proposals have been made then go with the best one so far
            if len(proposals) == 0:
                self.solution = max(self.proposals, key=lambda p: p['score'])
                if self.solution['score'] == -float('inf'):
                    raise ConflictNotSolved()
                break

            if len(proposals) == 1:
                self.solution = proposals[0]
                break

            # Evaluate the proposals
            for proposal in proposals:
                #print('Evaluation proposal', proposal)
                self.proposal = proposal
                proposal['score'] = 0
                # Plan new paths
                for i in range(proposal['level']):
                    proposal[0].plan(start_time, max_time)
                # Replanning for all agents shouldnt be too bad because
                # of caching
                for agent in self.agents:
                    agent.plan(start_time, max_time)
                # Evaluate new paths
                try:
                    for agent in self.agents:
                        paths = tuple(a.path for a in agents)
                        conflicts = util.paths_conflict(paths)
                        conflicts = convert_conflicts(agents, conflicts)
                        proposal['score'] += agent.evaluate(conflicts)
                except ConflictNotSolved:
                    proposal['score'] = -float('inf')
                    continue
                except ConflictPartiallySolved as e:
                    proposal['score'] += e.args[0]
                else:
                    partially_solved = False
                #print(f"Proposal score {proposal['score']}")

            # Pick the proposal with the highest sum of votes
            #pprint(self.proposals)
            self.solution = max(self.proposals, key=lambda p: p['score'])
            best_score = max(p['score'] for p in self.proposals)
            #print(f'Best score: {best_score}')

            self.leaf_proposals = sorted((p for p in self.proposals
                                            if not p['children']),
                                         key=lambda p: p['score'])

        self.proposal = None
        #print('SOLUTION', self.solution)
        # Tell the agents that we are done
        for agent in self.agents:
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
    init_conflicts = len(convert_conflicts(agents, conflicts))
    while conflicts:
        time = timeit.default_timer()
        if start_time != None and (time - start_time) > max_time:
            raise TimeExceeded()
        if visualize:
            print('Exporting conflicts')
            im = vis.draw_paths_with_conflicts(paths, conflicts)
            im.save(f'conflict_{count:05}.png')
            count += 1
        #print(f'Conflicts found: {len(conflicts)}')
        #pprint(conflicts)
        conflict_objs = convert_conflicts(agents, conflicts)
        #pprint(conflict_objs)
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
        #print() # Just a new line to break up iterations

    # Final visualisation
    if visualize:
        print('Exporting final conflicts')
        im = vis.draw_paths_with_conflicts(paths, conflicts)
        im.save(f'conflict_{count:05}.png')
    # Find number of conflicts solved
    conflicts = set()
    for agent in agents:
        conflicts.update(agent.resolved_conflicts)
    sizes = (len(c.agents) for c in conflicts)
    return {'paths': paths,
            'initial': init_conflicts,
            'solved': len(conflicts),
            'sizes': sizes,
        }

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
        else:
            pass
            #print('Conflict object found', time_place)
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
