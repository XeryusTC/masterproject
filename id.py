# -*- coding: utf-8 -*-
import heapq
import random
import sys
import timeit

from rra_star import RRAstar
import od
import world

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
    w = world.World(16, 16, 0.2)
    starts = tuple(random.choice(w.passable) for i in range(agents))
    goals  = tuple(random.choice(w.passable) for i in range(agents))
    print('starts:', starts)
    print('goals: ', goals)

    paths = odid(agents, w, starts, goals)

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
        # Merge groups
        group1, group2 = conflict
        groups[group1].merge(groups[group2])
        del groups[group2]
        end_time = timeit.default_timer()
        print('After merge:', tuple(groups[i].size for i in range(len(groups))))
        print(f'elapsed time: {(end_time - start_time) * 1000:5.3f}ms')
        # Calculate new paths for the merged groups
        groups[group1].paths = group_od(w, groups[group1])
        conflict = group_conflicts(groups)
    end_time = timeit.default_timer()
    print(f'elapsed time: {(end_time - start_time) * 1000:5.3f}ms')

def group_od(w, group):
    start_state = tuple(od.State(s) for s in group.starts)
    count = 0
    closed_set = set()
    open_set = []
    came_from = {}
    g = {start_state: 0}
    heapq.heappush(open_set, (0, count, 0, start_state))
    agents = len(group.starts)

    # Display predicted cost
    pred_cost = od.heur_dist(group.heur, group.goals, group.starts)
    print('predicted cost:', pred_cost)

    while open_set:
        f, _, agent, current = heapq.heappop(open_set)

        # Check if we've reached the goal
        if agent == 0:
            state = tuple(s.pos for s in current)
            if state == tuple(group.goals):
                print('open set size:  ', len(open_set))
                print('closed set size:', len(closed_set))
                print('final cost:     ', f)
                return od.reverse_paths(state, came_from)
            # Add the standard state to the closed set
            closed_set.add(current)

        # Add all possible actions
        for action in od.Actions:
            new_state = tuple(od.State(s.pos, s.action) for s in current)
            new_state[agent].action = action
            # Check if the action is valid
            if action != od.Actions.wait and \
                new_state[agent].new_pos() not in w.neighbours(new_state[agent].pos):
                    continue
            if not od.valid_action(new_state, agent):
                continue

            count += 1
            # If the agent is in its goal and the action is wait then there
            # should be no cost
            if action == od.Actions.wait and \
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
                    heapq.heappush(open_set, (score + h, count, 0, new_state))
                    came_from[simple_state] = tuple(s.pos for s in current)
            # Create intermediate state
            else:
                # if we found a longer path, ignore it
                if new_state in g and score >= g[new_state]:
                    continue
                h = 0
                for i in range(agent + 1):
                    h += group.heur[group.goals[i]].dist(new_state[i].new_pos())
                for i in range(agent + 1, agents):
                    h += group.heur[group.goals[i]].dist(new_state[i].pos)
                heapq.heappush(open_set,
                    (score + h, count, agent + 1, new_state))
            g[new_state] = score
    raise Exception('No paths found')

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

    for i in range(len(path1)-1):
        old_pos1 = path1[i]
        old_pos2 = path2[i]
        new_pos1 = path1[i+1]
        new_pos2 = path2[i+1]

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
    if len(path1) == 0: # When a path has 0 length i doesn't exist
        i = 0
    for j in range(i, len(path2)):
        if path2[j] == path1[i]:
            return True
    return False

if __name__ == '__main__':
    try:
        agents = int(sys.argv[1])
    except IndexError:
        agents = 2
    main(agents)
