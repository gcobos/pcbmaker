#!/usr/bin/python2

import sys
import mecode
import math

"""
Measurements in millimeters

Starts on X = 0.475, Y = 0.425 (reference point from the other side)

"""

board_thickness = 1.0
board_width = 7.2
board_height = 8.7
drillbit_diameter = 0.3
cutting_speed = 140.0
travelling_speed = 400.0
travelling_height = 2.0
cutting_z_increment = 0.1
pocket_depth = 0.75
motor_gap_depth = 0.65
motor_gap_height = 6.0
margin = drillbit_diameter
pocket_width = 1
pocket_height = 4.4

is_cutting = False

"""
    Naming the axis makes it very easy to transpose the piece in case we need it
"""
with mecode.G(setup = False, x_axis='X', y_axis='Y') as g:

    def cutting(depth=cutting_z_increment):
        global is_cutting
        if not is_cutting:
            g.move(z = 0.0)
        g.feed(cutting_speed)
        g.move(z=-depth)
        is_cutting = True

    def travelling(height=travelling_height):
        is_cutting = False
        g.feed(travelling_speed)
        g.move(z=height)

    def make_pocket(x_offset, y_offset):
        """
            Make the pocket for the stepper motor's header
            Asume we start at 0, 0, 0
        """
        travelling()
        g.move(x=x_offset, y=y_offset)

        for i in range(1, int(pocket_depth / cutting_z_increment)):
            cutting(i * cutting_z_increment)
            g.meander(pocket_width, pocket_height, drillbit_diameter * 0.9)
            g.move(x=x_offset, y=y_offset)

        g.relative()
        g.rect(pocket_width, pocket_height)
        g.absolute()

    def make_motor_gap():
        """
            Make the pocket for the stepper motor's body
            Asume we start at 0, 0, 0
        """
        travelling()
        g.move(x=-margin, y=(board_height / 2.0) - motor_gap_height / 2.0)

        for i in range(1, int(motor_gap_depth / cutting_z_increment)):
            cutting(i * cutting_z_increment)
            current_height = motor_gap_height - (motor_gap_height * math.sin((i-1) * (math.pi / 2.0) / (motor_gap_depth / cutting_z_increment)))
            y_offset = (board_height / 2.0) - current_height / 2.0
            g.move(x=-margin, y=y_offset)
            g.meander(board_width, current_height, drillbit_diameter * 0.9)

    def cut_board():
        """
            Asume we start at 0, 0, 0
        """
        travelling()
        x = -margin
        y = -margin
        g.move(x, y)

        for i in range(1, int( (board_thickness - 0.1) / cutting_z_increment)):
            cutting(i * cutting_z_increment)
            g.relative()
            g.rect(board_width, board_height)
            g.absolute()

    # Main program
    plot_view = False

    g.absolute()
    travelling()
    g.move(0.0, 0.0, 0.0)

    make_pocket(1.39 - (pocket_width / 2.0), (board_height) / 2.0 - pocket_height / 2.0)
    travelling()
    make_pocket(5.19 - (pocket_width / 2.0), (board_height) / 2.0 - pocket_height / 2.0)
    travelling()
    make_motor_gap()
    travelling()
    g.move(0.0, 0.0, 0.0)
    cut_board()
    travelling()

    if plot_view:
        g.view('matplotlib')

