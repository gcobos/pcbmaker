#!/usr/bin/python2.7

import os
from kivy import platform
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.properties import NumericProperty, ListProperty, BooleanProperty, ObjectProperty, StringProperty
from kivy.uix.popup import Popup
from jnius import autoclass, JavaException
from time import sleep
from lib.sheet import Sheet
from lib.gcode import GCodeExport

#if platform=='linux':
#    import cProfile

class ScreenManagement(ScreenManager):
    pass

class MainScreen(Screen):
    pass


class LoadFilesScreen(Screen):
    pass

class SaveFilesScreen(Screen):
    pass

class ExportFilesScreen(Screen):
    pass

#class exportPanel(TabbedPanel):
#    filename_input2 = ObjectProperty()


class CellWidget(Widget):
    has_hcut = BooleanProperty(False)
    has_vcut = BooleanProperty(False)
    celltype = StringProperty('clear')
    row_span = NumericProperty(1)

    def __init__(self, sheet, col, row, **kwargs):
        super(CellWidget, self).__init__(**kwargs)
        self.sheet = sheet
        self.col = col
        self.row = row

    def get_celltype_resource(self, value):
        return value.replace('/ Diagonal', 'slash').replace('\\ Diagonal', 'backslash').lower()

    def on_touch_down(self, touch):
        if touch.is_touch and self.collide_point(*touch.pos):
            touch.grab(self)
            form = App.get_running_app().cellform
            if App.get_running_app().root.clone_mode.state == 'down':
                self.configure_cell(form, set_dimensions = False)
                return True
            self.show_form(form)
            return True

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            # I received my grabbed touch
            return super(CellWidget, self).on_touch_move(touch)
        else:
            pass

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            # I receive my grabbed touch, I must ungrab it!
            touch.ungrab(self)
        else:
            # it's a normal touch
            pass
    """
    def on_touch_down(self, touch):
        form = App.get_running_app().cellform
        if self.collide_point(*touch.pos):
            touch.grab(self)
            if App.get_running_app().root.clone_mode.state == 'down':
                self.configure_cell(form)
                return True
            self.show_form(form)
            return True
        return super(CellWidget, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        return super(CellWidget, self).on_touch_move(touch)
    """ 

    def show_form(self, form):
        form.title="Editing cell ({}, {}) properties".format(self.col, self.row)
        form.ids['hcut'].state = 'down' if self.sheet.get_cut(self.col, self.row, axis=self.sheet.AXIS_HORIZONTAL) else 'normal'
        form.ids['vcut'].state = 'down' if self.sheet.get_cut(self.col, self.row, axis=self.sheet.AXIS_VERTICAL) else 'normal'
        form.ids['celltype'].text = self.sheet.get_celltype_text(self.sheet.get_cell(self.col, self.row), complete=True)
        form.ids['column_width'].text = unicode(self.sheet.get_cell_width(self.col))
        form.ids['row_height'].text = unicode(self.sheet.get_cell_height(self.row))
        form.ids['row_span'].text = unicode(self.sheet.get_row_span(self.col, self.row))
        form.bind(on_dismiss=self.configure_cell)
        form.open()
        form.closed = False
    
    def configure_cell(self, form, set_dimensions = True):        
        self.has_hcut = form.ids['hcut'].state == 'down'
        self.has_vcut = form.ids['vcut'].state == 'down'
        celltype_text = form.ids['celltype'].text
        self.celltype = self.get_celltype_resource(celltype_text)
        self.row_span = form.ids['row_span'].text
        column_width = float(form.ids['column_width'].text)
        row_height = float(form.ids['row_height'].text)
        row_span = int(form.ids['row_span'].text)
        self.sheet.set_cut(self.col, self.row, self.has_hcut, axis=self.sheet.AXIS_HORIZONTAL)
        self.sheet.set_cut(self.col, self.row, self.has_vcut, axis=self.sheet.AXIS_VERTICAL)
        self.sheet.set_cell(self.col, self.row, self.sheet.get_celltype_id(celltype_text))
        if set_dimensions:
            self.sheet.set_cell_width(self.col, column_width)
            self.sheet.set_cell_height(self.row, row_height)
        if row_span > 1:
            self.sheet.set_row_span(self.col, self.row, row_span)
            for i in range(1, row_span):
                pos = ((self.sheet.rows - self.row - i) * self.sheet.cols) - self.col -1
                if pos < self.sheet.cols * self.sheet.rows:
                    cell = self.parent.children[pos]
                    cell.celltype = 'row span'
        form.unbind(on_dismiss=self.configure_cell)


class CellForm(Popup):
    closed = True
    
    def on_dismiss(self):
        self.closed = True

class DrawingArea(GridLayout):

    cols = NumericProperty(20)
    rows = NumericProperty(20)
    cell_width = NumericProperty(1.0)
    cell_height = NumericProperty(1.0)

    def __init__(self, **kwargs):
        config = App.get_running_app().config
        cols = config.getdefaultint('sheet', 'cols', 20)
        rows = config.getdefaultint('sheet', 'rows', 20)
        self.cell_width = float(config.getdefault('cell', 'width', 1.0))
        self.cell_height = float(config.getdefault('cell', 'height', 1.0))

        super(DrawingArea, self).__init__(cols=cols, rows=rows)
        self.cols = cols
        self.rows = rows
        self.sheet = Sheet(cols=self.cols, rows=self.rows, 
                           cell_width=self.cell_width, cell_height=self.cell_height)
        self.resize_sheet(self.cols, self.rows)
        self.set_cells_width(self.cell_width)
        self.set_cells_height(self.cell_height)

    def set_cells_width(self, width):
        for i in range(self.sheet.cols+1):
            self.sheet.set_cell_width(i, width)

    def set_cells_height(self, height):
        for i in range(self.sheet.rows+1):
            self.sheet.set_cell_height(i, height)

    def resize_sheet(self, cols, rows, clear=False):
        # Generate as many children as we need
        if rows*cols > len(self.children):
            self.cols = cols
            self.rows = rows
            for i in range(rows*cols-len(self.children)):
                cell = CellWidget(self.sheet, 0, 0)
                self.add_widget(cell)
        else: 
            for i in range(len(self.children)-1, rows*cols-1, -1):
                self.remove_widget(self.children[i])
            self.cols = cols
            self.rows = rows

        self.sheet.cols = cols
        self.sheet.rows = rows

        i = self.cols*self.rows
        config = App.get_running_app().config
        if clear:
            self.set_cells_width(float(config.getdefault('cell', 'width', 1.0)))
            self.set_cells_height(float(config.getdefault('cell', 'height', 1.0)))

        for row in range(self.rows):
            for col in range(self.cols):
                i -= 1
                cell = self.children[i]
                if clear:                    
                    self.sheet.set_cell(col, row, self.sheet.CELL_TYPE_CLEAR)
                    self.sheet.set_cut(col, row, [False, False])
                cell.col = col
                cell.row = row
                cell.has_hcut = self.sheet.get_cut(col, row, axis=self.sheet.AXIS_HORIZONTAL)
                cell.has_vcut = self.sheet.get_cut(col, row, axis=self.sheet.AXIS_VERTICAL)
                cell.celltype = cell.get_celltype_resource(self.sheet.get_celltype_text(
                                                self.sheet.get_cell(col, row), complete=True))

    def load_sheet(self, path, filename):
        self.sheet.load(os.path.join(path, filename))
        self.resize_sheet(self.sheet.cols, self.sheet.rows)
        App.get_running_app().root.current = 'main'

    def save_sheet(self, path, filename):
        self.sheet.save(os.path.join(path, filename))
        App.get_running_app().root.current = 'main'

    def set_export_filename(self, default = ''):
        root_app = App.get_running_app().root
        default = default or root_app.ids['filename_input'].text
        _, default = os.path.split(default)
        basename, extension = os.path.splitext(default)
        extension = 'gcode'
        root_app.ids['export_panel'].ids['filename_input2'].text = ".".join((basename, extension))

    def export_sheet(self, options, path, filename):
        config = App.get_running_app().config
        gcode = GCodeExport(
            z_flying = float(config.getdefault('gcode', 'z_flying', 3.0)),
            feed_flying = float(config.getdefault('gcode', 'feed_flying', 1000)),
            z_cutting = float(config.getdefault('gcode', 'z_cutting', -0.1)),
            feed_cutting = float(config.getdefault('gcode', 'feed_cutting', 90)),
            heater_clearance = float(config.getdefault('gcode', 'heater_clearance', 1.0)),
            z_drilling = float(config.getdefault('gcode', 'z_drilling', 0.4)),
            z_pocket = float(config.getdefault('gcode', 'z_pocket', -0.2)),
            x_offset = float(config.getdefault('gcode', 'x_offset', 0.0)),
            y_offset = float(config.getdefault('gcode', 'y_offset', 0.0)),
            z_offset = float(config.getdefault('gcode', 'z_offset', 0.0)),
            x_backslash = float(config.getdefault('gcode', 'x_backslash', 0.01)),
            y_backslash = float(config.getdefault('gcode', 'y_backslash', 0.01)),
        )

        data = gcode.from_sheet(self.sheet, visualize=False and (platform=='linux'))
        app = App.get_running_app()

        # TODO Save only if you're asked to do it!
        path = App.get_running_app().user_data_dir
        with open(os.path.join(path, filename), 'w') as f:
            f.write("{}\n".format(data))
        print "Platform?", platform
        if platform=='android':  #  TODO: Set this as an option, True by default!!
            print "Conecta a bt..."
            app.do_connect()
            if app.connected:
                gcode.send_bt(data, app.recv_stream, app.send_stream)
        else:
            pass #gcode.send(data)
        App.get_running_app().root.current = 'main'



class PCBMakerApp(App):

    connected = False
    socket = None
    recv_stream = None
    send_stream = None
    
    cellform = ObjectProperty(None)
    if platform!='linux':
        use_kivy_settings = False

    def __init__(self, **kwargs):
        super(PCBMakerApp, self).__init__(**kwargs)

    def build_config(self, config):
        config.setdefaults('sheet', {
            'cols': '20',
            'rows': '20'
        })
        config.setdefaults('cell', {
            'width': '2.54',
            'height': '2.54'
        })
        config.setdefaults('gcode', {
            'z_flying': '5.0',
            'feed_flying': '800.0',
            'z_cutting': '-0.05',
            'feed_cutting': '50.0',
            'heater_clearance': '1.0',
            'z_drilling': '1.5',
            'z_pocket': '0.2',
            'x_backslash': '0.02',
            'y_backslash': '0.02',
            'x_offset': '0.0',
            'y_offset': '0.0',
            'z_offset': '0.0',
        })

    def build(self):
        self.cellform = CellForm()

    def do_connect(self):
        try:
            if self.connected:
                self.socket.close()
                self.connected = False
            self.socket, self.recv_stream, self.send_stream = self.get_socket_stream('BT UART')
            if self.send_stream:
                self.connected = self.socket.isConnected()
        except Exception as e:
            print 'Failed to connect'
            print(e)

    def get_socket_stream(self, name):
        try: 
            BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
            BluetoothDevice = autoclass('android.bluetooth.BluetoothDevice')
            BluetoothSocket = autoclass('android.bluetooth.BluetoothSocket')
            InputStreamReader = autoclass('java.io.InputStreamReader')
            BufferedReader = autoclass('java.io.BufferedReader')
            UUID = autoclass('java.util.UUID')
        except JavaException as e:
            print("Couldn't load some android classes %s" % str(e))
            return None, None, None

        paired_devices = BluetoothAdapter.getDefaultAdapter().getBondedDevices().toArray()
        socket = None
        if not paired_devices:
            print("There are no paired bluetooth devices")
            return None, None, None
        for device in paired_devices:
            print "Interface paired device", dir(device), device.describeContents(), device.getAddress(), device.toString()
            print "I see", repr(device.getName())
            if True or device.getName() == name:
                socket = device.createRfcommSocketToServiceRecord(
                    UUID.fromString("00001101-0000-1000-8000-00805F9B34FB"))
                socket.connect()
                sleep(2)
                reader = InputStreamReader(socket.getInputStream(), 'US-ASCII')
                recv_stream = BufferedReader(reader)
                send_stream = socket.getOutputStream()
                break
        return socket, recv_stream, send_stream
    
    def build_settings(self, settings):
        jsondata = """[
        { "type": "title",
          "title": "Grid settings" },
        { "type": "numeric",
          "title": "Columns",
          "desc": "Number of columns in the grid",
          "section": "sheet",
          "key": "cols" },
        { "type": "numeric",
          "title": "Rows",
          "desc": "Number of rows in the grid",
          "section": "sheet",
          "key": "rows" },
        { "type": "numeric",
          "title": "Cell width",
          "desc": "Default cell width in millimeters",
          "section": "cell",
          "key": "width" },
        { "type": "numeric",
          "title": "Cell height",
          "desc": "Default cell height in millimeters",
          "section": "cell",
          "key": "height" },
        { "type": "title",
          "title": "GCode settings" },
        { "type": "numeric",
          "title": "Height flying",
          "desc": "Height when moving around (in mm)",
          "section": "gcode",
          "key": "z_flying" },
        { "type": "numeric",
          "title": "Flying feed rate",
          "desc": "Feed rate when flying in mm/min",
          "section": "gcode",
          "key": "feed_flying" },
        { "type": "numeric",
          "title": "Height milling",
          "desc": "Height when milling (in mm)",
          "section": "gcode",
          "key": "z_cutting" },
        { "type": "numeric",
          "title": "Milling feed rate",
          "desc": "Feed rate when milling in mm/min",
          "section": "gcode",
          "key": "feed_cutting" },
        { "type": "numeric",
          "title": "Heater clearance",
          "desc": "Clearance for heaters in mm",
          "section": "gcode",
          "key": "heater_clearance" },
        { "type": "numeric",
          "title": "Height drilling",
          "desc": "Default height when drilling holes (in mm)",
          "section": "gcode",
          "key": "z_drilling" },
        { "type": "numeric",
          "title": "Height pocketing",
          "desc": "Default height for pockets in (in mm)",
          "section": "gcode",
          "key": "z_pocket" },
        { "type": "numeric",
          "title": "X Backslash",
          "desc": "Backslash in the X axis for PCB isolation, given in mm",
          "section": "gcode",
          "key": "x_backslash" },
        { "type": "numeric",
          "title": "Y Backslash",
          "desc": "Backslash in the X axis for PCB isolation, given in mm",
          "section": "gcode",
          "key": "y_backslash" },
        { "type": "numeric",
          "title": "X Offset",
          "desc": "Starting X position in mm",
          "section": "gcode",
          "key": "x_offset" },
        { "type": "numeric",
          "title": "Y Offset",
          "desc": "Starting Y position in mm",
          "section": "gcode",
          "key": "y_offset" },
        { "type": "numeric",
          "title": "Z Offset",
          "desc": "Starting Z position in mm",
          "section": "gcode",
          "key": "z_offset" }
        ]"""
        settings.add_json_panel('PCB Maker',
            self.config, data=jsondata)

    def on_config_change(self, config, section, key, value):
        if config is self.config:
            token = (section, key)
            if token == ('sheet', 'cols'):
                #print('Our cols have been changed to', value)
                #self.root.ids.sheet.clear_widgets()
                self.root.ids.sheet.cols = int(value)
                self.root.ids.sheet.resize_sheet(self.root.ids.sheet.cols, self.root.ids.sheet.rows)
            elif token == ('sheet', 'rows'):                                
                #print('Our rows have been changed to', value)
                #self.root.ids.sheet.clear_widgets()
                self.root.ids.sheet.rows = int(value)
                self.root.ids.sheet.resize_sheet(self.root.ids.sheet.cols, self.root.ids.sheet.rows)
            elif token == ('cell', 'width'):
                self.root.ids.sheet.default_width = float(value)
                self.root.ids.sheet.set_cells_width(float(value))
            elif token == ('cell', 'height'):
                self.root.ids.sheet.default_height = float(value)
                self.root.ids.sheet.set_cells_height(float(value))


    def on_start(self):
        pass
        #if platform=='linux':
        #    self.profile = cProfile.Profile()
        #    self.profile.enable()

    def on_pause(self):
        print "Pause..."
        return True

    def on_stop(self):
        pass
        #if platform=='linux':
        #    self.profile.disable()
        #    self.profile.dump_stats('myapp.profile')
        print "Stopping..."
        return True

    def on_resume(self):
        print "Resume..."
        pass

if __name__ == '__main__':
    PCBMakerApp().run()
    
