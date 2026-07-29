import os
from Range import *
from collections import OrderedDict
import bgui

class MainMenu(types.KX_PythonComponent):
    args = OrderedDict({
    })
    def start(self, args):
        self.scene = logic.getCurrentScene()
        self.cube = self.scene.objects["Cube"]
        self.gui_system = bgui.BGUISystem()
        
        script_dir = os.path.dirname(__file__)
        xml_path = os.path.join(script_dir, 'interface.xml')
        
        self.widgets = bgui.load_ui_from_xml(xml_path, self.gui_system.main_frame)
        self.slider = self.widgets.get("volume")
        self.input_field = self.widgets.get("user_input")
        
        def on_slider_change(value):
            scale = max(0.1, value / 50.0)
            self.cube.localScale = [scale, scale, scale]
        
        if self.slider:
            self.slider.set_on_value_change(on_slider_change)
            
        if self.input_field:
            def on_enter(widget):
                print(f"[BGUI TEST] Texto confirmado no TextInput (Enter): '{widget.text}'")
            self.input_field.on_enter_key = on_enter

    def update(self):
        self.gui_system.run()

        
