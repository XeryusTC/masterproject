# -*- coding: utf-8 -*-
import random
import heapq
from PIL import ImageDraw

import world

neighbours = ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1),
    (-1, 1))

def h(pos, goal):
    return min(abs(pos[0] - goal[0]), abs(pos[1] - goal[1]))

def astar(world, start, goal):
    closed_set = set()
    open_set = []
    came_from = {}
    g = {start: 0}
    heapq.heappush(open_set, (0, start))

    while open_set:
        cur = heapq.heappop(open_set)[1]
        if cur == goal:
            return reverse_path(goal, came_from)

        closed_set.add(cur)
        for neighbour in world.neighbours(cur):
            # Skip neighbours in closed list
            if neighbour in closed_set:
                continue

            score = g[cur] + 1
            # We found a longer path, ignore it
            if neighbour in g and score >= g[neighbour]:
                continue
            came_from[neighbour] = cur
            g[neighbour] = score
            heapq.heappush(open_set, (score + h(neighbour, goal), neighbour))
    return None

def reverse_path(pos, came_from):
    path = [pos]
    while pos in came_from:
        pos = came_from[pos]
        path.append(pos)
    path.reverse()
    return path

def draw_path(im, start, goal, path, scale=10):
    draw = ImageDraw.Draw(im)

    draw.ellipse((start[0]*scale+1, start[1]*scale+1,
        (start[0]+1)*scale-1, (start[1]+1)*scale-1), outline=(0, 255, 0))
    draw.ellipse((goal[0]*scale+1, goal[1]*scale+1, (goal[0]+1)*scale-1,
        (goal[1]+1)*scale-1), outline=(255, 0, 0))

    length = len(path)
    for i in range(length - 1):
        color = (int(255*i/length), int(255*(length-i)/length), 0)
        draw.line(((path[i][0]+.5)*scale, (path[i][1]+.5)*scale,
            (path[i+1][0]+.5)*scale, (path[i+1][1]+.5)*scale), fill=color)

    return im

if __name__ == '__main__':
    w = world.World(32, 32, 0.2)
    start = random.choice(w.passable)
    goal = random.choice(w.passable)
    print(start, goal)

    path = astar(w, start, goal)

    im = w.as_image()
    im = draw_path(im, start, goal, path)
    im.save('astar.png')
