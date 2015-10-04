#!/usr/bin/python

import os
#import cProfile
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.properties import NumericProperty, ListProperty, BooleanProperty, ObjectProperty, StringProperty
from kivy.uix.popup import Popup

from lib.sheet import Sheet
from lib.gcode import GCodeExport

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

class CellWidget(Widget):
    has_hcut = BooleanProperty(False)
    has_vcut = BooleanProperty(False)
    celltype = StringProperty('clear')

    def __init__(self, sheet, col, row, **kwargs):
        super(CellWidget, self).__init__(**kwargs)
        self.sheet = sheet
        self.col = col
        self.row = row
    
    def get_celltype_resource(self, value):
        return value.replace('/ Diagonal', 'slash').replace('\\ Diagonal', 'backslash').lower()
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            if App.get_running_app().root.repeat_mode.state == 'down':
                self.configure_cell(App.get_running_app().cellform)
                return True
            form = App.get_running_app().cellform
            self.show_form(form)
            return True
        return super(CellWidget, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        #print "Moving!"
        return super(CellWidget, self).on_touch_move(touch)

    def show_form(self, form):
        form.title="Editing cell ({}, {}) properties".format(self.col, self.row)
        form.ids['hcut'].state = 'down' if self.sheet.get_cut(self.col, self.row, axis=self.sheet.AXIS_HORIZONTAL) else 'normal'
        form.ids['vcut'].state = 'down' if self.sheet.get_cut(self.col, self.row, axis=self.sheet.AXIS_VERTICAL) else 'normal'
        form.ids['celltype'].text = self.sheet.get_celltype_text(self.sheet.get_cell(self.col, self.row), complete=True)
        form.ids['column_width'].text = unicode(self.sheet.get_cell_width(self.col))
        form.ids['row_height'].text = unicode(self.sheet.get_cell_height(self.row))
        form.bind(on_dismiss=self.configure_cell)
        form.open()
        form.is_open = True
    
    def configure_cell(self, form):        
        self.has_hcut = form.ids['hcut'].state == 'down'
        self.has_vcut = form.ids['vcut'].state == 'down'
        celltype_text = form.ids['celltype'].text
        self.celltype = self.get_celltype_resource(celltype_text)
        column_width = float(form.ids['column_width'].text)
        row_height = float(form.ids['row_height'].text)
        self.sheet.set_cut(self.col, self.row, self.has_hcut, axis=self.sheet.AXIS_HORIZONTAL)
        self.sheet.set_cut(self.col, self.row, self.has_vcut, axis=self.sheet.AXIS_VERTICAL)
        self.sheet.set_cell(self.col, self.row, self.sheet.get_celltype_id(celltype_text))
        self.sheet.set_cell_width(self.col, column_width)
        self.sheet.set_cell_height(self.row, row_height)
        form.unbind(on_dismiss=self.configure_cell)


class CellForm(Popup):
    pass

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


    def export_sheet(self, options, path, filename):
        gcode = GCodeExport()
        data = gcode.from_sheet(self.sheet)
        path = App.get_running_app().user_data_dir
        with open(os.path.join(path, filename), 'w') as f:
            f.write("{}\n".format(data))
        #gcode.send(data)
        App.get_running_app().root.current = 'main'


class PCBMakerApp(App):

    cellform = ObjectProperty(None)
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

    def build(self):
        self.cellform = CellForm()

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
          "key": "height" }
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
        #self.profile = cProfile.Profile()
        #self.profile.enable()
        pass

    def on_pause(self):
        print "Pause..."
        return True

    def on_stop(self):
        #self.profile.disable()
        #self.profile.dump_stats('myapp.profile')
        print "Stopping..."
        return True

    def on_resume(self):
        print "Resume..."
        pass

if __name__ == '__main__':
    PCBMakerApp().run()
    
