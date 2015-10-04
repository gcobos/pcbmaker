#!/usr/bin/python
# -*- coding: utf-8 -*-

from copy import deepcopy

"""
Working sheet

Keeps the logic needed to build or edit a circuit

There are two parts, one logical, in which whe define a grid by specifying the number of cols and rows, and another establishes the 
width and height of each individual column or row in millimeters

"""                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         

class Sheet(object):

    """
        Cell type can be ONE of this types
    """
    CELL_TYPE_CLEAR=0
    CELL_TYPE_HOLE=1
    CELL_TYPE_HEATER=2
    CELL_TYPE_POCKET=3
    CELL_TYPE_SLASH=4
    CELL_TYPE_BACK_SLASH=5
    CELL_TYPE_ROW_SPAN=6

    AXIS_HORIZONTAL=0
    AXIS_VERTICAL=1

    CELL_TYPES_LUT={
        CELL_TYPE_CLEAR:       (u' ', 'Clear'),
        CELL_TYPE_HOLE:         (u'o', 'Hole'),
        CELL_TYPE_HEATER:       (u'S', 'Heater'),
        CELL_TYPE_POCKET:       (u'=', 'Pocket'),
        CELL_TYPE_SLASH:        (u'/', '/ Diagonal'),
        CELL_TYPE_BACK_SLASH:   (u'\\','\\ Diagonal'),
        CELL_TYPE_ROW_SPAN:     (u'+', 'Row span'),
    }
        
    def __init__(self, cols=10, rows=10, cell_width = 1, cell_height = 1):

        self._cols = cols
        self._rows = rows

        self._cell_width = cell_width
        self._cell_height = cell_height
        
        self.cells = []
        self.cuts = []

        self.cells_width = []       # Specifies the width of each cell in millimeters 
        self.cells_height = []      # Specifies the height of each cell in millimeters
    
    @property
    def cols(self):
        return self._cols
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        
    @cols.setter
    def cols(self, value):
        if not isinstance(value, int):
            raise ValueError
        if value <= 0:
            raise ValueError
        self._cols = value
        self._resize()
        
    @property
    def rows(self):
        return self._rows

    @rows.setter
    def rows(self, value):
        if not isinstance(value, int):
            raise ValueError
        if value <= 0:
            raise ValueError
        self._rows = value
        self._resize()

    @property
    def cell_width(self):
        return self._cell_width
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        
    @cell_width.setter
    def cell_width(self, value):
        if not isinstance(value, (float, int)):
            raise ValueError
        if value <= 0:
            raise ValueError
        self._cell_width = float(value)

    @property
    def cell_height(self):
        return self._cell_height
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        
    @cell_height.setter
    def cell_height(self, value):
        if not isinstance(value, (float, int)):
            raise ValueError
        if value <= 0:
            raise ValueError
        self._cell_height = float(value)

    def size(self, axis=None):
        if axis is None:
            return (self.cols, self.rows)
        if axis==Sheet.AXIS_HORIZONTAL:
            return self.cols
        if axis==Sheet.AXIS_VERTICAL:
            return self.rows        
        raise IndexError

    def get_cell_size(self, which, axis):
        if axis==Sheet.AXIS_HORIZONTAL:
            return self.get_cell_width(which)
        if axis==Sheet.AXIS_VERTICAL:
            return self.get_cell_height(which)
        raise IndexError        
        
    def _ensure_pos_cell(self, col, row, default=None):
        if col<0 or row<0 or col>self.cols-1 or row>self.rows-1:
            return
        if row>=len(self.cells):
            for r in range(len(self.cells), row+1):
                self.cells.append([])
            for r in range(len(self.cells_height), row+1):
                self.set_cell_height(r, self.cell_height)

        if col>=len(self.cells[row]):
            if default is None:
                default = Sheet.CELL_TYPE_CLEAR or default
            for c in range(len(self.cells[row]), col+1):
                self.cells[row].append(deepcopy(default))

    def _ensure_pos_cut(self, col, row, default=None):
        if col<0 or row<0 or col>self.cols or row>self.rows:
            return
        if row>=len(self.cuts):
            for r in range(len(self.cuts), row+1):
                self.cuts.append([])
        if col>=len(self.cuts[row]):
            if default is None:
                default = [False, False] or list(default)
            for c in range(len(self.cuts[row]), col+1):
                self.cuts[row].append(deepcopy(default))
            for c in range(len(self.cells_width), col+1):
                self.set_cell_width(c, self.cell_width)

    def _resize(self, col_offset=0, row_offset=0):
        """
            Resizes the original sheet, moving it on top of the new size, and optionally giving an offset 
            where to place the old content. All the contents that are out of the new size are clipped out
        """
        old_sheet = deepcopy(self)
        self.cells = []
        for row in range(self.rows):
            for col in range(self.cols):
                self.set_cell(col, row, old_sheet.get_cell(col + col_offset, row + row_offset))

        self.cuts = []
        for row in range(self.rows+1):
            for col in range(self.cols+1):
                self.set_cut(col, row, old_sheet.get_cut(col + col_offset, row + row_offset))
        
        self.cells_width=self.cells_width[col_offset:]
        self.cells_height=self.cells_height[row_offset:]
        
    def get_cell(self, col, row):
        """
            Get the cell at the position specified by row, col
            return: A cell, or None if the coordinates are out of the sheet
        """
        if col>=0 and col<self.cols and row>=0 and row<self.rows:
            self._ensure_pos_cell(col, row)
            return self.cells[row][col]
        return None

    def is_heater(self, col, row):
        """
            return: True if the cell at the position specified is a heater
        """
        return self.get_cell(col, row) == Sheet.CELL_TYPE_HEATER

    def is_hole(self, col, row):
        """
            return: True if the cell at the position specified is a hole
        """
        return self.get_cell(col, row) == Sheet.CELL_TYPE_HOLE

    def is_slash(self, col, row):
        """
            return: True if the cell at the position specified contains a slash
        """
        return self.get_cell(col, row) == Sheet.CELL_TYPE_SLASH

    def is_backslash(self, col, row):
        """
            return: True if the cell at the position specified contains a backslash
        """
        return self.get_cell(col, row) == Sheet.CELL_TYPE_BACK_SLASH

    def is_pocket(self, col, row):
        """
            return: True if the cell at the position specified is a pocket
        """
        return self.get_cell(col, row) == Sheet.CELL_TYPE_POCKET


    def set_cell(self, col, row, value):
        """
            Set the cell at the position specified by row, col
            return: A cell, or None if the coordinates are out of the sheet
        """
        if col>=0 and col<self.cols and row>=0 and row<self.rows:
            self._ensure_pos_cell(col, row)
            self.cells[row][col] = value
            return
        raise IndexError

    def get_cut(self, col, row, axis=None):
        """
            Get the cut at the position specified by row, col
            param axis: Specifies the axis for the cut, 0=horizontal, 1=vertical
            return: A cut (False or True), or None if the coordinates are out of the sheet
        """
        if col>=0 and col<self.cols+1 and row>=0 and row<self.rows+1:
            self._ensure_pos_cut(col, row)
            cell_cuts = deepcopy(self.cuts[row][col])
            if axis is not None:
                try:
                    return cell_cuts[axis]
                except:
                    return False
            return cell_cuts
                
        return None
            
    def set_cut(self, col, row, value=None, axis=None):
        """
            Set the cut at the position specified by row, col
            param axis: Specifies the axis to retrieve, 0=horizontal, 1=vertical, or None for both
            return: None
        """
        if col>=0 and col<self.cols+1 and row>=0 and row<self.rows+1:
            self._ensure_pos_cut(col, row)
            if axis is not None:
                # Cuts in the last row/col, are constrained by the axis type
                if axis==Sheet.AXIS_HORIZONTAL and col>=self.cols:
                    raise IndexError
                if axis==Sheet.AXIS_VERTICAL and row>=self.rows:
                    raise IndexError
                if value is not None:
                    self.cuts[row][col][axis] = value
                else:
                    self.cuts[row][col][axis] = True
            else:
                self.cuts[row][col] = value
        else:
            raise IndexError

    def set_cell_width(self, col, value):
        if col>=0 and col<=self.cols:
            if col>=len(self.cells_width):
                for _ in range(len(self.cells_width), col+1):
                    self.cells_width.append(self.cell_width)
            self.cells_width[col] = value
            return
        raise IndexError

    def get_cell_width(self, col):
        if col>=0 and col<=self.cols:
            if col>=len(self.cells_width):
                for _ in range(len(self.cells_width), col+1):
                    self.cells_width.append(self.cell_width)
            return self.cells_width[col]
        raise IndexError

    def set_cell_height(self, row, value):
        if row>=0 and row<=self.rows:
            if row>=len(self.cells_height):
                for _ in range(len(self.cells_height), row+1):
                    self.cells_height.append(self.cell_height)
            self.cells_height[row] = value
            return
        raise IndexError

    def get_cell_height(self, row):
        if row>=0 and row<=self.rows:
            if row>=len(self.cells_height):
                for _ in range(len(self.cells_height), row+1):
                    self.cells_height.append(self.cell_height)
            return self.cells_height[row]
        raise IndexError

    def load(self, filename):
        with open(filename, 'r') as f:
            self.cols, self.rows = map(int, f.readline().split(',', 1))
            self.cells_width = map(float, f.readline().split(','))
            self.cells_height = map(float, f.readline().split(','))
            for row in range(self.rows+1):
                hcuts = f.readline()
                line = f.readline()
                for col in range(self.cols+1):
                    self.set_cut(col, row, [True if hcuts[col*2+1]=='-' else False, True if line[col*2]=='|' else False])
                    if col<self.cols and row<self.rows:
                        self.set_cell(col, row, self.get_celltype_id(line[col*2+1]))            

    def save(self, filename):
        with open(filename, 'w') as f:
            f.write("{}, {}\n".format(self.cols, self.rows))
            f.write("{}\n".format(', '.join([str(self.get_cell_width(i)) for i in range(self.cols+1)])))
            f.write("{}\n".format(', '.join([str(self.get_cell_height(i)) for i in range(self.rows+1)])))
            f.write("{}\n".format(str(self)))
        
    def get_celltype_text(self, value, complete=False):
        """
            Returns a printable symbol, given a cell type id
        """
        if value in Sheet.CELL_TYPES_LUT:
            return Sheet.CELL_TYPES_LUT[value][1 if complete else 0]
        return Sheet.CELL_TYPES_LUT[Sheet.CELL_TYPE_CLEAR][1 if complete else 0]

    def get_celltype_id(self, text):
        """
            Gets a suitable cell type id from its name. Defaults to clear cell if not found
        """
        try:
            result = [k for k, v in Sheet.CELL_TYPES_LUT.items() if text in v][0]
        except Exception as e:
            result = Sheet.CELL_TYPE_CLEAR
        return result

    def __str__(self):
        return self.__unicode__()
        
    def __unicode__(self):
        result = u""
        for row in range(self.rows+1):
            top_line = u""
            line = u""
            for col in range(self.cols+1):
                if self.get_cut(col, row, Sheet.AXIS_HORIZONTAL):
                    top_line += u" -"
                else:
                    top_line += u"  "
                if self.get_cut(col, row, Sheet.AXIS_VERTICAL):
                    line += u"|"
                else:
                    line += u" "
                if col<self.cols and row<self.rows:
                    line += self.get_celltype_text(self.get_cell(col, row))
                else:
                    line += u" "
            result += top_line + u"\n" + line + u"\n"
        return result
    
if __name__=='__main__':

    s = Sheet(10, 10)
    
    s.set_cut(0, 0, True, Sheet.AXIS_HORIZONTAL)
    s.set_cell(0, 0, Sheet.CELL_TYPE_HOLE)
    s.set_cut(0, 0, True, Sheet.AXIS_VERTICAL)
    s.set_cut(0, 1, True, Sheet.AXIS_HORIZONTAL)
    s.set_cut(1, 0, True, Sheet.AXIS_VERTICAL)
    s.set_cut(1, 1, True, Sheet.AXIS_VERTICAL)
    s.set_cut(1, 2, True, Sheet.AXIS_HORIZONTAL)
    s.set_cut(2, 2, True, Sheet.AXIS_VERTICAL)
    s.set_cut(2, 3, True, Sheet.AXIS_HORIZONTAL)
    s.set_cut(3, 3, True, Sheet.AXIS_VERTICAL)
    s.set_cut(3, 4, True, Sheet.AXIS_HORIZONTAL)
    #s.set_cut(9, 9, True, Sheet.AXIS_HORIZONTAL)
    #s.set_cut(9, 9, True, Sheet.AXIS_VERTICAL)
    s.set_cut(9, 10, True, Sheet.AXIS_HORIZONTAL)
    s.set_cut(10, 9, True, Sheet.AXIS_VERTICAL)
    s.set_cell(3, 3, Sheet.CELL_TYPE_HEATER)
    s.set_cell(4, 3, Sheet.CELL_TYPE_HEATER)
    s.set_cell(5, 3, Sheet.CELL_TYPE_HEATER)
    s.set_cell(6, 3, Sheet.CELL_TYPE_HEATER)

    s.set_cell_width(4, 2.1)
    print s
    s.cols=12
    print s.cells_width
    print s.cells_height
    print s
    
        
