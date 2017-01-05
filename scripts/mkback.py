#!/usr/bin/python2

import sys
import mecode

"""
Measurements in millimeters

Starts on X = 0.5, Y = 0.425 (reference point from the other side)

"""

board_thickness = 1.0
board_width = 6.9
board_height = 8.6
drillbit_diameter = 0.3
cutting_speed = 140.0
travelling_speed = 400.0
travelling_height = 2.0
cutting_z_increment = 0.1
pocket_depth = 0.6
margin = drillbit_diameter
pocket_width = 0.9
pocket_height = 4.2

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

        for i in range(int(pocket_depth / cutting_z_increment)):
            cutting(i * cutting_z_increment)
            g.meander(pocket_width, pocket_height, drillbit_diameter)
            g.move(x=x_offset, y=y_offset)


    def cut_board():
        """
            Asume we start at 0, 0, 0
        """
        travelling()
        x = -margin
        y = -margin
        g.move(x, y)

        for i in range(int(board_thickness / cutting_z_increment)):
            cutting(i * cutting_z_increment)
            x += board_width
            g.move(x = x)
            y += board_height
            g.move(y = y)
            x -= board_width
            g.move(x = x)
            y -= board_height
            g.move(y = y)


    # Main program
    plot_view = True

    g.absolute()
    travelling()
    g.move(0.0, 0.0, 0.0)

    make_pocket(1.4 - (pocket_width / 2.0), 1.9)
    travelling()
    make_pocket(5.0 - (pocket_width / 2.0), 1.9)
    travelling()
    g.move(0.0, 0.0, 0.0)
    cut_board()
    travelling()

    if plot_view:
        g.view('matplotlib')

