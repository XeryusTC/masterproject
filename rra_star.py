# -*- coding: utf-8 -*-
import heapq
import random
import timeit

import world

class NoValidPathExists(Exception):
    pass

class RRAstar:
    def __init__(self, world, origin, goal):
        self.world = world
        self.goal = goal
        self.g = {goal: 0}
        self.closed = set()
        self.open = []
        heapq.heappush(self.open, (0, goal))
        self._resume(origin)

    def dist(self, node):
        if node in self.closed:
            return self.g[node]
        if self._resume(node):
            return self.g[node]
        raise NoValidPathExists()

    def _resume(self, node):
        while self.open:
            # If the top of the queue is the node we can stop, do this
            # without removing it so we continue here next time
            if self.open[0][1] == node:
                return True

            current = heapq.heappop(self.open)[1]
            self.closed.add(current)
            for neighbour in self.world.neighbours(current):
                if neighbour in self.closed:
                    continue
                cost = self.g[current] + 1
                if neighbour not in self.g:
                    heapq.heappush(self.open,
                        (cost + self._h(neighbour, node), neighbour))
                elif cost > self.g[neighbour]:
                    continue # This path is longer
                self.g[neighbour] = cost
        return False

    def _h(self, cur, node):
        return max(abs(cur[0] - node[0]), abs(cur[1] - node[1]))


if __name__ == '__main__':
    tests = 1000
    w = world.World(32, 32, 0.2)
    origins = tuple(random.choice(w.passable) for i in range(tests))
    goals = tuple(random.choice(w.passable) for i in range(tests))

    print('Starting')
    start = timeit.default_timer()
    for i in range(tests):
        heuristic = RRAstar(w, origins[i], goals[i])
    end = timeit.default_timer()
    print('elapsed time:', (end - start) * 1000)
    print('mean time:', (end - start) / tests * 1000)

    # Export heuristic costs
    from PIL import Image, ImageDraw, ImageFont
    scale = 20
    im = w.as_image(scale=scale)
    draw = ImageDraw.Draw(im)
    font = ImageFont.load_default()
    draw.rectangle((goals[-1][0]*scale, goals[-1][1]*scale,
        (goals[-1][0]+1)*scale, (goals[-1][1]+1)*scale), fill='green')
    draw.rectangle((origins[-1][0]*scale, origins[-1][1]*scale,
        (origins[-1][0]+1)*scale, (origins[-1][1]+1)*scale), fill='red')
    for pos in heuristic.closed:
        cost = heuristic.g[pos]
        #cost = heuristic._h(pos)
        draw.text((pos[0]*scale+2, pos[1]*scale+2), str(cost), "black", font)
    im.save('rra_star.png')
