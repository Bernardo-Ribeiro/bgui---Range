"""

This module defines the following constants:

*InputText options*
	* BGUI_INPUT_NONE = 0
	* BGUI_INPUT_SELECT_ALL = 1

	* BGUI_INPUT_DEFAULT = BGUI_INPUT_NONE
"""

from .widget import Widget, WeakMethod, BGUI_DEFAULT, BGUI_CENTERY, \
	BGUI_NO_FOCUS, BGUI_MOUSE_ACTIVE, BGUI_MOUSE_CLICK, BGUI_MOUSE_RELEASE, \
	BGUI_NO_NORMALIZE
from .label import Label
from .frame import Frame

try:
	from Range import events
	BACKSPACEKEY = events.BACKSPACEKEY
	DELKEY = events.DELKEY
	LEFTARROWKEY = events.LEFTARROWKEY
	RIGHTARROWKEY = events.RIGHTARROWKEY
	ENTERKEY = getattr(events, 'ENTERKEY', getattr(events, 'RETKEY', 220))
	RETKEY = getattr(events, 'RETKEY', ENTERKEY)
	PADENTER = events.PADENTER
except ImportError:
	BACKSPACEKEY = 223
	DELKEY = 224
	LEFTARROWKEY = 137
	RIGHTARROWKEY = 139
	ENTERKEY = RETKEY = 220
	PADENTER = 163

import time


# InputText options
BGUI_INPUT_NONE = 0
BGUI_INPUT_SELECT_ALL = 1

BGUI_INPUT_DEFAULT = BGUI_INPUT_NONE


class TextInput(Widget):
	"""Widget for getting text input"""
	theme_section = 'TextInput'
	theme_options = {
				'TextColor': (1, 1, 1, 1),
				'FrameColor': (0, 0, 0, 0),
				'BorderSize': 0,
				'BorderColor': (0, 0, 0, 0),
				'HighlightColor': (0.6, 0.6, 0.6, 0.5),
				'InactiveTextColor': (1, 1, 1, 1),
				'InactiveFrameColor': (0, 0, 0, 0),
				'InactiveBorderSize': 0,
				'InactiveBorderColor': (0, 0, 0, 0),
				'InactiveHighlightColor': (0.6, 0.6, 0.6, 0.5),
				'LabelSubTheme': '',
				}

	def __init__(self, parent, name=None, text="", prefix="", font=None, pt_size=None, color=None,
					aspect=None, size=[1, 1], pos=[0, 0], sub_theme='', input_options=BGUI_INPUT_DEFAULT, options=BGUI_DEFAULT):
		"""
		:param parent: the widget's parent
		:param name: the name of the widget
		:param text: the text to display (this can be changed later via the text property)
		:param prefix: prefix text displayed before user input, cannot be edited by user (this can be changed later via the prefix property)
		:param font: the font to use
		:param pt_size: the point size of the text to draw
		:param color: color of the font for this widget
		:param aspect: constrain the widget size to a specified aspect ratio
		:param size: a tuple containing the width and height
		:param pos: a tuple containing the x and y position
		:param sub_theme: name of a sub_theme defined in the theme file (similar to CSS classes)
		:param options: various other options

		"""

		Widget.__init__(self, parent, name, aspect, size, pos, sub_theme, options)

		self.text_prefix = prefix
		self.pos = len(text)
		self.input_options = input_options
		self.colors = {}

		#create widgets
		self.frame = Frame(self, size=[1, 1], options=BGUI_NO_FOCUS | BGUI_DEFAULT | BGUI_CENTERY)
		self.highlight = Frame(self, size=[0, 0], border=0, options=BGUI_NO_FOCUS | BGUI_CENTERY | BGUI_NO_NORMALIZE)
		self.highlight.colors = [[0.0, 0.0, 0.0, 0.0]] * 4
		self.cursor = Frame(self, size=[1, 1], border=0, options=BGUI_NO_FOCUS | BGUI_CENTERY | BGUI_NO_NORMALIZE)
		self.label = Label(self, text=text, font=font, pt_size=pt_size, sub_theme=self.theme['LabelSubTheme'], options=BGUI_NO_FOCUS | BGUI_DEFAULT | BGUI_CENTERY, center_text=False)



		#Color and setting initialization
		self.colormode = 0

		theme = self.theme

		self.colors["text"] = [None, None]
		self.colors["text"][0] = theme['InactiveTextColor']
		self.colors["text"][1] = theme['TextColor']

		self.colors["frame"] = [None, None]
		self.colors["frame"][0] = theme['InactiveFrameColor']
		self.colors["frame"][1] = theme['FrameColor']

		self.colors["border"] = [None, None]
		self.colors["border"][0] = theme['InactiveBorderColor']
		self.colors["border"][1] = theme['BorderColor']

		self.colors["highlight"] = [None, None]
		self.colors["highlight"][0] = theme['HighlightColor']
		self.colors["highlight"][1] = theme['HighlightColor']

		self.border_size = [None, None]
		self.border_size[0] = theme['InactiveBorderSize']
		self.border_size[1] = theme['BorderSize']

		self.swapcolors(0)

		# Standardized pixel padding
		self.pad_x = 10
		px = self.pad_x / self.size[0] if self.size[0] > 0 else 0.02
		self.label.position = [px, 0]
		self.system.textlib.size(self.label.fontid, self.label.pt_size, 72)
		self.fd = self.system.textlib.dimensions(self.label.fontid, self.text_prefix)[0] if self.text_prefix else 0


		self.frame.size = [1, 1]
		self.frame.position = [0, 0]

		self.slice = [len(text), len(text)]
		self.slice_direction = 0
		self.mouse_slice_start = 0
		self.mouse_slice_end = 0
		#create the char width list
		self._is_placeholder = True if text else False
		self._update_char_widths()

		#initial call to update_selection
		self.selection_refresh = 1
		self.just_activated = 0
		self._active = 0  # internal active state to avoid confusion from parent active chain

		#blinking cursor
		self.time = time.time()

		#double/triple click functionality
		self.click_counter = 0
		self.single_click_time = 0.0
		self.double_click_time = 0.0

		# On Enter callback
		self._on_enter_key = None

	@property
	def text(self):
		return self.label.text

	@text.setter
	def text(self, value):
		#setter intended for external access, internal changes can just change self.label.text
		self.label.text = value
		self._update_char_widths()
		self.slice = [0, 0]
		self.update_selection()

	@property
	def prefix(self):
		return self.text_prefix

	@prefix.setter
	def prefix(self, value):
		self.text_prefix = value
		self.system.textlib.size(self.label.fontid, self.label.pt_size, 72)
		self.fd = self.system.textlib.dimensions(self.label.fontid, value)[0] if value else 0
		self.update_selection()

	@property
	def on_enter_key(self):
		"""A callback for when the enter key is pressed while the TextInput has focus"""
		return self._on_enter_key

	@on_enter_key.setter
	def on_enter_key(self, value):
		self._on_enter_key = WeakMethod(value)

	#utility functions
	def _update_char_widths(self):
		self.system.textlib.size(self.label.fontid, self.label.pt_size, 72)
		self.char_widths = []
		for char in self.text:
			self.char_widths.append(self.system.textlib.dimensions(self.label.fontid, char * 20)[0] / 20)

	def select_all(self):
		"""Change the selection to include all of the text"""
		self.slice = [0, len(self.text)]
		self.update_selection()

	def select_none(self):
		"""Change the selection to include none of the text"""
		self.slice = [0, 0]
		self.update_selection()

	#Activation Code
	def activate(self):
		if self.frozen:
			return
		self.system.focused_widget = self
		self.swapcolors(1)
		self.colormode = 1
		# Clear placeholder text on first activation
		if getattr(self, '_is_placeholder', False):
			self.label.text = ""
			self._update_char_widths()
			self._is_placeholder = False
			self.slice = [0, 0]
		else:
			self.slice = [len(self.text), len(self.text)]

		self.just_activated = 1
		self._active = 1

	def deactivate(self):
		self.system.focused_widget = self.system
		self.swapcolors(0)
		self.colormode = 0
		self.just_activated = 0
		self._active = 0

	def swapcolors(self, state=0):  # 0 inactive 1 active

		self.frame.colors = [self.colors["frame"][state]] * 4
		self.frame.border = self.border_size[state]
		self.frame.border_color = self.colors["border"][state]
		self.label.color = self.colors["text"][state]

		if state == 0:
			self.cursor.colors = [[0.0, 0.0, 0.0, 0.0]] * 4
			self.highlight.colors = [[0.0, 0.0, 0.0, 0.0]] * 4
		else:
			self.cursor.colors = [self.colors["text"][state]] * 4
			if abs(self.slice[0] - self.slice[1]) > 0:
				self.highlight.colors = [self.colors["highlight"][state]] * 4
			else:
				self.highlight.colors = [[0.0, 0.0, 0.0, 0.0]] * 4

	#Selection Code
	def update_selection(self):
		self.system.textlib.size(self.label.fontid, self.label.pt_size, 72)
		fd = self.system.textlib.dimensions(self.label.fontid, "Egj/|^,")
		font_h = fd[1]
		pad_x = getattr(self, 'pad_x', 10)

		prefix_w = self.system.textlib.dimensions(self.label.fontid, self.text_prefix)[0] if self.text_prefix else 0
		slice_left_w = self.system.textlib.dimensions(self.label.fontid, self.text[:self.slice[0]])[0] if self.slice[0] > 0 else 0
		slice_right_w = self.system.textlib.dimensions(self.label.fontid, self.text[:self.slice[1]])[0] if self.slice[1] > 0 else 0

		left = pad_x + prefix_w + slice_left_w
		right = pad_x + prefix_w + slice_right_w

		slice_len = abs(self.slice[0] - self.slice[1])
		if slice_len > 0:
			self.highlight.position = [left, 0]
			self.highlight.size = [right - left, font_h * 1.1]
			self.highlight.colors = [self.colors["highlight"][1]] * 4
		else:
			self.highlight.size = [0, 0]
			self.highlight.colors = [[0.0, 0.0, 0.0, 0.0]] * 4

		cursor_x = left if self.slice_direction in [0, -1] else right
		self.cursor.position = [cursor_x, 0]
		self.cursor.size = [2, font_h * 1.1]


	def find_mouse_slice(self, pos):
		cmc = self.calc_mouse_cursor(pos)
		mss = self.mouse_slice_start
		self.mouse_slice_end = cmc

		if cmc < mss:
			self.slice_direction = -1
			self.slice = [self.mouse_slice_end, self.mouse_slice_start]
		elif cmc > mss:
			self.slice_direction = 1
			self.slice = [self.mouse_slice_start, self.mouse_slice_end]
		else:
			self.slice_direction = 0
			self.slice = [self.mouse_slice_start, self.mouse_slice_start]
		self.selection_refresh = 1

	def calc_mouse_cursor(self, pos):
		self.system.textlib.size(self.label.fontid, self.label.pt_size, 72)
		pad_x = getattr(self, 'pad_x', 10)
		prefix_w = self.system.textlib.dimensions(self.label.fontid, self.text_prefix)[0] if self.text_prefix else 0
		adj_pos = pos[0] - (self.position[0] + pad_x + prefix_w)
		find_slice = 0
		i = 0
		for entry in self.char_widths:
			if find_slice + entry > adj_pos:
				if abs((find_slice + entry) - adj_pos) >= abs(adj_pos - find_slice):
					return i
				else:
					return i + 1
			else:
				find_slice += entry
			i += 1

		self.time = time.time() - 0.501
		return i


	def _handle_mouse(self, pos, event):
		"""Extend function's behaviour by providing focus to unfrozen inactive TextInput,
		swapping out colors.
		"""
		if self.frozen:
			return

		if event == BGUI_MOUSE_CLICK:

			self.mouse_slice_start = self.calc_mouse_cursor(pos)

			if not self._active:
				self.activate()

			if not self.input_options & BGUI_INPUT_SELECT_ALL:
				self.find_mouse_slice(pos)

		elif event == BGUI_MOUSE_ACTIVE:
			if not self.just_activated or self.just_activated and not self.input_options & BGUI_INPUT_SELECT_ALL:
				self.find_mouse_slice(pos)

		if event == BGUI_MOUSE_RELEASE:

			self.selection_refresh = 1
			if self.slice[0] == self.slice[1]:
				self.slice_direction = 0
			self.just_activated = 0

			#work out single / double / triple clicks
			if self.click_counter == 0:
				self.single_click_time = time.time()
				self.click_counter = 1
			elif self.click_counter == 1:
				if time.time() - self.single_click_time < .2:
					self.click_counter = 2
					self.double_click_time = time.time()
					words = self.text.split(" ")
					i = 0
					for entry in words:
						if self.slice[0] < i + len(entry):
							self.slice = [i, i + len(entry) + 1]
							break
						i += len(entry) + 1
				else:
					self.click_counter = 1
					self.single_click_time = time.time()
			elif self.click_counter == 2:
				if time.time() - self.double_click_time < .2:
					self.click_counter = 3
					self.slice = [0, len(self.text)]
					self.slice_direction = -1
				else:
					self.click_counter = 1
					self.single_click_time = time.time()
			elif self.click_counter == 3:
				self.single_click_time = time.time()
				self.click_counter = 1

			self.time = time.time()

		Widget._handle_mouse(self, pos, event)

	def _handle_text(self, text):
		"""Handle character input passed from Range Engine native keyboard.text"""
		if self != self.system.focused_widget:
			return

		# Clear placeholder if active
		if getattr(self, '_is_placeholder', False):
			self.label.text = ""
			self._update_char_widths()
			self._is_placeholder = False
			self.slice = [0, 0]

		for char in text:
			if char in ('\r', '\n', '\t'):
				continue
			if char in ('\b', '\x08'):
				self._handle_key(BACKSPACEKEY, False)
				continue
			self.label.text = self.text[:self.slice[0]] + char + self.text[self.slice[1]:]
			char_w = self.system.textlib.dimensions(self.label.fontid, char * 20)[0] / 20
			self.char_widths = self.char_widths[:self.slice[0]] + [char_w] + self.char_widths[self.slice[1]:]
			self.slice = [self.slice[0] + 1, self.slice[0] + 1]
			self.slice_direction = 0

		self.selection_refresh = 1
		self.time = time.time()

	def _handle_key(self, key, is_shifted):
		"""Handle control keys (navigation, backspace, delete, enter)"""
		if self != self.system.focused_widget:
			return

		# Try char to int conversion if key is string representation of int
		try:
			key = int(key)
		except:
			pass

		slice_len = abs(self.slice[0] - self.slice[1])

		key_str = str(key).upper()
		is_backspace = (key == BACKSPACEKEY) or (key in (8, 223)) or ('BACKSPACE' in key_str)
		is_delete = (key == DELKEY) or (key in (127, 224)) or ('DELETE' in key_str) or ('DEL' in key_str)
		is_space = (key in (32, getattr(events, 'SPACEKEY', 32))) or ('SPACE' in key_str)
		is_left = (key == LEFTARROWKEY) or (key in (137, 149, 203, 276)) or ('LEFT' in key_str)
		is_right = (key == RIGHTARROWKEY) or (key in (139, 151, 205, 275)) or ('RIGHT' in key_str)
		is_home = (key in (167, 278)) or ('HOME' in key_str)
		is_end = (key in (170, 279)) or ('END' in key_str)

		if is_space:
			self._handle_text(' ')
		elif is_backspace:

			if slice_len != 0:
				self.label.text = self.text[:self.slice[0]] + self.text[self.slice[1]:]
				self.char_widths = self.char_widths[:self.slice[0]] + self.char_widths[self.slice[1]:]
				self.slice = [self.slice[0], self.slice[0]]
			elif self.slice[0] > 0:
				self.label.text = self.text[:self.slice[0] - 1] + self.text[self.slice[1]:]
				self.char_widths = self.char_widths[:self.slice[0] - 1] + self.char_widths[self.slice[1]:]
				self.slice = [self.slice[0] - 1, self.slice[0] - 1]
		elif is_delete:
			if slice_len != 0:
				self.label.text = self.text[:self.slice[0]] + self.text[self.slice[1]:]
				self.char_widths = self.char_widths[:self.slice[0]] + self.char_widths[self.slice[1]:]
				self.slice = [self.slice[0], self.slice[0]]
			elif self.slice[1] < len(self.text):
				self.label.text = self.text[:self.slice[0]] + self.text[self.slice[1] + 1:]
				self.char_widths = self.char_widths[:self.slice[0]] + self.char_widths[self.slice[1] + 1:]

		elif is_left:
			if is_shifted:
				if self.slice_direction in (-1, 0) and self.slice[0] > 0:
					self.slice = [self.slice[0] - 1, self.slice[1]]
					self.slice_direction = -1
				elif self.slice_direction == 1:
					self.slice = [self.slice[0], self.slice[1] - 1]
					if self.slice[0] == self.slice[1]:
						self.slice_direction = 0
			else:
				if slice_len > 0:
					self.slice = [self.slice[0], self.slice[0]]
				elif self.slice[0] > 0:
					self.slice = [self.slice[0] - 1, self.slice[0] - 1]
				self.slice_direction = 0

		elif is_right:
			if is_shifted:
				if self.slice_direction in (1, 0) and self.slice[1] < len(self.text):
					self.slice = [self.slice[0], self.slice[1] + 1]
					self.slice_direction = 1
				elif self.slice_direction == -1:
					self.slice = [self.slice[0] + 1, self.slice[1]]
					if self.slice[0] == self.slice[1]:
						self.slice_direction = 0
			else:
				if slice_len > 0:
					self.slice = [self.slice[1], self.slice[1]]
				elif self.slice[1] < len(self.text):
					self.slice = [self.slice[1] + 1, self.slice[1] + 1]
				self.slice_direction = 0

		elif is_home:
			self.slice = [0, 0]
			self.slice_direction = 0

		elif is_end:
			self.slice = [len(self.text), len(self.text)]
			self.slice_direction = 0

		elif key in (ENTERKEY, PADENTER, RETKEY):
			if self.on_enter_key:
				self.on_enter_key(self)

		# Fallback for manual string key injection
		elif isinstance(key, str) and len(key) == 1:
			self._handle_text(key)

		# Update selection widgets immediately
		self.selection_refresh = 1
		self.update_selection()
		self.time = time.time()




	def _draw(self):
		if self == self.system.focused_widget and self._active == 0:
			self.activate()

		if self.colormode == 1 and self.system.focused_widget != self:
			self._active = 0
			self.swapcolors(0)
			self.colormode = 0

		# Ensure selection/cursor positions are updated BEFORE drawing children
		if self.selection_refresh == 1:
			self.update_selection()
			self.selection_refresh = 0

		# Handle blinking cursor color BEFORE drawing
		if self.slice[0] - self.slice[1] == 0 and self._active:
			if time.time() - self.time > 1.0:
				self.time = time.time()
			elif time.time() - self.time > 0.5:
				self.cursor.colors = [[0.0, 0.0, 0.0, 0.0]] * 4
			else:
				self.cursor.colors = [self.colors["text"][1]] * 4
		else:
			self.cursor.colors = [[0.0, 0.0, 0.0, 0.0]] * 4

		temp = self.text
		self.label.text = self.text_prefix + temp

		# Now draw children ONCE with up-to-date position and color
		Widget._draw(self)

		self.label.text = temp

