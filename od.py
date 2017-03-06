# -*- coding: utf-8 -*-
import enum
import heapq
import random
import sys
import timeit

import world
from rra_star import RRAstar

class Actions(enum.Enum):
    NW   = (-1, -1)
    N    = ( 0, -1)
    NE   = ( 1, -1)
    W    = (-1,  0)
    wait = ( 0,  0)
    E    = ( 1,  0)
    SW   = (-1,  1)
    S    = ( 0,  1)
    SE   = ( 1,  1)

class State:
    def __init__(self, pos, action=None):
        self.pos = pos
        self.action = action

    def __repr__(self):
        return f"{self.pos}:{self.action}"

    def __eq__(self, other):
        return self.pos == other.pos and self.action == other.action

    def __hash__(self):
        return hash((self.pos, self.action))

    def new_pos(self):
        if self.action == None:
            return self.pos
        return (self.pos[0] + self.action.value[0],
                self.pos[1] + self.action.value[1])


def main(agents):
    w = world.World(16, 16, 0.2)
    w.as_image().save('od.png')
    starts = tuple(random.choice(w.passable) for i in range(agents))
    goals  = tuple(random.choice(w.passable) for i in range(agents))
    print('starts:', starts)
    print('goals: ', goals)

    start_time = timeit.default_timer()
    paths = od(agents, w, starts, goals)
    end_time = timeit.default_timer()
    print('paths:', paths)
    print(f'elapsed time: {(end_time - start_time) * 1000:5.3f}ms')

def heur_dist(rra_heur, goals, positions):
    cost = 0
    for i in range(len(rra_heur)):
        cost += rra_heur[goals[i]].dist(positions[i])
    return cost

def od(agents, w, starts, goals):
    start_state = tuple(State(s) for s in starts)
    print(start_state)
    count = 0
    closed_set = set()
    open_set = []
    came_from = {}
    g = {start_state: 0}
    heapq.heappush(open_set, (0, count, 0, start_state))

    # Set up heuristics
    heur = {}
    for i in range(agents):
        heur[goals[i]] = RRAstar(w, starts[i], goals[i])

    # Display predicted cost
    pred_cost = heur_dist(heur, goals, starts)
    print('predicted cost:', pred_cost)

    while open_set:
        f, _, agent, current = heapq.heappop(open_set)
        #print(f'f: {f:4}, agent: {agent}, current: {current}')

        # Check if we've reached the goal
        if agent == 0:
            state = tuple(s.pos for s in current)
            if state == goals:
                print('open set size:  ', len(open_set))
                print('closed set size:', len(closed_set))
                print('final cost:     ', f)
                return True
            # If we haven't then add the standard state to the closed set
            closed_set.add(current)

        # Add all possible actions
        for action in Actions:
            count += 1
            new_state = tuple(State(s.pos, s.action) for s in current)
            new_state[agent].action = action
            # Check if the action is valid
            if action != Actions.wait and \
                new_state[agent].new_pos() not in w.neighbours(new_state[agent].pos):
                continue

            # If the agent is in its goal position and the action is wait
            # then there should be no cost
            if action == Actions.wait and new_state[agent].pos == goals[agent]:
                score = g[current]
            else:
                score = g[current] + 1

            # Create a standard state if necessary
            if agent == agents - 1:
                new_state = tuple(State(s.new_pos()) for s in new_state)
                # Don't add it if it already exists
                if new_state in g and score >= g[new_state]:
                    continue
                # Check if the standard state is already in the open set
                for _, _, _, candidate in open_set:
                    if candidate == new_state:
                        break
                else:
                    # No duplicate found, add this one
                    h = heur_dist(heur, goals,
                        tuple(s.new_pos() for s in new_state))
                    heapq.heappush(open_set, (score + h, count, 0, new_state))
                    came_from[new_state] = current
            # Create intermediate state
            else:
                # If we found a longer path, ignore it
                if new_state in g and score >= g[new_state]:
                    continue
                h = 0
                for i in range(agent + 1):
                    h += heur[goals[i]].dist(new_state[i].new_pos())
                for i in range(agent + 1, agents):
                    h += heur[goals[i]].dist(new_state[i].pos)
                heapq.heappush(open_set,
                    (score + h, count, agent + 1, new_state))
            g[new_state] = score
    return None


if __name__ == '__main__':
    try:
        agents = int(sys.argv[1])
    except IndexError:
        agents = 2
    main(agents)
