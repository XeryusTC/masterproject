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

    def as_image(self, scale=10):
        im = Image.new('RGB', (self.width*scale, self.height*scale), 'white')
        draw = ImageDraw.Draw(im)
        for x, y in self.world:
            if self.world[x, y] == World.WorldData.OBSTACLE:
                draw.polygon(((x*scale, y*scale), ((x+1)*scale, y*scale),
                    ((x+1)*scale, (y+1)*scale), (x*scale, (y+1)*scale)),
                    fill="black")
        return im


if __name__ == '__main__':
    w = World(32, 32, 0.2)
    im = w.as_image()
    im.save('world.png')
