# -*- coding: utf-8 -*-
import enum
import heapq
from PIL import ImageDraw
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
        return self.action == other.action and self.pos == other.pos

    def __hash__(self):
        return hash((self.pos, self.action))

    def new_pos(self):
        if self.action == None:
            return self.pos
        return (self.pos[0] + self.action.value[0],
                self.pos[1] + self.action.value[1])


def main(agents):
    w = world.World(16, 16, 0.2)
    w_im = w.as_image()
    w_im.save('od.png')
    starts = tuple(random.choice(w.passable) for i in range(agents))
    goals  = tuple(random.choice(w.passable) for i in range(agents))
    print('starts:', starts)
    print('goals: ', goals)

    start_time = timeit.default_timer()
    paths = od(agents, w, starts, goals)
    end_time = timeit.default_timer()
    print('paths:', paths)
    print(f'elapsed time: {(end_time - start_time) * 1000:5.3f}ms')

    paths_im = draw_paths(w_im.copy(), paths)
    paths_im.save('paths.png')

    animate_paths(w_im.copy(), paths)

def heur_dist(rra_heur, goals, positions):
    cost = 0
    for i in range(len(rra_heur)):
        cost += rra_heur[goals[i]].dist(positions[i])
    return cost

def od(agents, w, starts, goals):
    start_state = tuple(State(s) for s in starts)
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
                return reverse_paths(state, came_from)
            # If we haven't then add the standard state to the closed set
            closed_set.add(current)

        # Add all possible actions
        for action in Actions:
            new_state = tuple(State(s.pos, s.action) for s in current)
            new_state[agent].action = action
            # Check if the action is valid
            if action != Actions.wait and \
                new_state[agent].new_pos() not in w.neighbours(new_state[agent].pos):
                continue
            if not valid_action(new_state, agent):
                continue

            count += 1
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
                    simple_state = tuple(s.new_pos() for s in new_state)
                    h = heur_dist(heur, goals, simple_state)
                    heapq.heappush(open_set, (score + h, count, 0, new_state))
                    came_from[simple_state] = tuple(s.pos for s in current)
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

def reverse_paths(state, came_from):
    path = [state]
    while state in came_from:
        state = came_from[state]
        path.append(state)
    path = tuple(zip(*reversed(path)))
    return path

def valid_action(state, agent):
    pos = state[agent].pos
    new_pos = state[agent].new_pos()
    for i in range(agent):
        # Check if the agents are near each other
        if abs(state[i].pos[0] - state[agent].pos[0]) > 2 or \
                abs(state[i].pos[1] - state[agent].pos[1]) > 2:
            continue
        other_pos = state[i].pos
        other_new_pos = state[i].new_pos()
        # Same location
        if other_new_pos == new_pos:
            return False
        # Swapping position
        if other_pos == new_pos and pos == other_new_pos:
            return False
        # Crossing edge
        if (other_pos[0] == pos[0] and new_pos[0] == other_new_pos[0]
            and other_pos[1] == new_pos[1] and pos[1] == other_new_pos[1]):
            return False
        if (other_pos[1] == pos[1] and new_pos[1] == other_new_pos[1]
            and other_pos[0] == new_pos[0] and pos[0] == other_new_pos[0]):
            return False
    return True

def draw_paths(image, paths, scale=10):
    draw = ImageDraw.Draw(image)

    # Draw start and end points
    for path in paths:
        draw.ellipse((path[-1][0]*scale+1, path[-1][1]*scale+1,
            (path[-1][0]+1)*scale-1, (path[-1][1]+1)*scale-1),
            outline=(255, 0, 0))
        draw.ellipse((path[0][0]*scale+1, path[0][1]*scale+1,
            (path[0][0]+1)*scale-1, (path[0][1]+1)*scale-1),
            outline=(0, 255, 0))

        length = len(path)
        for i in range(length - 1):
            color = (int(255*i/length), int(255*(length-i)/length), 0)
            draw.line(((path[i][0]+.5)*scale, (path[i][1]+.5)*scale,
                (path[i+1][0]+.5)*scale, (path[i+1][1]+.5)*scale), fill=color)
    return image

def animate_paths(image, paths, scale=10):
    frame = 0
    for i in range(10):
        im = draw_paths(image.copy(), paths, scale)
        im.save(f'od_path{frame:05}.png')
        frame += 1

    for step in range(len(paths[0])):
        im = draw_paths(image.copy(), (p[step:] for p in paths))
        im.save(f'od_path{frame:05}.png')
        frame += 1

    im = image.copy()
    draw = ImageDraw.Draw(im)
    for path in paths:
        draw.ellipse((path[-1][0]*scale+1, path[-1][1]*scale+1,
            (path[-1][0]+1)*scale-1, (path[-1][1]+1)*scale-1),
            outline=(0, 255, 0))
    for i in range(10):
        im.save(f'od_path{frame:05}.png')
        frame += 1

if __name__ == '__main__':
    try:
        agents = int(sys.argv[1])
    except IndexError:
        agents = 2
    main(agents)
