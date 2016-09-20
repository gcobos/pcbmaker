#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
G-Code optimizer

Re-arranges the Gcode to optimize the toolpaths

"""

import re
import math
import StringIO

class GCodeOptimizer(object):

    GCODE_REGEX = r""

    def __init__(self, gcode='', absolute = True, feedrate = 30):
        self.absolute = absolute
        self.feedrate = feedrate
        self._gcode = self.parse_gcode(gcode) if gcode else []


    def parse_gcode(self, gcode_text):
        """
        Converts from relative to absolute coordinates if needed
        """
        points = []
        absolute = self.absolute
        feedrate = self.feedrate
        x = y = z = 0
        old_pos = pos = [feedrate, x, y, z]
        for line in gcode_text.splitlines(False):
            #print("Line", line)            
            G = self.get_int(line, 'G')
            if G is not None:
                if G == 0 or G == 1:    #Move
                    x = self.get_float(line, 'X')
                    y = self.get_float(line, 'Y')
                    z = self.get_float(line, 'Z')
                    f = self.get_float(line, 'F')
                    old_pos = pos
                    pos = pos[:]
                    if f is not None:
                        pos[0] = f
                    if absolute:
                        if x is not None:
                            pos[1] = x
                        if y is not None:
                            pos[2] = y
                        if z is not None:
                            pos[3] = z
                    else:
                        if x is not None:
                            pos[1] += x 
                        if y is not None:
                            pos[2] += y
                        if z is not None:
                            pos[3] += z
                    if pos[1:] != old_pos[1:]:
                        points.append(pos)

                elif G == 90:   # Change to absolute
                    absolute = True
                elif G == 91:   # Change to relative
                    absolute = False
                else:
                    print("Unknown G code:" + str(G))
        return points


    def get_int(self, line, code):
        n = line.find(code) + 1
        if n < 1:
            return None
        m = line.find(' ', n)
        try:
            if m < 0:
                return int(line[n:])
            return int(line[n:m])
        except:
            return None


    def get_float(self, line, code):
        n = line.find(code) + 1
        if n < 1:
            return None
        m = line.find(' ', n)
        try:
            if m < 0:
                return float(line[n:])
            return float(line[n:m])
        except:
            return None


    def optimize_2opt(self):
        """ 2-opt algorithm that doesn't seeem to work for me, as I have also pockets, that cannot be reversed """
        distances = []
        nodes = list(range(len(self._gcode)))
        print("Prepare data...")
        for i in nodes:
            distance = []
            for j in nodes:
                distance.append(self.get_distance(i, j))
            distances.append(distance)
        print("Optimize paths...")
        length_nodes = len(nodes)
        broken = False
        while True:
            i = 0
            while i < length_nodes - 2:
                j = i + 2
                while j < length_nodes:
                    if j == length_nodes - 1:
                        swap_length = distances[nodes[i]][nodes[j]] + distances[nodes[i + 1]][nodes[0]]
                        old_length = distances[nodes[i]][nodes[i + 1]] + distances[nodes[j]][nodes[0]]
                    else:
                        swap_length = distances[nodes[i]][nodes[j]] + distances[nodes[i + 1]][nodes[j + 1]]
                        old_length = distances[nodes[i]][nodes[i + 1]] + distances[nodes[j]][nodes[j + 1]]
                    if swap_length < old_length:
                        print("Make the new shortest path", swap_length, " instead of", old_length)
                        x = 0
                        while x < (j - i ) / 2:
                            temp = nodes[i + 1 + x]
                            nodes[i + 1 + x] = nodes[j - x]
                            nodes[j - x] = temp
                            x = x + 1
                        broken = True
                        break
                    j = j + 1
                i = i + 1
                if broken:
                    broken = False
                    break
                else:
                    sorted_gcode = [ self._gcode[i] for i in nodes]
                    self._gcode = sorted_gcode[:]
                    return

    def as_text(self):
        """
        Compose Gcode output as absolute
        """
        text_lines = ['G90']
        feedrate = None
        COORD_NAMES = ('X', 'Y', 'Z')
        old_pos = (0, 0, 0, 0)
        for pos in self._gcode:
            if feedrate != pos[0]:
                feedrate = pos[0]
                text_lines.append('G1 F{:.2f}'.format(round(feedrate, 2)))
            coords = [ (COORD_NAMES[j], coord) for j, coord in enumerate(pos[1:]) if coord != old_pos[j+1] ]
            if coords:
                variables = ["{}{:.6f}".format(coord[0], round(coord[1], 6)) for coord in coords]
                text_lines.append("G1 {}".format(" ".join(variables)))
            old_pos = pos
        return "\n".join(text_lines)


    def get_distance(self, p1, p2):
        a = self._gcode[p1]
        b = self._gcode[p2]
        dx = a[1] - b[1]
        dy = a[2] - b[2]
        dz = a[3] - b[3]
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    def load(self, filename):
        with open(filename, 'r') as f:
            self._gcode = self.parse_gcode(f.read())

    def save(self, filename):
        with open(filename, 'w') as f:
            f.write(self.as_text())


if __name__=='__main__':

    g = GCodeOptimizer()
    g.load('../tests/mosfet-pair.gcode')
    g.optimize_2opt()
    #print g.as_text()
    g.save("../tests/mosfet-pair-opt.gcode")
