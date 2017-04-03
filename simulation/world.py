# -*- coding: utf-8 -*-
from enum import Enum
from PIL import Image, ImageDraw
import random

class World:
    class WorldData(Enum):
        PASSABLE = 0
        OBSTACLE = 1


    def __init__(self, width, height, p_obst):
        self.width = width
        self.height = height
        self.world = {}

        for x in range(self.width):
            for y in range(self.height):
                if random.random() <= p_obst:
                    self.world[x, y] = World.WorldData.OBSTACLE
                else:
                    self.world[x, y] = World.WorldData.PASSABLE

    @property
    def passable(self):
        return [pos for pos in self.world
            if self.world[pos] == World.WorldData.PASSABLE]

    def neighbours(self, pos):
        NEIGHBOURS = ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1),
            (0, 1), (1, 1))
        neighbours = [(pos[0] + n[0], pos[1] + n[1]) for n in NEIGHBOURS]
        neighbours = [n for n in neighbours
            if n in self.world and self.world[n] == World.WorldData.PASSABLE]
        return neighbours


if __name__ == '__main__':
    w = World(32, 32, 0.2)
    im = w.as_image()
    im.save('world.png')
