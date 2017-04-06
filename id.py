# -*- coding: utf-8 -*-
import heapq
import imageio
import random
import sys
import timeit

from rra_star import RRAstar
import od
from simulation import util, visualisation

class NoPathsFoundException(Exception):
    pass


class Group:
    def __init__(self, starts, goals, w):
        self.starts = starts
        self.goals = goals
        self.paths = []
        self.heur = {}
        for i in range(len(starts)):
            self.heur[goals[i]] = RRAstar(w, starts[i], goals[i])

    @property
    def size(self):
        return len(self.starts)

    def merge(self, other):
        self.starts += other.starts
        self.goals += other.goals
        self.paths += other.paths
        self.heur.update(other.heur)

    def __str__(self):
        return f'{self.starts}, {self.goals}, {self.paths}, {self.heur}'


def main(agents):
    world, starts, goals = util.generate_problem(agents, 16, 16, 0.2)
    print('starts:', starts)
    print('goals: ', goals)

    paths = odid2(agents, world, starts, goals)

    print('Writing visualisations')
    vis = visualisation.Visualisation(world, agents, scale=20)
    frames = vis.draw_paths('odid.mkv', paths)

def odid(agents, w, starts, goals):
    conflict = True
    groups = []
    for i in range(agents):
        groups.append(Group([starts[i]], [goals[i]], w))

    start_time = timeit.default_timer()
    # Initial planning
    for i in range(agents):
        groups[i].paths = group_od(w, groups[i])

    # Merge groups and solve conflicts
    conflict = group_conflicts(groups)
    while conflict:
        group1, group2 = conflict
        # Try to replan the conflicting groups
        print('Replanning for group', group2)
        try:
            groups[group2].paths = group_od(w, groups[group2],
                groups[group1].paths)
            conflict = group_conflicts(groups)
        except NoPathsFoundException:
            print('No path found')
            pass # Do merging if no valid path is found
        else:
            if conflict and group2 not in conflict: # Successfully replanned
                continue
            elif not conflict:
                break

        # Merge groups
        print('Merging groups', group1, 'and', group2)
        groups[group1].merge(groups[group2])
        del groups[group2]
        end_time = timeit.default_timer()
        print(f'elapsed time: {(end_time - start_time) * 1000:5.3f}ms')
        print('After merge:', tuple(groups[i].size
            for i in range(len(groups))))
        # Calculate new paths for the merged groups
        groups[group1].paths = group_od(w, groups[group1])
        conflict = group_conflicts(groups)
    end_time = timeit.default_timer()
    print(f'elapsed time: {(end_time - start_time) * 1000:5.3f}ms')

    # Flatten paths
    paths = []
    for group in groups:
        paths += group.paths
    return paths

def group_od(w, group, conflicting_paths=None, max_length=None):
    start_state = tuple(od.State(s) for s in group.starts)
    count = 0
    closed_set = set()
    open_set = []
    came_from = {}
    g = {start_state: 0}
    heapq.heappush(open_set, (0, count, 0, 0, start_state))
    agents = len(group.starts)

    # Display predicted cost
    pred_cost = od.heur_dist(group.heur, group.goals, group.starts)

    while open_set:
        f, _, agent, time_step, current = heapq.heappop(open_set)
        if max_length and time_step > max_length:
            continue

        # Check if we've reached the goal
        if agent == 0:
            state = tuple(s.pos for s in current)
            if state == tuple(group.goals):
                return reverse_paths(state + (time_step,), came_from)
            # Add the standard state to the closed set
            closed_set.add(current)

        # Add all possible actions
        successors = od.next_states(current, w, agent)
        if conflicting_paths is not None:
            successors = filter_successors(successors, agent, time_step,
                conflicting_paths)
        for new_state in successors:
            count += 1
            # If the agent is in its goal and the action is wait then there
            # should be no cost
            if new_state[agent].action == od.Actions.wait and \
                new_state[agent].pos == group.goals[agent]:
                score = g[current]
            else:
                score = g[current] + 1

            # Create a standard state if necessary
            if agent == agents - 1:
                new_state = tuple(od.State(s.new_pos()) for s in new_state)
                # Don't add it if it already exists
                if new_state in g and score >= g[new_state]:
                    continue
                # Check if the standard state is already in the open set
                if new_state not in g:
                    # No duplicate found, add this one
                    simple_state = tuple(s.new_pos() for s in new_state)
                    h = od.heur_dist(group.heur, group.goals, simple_state)
                    heapq.heappush(open_set,
                        (score + h, count, 0, time_step+1, new_state))
                    came_from[simple_state + (time_step + 1,)] = tuple(s.pos
                        for s in current) + (time_step,)
            # Create intermediate state
            else:
                # if we found a longer path, ignore it
                if new_state in g and score >= g[new_state]:
                    continue
                h = 0
                for i in range(agent + 1):
                    h += group.heur[group.goals[i]].dist(
                        new_state[i].new_pos())
                for i in range(agent + 1, agents):
                    h += group.heur[group.goals[i]].dist(new_state[i].pos)
                heapq.heappush(open_set,
                    (score + h, count, agent + 1, time_step, new_state))
            g[new_state] = score
    raise NoPathsFoundException()

def filter_successors(successors, agent, time_step, other_paths):
    new_succ = []
    for state in successors:
        for path in other_paths:
            if len(path) <= time_step:
                new_succ.append(state)
            elif not path_conflicts(path[time_step:],
                    (state[agent].pos, state[agent].new_pos())):
                new_succ.append(state)
    return new_succ

def reverse_paths(state, came_from):
    path = [(state[0],)]
    while state in came_from:
        state = came_from[state]
        path.append((state[0],))
    path = tuple(zip(*reversed(path)))
    return path

def group_conflicts(groups):
    for group1 in range(len(groups)):
        for group2 in range(group1+1, len(groups)):
            for i in range(groups[group1].size):
                for j in range(groups[group2].size):
                    conflict = path_conflicts(groups[group1].paths[i],
                        groups[group2].paths[j])
                    if conflict:
                        return group1, group2
    return False

def path_conflicts(path1, path2):
    if len(path1) > len(path2):
        path1, path2 = path2, path1

    for i in range(len(path1)):
        old_pos1 = path1[i]
        old_pos2 = path2[i]
        new_pos1 = path1[i] if i == len(path1) - 1 else path1[i+1]
        new_pos2 = path2[i] if i == len(path2) - 1 else path2[i+1]

        if abs(old_pos1[0] - old_pos2[0]) > 2 or \
           abs(old_pos1[1] - old_pos2[1]) > 2:
            continue
        # Same location
        if new_pos1 == new_pos2:
            return True
        # Swapping positions
        if old_pos1 == new_pos2 and old_pos2 == new_pos1:
            return True
        # Crossing edge
        if (old_pos1[0] == old_pos2[0] and new_pos1[0] == new_pos2[0]
            and old_pos2[1] == new_pos1[1] and old_pos1[1] == new_pos2[1]):
            return True
        if (old_pos2[1] == old_pos1[1] and new_pos1[1] == new_pos2[1]
            and old_pos2[0] == new_pos1[0] and old_pos1[0] == new_pos2[0]):
            return True
    # Check if the longer path goes through the goal of the shorter
    if len(path1) <= 1: # When a path has 0 length i doesn't exist
        i = 0
    for j in range(i, len(path2)):
        if path2[j] == path1[i]:
            return True
    return False

def odid2(agents, w, starts, goals):
    conflicted = []
    old_conflicts = []
    groups = list(Group([starts[i]], [goals[i]], w) for i in range(agents))

    start_time = timeit.default_timer()
    # Initial planning
    for group in groups:
        group.paths = group_od(w, group)

    conflicted = groups_conflict(groups)
    while conflicted:
        print('conflicted groups:', conflicted)
        group1, group2 = random.choice(conflicted)
        print('Found conflict between', group1, 'and', group2)
        if (group1, group2) not in old_conflicts:
            print('Replanning for group', group1)
            # Get maximum length of groups
            max_length = max(len(path)
                for path in groups[group1].paths + groups[group2].paths)
            old_conflicts.append((group1, group2))
            old_paths = groups[group1].paths
            try:
                groups[group1].paths = group_od(w, groups[group1],
                    groups[group2].paths, max_length=max_length)
            except NoPathsFoundException:
                pass
            # See if this solved the problem
            if groups_conflict([groups[group1], groups[group2]]):
                print('Replanning for group', group2)
                groups[group1].paths = old_paths
                try:
                    groups[group2].paths = group_od(w, groups[group2],
                        groups[group1].paths, max_length=max_length)
                except NoPathsFoundException:
                    pass
            conflicted = groups_conflict(groups)

        # Conflict still not resolved, merge groups
        if (group1, group2) in conflicted:
            end_time = timeit.default_timer()
            print(f'elapsed time: {(end_time - start_time) * 1000:5.3f}ms')
            print('Merging groups', group1, 'and', group2)
            groups[group1].merge(groups[group2])
            del groups[group2]
            print('After merge:', tuple(groups[i].size
                for i in range(len(groups))))
            groups[group1].paths = group_od(w, groups[group1])
            # Remove stored conflict
            old_conflicts = [c for c in old_conflicts if c != (group1, group2)]
        conflicted = groups_conflict(groups)

    end_time = timeit.default_timer()
    print(f'elapsed time: {(end_time - start_time) * 1000:5.3f}ms')

    # Flatten paths
    paths = []
    for group in groups:
        paths += group.paths
    return paths

def groups_conflict(groups):
    num_groups = len(groups)
    conflicts = []
    for group1 in range(num_groups):
        for group2 in range(group1+1, num_groups):
            for path1 in groups[group1].paths:
                for path2 in groups[group2].paths:
                    if util.paths_conflict([path1, path2]):
                        conflicts.append((group1, group2))
    return conflicts

if __name__ == '__main__':
    try:
        agents = int(sys.argv[1])
    except IndexError:
        agents = 2
    main(agents)
