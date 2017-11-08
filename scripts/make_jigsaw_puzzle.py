#!/usr/bin/python3

"""

Generate the gcode to mill a random jigsaw puzzle

"""

import sys
import mecode
import random
import math
import copy

board_width = 300
board_height = 240

number_of_pieces = 40

random_seed = 2     # Every seed generates a different puzzle
tolerance = 1.8     # When comparing pieces

board_thickness = 1.6
cutting_speed = 70.0
cutting_z_increment = 0.2
travelling_speed = 400.0
travelling_height = 2.0
drillbit_diameter = 1.0
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

    def cut_box(x_offset, y_offset, box_width, box_height, box_depth = cutting_z_increment):
        """
            Make a box cut
            Asume we start at 0, 0, 0
        """
        travelling()
        g.move(x=x_offset, y=y_offset)

        for i in range(0, int(box_depth / cutting_z_increment)):
            cutting((i + 1) * cutting_z_increment)
            g.relative()
            g.rect(box_width, box_height)
            g.absolute()


class Arc:

    EQ_TOL = 1.0

    def __init__(self, x, y, r, direction):
        self.x = float(x)
        self.y = float(y)
        self.r = float(r)
        self.direction = direction

    @classmethod
    def set_eq_tolerance(cls, tolerance):
        cls.EQ_TOL = float(tolerance)

    def randomize(self, axis='X'):
        if axis=='X':
            self.x = random.uniform(self.x - self.EQ_TOL, self.x + self.EQ_TOL)
        else:
            self.y = random.uniform(self.y - self.EQ_TOL, self.y + self.EQ_TOL)
        self.r = random.uniform(self.r - self.EQ_TOL, self.r + self.EQ_TOL)

    def __eq__(self, other):
        if 0. in (self.r, other.r):
            return False
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2 + (self.r - other.r)**2) < self.EQ_TOL

    def __repr__(self):
        return "Arc(x={}, y={}, r={}, dir={})".format(self.x, self.y, self.r, self.direction)


def calculate_piece_size(board_width, board_height, number_of_pieces):

    if board_width < board_height:
        tmp = board_width
        board_width = board_height
        board_height = tmp

    board_area = float(board_width * board_height)
    board_ratio = board_width / board_height

    vertical_pieces = int(round(math.sqrt(number_of_pieces / board_ratio)))
    horizontal_pieces = int(round(number_of_pieces / vertical_pieces))

    piece_width = float(board_width) / horizontal_pieces
    piece_height = float(board_height) / vertical_pieces

    return piece_width, piece_height, horizontal_pieces, vertical_pieces


used_arcs = []
def get_piece_tap(x=0, y=0, axis='X', piece_width=100.0, piece_height=100.0, invert=False):

    single_piece_side_template = [
        Arc(0, 0, 0, 'CW'),
        Arc(50, 4, 100, 'CW'),
        Arc(75, 26, 40, 'CCW'),
        Arc(73, 70, 34, 'CW'),
        Arc(97, 70, 34, 'CW'),
        Arc(95, 26 , 34, 'CW'),
        Arc(120, 4, 40, 'CCW'),
        Arc(170, 0, 100, 'CW'),
    ]
    template_width = 170.0
    template_height = 240.0
    scale = math.sqrt(piece_width * piece_height) / template_width
    new_piece = copy.deepcopy(single_piece_side_template)
    flipped = random.choice((0, 1))
    for j in reversed(new_piece) if invert else new_piece:
        # Ensure every arc is different
        while j in used_arcs: j.randomize('Y')
        used_arcs.append(copy.deepcopy(j))
        
        if axis == 'Y':
            tmp = j.x
            j.x = -j.y
            j.y = tmp
            j.x *= piece_width / template_height
            j.y *= piece_height / template_width
            j.r *= scale
            if flipped:
                j.x =-j.x
                j.direction = 'CW' if j.direction=='CCW' else 'CCW'
        else:
            j.x *= piece_width / template_width
            j.y *= piece_height / template_height
            j.r *= scale
            if flipped:
                j.y = -j.y
                j.direction = 'CW' if j.direction=='CCW' else 'CCW'
        j.x += x
        j.y += y
    return new_piece
    

def generate_cut(x, y, axis, piece_count, piece_width, piece_height, invert = False):

    cut = []
    for i in range(piece_count):
        cut.extend(get_piece_tap(x, y, axis, piece_width, piece_height, invert))
        if axis == 'Y':
            y += piece_height
        else:
            x += piece_width
    #if invert:
    #    cut = list(reversed(cut))
        
    return cut


def generate_puzzle(board_width, board_height, number_of_pieces):

    cuts = []

    piece_width, piece_height, horizontal_pieces, vertical_pieces = calculate_piece_size(board_width, board_height, number_of_pieces)
        
    # Vertical cuts
    x = piece_width
    y = 0
    for i in range(horizontal_pieces - 1):
        cuts.append(generate_cut(x, y, 'Y', vertical_pieces, piece_width, piece_height, invert=i%2))
        x += piece_width

    # Horizontal cuts    
    x = 0
    y = piece_height
    for i in range(vertical_pieces - 1):
        cuts.append(generate_cut(x, y, 'X', horizontal_pieces, piece_width, piece_height, invert=i%2))
        y += piece_height

    return cuts


if __name__=='__main__':

    # Main program
    plot_view = int(sys.argv[1]) if len(sys.argv) > 1 else False

    random.seed(random_seed)
    Arc.set_eq_tolerance(tolerance)
    puzzle_cuts = generate_puzzle(board_width, board_height, number_of_pieces)

    g.absolute()
    travelling()
    g.move(0, 0)
    for cut in puzzle_cuts:
        travelling()
        g.move(cut[0].x, cut[0].y)
        cutting()
        for arc in cut:
            if arc.r:
                g.arc(x=arc.x, y=arc.y, radius=arc.r, direction=arc.direction)


    travelling()

    # Cut the board
    cut_box(0.0, 0.0, board_width, board_height, board_thickness)
    travelling()

    g.move(0.0, 0.0, 30.0)

    if plot_view:
        g.view('matplotlib')

