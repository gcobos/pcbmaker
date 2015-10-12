#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
G-Code exporter

Converts the contents in the working sheet to a G-Code

"""

import mecode
import math
import StringIO

class GCodeExport(object):

    def __init__(self,
                 z_flying = 3.0, feed_flying = 600,
                 z_cutting = -0.1, feed_cutting = 300, 
                 heater_clearance = 1.0, z_drilling = 0.4,
                 z_pocket = 0.2, x_offset = 0.0,
                 y_offset = 0.0, z_offset = 0.0):
        self.z_flying = z_flying
        self.z_cutting = z_cutting
        self.feed_flying = feed_flying
        self.feed_cutting = feed_cutting
        self.heater_clearance = heater_clearance        # In mm
        self.z_drilling = z_drilling                    # In mm
        self.z_pocket = z_pocket                        # In mm
        self.x_offset = x_offset                        # In mm
        self.y_offset = y_offset                        # In mm
        self.z_offset = z_offset                        # In mm
        self.g = None
        self.s = None
        
        self._is_cutting = None

    def from_sheet(self, sheet, visualize=False):

        result = StringIO.StringIO()

        with mecode.G(outfile=result, print_lines=False, 
                      x_axis='Y', y_axis='X',
                      setup=False, aerotech_include=False) as g:
            self.g = g
            self.s = sheet
            g.absolute()
            self._set_cutting(False)
            self._make_hcuts()
            self._make_vcuts()
            self._make_diagonals()
            self._make_heaters()
            self._make_pockets()
            self._make_holes()
            self._set_cutting(False)
            g.move(x=self.y_offset, y=self.x_offset)
            
            if visualize:
                g.view('matplotlib')
            result = result.getvalue()

        return result

    def _set_cutting(self, cutting, depth=None):
        if cutting == self._is_cutting:
            return
        self._is_cutting = cutting
        depth = depth or self.z_cutting
        if cutting:
            self.g.feed(self.feed_flying)
            self.g.move(z=self.z_offset)
            self.g.feed(self.feed_cutting)
            self.g.move(z=self.z_offset + depth)
        else:
            self.g.feed(self.feed_flying)
            self.g.move(z=self.z_offset + self.z_flying)            

    def _get_position(self, col, row):
        z = self.z_offset # This will matter when leveling the board
        x = self.x_offset + sum([self.s.get_cell_width(i) for i in range(col)])
        y = self.y_offset + sum([self.s.get_cell_height(j) for j in range(row)])
        return x, y, z

    def _get_segments(self, cols, rows, transposed=False, checker=None, **params):
        holder = {}
        if checker is None:
            checker = self.s.get_cell
        for j in range(rows):
            segments = []
            begin_segment_pos = 0
            coords = (j, 0) if transposed else (0, j)
            was_in_segment = checker(*coords, **params)
            for i in range(cols):
                coords = (j, i) if transposed else (i, j)
                now_in_segment  = checker(*coords, **params)
                if now_in_segment != was_in_segment:
                    if was_in_segment:
                        segments.append((begin_segment_pos, i))
                    else:
                        begin_segment_pos = i
                    was_in_segment = not was_in_segment
            if was_in_segment:
                segments.append((begin_segment_pos, i))
            holder[j] = segments
        return holder

    def _make_hcuts(self):
                
        # Horizontal cuts
        hcuts = self._get_segments(self.s.cols+1, self.s.rows+1, transposed=False,
                                   checker=self.s.get_cut, axis=self.s.AXIS_HORIZONTAL)
        #print "HCuts", hcuts
    
        direction = 1
        for row in range(self.s.rows+1):
            if not hcuts[row]:
                continue
            if direction==-1:
                cuts = list(reversed([[end, begin] for begin, end in hcuts[row]]))
            else:
                cuts = hcuts[row]
            for a, b in cuts:
                self._set_cutting(False)
                xpos, ypos, zpos = self._get_position(a, row)
                self.g.move(x=xpos, y=ypos)
                self._set_cutting(True)
                xpos, ypos, zpos = self._get_position(b, row)
                self.g.move(x=xpos, y=ypos)
            direction = -direction

    def _make_vcuts(self):
                
        # Vertical cuts
        vcuts = self._get_segments(self.s.rows+1, self.s.cols+1, transposed=True, 
                                   checker=self.s.get_cut, axis=self.s.AXIS_VERTICAL)
        #print "VCuts", vcuts
    
        direction = -1
        for col in range(self.s.cols, -1, -1):
            if not vcuts[col]:
                continue
            if direction==-1:
                cuts = list(reversed([[end, begin] for begin, end in vcuts[col]]))
            else:
                cuts = vcuts[col]
            for a, b in cuts:
                self._set_cutting(False)
                xpos, ypos, zpos = self._get_position(col, a)
                self.g.move(x=xpos, y=ypos)
                self._set_cutting(True)
                xpos, ypos, zpos = self._get_position(col, b)
                self.g.move(x=xpos, y=ypos)
            direction = -direction

    def _make_holes(self, depth = None):
        """
            Make all holes in the board
        """
        depth = depth or self.z_drilling
        direction = 1
        for row in range(self.s.rows):
            cols = range(self.s.cols)
            if direction==-1:
                cols = list(reversed(cols))
            if not filter(lambda k : self.s.is_hole(k, row), cols):
                continue
            for col in cols:
                if not self.s.is_hole(col, row):
                    continue
                self._set_cutting(False)
                xpos, ypos, zpos = self._get_position(col, row)
                self.g.move(x=xpos + self.s.get_cell_width(col)/2.0, y=ypos + self.s.get_cell_height(row)/2.0)
                self._set_cutting(True, depth = depth)
            direction = -direction

    def _make_diagonals(self, depth = None):
        """
            Make all holes in the board
        """
        direction = 1
        for row in range(self.s.rows):
            cols = range(self.s.cols)
            if direction==-1:
                cols = list(reversed(cols))
            if not filter(lambda k : self.s.is_slash(k, row) or self.s.is_backslash(k, row), cols):
                continue
            xlast, ylast = None, None
            for col in cols:
                if not (self.s.is_slash(col, row) or self.s.is_backslash(col, row)):
                    continue
                xpos1, ypos1, zpos1 = self._get_position(col, row)
                xpos2 = xpos1 + self.s.get_cell_width(col)
                ypos2 = ypos1 + self.s.get_cell_height(row)
                if direction == -1:
                    xpos1, xpos2 = xpos2, xpos1
                    ypos1, ypos2 = ypos2, ypos1
                if self.s.is_slash(col, row):
                    ypos1, ypos2 = ypos2, ypos1
                if not (xpos1==xlast and ypos1==ylast):
                    self._set_cutting(False)
                    self.g.move(x=xpos1, y=ypos1)
                self._set_cutting(True)
                self.g.move(x=xpos2, y=ypos2)
                xlast, ylast = xpos2, ypos2
            direction = -direction

    def _make_heaters(self, clearance = None):
        """
            For now, only horizontal heaters
        """
        clearance = clearance or self.heater_clearance
        # Heaters
        heaters = self._get_segments(self.s.cols, self.s.rows, checker=self.s.is_heater)
        #print "Heaters", heaters

        direction = 1
        for row in range(self.s.rows):
            if not heaters[row]:
                continue
            if direction==-1:
                heater_cols = list(reversed([[end, begin] for begin, end in heaters[row]]))
            else:
                heater_cols = heaters[row]
            for a, b in heater_cols:
                coords = (b, a) if a > b else (a, b)
                self._make_heater(row, *coords, clearance = clearance)
            direction = -direction


    def _make_heater(self, row, begin, end, clearance = None):
        """
            Create a single heater, horizontally only for now
        """
        clearance = clearance or self.heater_clearance
        self._set_cutting(False)
        xpos1, ypos1, zpos1 = self._get_position(begin, row)
        xpos2, ypos2, zpos2 = self._get_position(end, row + self.s.get_row_span(begin, row))
        i = xpos1
        direction = 1
        while i < xpos2:
            if direction==1:
                self.g.move(x=i, y=ypos1)
                self._set_cutting(True)
                self.g.move(x=i, y=ypos2-clearance)
            else:
                self.g.move(x=i, y=ypos2)
                self._set_cutting(True)
                self.g.move(x=i, y=ypos1+clearance)
            i += clearance
            direction = -direction
            self._set_cutting(False)

    def _make_pockets(self, depth = None):
        """
            Make all the pockets in the board (for now only horizontal)
        """
        depth = depth or self.z_pocket
        # Pockets
        pockets = self._get_segments(self.s.cols, self.s.rows, checker=self.s.is_pocket)
        #print "Pockets", pockets

        direction = 1
        for row in range(self.s.rows):
            if not pockets[row]:
                continue
            if direction==-1:
                pocket_cols = list(reversed([[end, begin] for begin, end in pockets[row]]))
            else:
                pocket_cols = pockets[row]
            for a, b in pocket_cols:
                self._make_pocket(row, a, b, depth=depth)
            direction = -direction

    def _make_pocket(self, row, begin, end, depth):

        self._set_cutting(False)
        xpos, ypos, zpos = self._get_position(begin, row)
        self.g.move(x=xpos, y=ypos + self.s.get_cell_height(row)/2.0)
        self._set_cutting(True, depth = depth)
        xpos, ypos, zpos = self._get_position(end, row)
        self.g.move(x=xpos, y=ypos + self.s.get_cell_height(row)/2.0)
        self._set_cutting(False)

    def send(self, data):
    
        import serial
        import time

        DEFAULT_PORTS='''rfcomm2
rfcomm0
rfcomm1
socket/bluetooth'''

        conn = None
        for device in DEFAULT_PORTS.split('\n'):
            try:
                # Open grbl serial port
                with serial.Serial("/dev/{}".format(device), 57600) as conn:
                    print "Pude conectar a ", device
                    # Wake up grbl
                    conn.write("\r\n\r\n")
                    time.sleep(2)   # Wait for grbl to initialize
                    conn.flushInput()  # Flush startup text in serial input
                    # Stream g-code to grbl
                    for line in data.split('\n'):
                        l = line.strip() # Strip all EOL characters for streaming
                        print 'Sending: ' + l
                        conn.write(l + '\n') # Send g-code block to grbl
                        grbl_out = conn.readline() # Wait for grbl response with carriage return
                        print ' : ' + grbl_out.strip()
            except:
                pass
        if not conn:
            print "No hay donde conectar!"
            return


    def send_bt(self, data, recvs, sends):
        import StringIO
        print "Actually sending data!!!"
        # Stream g-code to grbl
        try:
            for line in data.split('\n'):
                l = line.strip() # Strip all EOL characters for streaming
                print 'Sending: ' + l,
                for i in "{}\n".format(l):
                    sends.write(i) # Send g-code block to grbl

                grbl_out = ""
                while True:
                    if recvs.ready():
                        print "Is ready"
                        try:
                            print "About to wait"
                            grbl_out = recvs.readLine()
                            print "We get something!", grbl_out
                            break
                        except Exception as e:
                            print "Agghh!", e
                    print "Another loop with data :("
                            
                """
                readbuff = StringIO.StringIO()
                while not grbl_out.endswith('\n'):
                    time.sleep(1)
                    lread = recvs.read(readbuff)
                    print "Bytes leidos", lread
                    if lread > 0:
                        grbl_out += readbuff.getvalue()
                """
                print ' : ' + grbl_out.strip()
        except Exception as e:
            print e
    



if __name__=='__main__':
    
    from sheet import Sheet
    
    g = GCodeExport()
    
    s = Sheet(2, 2, cell_width=1, cell_height=1)
    #s.load('../tests/square.cb')
    #s.load('../tests/board.cb')
    s.load('../tests/octantes1y4.cb')
    print s
    #heaters = g._get_segments(s.cols, s.rows, checker=s.is_heater)
    #print "Heaters", heaters
    g.from_sheet(s)
    #g._make_heaters()

    
    #s.set_cut(0, 0, [True, True]); s.set_cut(1, 0, [True, True]); s.set_cut(2, 0, [False, True])
    #s.set_cut(0, 1, [False, False]); s.set_cut(1, 1, [True, True]); s.set_cut(2, 1, [False, True])
    #s.set_cut(0, 2, [False, False]); s.set_cut(1, 2, [False, False]); s.set_cut(2, 2, [False, False])
    #s.save('../tests/test.cb')
    
    #print s
    #g.from_sheet(s)
    
    