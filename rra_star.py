# -*- coding: utf-8 -*-
import heapq
import random
import timeit

import world

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
        return None

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
                        (cost + self._h(neighbour), neighbour))
                elif cost > self.g[neighbour]:
                    continue # This path is longer
                self.g[neighbour] = cost
        return False

    def _h(self, pos):
        return max(abs(pos[0] - self.goal[0]), abs(pos[1] - self.goal[1]))


if __name__ == '__main__':
    tests = 1000
    w = world.World(32, 32, 0.2)
    origins = tuple(random.choice(w.passable) for i in range(tests))
    goals = tuple(random.choice(w.passable) for i in range(tests))

    start = timeit.default_timer()
    for i in range(tests):
        heuristic = RRAstar(w, origins[i], goals[i])
    end = timeit.default_timer()
    print('elapsed time:', end - start)
    print('mean time:', (end - start) / tests)
