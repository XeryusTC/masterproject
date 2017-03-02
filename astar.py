# -*- coding: utf-8 -*-
import random
import heapq
from math import sqrt
from PIL import ImageDraw

import world

neighbours = ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1),
    (-1, 1))

def h(pos, goal):
    return max(abs(pos[0] - goal[0]), abs(pos[1] - goal[1]))

def cost(a, b):
    return sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)

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

            score = g[cur] + cost(cur, neighbour)
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

def astar_animation(w, start, goal):
    closed_set = set()
    open_set = []
    came_from = {}
    g = {start: 0}
    heapq.heappush(open_set, (0, start))
    im = w.as_image()
    im.save('astar00000.png')
    i = 0

    while open_set:
        i = i + 1
        cur = heapq.heappop(open_set)[1]
        if cur == goal:
            path = reverse_path(goal, came_from)
            frame = draw_path(im.copy(), start, goal, path)
            frame.save('astar%05d.png' % i)
            return path

        closed_set.add(cur)
        for neighbour in w.neighbours(cur):
            if neighbour in closed_set:
                continue

            score = g[cur] + cost(cur, neighbour)
            if neighbour in g and score >= g[neighbour]:
                continue
            came_from[neighbour] = cur
            g[neighbour] = score
            heapq.heappush(open_set, (score + h(neighbour, goal), neighbour))
        path = reverse_path(cur, came_from)
        frame = draw_path(im.copy(), start, cur, path)
        frame.save('astar%05d.png' % i)
    return None

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

def animate_path(image, path, scale=10):
    # Draw initial
    for i in range(10):
        im = draw_path(image.copy(), path[0], path[-1], path, scale)
        im.save('path%05d.png' % i)

    # Draw the path
    for step in range(len(path)):
        im = draw_path(image.copy(), path[step], path[-1], path[step:], scale)
        im.save('path%05d.png' % (step + 10))

    # Draw last step
    im = image.copy()
    draw = ImageDraw.Draw(im)
    goal = path[-1]
    draw.ellipse((goal[0]*scale+1, goal[1]*scale+1, (goal[0]+1)*scale-1,
        (goal[1]+1)*scale-1), outline=(0, 255, 0))
    for i in range(10):
        im.save('path%05d.png' % int(step + i + 11))


if __name__ == '__main__':
    w = world.World(32, 32, 0.2)
    start = random.choice(w.passable)
    goal = random.choice(w.passable)
    print(start, goal)

    path = astar(w, start, goal)

    im = w.as_image()
    im_path = draw_path(im.copy(), start, goal, path)
    im_path.save('astar.png')

    path = astar_animation(w, start, goal)
    animate_path(im.copy(), path)
