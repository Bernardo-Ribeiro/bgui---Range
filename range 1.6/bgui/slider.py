#Slider still doesn't work 100%

from .gl_utils import *
from .widget import Widget, BGUI_DEFAULT, BGUI_NO_NORMALIZE, BGUI_MOUSE_CLICK, BGUI_MOUSE_RELEASE, BGUI_MOUSE_ACTIVE
from Range import *

class Slider(Widget):
    """Widget to create a slider control"""
    
    theme_section = 'Slider'
    theme_options = {
        'FillColor1': (0.0, 0.42, 0.02, 1.0),
        'FillColor2': (0.0, 0.42, 0.02, 1.0),
        'FillColor3': (0.0, 0.42, 0.02, 1.0),
        'FillColor4': (0.0, 0.42, 0.02, 1.0),
        'BGColor1': (0, 0, 0, 1),
        'BGColor2': (0, 0, 0, 1),
        'BGColor3': (0, 0, 0, 1),
        'BGColor4': (0, 0, 0, 1),
        'BorderSize': 1,
        'BorderColor': (0, 0, 0, 1),
        'HoverColor': (0.3, 0.3, 0.3, 0.8),
        'ActiveColor': (0.4, 0.4, 0.4, 0.8)
    }
    
    def _to_color_tuple(self, value):
        """Converts a value to a color tuple (R, G, B, A)."""
        if isinstance(value, str):
            # Value is a string, e.g., "(0.1, 0.2, 0.3, 0.4)" or "0.1,0.2,0.3,0.4"
            try:
                evaluated = eval(value)
                if isinstance(evaluated, (list, tuple)):
                    # Ensure all elements are numbers and convert to float
                    processed = [float(x) for x in evaluated]
                    # Ensure 4 components (RGBA), add alpha=1.0 if it's RGB
                    if len(processed) == 3:
                        processed.append(1.0)
                    return tuple(processed) if len(processed) == 4 else (1.0, 0.0, 1.0, 1.0) # Magenta error
                # If eval result is not a list/tuple (e.g. a single number), it's an error for a color
                return (1.0, 0.0, 1.0, 1.0) # Magenta error color
            except:
                # Eval failed or other error
                return (1.0, 0.0, 1.0, 1.0) # Magenta error color
        
        elif isinstance(value, (list, tuple)):
            # Value is already a list or tuple.
            # It could be correctly formatted or a list of strings needing conversion.
            try:
                processed_color = []
                for item in value:
                    if isinstance(item, (int, float)):
                        processed_color.append(float(item))
                    elif isinstance(item, str):
                        # Clean string: remove leading/trailing spaces and parentheses
                        cleaned_item_str = item.strip().strip('()')
                        processed_color.append(float(cleaned_item_str))
                    else: # Unexpected type within the list/tuple
                        raise ValueError("Invalid item type in color sequence")
                
                if len(processed_color) == 3: processed_color.append(1.0) # Add alpha if RGB
                return tuple(processed_color) if len(processed_color) == 4 else (1.0,0.0,1.0,1.0) # Magenta error
            except (ValueError, TypeError): return (1.0, 0.0, 1.0, 1.0) # Magenta error color
        
        # If value is not a string, list, or tuple, or other cases
        return (1.0, 0.0, 1.0, 1.0) # Magenta error color

    def __init__(self, parent, name="", value=0.0, min_value=0.0, max_value=1.0, size=[100, 20], pos=[0, 0], sub_theme='', options=BGUI_DEFAULT, fill_color=None):
        # Initialize Slider-specific attributes
        self._min_value = min_value
        self._max_value = max_value
        # Initialize _value placeholder; actual value set via property later
        # to ensure setter logic (clamping, callback) is invoked.
        self._value = 0.0 
        self._on_value_change = None
        self._dragging = False
        self._mouse_over = False # Slider's own mouse over tracking

        # Call Widget constructor ONCE with correct arguments.
        # Widget.__init__ handles theme loading (self.theme) and position/size normalization.
        # Slider does not have an 'aspect' param, so pass None.
        super().__init__(parent, name, aspect=None, size=size, pos=pos, sub_theme=sub_theme, options=options)

        # Now self.theme is populated by super().__init__.
        # Load and process Slider-specific theme options.
        theme = self.theme
        self.fill_colors = [
            self._to_color_tuple(theme['FillColor1']),
            self._to_color_tuple(theme['FillColor2']),
            self._to_color_tuple(theme['FillColor3']),
            self._to_color_tuple(theme['FillColor4'])
        ]

        self.bg_colors = [
            self._to_color_tuple(theme['BGColor1']),
            self._to_color_tuple(theme['BGColor2']),
            self._to_color_tuple(theme['BGColor3']),
            self._to_color_tuple(theme['BGColor4'])
        ]

        self.border_color = self._to_color_tuple(theme['BorderColor'])
        # Process BorderSize safely, using the original logic if it's preferred
        self.border = theme['BorderSize'] if isinstance(theme['BorderSize'], int) else int(eval(str(theme['BorderSize'])))
        self.hover_color = self._to_color_tuple(theme['HoverColor'])
        self.active_color = self._to_color_tuple(theme['ActiveColor'])

        # Set the initial value using the property to ensure clamping and trigger callbacks if any
        self.value = value
        
        if fill_color:
            self.fill_colors = [tuple(fill_color)] * 4
        
    @property
    def value(self):
        return self._value
        
    @value.setter
    def value(self, value):
        old_value = self._value
        self._value = max(self._min_value, min(self._max_value, value))
        if self._value != old_value and self._on_value_change:
            self._on_value_change(self._value)
            
    def set_on_value_change(self, callback):
        self._on_value_change = callback
        
    def _draw(self):        
        # Enable alpha blending
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Enable polygon offset
        glEnable(GL_POLYGON_OFFSET_FILL)
        glPolygonOffset(1.0, 1.0)
        
        # Calculate the slider position
        value_range = self._max_value - self._min_value
        if value_range <= 0:
             percent = 0.0
        else:
            percent = (self._value - self._min_value) / value_range

        mid_x = self.gl_position[0][0] + (self.gl_position[1][0] - self.gl_position[0][0]) * percent

        # Set fill colors based on slider state
        current_fill_colors = list(self.fill_colors) # Start with default colors (make a copy)

        if self._dragging:
            current_fill_colors = [self.active_color] * 4
        elif self._hover: # Use the hover from the Widget base
            current_fill_colors = [self.hover_color] * 4
        
        # Draw fill
        glBegin(GL_QUADS)
        glColor4f(current_fill_colors[0][0], current_fill_colors[0][1], current_fill_colors[0][2], current_fill_colors[0][3])
        glVertex2f(self.gl_position[0][0], self.gl_position[0][1])
        
        glColor4f(current_fill_colors[1][0], current_fill_colors[1][1], current_fill_colors[1][2], current_fill_colors[1][3])
        glVertex2f(mid_x, self.gl_position[1][1])
        
        glColor4f(current_fill_colors[2][0], current_fill_colors[2][1], current_fill_colors[2][2], current_fill_colors[2][3])
        glVertex2f(mid_x, self.gl_position[2][1])
        
        glColor4f(current_fill_colors[3][0], current_fill_colors[3][1], current_fill_colors[3][2], current_fill_colors[3][3])
        glVertex2f(self.gl_position[3][0], self.gl_position[3][1])
        glEnd()
        
        # Draw background
        glBegin(GL_QUADS)
        glColor4f(self.bg_colors[0][0], self.bg_colors[0][1], self.bg_colors[0][2], self.bg_colors[0][3])
        glVertex2f(mid_x, self.gl_position[0][1])
        
        glColor4f(self.bg_colors[1][0], self.bg_colors[1][1], self.bg_colors[1][2], self.bg_colors[1][3])
        glVertex2f(self.gl_position[1][0], self.gl_position[1][1])
        
        glColor4f(self.bg_colors[2][0], self.bg_colors[2][1], self.bg_colors[2][2], self.bg_colors[2][3])
        glVertex2f(self.gl_position[2][0], self.gl_position[2][1])
        
        glColor4f(self.bg_colors[3][0], self.bg_colors[3][1], self.bg_colors[3][2], self.bg_colors[3][3])
        glVertex2f(mid_x, self.gl_position[3][1])
        glEnd()
        
        # Draw border
        glDisable(GL_POLYGON_OFFSET_FILL)
        
        r, g, b, a = self.border_color
        glColor4f(r, g, b, a)
        glPolygonMode(GL_FRONT, GL_LINE)
        glLineWidth(self.border)
        
        glBegin(GL_QUADS)
        for i in range(4):
            glVertex2f(self.gl_position[i][0], self.gl_position[i][1])
        glEnd()
        
        glPolygonMode(GL_FRONT, GL_FILL)
        
        Widget._draw(self)
        
    def _handle_click(self):
        self._update_value_from_mouse(self.cursor_pos)

    def _handle_active(self):
        if not self._dragging:
            self._dragging = True
        self._update_value_from_mouse(self.cursor_pos)
        self._dragging = False


    def _update_value_from_mouse(self, mouse_pos):
        # The slider's position on the X axis
        slider_x_start = self.gl_position[0][0]
        slider_x_end = self.gl_position[1][0]
        slider_width = slider_x_end - slider_x_start

        if slider_width <= 0:
            relative_x = 0.0
        else:
            # Calculate the mouse position as a percentage within the slider
            mouse_offset = mouse_pos[0] - slider_x_start
            relative_x = mouse_offset / slider_width
        
        # Ensure the percentage is between 0 and 1
        relative_x = max(0.0, min(1.0, relative_x))
        
        # Calculate the new value
        new_value = self._min_value + relative_x * (self._max_value - self._min_value)
        self.value = new_value

    def _is_inside(self, pos):
        is_inside = (self.gl_position[0][0] <= pos[0] <= self.gl_position[1][0] and
                     self.gl_position[0][1] <= pos[1] <= self.gl_position[2][1])
        return is_inside

    def _update_anims(self):
        """Updates the widget's animations"""
        self.anims[:] = [i for i in self.anims if i.update()]