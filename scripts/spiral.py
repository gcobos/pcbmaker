#!/usr/bin/python

__author__ = "Gonzalo Cobos <gcobos@gmail.com"


from mecode import G
from math import cos, sin, pi

RADIUS = 10
NUM_OF_ROUNDS = 20
STEPS_PER_ROUND = 200
DIRECTION = 1   # 1 or -1
CENTER_X = RADIUS
CENTER_Y = RADIUS

with G(setup = False, outfile = 'spiral.gcode', print_lines = False, aerotech_include = False) as g:

    radius = 0.0
    angle = 0.0
    g.absolute()
    g.move(CENTER_X, CENTER_Y)
    for r_count in range(NUM_OF_ROUNDS):
        for a_count in range(STEPS_PER_ROUND):
            x = CENTER_X + radius * cos(angle)
            y = CENTER_Y + radius * sin(angle)
            g.move(x, y)
            angle = float(a_count) * 2 * DIRECTION * pi / float(STEPS_PER_ROUND)
            radius += RADIUS / float(STEPS_PER_ROUND * NUM_OF_ROUNDS)                

    x = CENTER_X + radius
    y = CENTER_Y
    g.move(x, y)

    #g.view('matplotlib')
