# -*- coding: utf-8 -*-
import imageio
import numpy as np
import random
from PIL import Image, ImageDraw, ImageFont

class Visualisation():
    def __init__(self, world, agents, scale=10):
        self.scale = scale
        self.world = world
        self.colors = tuple((random.randrange(192), random.randrange(192),
            random.randrange(192)) for i in range(agents))

    @property
    def world(self):
        return self._world

    @world.setter
    def world(self, new_value):
        self._world = new_value
        im_width  = self.world.width * self.scale
        im_height = self.world.height * self.scale
        self._world_im = Image.new('RGB', (im_width, im_height), 'white')
        draw = ImageDraw.Draw(self._world_im)
        for x, y in self.world.world:
            if self.world.world[x, y] == self.world.WorldData.OBSTACLE:
                draw.polygon(((x*self.scale, y*self.scale),
                              ((x+1)*self.scale, y*self.scale),
                              ((x+1)*self.scale, (y+1)*self.scale),
                              (x*self.scale, (y+1)*self.scale)),
                              fill="black")

    def draw_paths(self, filename, paths, frames_per_step=None):
        if frames_per_step is None:
            frames_per_step = self.scale
        step_size = 1 / float(frames_per_step)
        imseq = []
        max_length = max(len(path) for path in paths)

        # Create base image (it contains end positions)
        end_im = self._world_im.copy()
        draw = ImageDraw.Draw(end_im)
        for i in range(len(paths)):
            pos = paths[i][-1]
            ellipse = (pos[0] * self.scale + 1,
                       pos[1] * self.scale + 1,
                       (pos[0] + 1) * self.scale - 1,
                       (pos[1] + 1) * self.scale - 1)
            draw.ellipse(ellipse, outline=self.colors[i])

        for step in range(max_length):
            for substep in range(frames_per_step):
                frame = end_im.copy()
                draw = ImageDraw.Draw(frame)
                for i in range(len(paths)):
                    if step >= len(paths[i]) - 1:
                        cur_pos = next_pos = paths[i][-1]
                    else:
                        cur_pos = paths[i][step]
                        next_pos = paths[i][step+1]
                    # Interpolate the position
                    inter = step_size * substep
                    pos = (cur_pos[0] + (next_pos[0] - cur_pos[0]) * inter,
                           cur_pos[1] + (next_pos[1] - cur_pos[1]) * inter)
                    # Draw agent
                    ellipse = (pos[0] * self.scale + .2 * self.scale,
                               pos[1] * self.scale + .2 * self.scale,
                               (pos[0] + 1) * self.scale - .2 * self.scale,
                               (pos[1] + 1) * self.scale - .2 * self.scale)
                    draw.ellipse(ellipse, self.colors[i], self.colors[i])
                    # Draw the agent number
                    draw.text(((pos[0] + .25) * self.scale,
                               (pos[1] + .25) * self.scale),
                              str(i), 'white', align='center')
                    # Draw remaining path
                    offset = .5 * self.scale
                    path = [(pos[0] * self.scale + offset,
                        pos[1] * self.scale + offset)]
                    path += [(pos[0] * self.scale + offset,
                            pos[1] * self.scale + offset) for
                        pos in paths[i][step+1:]]
                    draw.line(path, self.colors[i])

                # Add the frame to the final animation
                imseq.append(np.asarray(frame))
        # Output the animation
        imageio.mimwrite(filename, imseq, fps=24)
        return imseq

    def draw_paths_with_conflicts(self, paths, conflicts):
        max_length = max(len(path) for path in paths)

        # Start by getting world image
        im = self._world_im.copy()
        draw = ImageDraw.Draw(im)

        # Get number of conflicts per square
        conflict_positions = {}
        for conflict in conflicts:
            try:
                pos = paths[conflict['path1']][conflict['time']]
            except IndexError:
                pos = paths[conflict['path2']][conflict['time']]
            try:
                conflict_positions[pos] += 1
            except KeyError:
                conflict_positions[pos] = 1
        max_conflicts = max(conflict_positions.values(), default=1)
        weight = int(255 / max_conflicts)
        # Draw conflicts
        for pos, num in conflict_positions.items():
            draw.rectangle(((pos[0] + .1) * self.scale,
                            (pos[1] + .1)* self.scale,
                            (pos[0] + .9) * self.scale,
                            (pos[1] + .9) * self.scale),
                            fill=((weight * num),0,0))

        # Draw agents and paths
        for i in range(len(paths)):
            # Goal
            pos = paths[i][-1]
            ellipse = ((pos[0] + .2) * self.scale, (pos[1] + .2) * self.scale,
                       (pos[0] + .8) * self.scale, (pos[1] + .8) * self.scale)
            draw.ellipse(ellipse, outline=self.colors[i])
            # Path
            path = [((pos[0] + .5) * self.scale, (pos[1] + .5) * self.scale)
                    for pos in paths[i]]
            draw.line(path, self.colors[i])
            # Agent
            pos = paths[i][0]
            ellipse = ((pos[0] + .2) * self.scale, (pos[1] + .2) * self.scale,
                       (pos[0] + .8) * self.scale, (pos[1] + .8) * self.scale)
            draw.ellipse(ellipse, self.colors[i], self.colors[i])
            # Draw agent number
            draw.text(((pos[0] + .25) * self.scale,
                       (pos[1] + .25) * self.scale),
                      str(i), 'white')

        return im
