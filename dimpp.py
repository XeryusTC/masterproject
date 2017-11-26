# -*- coding: utf-8 -*-
import heapq
import itertools
from pprint import pprint
import sys
import timeit

from simulation import util, visualisation
from rra_star import RRAstar
from id import TimeExceeded
from poc import find_conflicts

class Agent:
    def __init__(self, world, start, goal):
        self.world = world
        self.start = start
        self.goal = goal
        self.h = RRAstar(world, start, goal)
        self.path = []

    def plan(self, global_plan, start_time, max_time):
        self.path = self._astar(global_plan, start_time, max_time)

    def _astar(self, global_plan, start_time, max_time):
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
            for successor in self._successors(cur, time_step, global_plan,
                                              start_time, max_time):
                # Skip successor in closed list
                if successor in closed_set and successor != cur:
                    continue

                score = g[cur] + 1
                # Ignore path if it is a longer variant
                if successor in g and score >= g[successor] \
                        and successor != cur:
                    continue
                came_from[time_step + 1, successor] = (time_step, cur)
                g[successor] = score
                heapq.heappush(open_set,
                               (score + self.h.dist(successor), time_step + 1,
                                successor))
        raise util.NoPathsFoundException()

    def _successors(self, pos, time, global_plan, start_time, max_time):
        successors = [pos] + self.world.neighbours(pos)
        filtered = []
        for successor in successors:
            for other_path in global_plan:
                cur_time = timeit.default_timer()
                if start_time != None and (cur_time - start_time) > max_time:
                    raise TimeExceeded()
                if len(other_path[time:]) >= 2:
                    if util.moves_conflict(other_path[time:time + 2],
                                           (pos, successor)):
                        break
                elif util.moves_conflict((other_path[-1], other_path[-1]),
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


def dimpp(agents, start_time, max_time):
    n = len(agents)

    for a in range(n):
        agents[a].plan([], start_time, max_time)
        global_plan = [agents[a].path]
        try:
            for i in range(1, n):
                cur_time = timeit.default_timer()
                if start_time != None and (cur_time - start_time) > max_time:
                    raise TimeExceeded()
                j = (a + i) % n
                agents[j].plan([], start_time, max_time)
                # Go to next agent if there are no conflicts
                conflicts = util.paths_conflict(global_plan + [agents[j].path])
                if len(conflicts) == 0:
                    global_plan.append(agents[j].path)
                    continue
                # Try to insert a wait in the plan at the first conflict
                time = min(conflicts, key=lambda c: c['time'])['time']
                if time < len(agents[j].path):
                    agents[j].path.insert(time, agents[j].path[time])
                # Check if solved
                conflicts = util.paths_conflict(global_plan + [agents[j].path])
                if len(conflicts) == 0:
                    global_plan.append(agents[j].path)
                    continue
                # If still not solved replan with constraints
                agents[j].plan(global_plan, start_time, max_time)
                conflicts = util.paths_conflict(global_plan + [agents[j].path])
                # If there are still conflicts than finding a solution
                # didn't work
                if len(conflicts) > 0:
                    raise util.NoPathsFoundException()
                global_plan.append(agents[j].path)
        except util.NoPathsFoundException:
            continue
        # If this is reached then we should have a good solution
        conflicts = util.paths_conflict(global_plan)
        assert len(conflicts) == 0
        global_plan = global_plan[n - a:] + global_plan[:n - a]
        assert len(global_plan) == n
        assert global_plan[0][0] == agents[0].start
        return {'paths': global_plan, 'initial': 0, 'solved': 0}
    # If we go through all agents and no plan has been found then we've failed
    raise util.NoPathsFoundException

def main(num_agents):
    world, starts, goals = util.generate_problem(num_agents, 16, 16, 0.2)

    # Create agents
    agents = [Agent(world, starts[i], goals[i]) for i in range(num_agents)]
    start_time = timeit.default_timer()
    paths = dimpp(agents, None, None)
    end_time = timeit.default_timer()
    print(f'elapsed time: {(end_time - start_time) * 1000:5.3f}ms')

    print('Making visualisation')
    vis = visualisation.Visualisation(world, num_agents, scale=20)
    vis.draw_paths('midpp.mkv', paths)

if __name__ == '__main__':
    try:
        agents = int(sys.argv[1])
    except IndexError:
        agents = 2
    main(agents)
