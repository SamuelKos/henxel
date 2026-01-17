############ Stucture briefing Begin

# Stucture briefing
# TODO
# Imports
# Module Utilities
# Other Classes

####################
# Class Editor Begin
#
# Constants
# Init etc.
# Bindings
# Linenumbers
# Tab Related
# Configuration Related
# Syntax highlight
# Theme Related
# Run file Related
# Select and move
# Overrides
# Utilities
# Gotoline etc
# Save and Load
# Bookmarks and Help
# Indent and Comment
# Elide
# Search
# Replace
#
# Class Editor End
############ Stucture briefing End
############ TODO Begin
#
# Get repo from:
#
# 	https://github.com/SamuelKos/henxel
#
# Todo is located at, counted from the root of repo:
#
#	dev/todo.txt
#
############ TODO End
############ Imports Begin

# From standard library
import tkinter.messagebox
import tkinter.font
import tkinter
import traceback
import pathlib
import inspect
import json
import copy
import ast

# Used in init
import importlib.resources
import importlib.metadata
import sys

# Used in syntax highlight
import tokenize
import keyword

# For executing edited file in the same env than this editor, which is nice:
# It means you have your installed dependencies available. By self.run()
import subprocess

# For making paste to work in Windows
import threading

# Only to sometimes get console, used in start_new_console
import code

# https://stackoverflow.com/questions/3720740/pass-variable-on-import/39360070#39360070
# Pass data to/from other modules and is used also in debugging, Look in: build_launch_test()
import importflags
FLAGS = importflags.FLAGS


# MacOS printing fix related Begin ###########
from . import printer

# Pass printer to other modules
DEFAUL_PRINTER = print
FIIXED_PRINTER = printer.get_fixed_printer()

importflags.PRINTER['default'] = DEFAUL_PRINTER
importflags.PRINTER['fixed'] = FIIXED_PRINTER
importflags.PRINTER['current'] = DEFAUL_PRINTER
# MacOS printing fix related End #########


# Used on debugging
from .decorators import do_twice, debug

# From this package
from . import wordexpand
from . import changefont
from . import fdialog


##import logging
##logger = logging.getLogger('henxel')
##console_handler = logging.StreamHandler()
##logger.addHandler(console_handler)
##logger.warning(10* ' This is Warning! ')

############ Imports End
############ Module Utilities Begin

# Note: These are not checked, for example: Alt here seems to be linux only
# It might be better not to use these much and use hardcoded event.state as usual
modifier_dict = {
# Modifier		Mask
'Shift':	0x0001,
'CapsLock':	0x0002,
'Control':	0x0004,
'Left-Alt':	0x0008,
'NumLock':	0x0010,
'Right-Alt':0x0080,
'Button1':	0x0100,
'Button2':	0x0200,
'Button3':	0x0400
}


def filter_keys_out(event, keys):
	for key in keys:
		# At least one key in keys was pressed
		if event.state & modifier_dict.get(key): return True
	return False


def filter_keys_in(event, keys):
	for key in keys:
		# At least one key in keys was missing
		if not event.state & modifier_dict.get(key): return False
	return True


def get_font(want_list):
	fontname = None

	fontfamilies = [f for f in tkinter.font.families()]

	for font in want_list:
		if font in fontfamilies:
			fontname = font
			break

	if not fontname: fontname = 'TkDefaulFont'

	return fontname


def get_info():
	''' Print names of methods in class Editor,
		which gathers some information.
	'''

	names = [
			'can_do_syntax',
			'can_expand_word',
			'check_caps',
			'check_indent_depth',
			'check_line',
			'check_sel',
			'checkpars',
			'cursor_is_in_multiline_string',
			'search_setting_edit',
			'ensure_idx_visibility',
			'find_empty_lines',
			'fonts_exists',
			'get_config',
			'get_line_col_as_int',
			'get_linenums',
			'get_safe_index',
			'get_scope_end',
			'get_scope_path',
			'get_scope_start',
			'get_sel_info',
			'handle_window_resize',
			'idx_lineend',
			'idx_linestart',
			'line_is_bookmarked',
			'line_is_defline',
			'line_is_elided',
			'line_is_empty',
			'tab_has_syntax_error',
			'bookmarks_print',
			'search_help_print',
			'search_setting_print',
			'test_launch_is_ok',
			'update_lineinfo',
			'update_linenums',
			'update_title',
			'update_tokens'
			]

	for name in names: print(name)


def stash_pop():
	''' When Editor did not launch after recent updates
		Note: This assumes last commit was launchable

		0: Copy error messages! For fixing.

		1: In shell: "git stash"
			  Files are now at last commit, changes are put in sort of tmp-branch.

		2: Launch python: "python"

		3: Import henxel: "import henxel"
			  Now Editor is set to last commit, so one can:

		4: Bring all files back to current state: "henxel.stash_pop()"

		5: Launch Editor: "e=henxel.Editor()"

		--> Editor and all the code executed, is from last commit!
		--> Files in the repo are up-to-date!
		--> Start fixing that error
	'''
	subprocess.run('git stash pop -q'.split())

############ Module Utilities End
############ Other Classes Begin

from dataclasses import dataclass, field
from typing import Any, List


@dataclass(repr=False)
class Tab:
	'''	Represents a tab-page of an Editor-instance
	'''

	# This must be first because it has no default value
	# same thing as with function arguments
	text_widget: tkinter.Text

	# dataclass does not want mutable default values
	bookmarks: List[str] = field(default_factory=list)
	bookmarks_stash: List[str] = field(default_factory=list)

	# False in creation, normally pathlib.Path
	filepath: Any = None

	chk_sum: int = 0
	oldlinenum: int = 0

	tcl_name_of_contents: str = ''
	position: str = '1.0'
	type: str = 'newtab'
	contents: str = ''
	oldcontents: str = ''
	anchorname: str = ''
	oldline: str = ''
	bid_space: str = ''

	active: bool = False
	par_err: bool = False
	check_scope: bool = False


@dataclass
class FakeEvent:
	''' Used in move_by_words2
	'''

	keysym: str = 'Left'
	state: int = 999

############ Other Classes End
############ Class Editor Begin

###############################################################################
# config(**options) Modifies one or more widget options. If no options are
# given, method returns a dictionary containing all current option values.
#
# https://tcl.tk/man/tcl9.0/TkCmd/index.html
#
# Look in: 'text', 'event' and 'bind'
#
# https://docs.python.org/3/library/tkinter.html
#
###############################################################################

############ Constants Begin
CACHEPATH = 'henxel.cache'
CONFPATH = 'henxel.cnf'
ICONPATH = 'editor.png'
HELPPATH = 'help.txt'
KEYS_HLP = 'shortcuts.txt'
KEYS_MAC = 'shortcuts_mac.txt'

VERSION = importlib.metadata.version('henxel')


TAB_WIDTH = 4
TAB_WIDTH_CHAR = 'A'


GOODFONTS = [
			'Andale Mono',
			'FreeMono',
			'DejaVu Sans Mono',
			'Liberation Mono',
			'Inconsolata',
			'Consolas',
			'Noto Mono',
			'Noto Sans Mono',
			'FreeMono',
			'Courier 10 Pitch',
			'Courier',
			'Courier New'
			]

# Want list for keywords, used with italic-setting
GOODFONTS2 = [
'Optima',
'DejaVu Serif',
'Sitka Text',
'Sitka Text Semibold',
'Avenir',
'Rockwell',
'Trebuchet MS',
'Menlo',
'Courier New'
'DejaVu Sans',
'Comic Sans MS'
]


############ Constants End
############ Init etc. Begin

class Editor(tkinter.Toplevel):

	# import flags
	flags = FLAGS

	alive = False
	in_mainloop = False
	files_to_be_opened = False

	pkg_contents = None
	no_icon = True
	pic = None
	helptxt = None

	root = None
	textfont = None
	menufont = None
	boldfont = None
	keyword_font = None
	linenum_font = None

	mac_term = None
	win_id = None
	os_type = None

	if sys.platform == 'darwin': os_type = 'mac_os'
	elif sys.platform[:3] == 'win': os_type = 'windows'
	elif sys.platform.count('linux'): os_type = 'linux'
	else: os_type = 'linux'

	# No need App-name at launch-test, also this would deadlock the editor
	# in last call to subprocess with osascript. Value of mac_term would be 'Python'
	# when doing launch-test, that might be the reason.
	if flags and flags.get('launch_test') == True: pass
	elif os_type == 'mac_os':
		# macOS: Get name of terminal App.
		# Used to give focus back to it when closing editor, in quit_me()

		# This have to be before tkinter.tk()
		# or appname is set to 'Python'
		try:

##			# With this method one can get appname with single run but is still slower
##			# than the two run method used earlier and now below:
##			tmp = ['lsappinfo', 'metainfo']
##			tmp = subprocess.run(tmp, check=True, capture_output=True).stdout.decode()
##			# Returns many lines.
##			# Line of interest is like:
##			#bringForwardOrder = "Terminal" ASN:0x0-0x1438437:  "Safari" ASN:0x0-0x1447446:  "Python" ASN:0x0-0x1452451:  "Finder" ASN:0x0-0x1436435:
##
##			# Get that line
##			tmp = tmp.partition('bringForwardOrder')[2]
##			# Get appname from line
##			mac_term = tmp.split(sep='"', maxsplit=2)[1]


			tmp = ['lsappinfo', 'front']
			tmp = subprocess.run(tmp, check=True, capture_output=True).stdout.decode()
			tmp = tmp[:-1]

			tmp = ('lsappinfo info -only name %s' % tmp).split()
			tmp = subprocess.run(tmp, check=True, capture_output=True).stdout.decode()
			tmp = tmp[:-1]
			mac_term = tmp.split('=')[1].strip('"')

			# Get window id in case many windows of app is open
			tmp = ['osascript', '-e', 'id of window 1 of app "%s"' % mac_term]
			tmp = subprocess.run(tmp, check=True, capture_output=True).stdout.decode()

			win_id = tmp[:-1]
			del tmp

			#print(win_id)
			#print('AAAAAAAAA', mac_term)

		except (FileNotFoundError, subprocess.SubprocessError):
			pass


	def __new__(cls, *args, debug=False, **kwargs):

		if not cls.root:
			# Q: Does launch-test have its own root? A: Yes

			cls.root = tkinter.Tk()
			cls.root.withdraw()


		if not cls.textfont:
			cls.textfont = tkinter.font.Font(family='TkDefaulFont', size=12, name='textfont')
			cls.menufont = tkinter.font.Font(family='TkDefaulFont', size=10, name='menufont')
			cls.keyword_font = tkinter.font.Font(family='TkDefaulFont', size=12, name='keyword_font')
			cls.linenum_font = tkinter.font.Font(family='TkDefaulFont', size=12, name='linenum_font')

			cls.boldfont = cls.textfont.copy()


		if not cls.pkg_contents:
			cls.pkg_contents = importlib.resources.files('henxel')


		if cls.pkg_contents:

			if cls.no_icon:
				for item in cls.pkg_contents.iterdir():

					if item.name == ICONPATH:
						try:
							cls.pic = tkinter.Image("photo", file=item)
							cls.no_icon = False
							break

						except tkinter.TclError as e:
							print(e)

			if not cls.helptxt:
				keystext = False
				helptext = False
				helpfile = HELPPATH
				keysfile = KEYS_HLP
				if cls.os_type == 'mac_os': keysfile = KEYS_MAC

				for item in cls.pkg_contents.iterdir():

					if item.name == keysfile:
						try:
							keystext = item.read_text()

						except Exception as e:
							print(e.__str__())

					elif item.name == helpfile:
						try:
							helptext = item.read_text()

						except Exception as e:
							print(e.__str__())

					if keystext and helptext:
						cls.helptxt = keystext + helptext
						break


		if cls.no_icon: print('Could not load icon-file.')


		if not cls.alive:

			return super(Editor, cls).__new__(cls, *args, **kwargs)

		else:
			print('Instance of ', cls, ' already running!\n')

			# By raising error here, one avoids this situation:
			# Editor was called with: e=henxel.Editor() and there
			# already was Editor. Then, if not raising error here:
			# 'e' would then be Nonetype, but old Editor would survive.
			# To avoid that type-change, one raises the error
			raise ValueError()


	def __init__(self, *args, debug=False, **kwargs):
		try:
			self.root = self.__class__.root
			self.flags = self.__class__.flags
			self.debug = debug
			# Pass info to other modules
			if self.in_mainloop: importflags.IN_MAINLOOP = True


			super().__init__(self.root, *args, class_='Henxel', bd=4, **kwargs)

			if self.debug: self.protocol("WM_DELETE_WINDOW", self.quit_me)
			# When not debugging, exit editor from close-button even if there are any kind of errors, even saving errors
			else: self.protocol("WM_DELETE_WINDOW", self.force_quit_editor)

			# Dont map too early to prevent empty windows at startup
			# when init is taking long
			self.withdraw()

			# Prevent flashing 1/3
			# Get original background, which is returned at end of init
			# after editor gets mapped
			self.orig_bg_color = self.cget('bg')
			# This would set background to transparent: self.config(bg='')
			# but setting it to: self.bgcolor later works better


			# Other widgets
			self.to_be_closed = list()

			# Used for cancelling pending tasks
			self.to_be_cancelled = dict()
			self.to_be_cancelled['message'] = list()
			self.to_be_cancelled['message2'] = list()
			self.to_be_cancelled['completions'] = list()
			self.to_be_cancelled['flash_btn_git'] = list()

			# Used to bypass conf in such a way it enables use of editor adhoc(normally)
			# like: python -m henxel file1 file2
			self.one_time_conf = False
			if self.files_to_be_opened:
				self.one_time_conf = True


			self.flag_check_lineheights = False
			self.ln_string = ''
			self.want_ln = 2
			self.syntax = True
			self.oldconf = None
			self.tab_char = TAB_WIDTH_CHAR
			# Check syntax at exit
			self.check_syntax = True

			self.cachepath = CACHEPATH
			self.confpath = CONFPATH
			################################
			# henxel.cnf is read from here #
			################################
			# if in venv, put conf in venv-dir
			if sys.prefix != sys.base_prefix:
				self.env = sys.prefix
			# if not, in home-dir
			else:
				self.env = pathlib.Path().home()
				self.cachepath = '.henxel.cache'
				self.confpath = '.henxel.cnf'



			self.tabs = list()
			self.title_string = ''
			self.tabindex = None
			self.branch = None
			self.version = VERSION
			self.os_type = self.__class__.os_type

			self.geom = '+%d+0'
			if self.os_type == 'windows': self.geom = '-0+0'
			self.start_fullscreen = False
			self.check_next_esc = False

			self.textfont = self.__class__.textfont
			self.menufont = self.__class__.menufont
			self.boldfont = self.__class__.boldfont
			self.keyword_font = self.__class__.keyword_font
			self.linenum_font = self.__class__.linenum_font
			self.fonts = dict()
			for font in [self.textfont, self.menufont, self.keyword_font, self.linenum_font]:
				self.fonts[font.name] = font

			# Can be changed with: version_control_cmd_set
			self.version_control_cmd = 'git branch --show-current'.split()

			# Used in filedialog, can be changed with: filedialog_sorting_order_set
			self.dir_reverse = True
			self.file_reverse = False


			##### Search related variables Begin

			# This marks range of focus-tag:
			self.search_focus = ('1.0', '1.0')
			self.mark_indexes = list() # of int
			self.match_lenghts = list() # of int
			self.match_lenghts_var = tkinter.StringVar()

			self.search_settings = False
			self.search_starts_at = '1.0'
			self.search_ends_at = False

			self.search_matches = 0
			self.old_word = ''
			self.new_word = ''
			self.search_history = ([],[]) # old_words, new_words
			self.search_history_index = 0
			self.flag_use_replace_history = False

			# Used for counting indentation
			self.search_count_var = tkinter.IntVar()

			##### Search related variables End


			self.timeout = 1
			self.popup_run_action = 1
			# Used in popup_run_action_set
			self.popup_run_action_idx = 2
			self.module_run_name = None
			self.custom_run_cmd = None
			self.errlines = list()
			self.err = False


			# Used for showing insertion cursor when text is disabled
			self.cursor_frame = None

			# Used for showing setting-console
			self.setting_frame = None

			# Used for showing Openfile-dialog
			self.fdialog_frame = None

			# Used for showing short-lived messages
			self.message_frame = None


			# When clicked with mouse button 1 while searching
			# to set cursor position to that position clicked.
			self.save_pos = ''

			# Help enabling: "exit to goto_def func with space" while searching
			self.goto_def_pos = False

			# Used as flag to check if need to update self.deflines
			self.cur_defline = '-1.-1'

			# Used in load()
			self.tracevar_filename = tkinter.StringVar()
			self.tracefunc_name = None
			self.lastdir = None

			self.par_err = False

			# Used in copy() and paste()
			self.flag_fix_indent = False
			self.checksum_fix_indent = False

			self.waitvar = tkinter.IntVar()

			# distance from left screen edge to text
			# can be set with: left_margin_set(width_normal, width_fullscreen)
			# and: left_margin_gap_set(gap_normal, gap_fullscreen)
			self.default_margin, self.margin, self.margin_fullscreen = 4, 5, 5
			self.gap, self.gap_fullscreen = 0, 0

			## Fix for macos printing issue starting from about Python 3.13
			self.mac_print_fix = False

			# Just in case, set to normal at end of init
			self.state = 'init'



			self.helptxt = 'Could not load help-file. Press ESC to return.'

			if self.__class__.helptxt:
				self.helptxt = self.__class__.helptxt

			try:
				self.tk.call('wm','iconphoto', self._w, self.__class__.pic)
			except tkinter.TclError as e:
				print(e)


			# Initiate widgets
			####################################
			self.btn_git = tkinter.Button(self, takefocus=0, relief='flat', compound='left', bd=0,
										highlightthickness=0, padx=0, command=self.setting_console)

			self.entry = tkinter.Entry(self, highlightthickness=0, takefocus=0)
			if self.os_type != 'mac_os': self.entry.config(bg='#d9d9d9')

			self.btn_open = tkinter.Button(self, takefocus=0, text='Open',
										highlightthickness=0, command=self.load)
			self.btn_save = tkinter.Button(self, takefocus=0, text='Save',
										highlightthickness=0, command=self.save)



			self.text_widget_basic_config = dict(undo=True, maxundo=-1, autoseparators=True,
											tabstyle='wordprocessor', highlightthickness=0,
											relief='flat')
			#############
			self.text_frame = tkinter.Frame(self, bd=0, padx=0, pady=0, highlightthickness=0)

			self.ln_widget = tkinter.Text(self.text_frame, width=self.margin, highlightthickness=0, relief='flat')



			self.scrollbar = tkinter.Scrollbar(self, orient=tkinter.VERTICAL,
											highlightthickness=0, bd=0, takefocus=0)


			self.popup = tkinter.Menu(self, tearoff=0, bd=0, activeborderwidth=0)

			if self.debug:
				self.popup.add_command(label="test", command=lambda: self.after_idle(self.do_test_launch))

				if self.flags and self.flags.get('test_fake_error'): this_func_no_exist()
				#this_func_no_exist()

			else: self.popup.add_command(label="copy", command=self.copy)

			self.popup.add_command(label="     runfile", command=lambda: self.after_idle(self.run))
			self.popup.add_command(label="  select all", command=self.select_all) # this will be replaced by "run command"
			self.popup.add_command(label=" draw syntax", command=self.redraw_syntax)
			self.popup.add_command(label="  chk syntax",
				command=lambda kwargs={'curtab':True}: self.tab_has_syntax_error(**kwargs) )

			self.popup.add_command(label="   strip one", command=self.strip_first_char)
			self.popup.add_command(label="    open mod", command=self.view_module)
			self.popup.add_command(label="      config", command=self.setting_console)
			self.popup.add_command(label="      errors", command=self.show_errors)
			self.popup.add_command(label="        help", command=self.help)



			# Get conf #####################
			self.conf_load_success = False
			string_representation = None
			data, p = None, None

			if self.flags and self.flags.get('test_skip_conf') == True: pass
			else:
				p = pathlib.Path(self.env) / self.confpath

				if p.exists():
					try:
						with open(p, 'r', encoding='utf-8') as f:
							string_representation = f.read()
							data = json.loads(string_representation)

					except EnvironmentError as e:
						print(e.__str__())
						print(f'\n Could not load existing configuration file: {p}')

			if data:
				self.oldconf = string_representation
				self.conf_load_success = self.load_config(data)

			###############################################
			# Could not load files from conf, err-msg is already printed out from set_config
			if self.tabindex == None:
				# No conf and wanting to open some files from terminal
				if self.one_time_conf:
					self.handle_one_time_conf()
					self.conf_read_files()

				else:
					if len(self.tabs) == 0:
						newtab = Tab(self.create_textwidget())
						newtab.active = True
						self.tabindex = 0
						self.tabs.insert(self.tabindex, newtab)

					# Recently active normal tab is gone
					else:
						self.tabindex = 0
						self.tabs[self.tabindex].active = True
			## Get conf End ################################


			self.update_popup_run_action()


			## Fix for macos printing issue starting from about Python 3.13 Begin
			# Can be set with: mac_print_fix_use
			tests = (not self.in_mainloop, self.mac_print_fix, self.os_type == 'mac_os')
			if all(tests):
				self.change_printer_to(FIIXED_PRINTER)
				print('using fixed printer')


			# Get version control branch #######
			if self.flags and self.flags.get('launch_test') == True: pass
			else:
				try:
					self.branch = subprocess.run(self.version_control_cmd,
							check=True, capture_output=True).stdout.decode().strip()
				except Exception as e:
					pass


			# Colors Begin #######################

			# This is also color of comments
			ln_color = '#c0c0c0'
			red = r'#c01c28'
			cyan = r'#2aa1b3'
			magenta = r'#a347ba'
			green = r'#26a269'
			orange = r'#e95b38'
			yellow = r'#d0d101'
			gray = r'#508490'
			#plain_black = r'#000000' # Should not be used unless there is 'hardware tint'(old/'bad' screen)
			black = r'#221247' # blue tint
			white = r'#d3d7cf'

			strings_day = '#1b774c'
			calls_day = '#1b3db5'

			self.default_themes = dict()
			self.default_themes['day']   = d = dict()
			self.default_themes['night'] = n = dict()

			# self.default_themes[self.curtheme][tagname] = [backgroundcolor, foregroundcolor]
			d['normal_text'] = [white, black]
			n['normal_text'] = [black, white]


			d['keywords'] = ['', orange]
			n['keywords'] = ['', 'deep sky blue']

##			d['tests'] = ['', yellow] # NOTE: this (with any color) just doesn't work, and same with deflines
##			n['tests'] = ['', yellow]
			d['numbers'] = ['', red]
			n['numbers'] = ['', red]
			d['bools'] = ['', magenta]
			n['bools'] = ['', magenta]
			d['strings'] = ['', strings_day]
			n['strings'] = ['', green]
			d['comments'] = ['', black]
			n['comments'] = ['', ln_color]
			d['calls'] = ['', calls_day]
			n['calls'] = ['', cyan]
			d['breaks'] = ['', orange]
			n['breaks'] = ['', orange]
			d['selfs'] = ['', gray]
			n['selfs'] = ['', gray]

			d['match'] = ['lightyellow', 'black']
			n['match'] = ['lightyellow', 'black']
			d['focus'] = ['lightgreen', 'black']
			n['focus'] = ['lightgreen', 'black']

			d['replaced'] = [yellow, 'black']
			n['replaced'] = [yellow, 'black']

			d['mismatch'] = ['brown1', 'white']
			n['mismatch'] = ['brown1', 'white']

			d['sel'] = ['#c3c3c3', black]
			n['sel'] = ['#c3c3c3', black]



			## No conf Begin ########
			if not self.conf_load_success:

				self.curtheme = 'night'
				self.themes = copy.deepcopy(self.default_themes)
				self.bgcolor, self.fgcolor = self.themes[self.curtheme]['normal_text'][:]

				# Set Font
				fontname = get_font(GOODFONTS)
				fontname_keyword = get_font(GOODFONTS2)
				# Want Courier for linenum_font
				fontname_linenum = get_font(reversed(GOODFONTS))

				size0, size1 = 12, 10
				# There is no font-scaling in macOS?
##				if self.os_type == 'mac_os': size0, size1 = 22, 16
				if self.os_type == 'mac_os': size0, size1 = 16, 14

				self.textfont.config(family=fontname, size=size0)
				self.menufont.config(family=fontname, size=size1)
				self.linenum_font.config(family=fontname_linenum, size=size0-2)
				self.keyword_font.config(family=fontname_keyword, size=size0-3, slant='italic')
				# keywords are set little smaller size than normal text and cursived


				self.ind_depth = TAB_WIDTH
				self.tab_width = self.textfont.measure(self.ind_depth * self.tab_char)
				# One char width is: self.tab_width // self.ind_depth
				# Use this in measuring padding
				pad_x =  self.tab_width // self.ind_depth // 3
				pad_y = pad_x
				# Currently self.pad == One char width // 3
				# This is ok?
				self.pad = pad_x ####################################


				self.scrollbar_width = self.tab_width // self.ind_depth
				self.elementborderwidth = max(self.scrollbar_width // 6, 1)
				if self.elementborderwidth == 1: self.scrollbar_width = 9

				self.flag_check_lineheights = True
				self.spacing_linenums = 0
				self.offset_comments = 0
				self.offset_keywords = 0
				## No conf End ########



			#################
			self.text_frame.config(bg=self.bgcolor)

			# Configure Text-widgets of tabs
			self.config_tabs()

			#################################
			# self.text_widget gets defined #
			#################################
			for tab in self.tabs:
				if tab.active: self.text_widget = tab.text_widget



			msg_defaults = dict(parent=self.text_frame, type='okcancel')
			self.msgbox = tkinter.messagebox.Message(**msg_defaults)

			# Needed in leave() taglink in: Run file Related
			self.name_of_cursor_in_text_widget = self.text_widget['cursor']

			self.scrollbar.config(command=self.text_widget.yview,
								width=self.scrollbar_width,
								elementborderwidth=self.elementborderwidth)

			for widget in [self.entry, self.btn_open, self.btn_save, self.ln_widget]:
				widget.config(bd=self.pad)

			self.entry.config(font=self.menufont)
			self.btn_open.config(font=self.menufont)
			self.btn_save.config(font=self.menufont)
			self.popup.config(font=self.menufont)
			self.btn_git.config(font=self.menufont)

			# Hide selection in linenumbers, etc
			bg, fg = self.themes[self.curtheme]['comments'][:]
			self.ln_widget.config(font=self.linenum_font, foreground=fg, background=self.bgcolor, selectbackground=self.bgcolor, selectforeground=fg, inactiveselectbackground=self.bgcolor, state='disabled', padx=self.pad, pady=self.pad, width=self.margin)
			self.ln_widget.tag_config('justright', justify=tkinter.RIGHT, rmargin=self.gap,
							spacing1=self.spacing_linenums, offset=self.offset_comments)




			# In apply_conf now

##			# Get anchor-name of selection-start.
##			# Used in for example select_by_words():
##			self.text_widget.insert(1.0, 'asd')
##			# This is needed to get some tcl-objects created,
##			# ::tcl::WordBreakRE and self.anchorname
##			self.text_widget.event_generate('<<SelectNextWord>>')
##			# This is needed to clear selection
##			# otherwise left at the end of file:
##			self.text_widget.event_generate('<<PrevLine>>')
##
##			# Now also this array is created which is needed
##			# in RE-fixing ctrl-leftright behaviour in Windows below.
##			# self.tk.eval('parray ::tcl::WordBreakRE')
##
##			self.anchorname = None
##			for item in self.text_widget.mark_names():
##				if 'tk::' in item:
##					self.anchorname = item
##					break
##
##			self.text_widget.delete('1.0', '1.3')


			# In Win11 event: <<NextWord>> does not work (as supposed) but does so in Linux and macOS
			# https://www.tcl.tk/man/tcl9.0/TclCmd/tclvars.html
			# https://www.tcl.tk/man/tcl9.0/TclCmd/library.html

			if self.os_type == 'windows':

				# To fix: replace array ::tcl::WordBreakRE contents with newer version, and
				# replace proc tk::TextNextWord with newer version which was looked in Debian 12
				# Need for some reason generate event: <<NextWord>> before this,
				# because array ::tcl::WordBreakRE does not exist yet,
				# but after this event it does. This was done above.
				try:
					self.tk.eval(r'set l3 [list previous {\W*(\w+)\W*$} after {\w\W|\W\w} next {\w*\W+\w} end {\W*\w+\W} before {^.*(\w\W|\W\w)}] ')
					self.tk.eval('array set ::tcl::WordBreakRE $l3 ')
					self.tk.eval('proc tk::TextNextWord {w start} {TextNextPos $w $start tcl_endOfWord} ')
				except tkinter.TclError as err: print(err)

			# Configure btn_git Begin
			# Create bitmap-image to show on btn_git
			create_pic_cmd = '''
set infopic [image create bitmap -data {
# define infopic_width 8
# define infopic_height 21
static unsigned char infopic_bits[] = {
0x3c, 0x2a, 0x16, 0x2a, 0x14, 0x00, 0x00, 0x3f, 0x15,
0x2e, 0x14, 0x2c, 0x14, 0x2c, 0x14, 0x2c, 0x14, 0x2c,
0xd7, 0xab, 0x55
}}]
'''
			try: self.img_name = self.tk.eval(create_pic_cmd)
			except tkinter.TclError as err: print(err)

			width_text = self.menufont.measure('123456')
			width_img = 8
			width_total = width_text + width_img + self.pad*4
			self.btn_git.config(image=self.img_name, width=width_total)

			self.restore_btn_git() # Show branch if on one
			# Configure btn_git End

			# Widgets are now initiated (except error and help-tabs)
			###########################


			# Some more configuration
			###############################
			self.update_idletasks() # Check is this needed?

			# if self.y_extra_offset > 0, it needs attention in update_linenums
			self.y_extra_offset = self.text_widget['highlightthickness'] + self.text_widget['bd'] + self.text_widget['pady']
			# These two are needed in update_linenums() and sbset_override(), and are set to correct values later in init
			self.line_height = 1
			self.text_widget_height = 1

			# Register validation-functions, note the tuple-syntax:
			self.validate_gotoline = (self.register(self.do_validate_gotoline), '%i', '%S', '%P')
			self.validate_search = (self.register(self.do_validate_search), '%i', '%s', '%S')


			self.helptxt = f'{self.helptxt}\n\nHenxel v. {self.version}'



			# Layout Begin
			################################
			self.rowconfigure(1, weight=1)
			self.columnconfigure(1, weight=1)

			# First row, widgets are in root:
			# btn_git / entry / btn_open / btn_save
			# Normally, widget is shown on screen when doing grid_configure
			# But not if root-window is withdrawn earlier(it is)
			self.btn_git.grid_configure(row=0, column = 0, sticky='nsew')
			self.entry.grid_configure(row=0, column = 1, sticky='nsew')
			self.btn_open.grid_configure(row=0, column = 2, sticky='nsew')
			self.btn_save.grid_configure(row=0, column = 3, columnspan=2,
										sticky='nsew')



			self.text_frame.rowconfigure(0, weight=1)

			# Second and final row is in text_frame, excluding scrollbar:
			# text_frame(ln_widget) / text_frame(text_widget) / scrollbar
			self.text_frame.grid_configure(row=1, column=0, columnspan=4,
										sticky='nswe')

			if self.want_ln > 0:
				self.text_frame.columnconfigure(1, weight=1)
				self.ln_widget.grid_configure(row=0, column = 0, sticky='nsew')
				self.text_widget.grid_configure(row=0, column=1, columnspan=3, sticky='nsew')

			else:
				self.text_frame.columnconfigure(0, weight=1)
				self.text_widget.grid_configure(row=0, column=0, columnspan=4, sticky='nsew')


			self.scrollbar.grid_configure(row=1,column=4, sticky='nse')
			#################



			self.syntax_can_auto_update = False

			self.boldfont.config(**self.textfont.config())
			self.boldfont.config(weight='bold')


			self.init_syntags()


			# Used in on_fontchange
			# This is here to get little time-gap before first measuring, right after Tabs
			self.measure_frame_init()

			# Show Tab-completion -windows
			# This is here, before first call to set_bindings, since there is a reference to self.comp_frame
			self.completion_frame_init()

			# Tab-completion, used in indent() and unindent()
			self.expander = wordexpand.ExpandWord(self)


			################
			# Tabs Begin
			##################

			# Create tabs for help and error pages
			newtab = Tab(self.create_textwidget())
			self.set_textwidget(newtab)
			self.set_syntags(newtab)
			self.help_tab = newtab
			self.help_tab.type = 'help'
			self.help_tab.text_widget.insert('insert', self.helptxt)
			self.init_help_tags()
			self.help_tab.text_widget.mark_set('insert', newtab.position)
			self.help_tab.text_widget.see(newtab.position)
			self.set_bindings(newtab)
			self.help_tab.text_widget['yscrollcommand'] = lambda *args: self.sbset_override(*args)


			newtab = Tab(self.create_textwidget())
			self.set_textwidget(newtab)
			self.set_syntags(newtab)
			self.err_tab = newtab
			self.err_tab.type = 'error'
			self.err_tab.text_widget.mark_set('insert', newtab.position)
			self.err_tab.text_widget.see(newtab.position)
			self.set_bindings(newtab)
			self.err_tab.text_widget['yscrollcommand'] = lambda *args: self.sbset_override(*args)


			tags_from_cache = list()
			p = pathlib.Path(self.env) / self.cachepath

			for tab in self.tabs:

				self.set_syntags(tab)

				if tab.type == 'normal':
					tab.text_widget.insert('1.0', tab.contents)
					self.restore_bookmarks(tab, also_stashed=True)

					# Set cursor pos
					try:
						tab.text_widget.mark_set('insert', tab.position)
						tab.text_widget.see(tab.position)
						#self.ensure_idx_visibility(line)

					except tkinter.TclError:
						tab.text_widget.mark_set('insert', '1.0')
						tab.position = '1.0'
						tab.text_widget.see('1.0')


					if self.can_do_syntax(tab):
						self.update_lineinfo(tab)

						###
##						a = self.get_tokens(tab)
##						t1 = int(self.root.tk.eval('clock seconds'))
##						self.insert_tokens(a, tab=tab)
##						t2 = int(self.root.tk.eval('clock seconds'))
##						print(t2-t1, 's')
						###


						# if length of file has changed
						# count tokens from scratch
						if not self.one_time_conf and p.exists() and tab.chk_sum == len(tab.contents):
							tags_from_cache.append(tab)
						else:
							if not self.one_time_conf:
								if not p.exists(): print('Missing cache-file')
								else: print('Content changed:')
								print(tab.filepath, tab.chk_sum, len(tab.contents))

							a = self.get_tokens(tab)
							self.insert_tokens(a, tab=tab)


				self.set_bindings(tab)
				tab.text_widget['yscrollcommand'] = lambda *args: self.sbset_override(*args)
				tab.text_widget.edit_reset()
				tab.text_widget.edit_modified(0)


			#########################################
			# Load tags from cache whenever possible,
			# even though it makes almost no difference for any normal computer
			# under 20 years old. Still, init takes much less time if using
			# really slow computer like rpi1.
			if len(tags_from_cache) > 0:
				#t1 = int(self.root.tk.eval('clock milliseconds'))
				success = self.load_tags(tags_from_cache)
				#t2 = int(self.root.tk.eval('clock milliseconds'))
				#print(t2-t1, 'ms')

				if not success:
					print('Could not load tags from cache-file:\n %s' % p)
					for tab in tags_from_cache:
						a = self.get_tokens(tab)
						self.insert_tokens(a, tab=tab)


			curtab = self.tabs[self.tabindex]

			self.scrollbar.set(*self.text_widget.yview())
			self.anchorname = curtab.anchorname
			self.tcl_name_of_contents = curtab.tcl_name_of_contents
			self.syntax_can_auto_update = True

			if curtab.filepath:
				self.entry.insert(0, curtab.filepath)
				self.entry.xview_moveto(1.0)

			#################
			# Tabs End
			#############


			# Now, get better values for these
			self.line_height = self.get_lineheights()
			self.text_widget_height = self.scrollbar.winfo_height()


			############
			# Bindings #
			############
			self.set_bindings_other()
			############

			#curtab.text_widget.bind( "<Control-O>", self.test_bind)

			# Prevent flashing 2/3
			self.config(bg=self.bgcolor)

			############
			# Get window positioning with geometry call to work below
			self.update_idletasks()

			# Sticky top right corner by default,
			# --> get some space for console on left
			# This geometry call has to be before deiconify
			diff = self.winfo_screenwidth() - self.winfo_width()
			tests = (self.os_type != 'windows', self.geom == '+%d+0', diff > 0)
			if self.geom:
				if all(tests):
					# Not Windows and first launch
					self.geometry('+%d+0' % diff )
				else:
					self.geometry(self.geom)


			############
			# map Editor
			if self.flags and not self.flags.get('test_is_visible'): pass
			else: self.deiconify()

			# Focus has to be after deiconify if on Windows
			if self.os_type == 'windows':
				self.text_widget.focus_force()
			else:
				self.text_widget.focus_set()

			# Prevent flashing 3/3
			if self.flags and not self.flags.get('test_is_visible'): pass
			else:
				while not self.text_widget.winfo_viewable():
					self.wait_for(200)
				self.config(bg=self.orig_bg_color)


			# no conf, or geometry reset to 'default'
			self.flag_check_geom_at_exit = False
			if self.geom in ['+%d+0', '-0+0']:
				self.flag_check_geom_at_exit = True
				self.after(200,
				lambda args=['current']: self.use_geometry(*args))


			# Used to show cursor when text is disabled
			self.cursor_frame_init()

			# Used for showing setting-console
			self.setting_frame_init()
			self.setting_console_namespace_init()
			self.setting_console_history = list()
			self.setting_console_history_index = 0

			# Filedialog
			self.fdialog_frame_init()

			# Show info-messages like scope while goto_bookmark etc
			self.message_frame_init()

			# Show info-messages when other frame is already in use
			self.message_frame2_init()



			if self.start_fullscreen:
				delay = 300
				self.put_editor_fullscreen(delay)


			if self.flags and not self.flags.get('test_is_visible'): pass
			else:
				if self.flag_check_lineheights:
					self.handle_diff_lineheights()


			self.__class__.alive = True


			self.state = 'normal'
			self.update_title()


		except Exception as init_err:

			doing_launchtest = False
			if self.flags and self.flags.get('launch_test'): doing_launchtest = True

			if doing_launchtest: raise init_err

			try: self.cleanup()
			except Exception as err:
				# Some object, that cleanup tried to delete,
				# did not yet had been created.
				print(err)

			if self.debug:
				# Give info about recovering from unlaunchable state
				info_start = '''
################################################
Editor did not Launch!

Below is printed help(henxel.stash_pop), read and follow.
################################################
help(henxel.stash_pop) Begin

'''

			else:
				info_start = '''
################################################
Editor did not Launch!

Maybe upgraded henxel, and using old conf?

Try deleting your conf-file from venv-folder:
henxel.cnf and henxel.cache
Then restart python-console and editor
'''


			info_end = '''
################################################
Error messages Begin
'''

			if self.debug:
				info = info_start + stash_pop.__doc__.replace('\t', '  ') + info_end
				print(info)
				traceback.print_exception(init_err)
				sys.exit(1)
			else:
				info = info_start + info_end
				print(info)
				raise init_err

			############################# init End ##########################


	def update_title(self, event=None):
		tail = len(self.tabs) - self.tabindex - 1
		self.title_string = f'{"0"*self.tabindex}@{"0"*(tail)}'
		self.title( f'Henxel {self.title_string}' )


	def handle_window_resize(self, event=None):
		'''	In case of size change, like maximize etc. viewsync-event is not
			generated, so need to bind to <Configure>-event.

			note: setting fullscreen is done in esc_override
		'''
		self.update_idletasks()
		# Needed in update_linenums() and sbset_override()
		self.text_widget_height = self.scrollbar.winfo_height()


	def copy_windows(self, event=None, selection=None, flag_cut=False):

		try:
			#self.clipboard_clear()
			# From copy():
			if selection:
				tmp = selection
			else:
				tmp = self.selection_get()


			if flag_cut and event:
				# in Entry
				w = event.widget
				w.delete('sel.first', 'sel.last')


			# https://stackoverflow.com/questions/51921386
			# pyperclip approach works in windows fine
			# import clipboard as cb
			# cb.copy(tmp)

			# os.system approach also works but freezes editor for a little time


			d = dict()
			d['input'] = tmp.encode('ascii')

			t = threading.Thread( target=subprocess.run, args=('clip',), kwargs=d, daemon=True )
			t.start()


			#self.clipboard_append(tmp)
		except tkinter.TclError:
			# is empty
			return 'break'


		#print(#self.clipboard_get())
		return 'break'


	def wait_for(self, ms):
		''' Block until ms milliseconds have passed

			NOTE: 'cancel' all bindings, which checks the state,
			for waiting time duration. It may be what one wants.

			Remember that, wait_for()  A: changes state to 'waiting' B: is usually blocking
			BUT in same quite rare occasions can be non-blocking!

			--> One should debug self.state before and after every call to wait_for
				to be 100% sure, before making decission of the blockiness of wait_for
				in callback in case.

				This is easy: just print out state before and after wait_for and see result:
				if state after is 'waiting'
					--> non-blocking, take necessary actions (like check if state is 'waiting' because IT IS)
				if state after is not 'waiting':
					--> all is good, nothing needs to be done
		'''

		state = self.state
		self.state = 'waiting'

		self.waitvar.set(False)
		self.after(ms, self.waiter)
		self.wait_variable(self.waitvar)

		# 'Release' bindings
		self.state = state


	def waiter(self):
		self.waitvar.set(True)


	def do_nothing(self, event=None):
		self.bell()
		return 'break'


	def do_nothing_without_bell(self, event=None):
		return 'break'


	# Not used, move this to notes or something?
	def do_after_proxy(self, delay, callbacks, event=None):
		''' Enable adding delay to callback without
			'slipping event' to parents
			(This is maybe because of using after in binding)


			Example, instead of, This will slip:
			entry.bind("<Control-h>", lambda event,
					args=[30, self.show_help]: self.after(*args) )

			Do this instead:
			entry.bind("<Control-h>", lambda event,
					args=[30, self.show_help]: self.do_after_proxy(*args) )


			Note: In general delays should be/are in callbacks already

		'''
		for callback  in callbacks:
			self.after(delay, callback)

		return 'break'


	def start_new_console(self, event=None):
		if not self.in_mainloop:
			self.wait_for(30)
			self.bell()
			print('Already should have Python-console')
		else:
			code.interact(local={'print':print, 'e':self})
		return 'break'


	def show_help(self, event=None):
		self.wait_for(30)

		c = self.setting_frame
		#print(c.lastword)
		tmp = c.entry.get().strip()
		if '(' in tmp:
			idx = tmp.index('(')
			tmp = tmp[:idx]

		if tmp:
			try: eval( f'help({tmp})', {'print':print}, {'e':self, 'ee':self} )
			except Exception as err: print(err)
		return 'break'


	def setting_console_namespace_init(self):
		# Define settings to be used in setting_console like: e.timeout_set
		settables = [
		self.custom_run_cmd_set,
		self.popup_run_action_set,
		self.run_module_set,
		self.timeout_set,
		self.version_control_cmd_set,
		self.check_syntax_on_exit,
		self.filedialog_sorting_order_set,
		self.left_margin_set,
		self.left_margin_gap_set,
		self.scrollbar_widths_set,
		self.tabsize_change,
		self.export_config,
		self.bookmarks_remove,
		self.bookmarks_print,
		self.bookmarks_export,
		self.bookmarks_import,
		self.bookmarks_unstash,
		self.use_geometry,
		self.geometry,
		self.wm_geometry,
		self.editor_starts_fullscreen,
		self.mac_print_fix_use,
		self.search_help_print,
		self.search_setting_print,
		self.search_setting_reset,
		self.search_setting_edit,
		self.font_choose,
		self.color_choose,
		self.save_forced,
		self.tab_has_syntax_error
		]

		self.setting_frame.namespace = [ f'{func.__name__}' for func in settables ]

	#@debug
	def do_eval(self, cmd_as_string, event=None):
		res = False
		try:
			# debug-decorator doesn't catch these
			res = eval(cmd_as_string, {'print':print}, {'e':self, 'ee':self})
			self.setting_frame.last_eval_raised_error = False
		except Exception as err:
			self.setting_frame.last_eval_raised_error = True
			print(err)
		return res

	#@debug
	def do_cmd(self, event=None):
		c = self.setting_frame

		tmp = c.entry.get().strip()
		if len(tmp) > 0:
			res = self.do_eval(tmp)
			if not self.setting_frame.last_eval_raised_error:
				if tmp not in self.setting_console_history:
					self.setting_console_history.append(tmp)
					self.setting_console_history_index = len(self.setting_console_history) -1
					# show position among history items
					c.config(text='Edit Settings  %d/%d' % (self.setting_console_history_index+1, len(self.setting_console_history)) )
			# If some setting is None, it should be printed out from callback
			if res not in [None, 'break', 'continue']:
				print(res)

		return 'break'

	#@debug
	def setting_console_history_walk(self, event=None, direction='up'):
		''' Walk history in entry with arrow up/down
		'''
		index = self.setting_console_history_index
		h = self.setting_console_history
		if len(h) == 0: return 'break'

		# Get history item
		if direction == 'up':
			index -= 1

			if index < 0:
				index += 1
				return 'break'
		else:
			index += 1

			if index > len(h) -1:
				index -= 1
				return 'break'

		# Update self.setting_console_history_index
		self.setting_console_history_index = index
		history_item = h[index]

		e = self.setting_frame.entry
		e.delete(0, 'end')
		e.insert(0, history_item)
		e.icursor('end')
		e.xview_moveto(1)
		self.setting_frame.config(text='Edit Settings  %d/%d' % (self.setting_console_history_index+1, len(self.setting_console_history)) )

	#@debug
	def complete_print(self, completions):
		''' Print completions in two colums
		'''
		num = len(completions)
		half = num // 2

		even = True
		# not even
		if num % 2:
			half += 1
			even = False

		col1 = completions[:half]
		col2 = completions[half:]

		max_len = max(map(len, completions))
		patt = '{0:%s}\t{1}' % max_len
		num = half
		if not even: num -= 1
		print('\n')
		for i in range(num): print(patt.format(col1[i], col2[i]))
		if not even: print(col1[-1])

	#@debug
	def do_complete(self, event=None):
		self.wait_for(30)

		c = self.setting_frame

		tmp = c.entry.get().strip()


		if c.lasttmp and tmp.startswith(c.lasttmp):
			if c.lastword and (tmp == c.lastword or tmp == c.lastword +'()'):
				tmp = c.lasttmp
		else:
			c.lastword = False


		options = []
		options_minus_parent = []
		child = False


		if '.' in tmp:
			idx = tmp.rindex('.')
			if idx == 0: return 'break'

			parent = tmp[:idx]

			# Child can be just dot: "e."
			child = tmp[idx:]

			# options includes whole namespace of parent, for now
			if res := self.do_eval( 'dir(' +parent+ ')' ):
				# Give whole namespace
				if tmp.startswith('ee.'):
					options = res
				# Give just settings
				else:
					options = [option for option in res if option in self.setting_frame.namespace]

		# Give something, not much though
		elif res := self.do_eval('dir()'):
			options = res



		if len(options) > 0:

			if child:
				options = map(lambda item: (parent +'.'+ item), options)

			# Filter down namespace of parent, unless child was only dot: "e."
			completions = [ option for option in options if option.startswith(tmp) ]
			if child:
				# Most of time, show only childs in prints
				m = map(lambda item: item.split('.')[-1], completions)
				# Filter out dunder-methods for brevity in prints
				options_minus_parent = [ item for item in m if not item.startswith('__') ]
		else:
			# When trying for example: "a."
			return 'break'


		if len(completions) > 0:
			# tmp has changed, one already knows this?
			if completions != c.completions:
				c.completions = completions
				c.lasttmp = tmp

				if len(completions) > 1:
					if child: self.complete_print(options_minus_parent)
					else: self.complete_print(completions)

					# Find common prefix
					first_comp = c.completions[0]
					len_tmp = len(tmp)
					len_tail = len(c.completions[0][len_tmp:])

					flag_add = 0
					flag_break = False
					for i in range(1, len_tail+1, 1):
						for completion in c.completions[1:]:
							if not first_comp[:len_tmp+i] in completion:
								flag_break = True
								break
						if not flag_break: flag_add += 1
						else: break

					# Extend word to common prefix
					if flag_add > 0:
						c.lasttmp = first_comp[:len_tmp+flag_add]
						c.entry.delete(0, 'end')
						c.entry.insert(0, c.lasttmp)


				else:
					# insert when only one completions is left
					c.lastword = word = c.completions[0]
					c.entry.delete(0, 'end')
					c.entry.insert(0, word)

					# If word is function, add braces and put cursor in between
					check_if_func = f"type({word}).__name__ in ('method', 'function')"

					if is_func := self.do_eval(check_if_func):
						c.entry.insert('end', '()')
						# Put cursor in between braces
						try:c.entry.icursor(len(word)+1)
						except Exception as err: print(err)



		# Trying for example: "aa"
		elif '.' not in tmp:
			c.lasttmp = False

			if res := self.do_eval('dir()'):
				options = res
				print('locals:', options)

		# Should not happen
		else: c.lasttmp = False


		return 'break'

		#### do_complete End ######


	def stop_fdialog(self, event=None):
		self.fdialog_frame.place_forget()
		self.tracevar_filename.set('')
		self.bind( "<Escape>", self.esc_override )
		return 'break'


	def set_fdialog_widths(self):
		f = self.fdialog_frame
		f.dialog.scrollbar_width, f.dialog.elementborderwidth = self.scrollbar_width, self.elementborderwidth
		f.dialog.dirsbar.configure(width=self.scrollbar_width, elementborderwidth=self.elementborderwidth)
		f.dialog.filesbar.configure(width=self.scrollbar_width, elementborderwidth=self.elementborderwidth)


	def fdialog_frame_init(self):
		''' Initialize file-dialog-widget
		'''
		# Note about parent being self, if it would be self.text_frame, there would be
		# bad geometry-handling after: new_tab(), open filedialog
		# Same is true with setting_frame. Cursor frame manages being so small, or something.
		self.fdialog_frame = f = tkinter.LabelFrame(self,
			text='Select File', width=1, height=1, takefocus=1)

		f.path = pathlib.Path().cwd()

		if self.lastdir: f.path = f.path / self.lastdir

		f.dialog = fdialog.FDialog(self.fdialog_frame, f.path, self.tracevar_filename,
					font=self.textfont, menufont=self.menufont, os_type=self.os_type)


		f.dialog.dir_reverse = self.dir_reverse
		f.dialog.file_reverse = self.file_reverse
		self.set_fdialog_widths()


		f.old_x = f.old_y = self.pad
		offset_y = self.entry.winfo_height()
		f.old_y += offset_y
		f.place_configure(x=f.old_x, y=f.old_y, width=1, height=1)
		f.place_forget()

		self.to_be_closed.append(f)


	def setting_frame_init(self):
		''' Initialize setting-console, binded to btn_git
		'''

		self.setting_frame = c = tkinter.LabelFrame(self,
			text='Edit Settings', width=1, height=1, takefocus=1)

		c.entry = tkinter.Entry(c, width=50, highlightthickness=0, bd=4,
							font=self.menufont)

		if self.os_type != 'mac_os': c.entry.config(bg='#d9d9d9')


		c.completions = []
		c.compidx = 0
		# last completed word
		c.lastword = False
		# last word(prefix) in entry before hitting Tab
		c.lasttmp = False
		c.last_eval_raised_error = False

		# Used in move_setting_console
		c.direction = ['down', 'right']

		c.entry.bind("<Escape>", self.setting_console)
		c.entry.bind("<Return>", self.do_cmd)
		c.entry.bind("<Tab>",  self.do_complete)
		c.entry.bind("<Up>", func=lambda event: self.setting_console_history_walk(event, **{'direction':'up'}) )
		c.entry.bind("<Down>", func=lambda event: self.setting_console_history_walk(event, **{'direction':'down'}) )


		# Even more binding notes, Not ok: "<1-Motion>", "<Button-1-Motion>"
		c.bind("<B1-Motion>",  self.move_setting_console)

		# Get doc-strings
		c.entry.unbind_class('Entry', "<Control-h>")
		c.entry.bind("<Control-h>", self.show_help )

		# Don't select text in entry after hitting Tab
		c.entry.unbind_class('Entry', '<<TraverseIn>>')
		c.entry.pack()

		offset_y = self.entry.winfo_height()
		c.old_x = c.old_y = self.pad*2
		c.old_y += offset_y

		c.place_configure(x=c.old_x, y=c.old_y, width=1, height=1)
		c.place_forget()

		self.to_be_closed.append(c)


	def move_setting_console(self, event=None):
		''' Move setting-console, bit wonky
		'''
		c = self.setting_frame
		# Cursor
		x = event.x
		y = event.y
		# Widget
		old_x = c.old_x
		old_y = c.old_y

		if x > 0:
			new_x = old_x + self.pad

			if c.direction[1] == 'right':
				new_x += self.pad*3
			c.direction[1] = 'right'

		else:
			new_x = old_x - self.pad*3

			if c.direction[1] == 'left':
				new_x -= self.pad*6
			c.direction[1] = 'left'


		if y > old_y:
			new_y = old_y + self.pad * 4

			if c.direction[0] == 'down':
				new_y += self.pad*6
			c.direction[0] = 'down'

		else:
			new_y = old_y - 1

			if c.direction[0] == 'up':
				new_y -= 1
			c.direction[0] = 'up'


		# This helps
		new_y = old_y + y
		new_x = old_x + x
		c.old_x = new_x
		c.old_y = new_y

		kwargs = {'x':new_x, 'y':new_y}
		#c.place_configure(**kwargs)
		self.after(50, c.place_configure(**kwargs))
		return 'break'


	def setting_console(self, event=None):
		''' Toggle: show setting-console, binded to btn_git
		'''
		self.wait_for(30)
		c = self.setting_frame

		if c.winfo_ismapped():
			c.place_forget()
			self.text_widget.focus_set()
		else:
			c.place_configure(x=c.old_x, y=c.old_y)
			c.update_idletasks()
			c.entry.focus_set()

		return 'break'

	#@debug
	def show_message(self, message, delay):
		''' Show message for time delay
		'''
		self.wait_for(30)

		m = self.message_frame
		l = m.label
		l.config(text=message, width=len(message)+2)

		# Remove possible old m.place_forgets
		for item in self.to_be_cancelled['message'][:]:
			self.after_cancel(item)
			self.to_be_cancelled['message'].remove(item)

		# Keep message closer to entry when in fullscreen
		if not m.winfo_ismapped():
			kwargs = {'relx':0.1, 'rely':0.1}
			if self.is_fullscreen():
				x = self.ln_widget.winfo_width()*2
				kwargs = {'x':x, 'y':self.pad*17}

			m.place_configure(**kwargs)
			# This, for same reason, is necessary
			# Otherwise, sometimes in fullscreen, text is not immediately shown
			m.update_idletasks()

		c = self.after(delay, m.place_forget)
		self.to_be_cancelled['message'].append(c)
		return 'break'


	def show_message2(self, message, delay):
		''' Show message for time delay
			when self.message_frame is already in use
		'''
		self.wait_for(30)

		m = self.message_frame2
		l = m.label
		l.config(text=message, width=len(message)+2)

		# Remove possible old m.place_forgets
		for item in self.to_be_cancelled['message2'][:]:
			self.after_cancel(item)
			self.to_be_cancelled['message2'].remove(item)


		m.place_configure(relx=0.8, rely=0.1)
		# This, for same reason, is necessary
		# Otherwise, sometimes in fullscreen, text is not immediately shown
		m.update_idletasks()

		c = self.after(delay, m.place_forget)
		self.to_be_cancelled['message2'].append(c)
		return 'break'


	def message_frame_init(self):
		self.message_frame = f = tkinter.LabelFrame(self, width=1, height=1)
		self.message_frame.label = tkinter.Label(self.message_frame, width=50,
							highlightthickness=0, bd=4, font=self.textfont)
		self.message_frame.configure(labelwidget=self.message_frame.label)
		self.message_frame.label.pack()

		f.place_configure(relx=0.1, rely=0.1, width=1, height=1)
		f.place_forget()

		self.to_be_closed.append(f)


	def message_frame2_init(self):
		self.message_frame2 = f = tkinter.LabelFrame(self, width=1, height=1)
		f.label = tkinter.Label(self.message_frame2, width=50,
							highlightthickness=0, bd=4, font=self.textfont)
		f.configure(labelwidget=self.message_frame2.label)
		f.label.pack()

		f.place_configure(relx=0.9, rely=0.1, width=1, height=1)
		f.place_forget()

		self.to_be_closed.append(f)


	def measure_frame_init(self):
		''' line 1 comments
			line 2 keywords
			line 3 normal_text
		'''
		self.measure_frame = f = tkinter.Frame(self, width=1, height=1)
		f.t = tkinter.Text(f)

		# Not sure does these matter anything
		bg = self.bgcolor
		f.t.config(font=self.textfont, foreground=bg, background=bg, selectbackground=bg,
					selectforeground=bg, inactiveselectbackground=bg, width=100)

		f.t.tag_config('measure_comment', font=self.linenum_font)
		f.t.tag_config('measure_keyword', font=self.keyword_font)
		f.t.insert('1.0', 'BBB\nBBB\nBBB\n')

		# Line *has to be* comments only starting from indent0
		f.t.mark_set('insert', '1.0')
		#########################################
		f.t.tag_add('measure_comment', '1.0', '1.3')
		f.t.tag_add('measure_keyword', '2.0', '2.3')
		f.t.pack()

		f.place_configure(relx=0.1, rely=0.1, width=1, height=1)
		f.place_forget()
		self.to_be_closed.append(f)


	def show_info_message(self, event=None):
		''' Show informatic message
		'''
		self.wait_for(30)
		m = self.message_frame
		l = m.label
		l.config(anchor='w', justify='left')

		# Build info-string msg
		maxlen_msg = 0
		for tab in self.tabs:
			if filepath := tab.filepath:
				lenght = len(filepath.stem + filepath.suffix)
				if lenght > maxlen_msg: maxlen_msg = lenght

		maxlen_msg += 2 # two spaces after title_string

		msg = ' ' +self.title_string +maxlen_msg*' '
		num_spaces = 0
		tail = False
		if filepath := self.tabs[self.tabindex].filepath:
			tail = '  ' +filepath.stem +filepath.suffix
			num_spaces = maxlen_msg - len(tail)

		if tail:
			msg = self.title_string + tail + num_spaces*' '

		msg += ' \n\n' +'State: ' +self.state +' \n\n' +self.get_scope_path('insert')

		self.show_message(msg, 2500)
		self.flash_line(delay=800)
		# Return original setting after window has been forget
		self.after(2600, lambda kwargs={'anchor':'center', 'justify':'center'}: l.config(**kwargs))


	def carousel(self, frame, idx, back):
		''' Handle highlight and scrolling of completions-window
			Called from show_completions
		'''

		widget = frame.listbox
		needs_scroll = False
		one_fifth = 4 # more like one third
		num_items = widget.size()

		start = idx_start = widget.index('@0,0')
		end = idx_end = widget.index('@0,65535')

		idx_last = num_items - 1
		num_items_onscreen = idx_end - idx_start +1
		if num_items > num_items_onscreen:
			needs_scroll = True


		def get_max_len(start):
			end = start + num_items_onscreen
			items = frame.completions[start:end]
			return max(map(len,items))


		widget.select_set(idx)


		if back:
			if idx == idx_last:
				widget.see(idx_last)
				start = num_items - num_items_onscreen


			# if all items does not fit to listbox
			elif needs_scroll:
				idx_new = idx_start + one_fifth

				if idx < idx_new:
					# scroll up one line
					if not idx_start-1 < 0:
						widget.see(idx_start - 1)
						start = idx_start - 1

		else:
			if idx == 0:
				widget.see(0)
				start = 0


			# if all items does not fit to listbox
			elif needs_scroll:
				idx_new = idx_end - one_fifth

				if idx > idx_new:
					# scroll down one line
					if not idx_end+1 > idx_last:
						widget.see(idx_end + 1)
						start = idx_start + 1

		return get_max_len(start)


	def show_completions(self, event=None, back=False):
		''' Show completions-window

			Returns False if there are no completions or unique completion
			Else: True
		'''
		self.wait_for(30)

		f = self.comp_frame
		lb = f.listbox
		lb.selection_clear(0, 'end')

		# Note: update is the prefix-string
		update, word_list, pos, completion = self.expander.expand_word(event=event, back=back)
		# No completions, wrap around or unique
		if pos in [None, -1, 'unique']:
			f.place_forget()
			if pos is None: self.bell()
			return False

		flag_scroll = False

		# New word_list
		if update:
			f.place_forget()

			f.completions = word_list
			lb.delete(0, 'end')
			for item in word_list: lb.insert('end', item)
			lb.see(0)

			# Figuring out the geometry of listbox
			height = len(word_list)
			if  height > 11: height = 11
			lb.height = height

			f.max_len = width = 30
			flag_update_width = False
			# carousel: Handle highlight, scrolling and width
			tmp_max = self.carousel(f, pos, back)

			if tmp_max > f.max_len:
				f.max_len = tmp_max
				width = tmp_max +2
				flag_update_width = True

			lb.config(width=width, height=height)
			# These are important info about geometry
			f.height = lb.winfo_reqheight()
			f.width = width * f.char_width

			# Used to check if scrolling has happened between completions
			f.last_y_top_row = self.text_widget.bbox('@0,0')[1]
			f.lastlinenum, _  = self.get_line_col_as_int(index='@0,0')


		# Handling of f.width here should be better (== only here and nowhere else)
		if not update:
			flag_update_width = False

			# carousel: Handle highlight, scrolling and width
			# returns max item length
			tmp_max = self.carousel(f, pos, back)

			if tmp_max > f.max_len:
				f.max_len = tmp_max
				lb.config(width=tmp_max+2)
				flag_update_width = True

			# Check for possible scrolling between completions, since comp-window is not part of text,
			# and update pos if necessary.
			y_top_row = self.text_widget.bbox('@0,0')[1]
			linenum, _  = self.get_line_col_as_int(index='@0,0')
			if f.lastlinenum != linenum or f.last_y_top_row != y_top_row:
				f.lastlinenum = linenum
				f.last_y_top_row = y_top_row
				update = True
				flag_scroll = True



		# update_pos: Tab-completing first time
		# Completion has *already been inserted* by expander
		# --> affects insertion position
		if update:
			# Count adjust len
			# Explanation: If prefix does not have dot --> adjust would be len(newword)
			# If prefix does have dot --> adjust would also be len(newword)
			# (because words have been lstripped to last dot by expander)
			len_comp = len(completion)

			# Completion has already been inserted by expander.
			# Adjust window position accordingly
			x, y, _, h = self.text_widget.bbox('insert -%dc' % len_comp)

			# These are offsets of text_widget, relative to root.
			# They have to be added, because frame is in root
			offset_x = self.ln_widget.winfo_width()
			if self.want_ln == 0: offset_x = 0
			offset_y = self.entry.winfo_height()

			pad = self.pad*5
			one_line_below = h +2*self.pad


			# Make border-check
			# If near bottom, (window-height +pad +one_line_below insertionline)
			# Then map window above insertionline
			tmp_height = y +f.height +offset_y +pad +one_line_below
			total_height  = self.winfo_height()
			if tmp_height > total_height:
				anchor = 'sw'
				y = y -2*self.pad

				# Make list shorter when necessary
				tmp_height = y -f.height -pad
				while tmp_height < 0:
					# Take one line off
					lb.height -= 1
					lb.config(height=lb.height)
					f.height = lb.winfo_reqheight()
					tmp_height = y -f.height -pad
					if lb.height < 4: break

				# Near right edge, move window left to fit screen
				tmp = self.text_widget.winfo_width()
				if x +f.width +pad > tmp:
					anchor = 'se'
					x = tmp -pad

			# Map window below insertionline (default)
			else:
				anchor = 'nw'
				y = y + one_line_below

				# Near right edge, move window left to fit screen
				tmp = self.text_widget.winfo_width()
				if x +f.width +pad > tmp:
					anchor = 'ne'
					x = tmp -pad


			#print(offset_x, offset_y, f.width, f.height)
			# kwargs for f.place_configure
			f.cur_anchor = anchor
			f.comp_x = x + offset_x
			f.comp_y = y + offset_y
			############################


		# Adjust width while completing, again
		# Handling of width should be done in one place (== not here)
		w = f.char_width * f.max_len
		if flag_update_width:
			w = f.char_width * (f.max_len +2)


		kwargs = {'x':f.comp_x, 'y':f.comp_y, 'width':w, 'anchor':f.cur_anchor}


		# Remove possible old m.place_forgets
		for item in self.to_be_cancelled['completions'][:]:
			self.after_cancel(item)
			self.to_be_cancelled['completions'].remove(item)

		if not f.winfo_ismapped() or flag_scroll:
			f.place_configure(**kwargs)
			# This, for some reason, is necessary
			# Otherwise, sometimes text is not immediately shown
			f.update_idletasks()


		elif flag_update_width:
			f.place_configure(**kwargs)
			flag_update_width = False


		c = self.after(2000, f.place_forget)
		self.to_be_cancelled['completions'].append(c)

		return True
		# show_completions End #######


	def completion_frame_init(self):
		''' Initialize Tab-completions-frame
		'''
		self.comp_frame = f = tkinter.LabelFrame(self, width=1, height=1)


		f.completions = list()

		bg = self.bgcolor
		fg = self.fgcolor
		white = r'#e3e7e3'

		kwargs = {
		'highlightthickness':0,
		'selectborderwidth':0,
		'selectmode':'single',
		'exportselection':0,
		'height':10,
		'bd':0,
		'bg':fg,
		'fg':bg,
		'font':self.textfont,
		'disabledforeground':fg,
		'selectbackground':'blue',
		'selectforeground':white,
		'justify':'left',
		'relief':'flat'
		}

		f.listbox = tkinter.Listbox(self.comp_frame, **kwargs)
		f.listbox.pack()
		f.listbox.height = 11

		f.max_len = 30
		f.comp_x = 1
		f.comp_y = 1
		f.height = 1
		f.width = 1
		f.cur_anchor = 'sw'
		f.char_width = self.textfont.measure('A')

		f.place_configure(relx=0.1, rely=0.1, width=1, height=1)
		f.place_forget()

		self.to_be_closed.append(f)


##	#@debug
##	def test_bind(self, event=None):
##
##		print(60*'  BBB  ')
##		l = [i for i in range(6)]
##		try:
##			print(l[10])
##
##		except IndexError:
##			eval('print("s"')
##
##
##		t1 = int(self.root.tk.eval('clock milliseconds'))
##		a = self.get_scope_path('insert')
##		t2 = int(self.root.tk.eval('clock milliseconds'))
##		t3 = t2-t1
##		print(a, t3, t4, 'ms')
##
##		# When syntax is not updating use this:
##		print('\nState:', self.state,
##		'\ntcl_name_self:', self.tcl_name_of_contents,
##		'\ntcl_name_tab:', self.tabs[self.tabindex].tcl_name_of_contents,
##		'\ncheck_scope:', self.tabs[self.tabindex].check_scope,
##		'\nsyntax_can_auto_update:', self.syntax_can_auto_update)
##
##		return 'break'


	def skip_bindlevel(self, event=None):
		return 'continue'


	def ensure_idx_visibility(self, index, tab=None, back=None):
		''' Ensures index is visible on screen.

			Does not set insert-mark to index.

			May not work on tab if it is not open.
		'''

		b = 2
		if back:
			b = back

		idx_s = '@0,0'
		idx_e = '@0,65535'

		if not tab:
			tab = self.tabs[self.tabindex]

		lineno_start = self.get_line_col_as_int(tab=tab, index=idx_s)[0]
		lineno_end = self.get_line_col_as_int(tab=tab, index=idx_e)[0]
		lineno_ins = self.get_line_col_as_int(tab=tab, index=index)[0]


		# Note, see takes times
		if not lineno_start + b < lineno_ins:
			self.text_widget.see( '%s - %i lines' % (index, b) )
		elif not lineno_ins + 4 < lineno_end:
			self.text_widget.see( '%s + 4 lines' % index )


	def build_launch_test(self, mode):
		''' Used only if debug=True and even then *only* when doing launch-test

			Called from test_launch_is_ok(), mode is "NORMAL" or "DEBUG"

			returns: byte-string, suitable as input for: 'python -',
			which is used in subprocess.run -call in test_launch_is_ok()

			Info on usage: help(henxel.importflags)
			Read before things go wrong: help(henxel.stash_pop)
		'''

		# For example, called from incomplete, or zombie Editor.
		# And for preventing recursion if doing test-launch
		if (self.flags and self.flags.get('launch_test')) or not self.__class__.alive:
			raise ValueError

		# Test-launch Editor (it is set to non visible, but flags can here be edited)
		###################################################################
		# ABOUT TEST-LAUNCH
		# Note that currently, quit_me()
		#				(and everything called from there, like this build_launch_test()
		#				or save_forced() etc.)
		# that currently, quit_me() executes the code that was there at previous import.
		#
		#
		# This means, when one changes flags here,
		#		(or even some normal code, in for example quit_me or save_forced)
		# When one makes changes here, and does launch-test
		# 		--> old flags/code are still used in *executing test-launch*,
		# 									that is, executing quit_me().
		#
		# On the other hand, everything that was saved in save_forced, AND
		# executed in launch-test, DOES use the new code, it is the meaning of
		# launch-test. That is, executed stuff in: launch_test_as_string below.
		###############################################################
		# But after next restart, new flags/code (in quit_me etc) are binded, and used.
		# In short:	When changing flags, and want to see the difference:
		#			1: restart 2: see the difference at next test-launch
		###################################################################



		# Currently used flags are in list below. These have to be in flag_string.
		###################################################################
		# Want to remove some flag completely:
		# 1: Remove/edit all related lines of code, most likely tests like this:
		# 	if self.flags and not self.flags.get('test_is_visible'): self.withdraw()
		# 2: Remove related line from list below: 'test_is_visible=False'
		###################################################################
		# Want to add new flag: 1: add line in list below: 'my_flag=True'
		# 	Flag can be any object: 'my_flag=MyClass(myargs)'
		# 2: Add/edit lines of code one wants to change if this flag is set,
		# most likely tests like this:
		# 	if self.flags and self.flags.get('my_flag'): self.do_something()
		###################################################################
		# Just want to change a flag: edit line in list below,
		# when editing conf-related stuff, for example, one would(in theory):
		# 	'test_skip_conf=False'
		###################################################################
		# And when doing any of above, to see the difference:
		# 	1: restart 2: see the difference at next test-launch
		###################################################################

		flags = ['launch_test=True',
				'test_is_visible=False',
				'test_skip_conf=True',
				'test_fake_error=False',
				'test_func=print_jou'
				]

		flags_as_string = ', '.join(flags)
		flag_string = 'dict(%s)' % flags_as_string
		mode_string = ''
		if mode == 'DEBUG': mode_string = 'debug=True'


		# Basicly, one can do *anything* here, do imports, make
		# function or class definitions on the fly, pass those as values
		# in importflags.FLAGS, then use them in actual code even at import-time!
		###########################################################################
		# If want to test 'safe' runtime error someplace, set: test_fake_error = True
		# And put this line to place where one wants to generate error:
		# if self.flags and self.flags.get('test_fake_error'): this_func_no_exist()
		#
		# in help(henxel.stash_pop) is info about recovering from such errors
		#############################################################################
		# If want also to test some methods, add those lines to: launch_test_as_string
		# below, right after Editor creation, for example:
		# 	a.test_bind()

		launch_test_as_string = '''

def print_jou():
	print('jou')

import importflags
importflags.FLAGS=%s
import henxel
#henxel.FLAGS['test_func']()

a=henxel.Editor(%s)''' % (flag_string, mode_string)

		return bytes(launch_test_as_string, 'utf-8')


	def test_launch_is_ok(self):
		''' Called from quit_me()
		'''
		# For example, called from incomplete, or zombie Editor.
		# And for preventing recursion if doing test-launch
		if (self.flags and self.flags.get('launch_test')) or not self.__class__.alive:
			raise ValueError

		success_all = True

		print()
		#for mode in ['NORMAL', 'DEBUG']:
		for mode in ['DEBUG']:
			flag_success = True
			print('LAUNCHTEST, %s, START' % mode)

			max_time = 5
			tmp = self.build_launch_test(mode)
			d = dict(capture_output=True, timeout=max_time, start_new_session=True)

			# This try block catches only timeouts
			try:
				p = subprocess.run([sys.executable, '-'], input=tmp, **d)

			except subprocess.TimeoutExpired as e:
				print('TIMED OUT')
				print(e)
				return False

			# Now, get the real Errors
			try: p.check_returncode()

			except subprocess.CalledProcessError:
				print('\n' + p.stderr.decode().strip())
				print('\nLAUNCHTEST, %s, FAIL' % mode)
				print(30*'-')
				flag_success = success_all = False

			out = p.stdout.decode().strip()
			if len(out) > 0: print(out)
			if flag_success:
				print('LAUNCHTEST, %s, OK' % mode)
				print(30*'-')

		return success_all


	def version_control_cmd_set(self, cmd_as_list=None):
		''' Set command to fetch current version control branch.
			Command must be given as list. Command is tried before
			setting. You can split command string to list with split,
			or use shlex-modules split.

			Default commands splitting:
			  cmd_as_list = 'git branch --show-current'.split()
			Then:
			  e.version_control_cmd_set(cmd_as_list)

			Likely not needed, but in tricky cases, make
			shell-script to get branch and then use path to that script as command.
			Just remember to put: #!/usr/bin/env bash  or whatever to first line of script.
			And likely the script has to be runnable by user: chmod u+x my_script.sh
			Then: s = ['/path/to/my_script.sh'] and: e.version_control_cmd_set(s)
		'''
		if cmd_as_list == None:
			print(self.version_control_cmd)
			return
		elif type(cmd_as_list) != list:
			self.bell()
			return


		d = dict(stderr=subprocess.PIPE, stdout=subprocess.PIPE)
		if self.os_type == 'mac_os': d = dict(capture_output=True)
		d['timeout'] = 3
		has_err = False
		out = ''

		# fix for macos printing issue
		if self.os_type == 'mac_os':
			try:
				p = subprocess.run(cmd_as_list, **d)

				try: p.check_returncode()
				except subprocess.CalledProcessError:
					has_err = True

			# Note: catches also subprocess.TimeoutExpired
			except Exception as ee:
				print(ee.__str__())
				return

			if has_err:
				err = p.stderr.decode()
				err = err.splitlines()
				for item in err: print(item)
				return

			out = p.stdout.decode().strip()

		else:
			try:
				p = subprocess.run(cmd_as_list, **d)
			except subprocess.TimeoutExpired:
				print('TIMED OUT')
				return

			err = p.stderr.decode()
			if len(err) > 0:
				print(err)
				return

			else: out = p.stdout.decode().strip()


		if len(out) > 0:
			branch = out
			print('Current branch:', branch)
			self.branch = branch
			self.version_control_cmd = cmd_as_list
			self.restore_btn_git()


	def check_syntax_on_exit(self, setting=None):
		''' Should syntax of open py-files be checked at exit
			Without arguments, return current setting
			1: do check (default)
			0: no check
		'''

		if setting is None: pass
		elif setting: self.check_syntax = True
		else: self.check_syntax = False
		print(self.check_syntax)
		return


	def tab_has_syntax_error(self, curtab=False):
		flag_cancel = False

		if curtab:
			if not self.save_forced(curtab=curtab): return 'break'
			tabs = [self.tabs[self.tabindex]]
		else: tabs = self.tabs


		for tab in tabs:
			if tab.filepath:
				if '.py' in tab.filepath.suffix:

					try: ast.parse(tab.contents, filename=tab.filepath.resolve())

					except Exception as e:
						err = '\t' +  e.__str__()
						print( '\nIn: ', tab.filepath.resolve().__str__() )
						print(err)
						flag_cancel = True
						continue

		if curtab:
			if not flag_cancel: self.show_message(' OK ', 1100)
			return 'break'
		else: return flag_cancel


	def do_test_launch(self, event=None, checking_before_quit=False):

		def delayed_break(delay):
			self.wait_for(delay)
			self.bell()
			return 'break'


		if (self.flags and self.flags.get('launch_test')) or not self.__class__.alive:
			raise ValueError

		# checking_before_quit: ensure quit_me gets False (when some check fails)
		# --> cancel exit (when debugging)
		elif not self.save_forced():
			if checking_before_quit: return False
			return delayed_break(33)

		elif self.tab_has_syntax_error():
			self.activate_terminal()
			if checking_before_quit: return False
			return delayed_break(33)

		elif checking_before_quit: return self.test_launch_is_ok()

		# Doing test_launch volunteerily, great!
		else: self.test_launch_is_ok()

		return 'break'


	def force_quit_editor(self):
		self.quit_me(force_close=True)
		return 'break'


	def activate_terminal(self, event=None):
		''' Give focus back to Terminal when quitting
		'''
		if self.os_type != 'mac_os': return

		# https://ss64.com/osx/osascript.html
		mac_term = 'Terminal'

		try:
			# Giving focus back to python terminal-window is not very simple task in macOS
			# https://apple.stackexchange.com/questions/421137
			tmp = None
			if self.__class__.mac_term and self.__class__.win_id:
				mac_term = self.__class__.mac_term
				win_id  = self.__class__.win_id

				if mac_term == 'iTerm2':
					tmp = [ 'osascript', '-e', 'tell app "%s" to select windows whose id = %s' % (mac_term, win_id), '-e', 'tell app "%s" to activate' % mac_term ]

				else:
					tmp = [ 'osascript', '-e', 'tell app "%s" to set frontmost of windows whose id = %s to true' % (mac_term, win_id), '-e', 'tell app "%s" to activate' % mac_term ]

			elif self.__class__.mac_term:
				mac_term = self.__class__.mac_term
				tmp = ['osascript', '-e', 'tell app "%s" to activate' % mac_term ]

			else:
				tmp = ['osascript', '-e', 'tell app "%s" to activate' % mac_term ]

			subprocess.run(tmp)

		except (FileNotFoundError, subprocess.SubprocessError):
			pass

		# No need to put in thread
		#t = threading.Thread( target=subprocess.run, args=(tmp,), daemon=True )
		#t.start()


	def	cleanup(self, event=None):

		# Affects color, fontchoose, load:
		for widget in self.to_be_closed:
			widget.destroy()

		for tab in self.tabs + [self.help_tab, self.err_tab]:
			tab.text_widget.destroy()
			del tab.text_widget

		self.quit()
		self.destroy()

		if self.os_type == 'mac_os': self.activate_terminal()

		if self.tracefunc_name:
			self.tracevar_filename.trace_remove('write', self.tracefunc_name)

		del self.btn_git
		del self.entry
		del self.btn_open
		del self.btn_save
		del self.ln_widget
		del self.text_widget
		del self.scrollbar
		del self.expander
		del self.popup
		del self.text_frame
		del self.msgbox


	def quit_me(self, event=None, force_close=False):

		def delayed_break(delay):
			self.wait_for(delay)
			return 'break'


		# For example, called from incomplete, or zombie Editor.
		# And for preventing recursion if doing test-launch
		if (self.flags and self.flags.get('launch_test')) or not self.__class__.alive:
			raise ValueError


		if self.debug:
			# Forced launch-test at exit
			if not self.do_test_launch(checking_before_quit=True):
				self.activate_terminal()
				return delayed_break(33)

		else:
			if not self.save_forced() and not force_close: return delayed_break(33)
			elif self.check_syntax and self.tab_has_syntax_error() and not force_close:
				self.activate_terminal()
				return delayed_break(33)


		# Prepare for quit (save bookmarks and configuration)
		for tab in self.tabs: self.save_bookmarks(tab, also_stashed=True)

		# Closing after: first launch, no conf or geometry reset to 'default'
		# Assuming if user changed geometry, it was not satisfactory
		# --> use current geometry
		if self.flag_check_geom_at_exit and not self.is_fullscreen():
			geom_current = self.get_geometry()
			if self.geom != geom_current: self.geom = geom_current


		# Save config after possibly first launch from terminal
		if not self.conf_load_success: self.save_config()
		# Do not overwrite 'real' config
		elif not self.one_time_conf: self.save_config()

		self.config(bg='') # Prevent flashing if slow machine
		self.update_idletasks()
		self.cleanup()


		self.__class__.alive = False

		#### quit_me End ##############


	def get_line_col_as_int(self, tab=None, index='insert'):
		''' index: tk text -index
		'''
		if not tab:
			tab = self.tabs[self.tabindex]

		line,col = map(int, tab.text_widget.index(index).split('.'))
		return line,col


	def cursor_is_in_multiline_string(self, tab=None):
		''' Called from check_line
		'''
		# Note:
		# 'strings' in self.text_widget.tag_names('insert')
		# will return True when cursor is at marked places or between them:

		# <INSERT>''' multiline string
		# multiline string
		# ''<INSERT>'

		if ('strings' in tab.text_widget.tag_names('insert')):
			try:
				s, e = tab.text_widget.tag_prevrange('strings', 'insert')

				l0,_ = self.get_line_col_as_int(tab=tab, index=s)
				l1,_ = self.get_line_col_as_int(tab=tab, index=e)

				if l0 != l1: return True

			except ValueError:
				pass

		return False


	def check_line(self, oldline=None, newline=None, on_oldline=True, tab=None):
		''' oldline, newline:	string
			on_oldline:			bool	(tab.oldlinenum == linenum curline)
		'''

		ins_col = col = self.get_line_col_as_int(tab=tab)[1]

		triples = ["'''", '"""']
		pars = '()[]{}'

		# Counted from insert
		prev_char = newline[col-1:col]


		# Paste/Undo etc is already checked.
		# Also deletion is already checked in backspace_override.
		#
		# There should only be:
		# Adding one letter

		############
		# In short:
		# Every time char is added or deleted inside multiline string,
		# or on such line that contains triple-quote
		# --> update tokens of whole scope
		########################


		#############
		# Check pars:
		# Deletion is already checked in backspace_override
		# Only add one letter is left unchecked
		# -->
		if not tab.par_err:
			if prev_char in pars: tab.par_err = True
##			else:
##				for char in newline:
##					if char in pars:
##						tab.par_err = True
##						break
		############


		# Check if need to update tokens in whole scope
		if not tab.check_scope:

			if self.cursor_is_in_multiline_string(tab): tab.check_scope = True

			elif on_oldline:

				for triple in triples:
					# Not in multiline string, but on same line with triple-quote
					# 1: Before first triple
					# 2: After last triple
					# 3: Triple was just born by addition
					if triple in newline:
						tab.check_scope = True
						break

					# Triple die (by addition in middle: ''a' or 'a'')
					# Should already be covered by: cursor_is_in_multiline_string-call above
					# (Except it is not in case both triples were on the same line)
					elif triple in oldline and triple not in newline:
						tab.check_scope = True
						break

			# On newline, one letter changed, deletion is checked already
			# --> Only add one letter is left unchecked
			# Note: triple die: ''a' and 'a'' is already covered by
			# cursor_is_in_multiline_string -call above
			# (Except it is not in case both triples were/are on the same line)
			# In that case, test below works only if one triple is alive
			else:
				for triple in triples:
					if triple in newline:
						tab.check_scope = True
						break



		s,e = '',''

		if tab.check_scope:
##			# This generates indentation errors:
##			# fix for multiline strings at __main__()
##			###
##			if r := self.text_widget.tag_prevrange('deflin', 'insert'):
##				s = r[0] + ' linestart'
##			else:
##				s = '1.0'
##
##			if r := self.text_widget.tag_nextrange('deflin', 'insert'):
##				e = r[0] + ' -1 lines linestart'
##			else:
##				e = 'end'

##			# Another version
##			if t := self.get_absolutely_next_defline(down=False, update=True):
##				_, next_deflinenum_as_float, _ = t
##				s = str(next_deflinenum_as_float) + ' linestart'
##			else:
##				s = '1.0'
##
##			if t := self.get_absolutely_next_defline(down=True, update=False):
##				_, next_deflinenum_as_float, _ = t
##				e = str(next_deflinenum_as_float) + ' -1 lines linestart'
##			else:
##				e = 'end'


			# Currently used version
			( scope_line, ind_defline, idx_scope_start) = self.get_scope_start()

			idx_scope_end = self.get_scope_end(ind_defline, idx_scope_start)

			s = '%s linestart' % idx_scope_start
			e = idx_scope_end

		else:
			s = 'insert linestart'
			e = 'insert lineend'

##		print('\ncheck_line:', '\nold_line:', oldline, '\nnew_line:', newline,
##			'\non_oldline:', on_oldline, '\ncheck_scope:', tab.check_scope, s, e)


		if tab.check_scope:
			self.update_tokens(start=s, end=e)
		else:
			self.update_tokens(start=s, end=e, line=newline)

		###### check_line End ##########


	def update_lineinfo(self, tab=None):
		''' Update info about current line, which is used to determine if
			tokens of the line has to be updated for syntax highlight.

			When this is called, the info is up to date and thus
			prevents update for the line (in auto_update_syntax), which is the purpose.

			This should be called before calling: auto_update_syntax_continue
		'''

		if not tab:
			tab = self.tabs[self.tabindex]

		linestart = 'insert linestart'
		lineend = 'insert lineend'
		tab.oldline = tab.text_widget.get( linestart, lineend )
		tab.oldlinenum,_ = self.get_line_col_as_int(tab=tab)


	def auto_update_syntax_stop(self):
		''' syntax_can_auto_update is only temporary stopper-flag
			used in many places to temporarily stop auto_update_syntax.
		'''
		self.syntax_can_auto_update = False


	def auto_update_syntax_continue(self):
		''' syntax_can_auto_update is only temporary stopper-flag
			used in many places to temporarily stop auto_update_syntax.
		'''
		if self.syntax: self.syntax_can_auto_update = True


	def auto_update_syntax(self, event=None):
		'''	Triggers after event: <<WidgetViewSync>>

			Used to update linenumbers and syntax highlighting of current line.
			Intention of this is to update syntax when normally just typing in.
			This is not used for example when doing paste.

			The event itself is generated *after* when inserting, deleting
			or on screen geometry change, but not when just scrolling (like yview).
			Almost all font-changes also generate this event.

		'''

		tab = self.tabs[self.tabindex]
		if self.want_ln == 2: self.update_linenums()


		if self.can_do_syntax(tab) and self.syntax_can_auto_update:

			# Tag alter triggers this event if font changes, like from normal to bold.
			# --> need to check if line is changed to prevent self-trigger
			linenum,_ = self.get_line_col_as_int(tab=tab)

			lineend = 'insert lineend'
			linestart = 'insert linestart'

			curline = tab.text_widget.get( linestart, lineend )
			on_oldline = bool(tab.oldlinenum == linenum)


			if tab.oldline != curline or not on_oldline:
				tab.oldline = curline
				tab.oldlinenum = linenum
				#t1 = int(self.root.tk.eval('clock milliseconds'))
				self.check_line( oldline=tab.oldline, newline=curline,
								on_oldline=on_oldline, tab=tab)

				#t2 = int(self.root.tk.eval('clock milliseconds'))
				#print(t2-t1, 'ms')
				#print('sync')


############## Init etc End
############## Bindings Begin

	def set_bindings(self, tab):
		''' Set bindings for text_widget

			text_widget:	tkinter Text-widget

			Called from init

		'''

		w = tab.text_widget

		# Binds with ID Begin
		tab.bid_space = w.bind( "<space>", self.space_override)
		# Binds with ID End

		if self.os_type == 'linux':
			w.bind( "<ISO_Left_Tab>", self.unindent)
			# Move by two words right/left
			w.bind( "<Control-period>", self.move_by_words2)
			w.bind( "<Control-comma>", self.move_by_words2)
		else:
			w.bind( "<Shift-Tab>", self.unindent)
			w.bind( "<Control-.>", self.move_by_words2)
			w.bind( "<Control-,>", self.move_by_words2)


		w.unbind_class('Text', '<Button-3>')
		w.unbind_class('Text', '<B3-Motion>')
		w.event_delete('<<PasteSelection>>')

		############################################################
		# In macOS all Alt-shortcuts makes some special symbol.
		# Have to bind to this symbol-name to get Alt-shorcuts work.
		# For example binding to Alt-f:
		# w.bind( "<function>", self.font_choose)

		# Except that tkinter does not give all symbol names, like
		# Alt-x or l
		# which makes these key-combinations quite unbindable.
		# It would be much easier if one could do bindings normally:
		# Alt-SomeKey
		# like in Linux and Windows.

		# Also binding to combinations which has Command-key (apple-key)
		# (or Meta-key as reported by events.py)
		# must use Mod1-Key as modifier name:
		# Mod1-Key-n == Command-Key-n

		# fn-key -bindings have to be done by checking the state of the event
		# in proxy-callback: mac_cmd_overrides

		# In short, In macOS one can not just bind like:
		# Command-n
		# fn-f
		# Alt-f

		# This is the reason why below is some extra
		# and strange looking binding-lines when using macOS.
		##############################################################
		if self.os_type != 'mac_os':

			w.bind( "<Alt-b>", self.goto_bookmark)
			w.bind( "<Alt-B>",
				lambda event: self.goto_bookmark(event, **{'back':True}) )

			w.bind( "<Control-l>", self.gotoline)
			w.bind( "<Alt-g>", self.goto_def)
			w.bind( "<Alt-p>", self.toggle_bookmark)
			w.bind( "<Alt-u>", self.stash_bookmark)

			w.bind( "<Alt-i>", self.show_info_message)
			w.bind( "<Alt-c>", self.start_new_console)
			w.bind( "<Alt-m>", self.popup_raise)


			w.bind( "<Alt-s>", self.color_choose)
			w.bind( "<Alt-t>", self.toggle_color)

			w.bind( "<Alt-Return>", self.load)
			w.bind( "<Alt-l>", self.toggle_ln)
			w.bind( "<Alt-x>", self.toggle_syntax)
			w.bind( "<Alt-f>", self.font_choose)

			w.bind( "<Control-c>", self.copy)
			w.bind( "<Control-v>", self.paste)
			w.bind( "<Control-x>",
				lambda event: self.copy(event, **{'flag_cut':True}) )

			w.bind( "<Control-y>", self.yank_line)

			w.bind( "<Control-Left>", self.move_by_words)
			w.bind( "<Control-Right>", self.move_by_words)
			w.bind( "<Control-Shift-Left>", self.select_by_words)
			w.bind( "<Control-Shift-Right>", self.select_by_words)

			w.bind( "<Alt-a>", self.goto_linestart)
			w.bind( "<Alt-e>", self.goto_lineend)
			w.bind( "<Alt-Shift-Left>", self.goto_linestart)
			w.bind( "<Alt-Shift-Right>", self.goto_lineend)

			w.bind( "<Control-Up>", self.move_many_lines)
			w.bind( "<Control-Down>", self.move_many_lines)
			w.bind( "<Control-Shift-Up>", self.move_many_lines)
			w.bind( "<Control-Shift-Down>", self.move_many_lines)

			w.bind( "<Control-Shift-parenleft>", self.walk_scope)
			w.bind( "<Control-8>",
				lambda event: self.walk_scope(event, **{'absolutely_next':True}) )
			w.bind( "<Control-Shift-parenright>",
				lambda event: self.walk_scope(event, **{'down':True}) )
			w.bind( "<Control-9>",
				lambda event: self.walk_scope(event, **{'down':True, 'absolutely_next':True}) )

			w.bind( "<Alt-Shift-F>", self.select_scope)
			w.bind( "<Alt-Shift-E>", self.elide_scope)

			w.bind("<Left>", self.check_sel)
			w.bind("<Right>", self.check_sel)

			# Hide completions-window with arrow up/down
			w.bind("<Up>", func=self.handle_updown)
			w.bind("<Down>", func=self.handle_updown)

			w.bind( "<Alt-Key-BackSpace>", self.del_to_dot)


		# self.os_type == 'mac_os':
		else:

			w.bind( "<Left>", self.mac_cmd_overrides)
			w.bind( "<Right>", self.mac_cmd_overrides)
			w.bind( "<Up>", self.mac_cmd_overrides)
			w.bind( "<Down>", self.mac_cmd_overrides)

			w.bind( "<f>", self.mac_cmd_overrides)		# + fn full screen

			# Have to bind using Mod1 as modifier name if want bind to Command-key,
			# Last line is the only one working:
			#w.bind( "<Meta-Key-k>", lambda event, arg=('AAA'): print(arg) )
			#w.bind( "<Command-Key-k>", lambda event, arg=('AAA'): print(arg) )
			#w.bind( "<Mod1-Key-k>", lambda event, arg=('AAA'): print(arg) )

			# 8,9 as '(' and ')' without Shift, nordic key-layout
			# 9,0 in us/uk ?
			w.bind( "<Mod1-Shift-(>", self.walk_scope)
			w.bind( "<Mod1-Key-8>",
				lambda event: self.walk_scope(event, **{'absolutely_next':True}) )
			w.bind( "<Mod1-Shift-)>",
				lambda event: self.walk_scope(event, **{'down':True}) )
			w.bind( "<Mod1-Key-9>",
				lambda event: self.walk_scope(event, **{'down':True, 'absolutely_next':True}) )

			w.bind( "<Mod1-Shift-F>", self.select_scope)
			w.bind( "<Mod1-Shift-E>", self.elide_scope)

			w.bind( "<Mod1-Key-y>", self.yank_line)
			w.bind( "<Mod1-Key-n>", self.new_tab)

			w.bind( "<Mod1-Key-i>", self.show_info_message)

			w.bind( "<Mod1-Key-f>", self.search)
			w.bind( "<Mod1-Key-r>", self.replace)
			w.bind( "<Mod1-Key-R>", self.replace_all)

			w.bind( "<Mod1-Key-c>", self.copy)
			w.bind( "<Mod1-Key-v>", self.paste)
			w.bind( "<Mod1-Key-x>",
				lambda event: self.copy(event, **{'flag_cut':True}) )

			w.bind( "<Mod1-Key-b>", self.goto_bookmark)
			w.bind( "<Mod1-Key-B>",
				lambda event: self.goto_bookmark(event, **{'back':True}) )

			w.bind( "<Mod1-Key-p>", self.toggle_bookmark)
			w.bind( "<Mod1-Key-u>", self.stash_bookmark)
			w.bind( "<Mod1-Key-g>", self.goto_def)
			w.bind( "<Mod1-Key-l>", self.gotoline)
			w.bind( "<Mod1-Key-a>", self.goto_linestart)
			w.bind( "<Mod1-Key-e>", self.goto_lineend)

			w.bind( "<Mod1-Key-z>", self.undo_override)
			w.bind( "<Mod1-Key-Z>", self.redo_override)

			# Could not get keysym for Alt-l and x, so use ctrl
			w.bind( "<Control-l>", self.toggle_ln)
			w.bind( "<Control-x>", self.toggle_syntax)

			# have to bind to symbol name to get Alt-shorcuts work in macOS
			# This is: Alt-f
			w.bind( "<function>", self.font_choose)		# Alt-f
			w.bind( "<dagger>", self.toggle_color)		# Alt-t
			w.bind( "<ssharp>", self.color_choose)		# Alt-s
			w.bind( "<ccedilla>", self.start_new_console) # Alt-c
			w.bind( "<rightsinglequotemark>", self.popup_raise) # Alt-m


			w.bind( "<Mod1-Key-BackSpace>", self.del_to_dot)
			w.bind( "<Mod1-Key-Return>", self.load)


		#######################################################

		# self.os_type == any:
		w.bind( "<Control-u>", self.center_view)
		w.bind( "<Control-j>",
			lambda event: self.center_view(event, **{'up':True}) )
		w.bind( "<Control-Shift-U>", self.center_view)
		w.bind( "<Control-Shift-J>",
			lambda event: self.center_view(event, **{'up':True}) )


		w.bind( "<Control-d>", self.del_tab)
		w.bind( "<Control-Q>",
			lambda event: self.del_tab(event, **{'save':False}) )

		w.bind( "<Shift-Return>", self.comment)
		w.bind( "<Shift-BackSpace>", self.uncomment)
		w.bind( "<Tab>", self.indent)

		w.bind( "<Control-Tab>", self.insert_tab)

		w.bind( "<Control-Shift-K>", self.strip_first_char)
		w.bind( "<Control-t>", self.tabify_lines)
		w.bind( "<Control-z>", self.undo_override)
		w.bind( "<Control-Z>", self.redo_override)
		w.bind( "<Control-f>", self.search)

		w.bind( "<Return>", self.return_override)
		w.bind( "<BackSpace>", self.backspace_override)


		# Used in searching
		w.bind( "<Control-n>", self.search_next)
		w.bind( "<Control-p>",
				lambda event: self.search_next(event, **{'back':True}) )


		# Unbind some default bindings
		# Paragraph-bindings: too easy to press by accident
		w.unbind_class('Text', '<<NextPara>>')
		w.unbind_class('Text', '<<PrevPara>>')
		w.unbind_class('Text', '<<SelectNextPara>>')
		w.unbind_class('Text', '<<SelectPrevPara>>')

		# LineStart and -End:
		# fix goto_linestart-end and
		# enable tab-walking in mac_os with cmd-left-right
		w.unbind_class('Text', '<<LineStart>>')
		w.unbind_class('Text', '<<LineEnd>>')
		w.unbind_class('Text', '<<SelectLineEnd>>')
		w.unbind_class('Text', '<<SelectLineStart>>')

		# Binded after linestart/end unbinds, just in case
		w.bind( "<Home>", self.goto_linestart)
		w.bind( "<End>", self.goto_lineend)
		w.bind( "<Shift-Key-Home>", self.goto_linestart)
		w.bind( "<Shift-Key-End>", self.goto_lineend)


		# Below, compensation for (possibly) missing PgUp/Down -keys,
		# Control-1/2 (selecting), Control-3/4 just moving
		#
		# Copying Tcl func from one bind to other, example:
		# ( Next means PgDown, Prior means PgUp )
		# proc = w.bind_class('Text', '<Key-Next>').strip()
		# w.bind('<Control-Key-4>', proc)
		#
		# Using hardcoded binds to save time, though

		proc = 'tk::TextSetCursor %W [tk::TextScrollPages %W 1]'
		w.bind('<Control-Key-4>', proc)
		proc = 'tk::TextSetCursor %W [tk::TextScrollPages %W -1]'
		w.bind('<Control-Key-3>', proc)
		proc = 'tk::TextKeySelect %W [tk::TextScrollPages %W 1]'
		w.bind('<Control-Key-2>', proc)
		proc = 'tk::TextKeySelect %W [tk::TextScrollPages %W -1]'
		w.bind('<Control-Key-1>', proc)


		# Remove some unwanted key-sequences, which otherwise would
		# mess with searching, from couple of virtual events.
		tmp = list()
		for seq in w.event_info('<<NextLine>>'):
			if seq != '<Control-Key-n>': tmp.append(seq)

		w.event_delete('<<NextLine>>')
		w.event_add('<<NextLine>>', *tmp)

		tmp.clear()
		for seq in w.event_info('<<PrevLine>>'):
			if seq != '<Control-Key-p>': tmp.append(seq)

		w.event_delete('<<PrevLine>>')
		w.event_add('<<PrevLine>>', *tmp)

		w.bind( "<<WidgetViewSync>>", self.auto_update_syntax)
		# Viewsync-event does not trigger at window size changes,
		# to get linenumbers right, one binds to this:
		w.bind("<Configure>", self.handle_window_resize)

		#### set_bindings for Text-widget End #######


	def set_bindings_other(self):
		''' Set bindings for other than Text-widgets

			Called from init
		'''

		## popup
		self.right_mousebutton_num = 3

		# This is changing to 3?
		if self.os_type == 'mac_os':
			self.right_mousebutton_num = 2


		# Binds with ID Begin
		self.entry.bid_ret = self.entry.bind("<Return>", self.load)
		# Binds with ID End

		# While not in normal mode:
		# Don't do: (select text in entry) after pressing Tab (in entry)
		self.entry.unbind_class('Entry', '<<TraverseIn>>')
		self.entry.bind( "<Control-Tab>", self.insert_tab)


		self.bind( "<Button-%i>" % self.right_mousebutton_num, self.popup_raise)
		self.popup.bind("<FocusOut>", self.popup_focusOut) # to remove popup when clicked outside

		# Disable popup in other than Text-widget
		for widget in [self.entry, self.btn_open, self.btn_save, self.btn_git,
			self.ln_widget, self.scrollbar]:
			widget.bind( "<Button-%i>" % self.right_mousebutton_num, self.do_nothing_without_bell)
		## popup end


		if self.os_type == 'mac_os':

			self.entry.bind( "<Right>", self.mac_cmd_overrides)
			self.entry.bind( "<Left>", self.mac_cmd_overrides)

			self.entry.bind( "<Mod1-Key-a>", self.goto_linestart)
			self.entry.bind( "<Mod1-Key-e>", self.goto_lineend)

			self.entry.bind("<registered>", func=self.toggle_search_setting_regexp )
			self.entry.bind("<idotless>", func=self.toggle_search_setting_starts_from_insert )
			self.bind("<registered>", func=self.toggle_search_setting_regexp )
			self.bind("<idotless>", func=self.toggle_search_setting_starts_from_insert )


			#######################################
			# Default cmd-q does not trigger quit_me
			# Override Cmd-Q (can cancel quit app when necessary)
			# https://www.tcl.tk/man/tcl8.6/TkCmd/tk_mac.html
			self.root.createcommand("tk::mac::Quit", self.quit_me)
			#self.root.createcommand("tk::mac::OnHide", self.test_hide)
			#########################################

		else:

			self.entry.bind("<Alt-r>", func=self.toggle_search_setting_regexp )
			self.entry.bind("<Alt-i>", func=self.toggle_search_setting_starts_from_insert )
			self.bind("<Alt-r>", func=self.toggle_search_setting_regexp )
			self.bind("<Alt-i>", func=self.toggle_search_setting_starts_from_insert )

			self.bind( "<Alt-n>", self.new_tab)
			self.bind( "<Control-q>", self.quit_me)

			self.bind( "<Control-R>", self.replace_all)
			self.bind( "<Control-r>", self.replace)

			self.bind( "<Alt-w>", self.walk_tabs)
			self.bind( "<Alt-q>", lambda event: self.walk_tabs(event, **{'back':True}) )
			self.bind( "<Alt-Right>", self.walk_tabs)
			self.bind( "<Alt-Left>", lambda event: self.walk_tabs(event, **{'back':True}) )


			self.entry.bind("<Left>", self.check_sel)
			self.entry.bind("<Right>", self.check_sel)


		if self.os_type == 'windows':

			self.entry.bind( "<Control-E>",
				lambda event, arg=('<<SelectLineEnd>>'): self.entry.event_generate)
			self.entry.bind( "<Control-A>",
				lambda event, arg=('<<SelectLineStart>>'): self.entry.event_generate)

			self.entry.bind( "<Control-c>", self.copy_windows)
			self.entry.bind( "<Control-x>",
				lambda event: self.copy_windows(event, **{'flag_cut':True}) )


		# Arrange detection of CapsLock-state
		self.capslock = 'init'
		self.motion_bind = self.bind('<Motion>', self.check_caps)
		if self.os_type != 'mac_os':
			self.bind('<Caps_Lock>', self.check_caps)
		else:
			self.bind('<KeyPress-Caps_Lock>', self.check_caps)
			self.bind('<KeyRelease-Caps_Lock>', self.check_caps)


		self.bind( "<Escape>", self.esc_override )
		self.bind( "<Return>", self.do_nothing_without_bell)


		self.ln_widget.bind("<Control-n>", self.do_nothing_without_bell)
		self.ln_widget.bind("<Control-p>", self.do_nothing_without_bell)

		# Disable copying linenumbers
		shortcut = '<Mod1-Key-c>'
		if self.os_type != 'mac_os': shortcut = '<Control-c>'
		self.ln_widget.bind(shortcut, self.do_nothing_without_bell)


############## Bindings End
############## Linenumbers Begin

	def toggle_ln(self, event=None):

		self.wait_for(100)

		# 2 1 0
		self.want_ln -= 1
		if self.want_ln < 0: self.want_ln = 2


		if self.want_ln == 1:
			self.ln_widget.config(state='normal')
			self.ln_widget.delete('1.0', 'end')
			self.ln_widget.config(state='disabled')

		elif self.want_ln == 0:
			self.wait_for(100)

			self.ln_widget.grid_remove()
			self.text_frame.columnconfigure(1, weight=0)
			self.text_frame.columnconfigure(0, weight=1)
			self.text_widget.grid_configure(row=0, column=0, columnspan=4,
									sticky='nsew')
		else:
			self.text_frame.columnconfigure(0, weight=0)
			self.text_frame.columnconfigure(1, weight=1)
			self.ln_widget.grid_configure(row=0, column=0, sticky='nsew')
			self.text_widget.grid_configure(row=0, column=1, columnspan=3,
										sticky='nswe')
			self.ln_string = ''
			self.update_linenums()


		return 'break'


	def get_linenums(self):

		x = 0
		line = '0'
		col= ''
		ln = ''

		# line-height is used as step, it depends on many things, one is font
		step = self.line_height

		nl = '\n'
		lineMask = '%s\n'

		# @x,y is tkinter text-index -notation:
		# The character that covers the (x,y) -coordinate within the text's window.
		indexMask = '@0,%d'

		# stepping lineheight at time, checking index of each lines first cell, and splitting it.

		for i in range(0, self.text_widget_height, step):

			ll, cc = self.text_widget.index( indexMask % i).split('.')

			if line == ll:
				# line is wrapping
				if col != cc:
					col = cc
					ln += nl
			else:
				line, col = ll, cc
				# -5: show up to four smallest number (0-9999)
				# then starts again from 0 (when actually 10000)
				ln += (lineMask % line)[-5:]

		return ln


	def update_linenums(self):

		# self.ln_widget is linenumber-widget,
		# self.ln_string is string which holds the linenumbers in self.ln_widget
		tt = self.ln_widget
		ln = self.get_linenums()

		if self.ln_string != ln:
			self.ln_string = ln

			#########################
			# About bbox and indexes
			#
			# There are two very different class of indexes in tk text widget
			#
			# Most often used are 'normal' indexes like 'insert +2lines'
			# or '12.1'. They refer to lines and characters of Text-widget.
			# This kind of index can be offscreen, not currently visible.
			# And if that index is not currently visible, then calling
			#
			#	bbox(idx_not_visible) returns: None
			#
			#
			# There is also index notation like '@0,0' which refer to
			# coordinates(inner == relative == not absolute) of widget window.
			#
			# These indexes are always visible by definition and calling
			#
			#	bbox(@X,Y) should never return None
			#
			###################################


			# 1 - 3 : adjust linenumber-lines with text-lines

			# 1:
			# @0,0 is currently visible first character at
			# x=0 y=0 in text-widget.

			# 2: bbox returns this kind of tuple: (3, -9, 19, 38)
			# (bbox is cell that holds a character)
			# (x-offset, y-offset, width, height) in pixels
			# Want y-offset of first visible line, and reverse it

			# note: if font is different at @0,0 like def with smaller font
			# its bbox is different. --> sometimes wonky linenums
			# --> should use dlineinfo?

			# See dev/todo.txt for explanation why this is currently
			# commented out, search "strange bug"
			#y_offset = self.text_widget.bbox('@0,0')[1]
			y_offset = self.text_widget.dlineinfo('@0,0')[1]
			y_offset *= -1

			# if self.y_extra_offset > 0, this is needed:
			if y_offset != 0:
				y_offset += self.y_extra_offset

			tt.config(state='normal')
			tt.delete('1.0', 'end')
			tt.insert('1.0', ln)
			tt.tag_add('justright', '1.0', 'end')


			# 3: Then scroll ln_widget same amount to fix offset
			# compared to text-widget:
			tt.yview_scroll(y_offset, 'pixels')

			tt.config(state='disabled')


############## Linenumbers End
############## Tab Related Begin

	def new_tab(self, event=None):

		if self.state != 'normal':
			self.bell()
			return 'break'


		newtab = Tab(self.create_textwidget())

		self.set_textwidget(newtab)
		self.set_syntags(newtab)
		self.set_bindings(newtab)
		newtab.text_widget['yscrollcommand'] = lambda *args: self.sbset_override(*args)
		newtab.text_widget.mark_set('insert', '1.0')


		self.tab_close(self.tabs[self.tabindex])
		self.tab_open(newtab)

		self.tabindex += 1
		self.tabs.insert(self.tabindex, newtab)

		self.update_title()
		return 'break'


	def del_tab(self, event=None, save=True):
		''' save=False from Cmd/Control-Shift-Q
		'''

		if self.state != 'normal':
			self.bell()
			return 'break'

		oldindex = self.tabindex
		oldtab = self.tabs[oldindex]


		if len(self.tabs) == 1 and oldtab.type == 'newtab':
			self.clear_bookmarks()
			oldtab.bookmarks.clear()
			self.text_widget.delete('1.0', tkinter.END)
			self.bell()
			return 'break'


		# Prevent loosing bookmarks when mistakenly pressed ctrl-d
		# --> Ask confirmation if tab have bookmarks
		tests = ( save == True and len(oldtab.bookmarks) > 0,
				oldtab.type == 'normal'
				)
		if all(tests):
			msg_options = dict(message='Current tab has bookmarks',
				detail='Will loose those bookmarks, close anyway?')
			res = self.msgbox.show(**msg_options)
			if res == 'cancel':
				return 'break'


		if oldtab.type == 'normal' and save:
			if not self.save(activetab=True):
				self.bell()
				return 'break'



		if len(self.tabs) == 1:
			newtab = Tab(self.create_textwidget())

			self.set_textwidget(newtab)
			self.set_syntags(newtab)
			self.set_bindings(newtab)
			newtab.text_widget['yscrollcommand'] = lambda *args: self.sbset_override(*args)
			newtab.text_widget.mark_set('insert', '1.0')

			self.tabs.append(newtab)


		flag_at_end = False
		# Popping at end
		if len(self.tabs) == self.tabindex +1:
			# Note: self.tabindex decreases by one in this case
			newtab = self.tabs[-2]
			flag_at_end = True
		else:
			# Note: self.tabindex remains same in this case
			newtab = self.tabs[self.tabindex +1]


		self.tab_close(oldtab)
		self.tab_open(newtab)

		oldtab.text_widget.destroy()
		del oldtab.text_widget
		self.tabs.pop(oldindex)
		if flag_at_end: self.tabindex -= 1

		self.update_title()

		return 'break'


	def tab_open(self, tab):
		''' Called from:

			del_tab
			new_tab
			walk_tabs
			tag_link
			stop_help
			stop_show_errors

			Important side effect: changes where self.text_widget references
		'''

		tab.active = True

		self.anchorname = tab.anchorname
		self.tcl_name_of_contents = tab.tcl_name_of_contents

		if tab.filepath:
			self.entry.insert(0, tab.filepath)
			self.entry.xview_moveto(1.0)

		#########################################
		self.text_widget = tab.text_widget
		#########################################

		self.scrollbar.config(command=self.text_widget.yview)
		self.scrollbar.set(*self.text_widget.yview())
		if self.want_ln == 2: self.update_linenums()

		if self.want_ln > 0:
			self.text_widget.grid_configure(row=0, column=1, columnspan=3, sticky='nsew')
		else:
			self.text_widget.grid_configure(row=0, column=0, columnspan=4, sticky='nsew')


		self.text_widget.focus_set()

		# This is needed for some reason to prevent flashing
		# when using fast machine
		self.update_idletasks()


	def tab_close(self, tab):
		''' Called from:
			new_tab
			walk_tabs
			show_errors
			run
			help
		'''

		tab.active = False

		if tab.type in ('normal', 'newtab'):
			# Return view to cursor in closed tab
			self.ensure_idx_visibility('insert', tab=tab)

		self.entry.delete(0, tkinter.END)
		self.scrollbar.config(command='')
		self.text_widget.grid_forget()

		if len(self.text_widget.tag_ranges('sel')) > 0:
			self.text_widget.tag_remove('sel', '1.0', 'end')


	def walk_tabs(self, event=None, back=False):

		if self.state != 'normal' or len(self.tabs) < 2:
			self.bell()
			return 'break'


		if filter_keys_out(event, ['Control', 'Shift']): return


		idx = old_idx = self.tabindex

		if back:
			if idx == 0:
				idx = len(self.tabs)
			idx -= 1

		else:
			if idx == len(self.tabs) - 1:
				idx = -1
			idx += 1

		self.tabindex = new_idx = idx


		# Build info-string (same as in window-title, with filaname)
		# to clarify current tabs content on tab-change.
		# Useful especially when in fullscreen.
		maxlen_msg = 0
		for tab in self.tabs:
			if filepath := tab.filepath:
				lenght = len(filepath.stem + filepath.suffix)
				if lenght > maxlen_msg: maxlen_msg = lenght

		maxlen_msg += 2 # two spaces after title_string

		msg1 =msg2= self.title_string + maxlen_msg*' '
		num_spaces = 0
		tail = False
		if filepath := self.tabs[new_idx].filepath:
			tail = '  ' +filepath.stem +filepath.suffix
			num_spaces = maxlen_msg - len(tail)

		self.wait_for(30)
		self.show_message(msg1, 1000)
		self.tab_close(self.tabs[old_idx])
		self.tab_open(self.tabs[new_idx])
		self.update_title()

		if tail:
			msg2 = self.title_string + tail + num_spaces*' '
		else:
			# For example, tab without filepath
			msg2 = self.title_string + maxlen_msg*' '
		self.show_message(msg2, 1100)


		return 'break'

########## Tab Related End
########## Configuration Related Begin

	def export_config(self):
		''' Export configuration without tabs and no geometry-conf
			--> in effect, theme related-stuff
		'''
		# Considering as rarely used
		import tkinter.filedialog
		fname_as_string = p = tkinter.filedialog.asksaveasfilename(initialfile='henxel.cnf')

		data = self.get_config(notabs=True)

		string_representation = json.dumps(data)

		try:
			with open(p, 'w', encoding='utf-8') as f:
				f.write(string_representation)
				print('\nExported configuration to:\n%s' % p)

		except EnvironmentError as e:
			print(e.__str__())
			print('\nCould not export configuration')


	def save_config(self):
		data = self.get_config()

		string_representation = json.dumps(data)

		if string_representation == self.oldconf:
			return

		p = pathlib.Path(self.env) / self.confpath
		try:
			with open(p, 'w', encoding='utf-8') as f:
				f.write(string_representation)
		except EnvironmentError as e:
			print(e.__str__())
			print('\nCould not save configuration')


	def load_config(self, data):

		textfont, menufont, keyword_font, linenum_font = self.fonts_exists(data)
		return self.set_config(data, textfont, menufont, keyword_font, linenum_font)


	def fonts_exists(self, data):

		fontfamilies = [f for f in tkinter.font.families()]

		def set_font_no_exist(font):
			if font not in fontfamilies:
				print(f'Font {font.upper()} does not exist.')
				return False

		textfont = data['fonts']['textfont']['family']
		menufont = data['fonts']['menufont']['family']
		keyword_font = data['fonts']['keyword_font']['family']
		linenum_font = data['fonts']['linenum_font']['family']

		for font in (textfont, menufont, keyword_font, linenum_font):
			font = set_font_no_exist(font)

		return textfont, menufont, keyword_font, keyword_font


	def get_config(self, notabs=False):
		''' notabs: for export_config
		'''

		d = dict()
		d['curtheme'] = self.curtheme
		d['lastdir'] = self.lastdir.__str__()

		###################
		# Replace possible Tkdefaulfont as family with real name,
		# if not mac_os, because tkinter.font.Font does not recognise
		# this: .APPLESYSTEMUIFONT
		fonts = dict()

		def fix_fontname(font):
			if font.cget('family') == 'TkDefaulFont':
				return font.config()
			else:
				return font.actual()


		if self.os_type == 'mac_os':
			for font in self.fonts.values():
				fonts[font.name] = fix_fontname(font)
		else:
			for font in self.fonts.values():
				fonts[font.name] = font.actual()

		d['fonts'] = fonts
		####################

		d['scrollbar_widths'] = self.scrollbar_width, self.elementborderwidth
		d['version_control_cmd'] = self.version_control_cmd
		d['marginals'] = self.margin, self.margin_fullscreen, self.gap, self.gap_fullscreen
		d['spacing_linenums'] = self.spacing_linenums
		d['offsets'] = self.offset_comments, self.offset_keywords
		d['start_fullscreen'] = self.start_fullscreen
		d['fdialog_sorting'] = self.dir_reverse, self.file_reverse
		d['popup_run_action'] = self.popup_run_action
		d['run_timeout'] = self.timeout
		d['run_module'] = self.module_run_name
		d['run_custom'] = self.custom_run_cmd
		d['check_syntax'] = self.check_syntax
		d['fix_mac_print'] = self.mac_print_fix
		d['want_ln'] = self.want_ln
		d['syntax'] = self.syntax
		d['ind_depth'] = self.ind_depth
		d['themes'] = self.themes

		geom = self.geom
		if notabs: geom = False
		d['geom'] = geom

		tabs = self.tabs
		if notabs:
			tabs = list()
			newtab = Tab(self.create_textwidget())
			newtab.active = True
			tabs.append(newtab)


		for tab in tabs:
			# Convert tab.filepath to string for serialization
			if tab.filepath:
				tab.filepath = tab.filepath.__str__()
			else:
				tab.bookmarks.clear()
				tab.bookmarks_stash.clear()


		whitelist = (
					'active',
					'filepath',
					'position',
					'type',
					'bookmarks',
					'bookmarks_stash',
					'chk_sum'
					)


		d['tabs'] = [ dict([
							(key, tab.__dict__.get(key)) for key in whitelist
							]) for tab in tabs ]

		return d


	def handle_one_time_conf(self):
		# Started editor from terminal: python -m henxel file1 file2..
		# --> skip messing original tabs and bookmarks by using:
		# One time conf begin

		# Intention: enable use of editor as adhoc(normal) editor

		tmppath = pathlib.Path().cwd()

		# Create tab for: 'to be opened' -file
		for fname in self.files_to_be_opened:
			newtab = Tab(self.create_textwidget())
			newtab.filepath = tmppath / fname
			newtab.filepath = newtab.filepath.resolve().__str__()
			newtab.type = 'normal'
			self.tabs.append(newtab)

		self.tabs[0].active = True


	def conf_read_files(self):
		for tab in self.tabs[:]:

			if tab.type == 'normal':
				try:
					with open(tab.filepath, 'r', encoding='utf-8') as f:
						tmp = f.read()
						tab.contents = tmp
						tab.oldcontents = tab.contents

					tab.filepath = pathlib.Path(tab.filepath)


				except (EnvironmentError, UnicodeDecodeError) as e:
					print(e.__str__())
					# Note: remove(val) actually removes the first occurence of val
					self.tabs.remove(tab)
			else:
				tab.bookmarks.clear()
				tab.filepath = None
				tab.position = '1.0'

		for i,tab in enumerate(self.tabs):
			if tab.active == True:
				self.tabindex = i
				break


	def set_config(self, data, textfont, menufont, keyword_font, linenum_font):

		d = data

		# Set Font Begin ##############################
		flag_check_lineheights = False
		if not all((textfont, linenum_font, keyword_font)): flag_check_lineheights = True

		# Both missing:
		if not textfont and not menufont:
			fontname = get_font(GOODFONTS)
			d['fonts']['textfont']['family'] = fontname
			d['fonts']['menufont']['family'] = fontname

		# One missing, copy existing:
		elif bool(textfont) ^ bool(menufont):

			if textfont:
				d['fonts']['menufont']['family'] = textfont
			else:
				d['fonts']['textfont']['family'] = menufont

		if not keyword_font:
			fontname = get_font(GOODFONTS2)
			d['fonts']['keyword_font']['family'] = fontname

		if not linenum_font:
			fontname = get_font(reversed(GOODFONTS))
			d['fonts']['linenum_font']['family'] = fontname


		self.spacing_linenums = d['spacing_linenums']
		self.offset_comments, self.offset_keywords = d['offsets']

		if flag_check_lineheights:
			self.flag_check_lineheights = True
			self.spacing_linenums = self.offset_comments = self.offset_keywords = 0



		self.textfont.config(**d['fonts']['textfont'])
		self.menufont.config(**d['fonts']['menufont'])
		self.keyword_font.config(**d['fonts']['keyword_font'])
		self.linenum_font.config(**d['fonts']['linenum_font'])
		self.scrollbar_width, self.elementborderwidth = d['scrollbar_widths']
		self.margin, self.margin_fullscreen, self.gap, self.gap_fullscreen = d['marginals']
		self.dir_reverse, self.file_reverse = d['fdialog_sorting']
		self.version_control_cmd = d['version_control_cmd']
		self.start_fullscreen = d['start_fullscreen']
		self.popup_run_action = d['popup_run_action']
		self.check_syntax = d['check_syntax']
		self.mac_print_fix = d['fix_mac_print']
		self.module_run_name = d['run_module']
		self.custom_run_cmd = d['run_custom']
		self.timeout = d['run_timeout']
		self.want_ln = d['want_ln']
		self.syntax = d['syntax']
		self.geom = d['geom']
		self.ind_depth = d['ind_depth']
		self.themes = d['themes']
		self.curtheme = d['curtheme']

		self.bgcolor, self.fgcolor = self.themes[self.curtheme]['normal_text'][:]

		###
		self.tab_width = self.textfont.measure(self.ind_depth * TAB_WIDTH_CHAR)

		pad_x =  self.tab_width // self.ind_depth // 3
		pad_y = pad_x
		self.pad = pad_x ###################################
		###

		self.lastdir = d['lastdir']

		if self.lastdir != None:
			self.lastdir = pathlib.Path(d['lastdir'])
			if not self.lastdir.exists():
				self.lastdir = None


		if self.one_time_conf:
			# Don't load tabs from conf
			self.handle_one_time_conf()
		else:
			# Load tabs from conf
			self.tabs = [ Tab(self.create_textwidget(), **items) for items in d['tabs'] ]

		self.conf_read_files()

		return True

		## set_config End #########


	def create_textwidget(self):
		return tkinter.Text(self.text_frame, **self.text_widget_basic_config)


	def set_textwidget(self, tab):

		w = tab.text_widget

		w.insert(1.0, 'asd')
		w.event_generate('<<SelectNextWord>>')
		w.event_generate('<<PrevLine>>')

		tab.anchorname = ''
		for item in w.mark_names():
			if 'tk::' in item:
				tab.anchorname = item
				break

		w.delete('1.0', '1.3')

		tab.tcl_name_of_contents = w._w  # == str( w.nametowidget(w) )
		tab.oldline = ''
		tab.par_err = False
		tab.check_scope = False

		self.update_syntags_colors(tab)


		w.config(font=self.textfont, tabs=(self.tab_width, ), bd=self.pad,
				padx=self.pad, pady=self.pad, foreground=self.fgcolor,
				background=self.bgcolor, insertbackground=self.fgcolor)


	def config_tabs(self):
		for tab in self.tabs: self.set_textwidget(tab)


########## Configuration Related End
########## Syntax highlight Begin

	def init_syntags(self):

		keywords = keyword.kwlist
		keywords.insert(0, 'self')
		self.keywords = dict()
		for key in keywords: self.keywords.setdefault(key, 1)

		bools = [ 'False', 'True', 'None' ]
		self.bools = dict()
		for key in bools: self.bools.setdefault(key, 1)

		breaks =[
				'break',
				'return',
				'continue',
				'pass',
				'raise',
				'assert',
				'yield'
				]
		self.breaks = dict()
		for key in breaks: self.breaks.setdefault(key, 1)

		tests = [
				'not',
				'or',
				'and',
				'in',
				'as'
				]
		self.tests = dict()
		for key in tests: self.tests.setdefault(key, 1)


		# Used in insert_tokens()
		deflines = list()
		for i in range(10):
			deflines.append('defline%i' % i)
		self.defline_tags = dict()
		for key in deflines: self.defline_tags.setdefault(key, 1)


		self.tagnames = [
				'keywords',
				'numbers',
				'bools',
				'strings',
				'comments',
				'breaks',
				'calls',
				'selfs'
				]
		self.tagnames.extend(deflines)
		# not 'defline' for reason
		self.tagnames.append('deflin')
		self.tagnames = set(self.tagnames)


		self.tags = dict()
		for tag in self.tagnames: self.tags[tag] = list()


	def set_syntags(self, tab):
		''' This must be called after set_textwidget(tab)
			because most of tags are created there.

			This should be called only when creating text_widget
		'''

		w = tab.text_widget

		w.tag_config('keywords', font=self.keyword_font, offset=self.offset_keywords)
		#w.tag_config('tests', font=self.keyword_font)
		w.tag_config('numbers', font=self.boldfont)
		w.tag_config('comments', font=self.linenum_font, offset=self.offset_comments)
		w.tag_config('breaks', font=self.boldfont)
		w.tag_config('calls', font=self.boldfont)

		w.tag_config('focus', underline=True)
		w.tag_config('elIdel', elide=True)
		w.tag_config('animate')
		w.tag_config('animate_stash', background='yellow')

		# Used in insert_tokens()
		for key in self.defline_tags.keys():
			w.tag_config(key)

		w.tag_config('highlight_line')
		w.tag_config('match_zero_lenght')

		# Search-tags have highest priority
		w.tag_raise('match')
		w.tag_raise('replaced')
		w.tag_raise('sel')
		w.tag_raise('focus')


	def toggle_syntax(self, event=None):

		if self.syntax:
			self.syntax = False
			self.auto_update_syntax_stop()

			for tab in self.tabs:
				for tag in self.tagnames:
					tab.text_widget.tag_remove( tag, '1.0', tkinter.END )

			return 'break'

		else:
			self.syntax = True
			self.auto_update_syntax_stop()

			for tab in self.tabs:

				if self.can_do_syntax(tab):
					self.update_lineinfo(tab)

					a = self.get_tokens(tab)
					self.insert_tokens(a, tab=tab)


			self.auto_update_syntax_continue()

			return 'break'


	def can_do_syntax(self, tab=None):

		if not tab: tab = self.tabs[self.tabindex]

		res = True

		if tab.filepath and '.py' not in tab.filepath.suffix:
			res = False

		if tab.type == 'help': res = False

		res = self.syntax and res

		return res


	def redraw_syntax(self):
		''' Redraw syntax of current tab
		'''
		if self.can_do_syntax(): self.update_tokens('1.0', 'end')
		return 'break'


	def get_tokens(self, tab, update=False):
		''' Get syntax-tokens for insert_tokens()

			Called from: walk_tabs
		'''
		if update: tmp = tab.text_widget.get('1.0', 'end')
		else: tmp = tab.contents

		g = iter( tmp.splitlines(keepends=True) )
		tokens = tokenize.generate_tokens( g.__next__ )

		return tokens


	class LastToken:
		''' Used in insert_tokens and update_tokens
			to prevent error

			when brace-opener (,[ or { is first character of py-file

		'''
		type = 999
		end = (-1, -1)


	def insert_tokens(self, tokens, tab=None):
		''' Syntax-highlight text

			Syntax-tokens are from get_tokens()
			Percentages were counted using dev/token_stats.py

			Called from: update_tokens, walk_tabs, etc
		'''

		if not tab:
			tab = self.tabs[self.tabindex]

		patt = f'{tab.tcl_name_of_contents} tag add '
		flag_async = False
		last_name = self.LastToken()


		for tag in self.tagnames: self.tags[tag].clear()
		#t0 = int(self.root.tk.eval('clock milliseconds'))
		try:
			for token in tokens:

				# Over 30% of all tokens
				if token.type == tokenize.OP:

					if token.exact_type != tokenize.LPAR: continue

					# Calls
					else:
						# Need to know if absolutely last token was NAME:
						if token.start == last_name.end:
							self.tags['calls'].append((last_name.start, last_name.end))

				# 30% of all tokens
				elif token.type == tokenize.NAME:
					last_name = token

					if not self.keywords.get(token.string): continue
					else:

						if token.string == 'self':
							self.tags['selfs'].append((token.start, token.end))

						elif self.bools.get(token.string):
							self.tags['bools'].append((token.start, token.end))

##						elif self.tests.get(token.string):
##							self.tags['tests'].append((token.start, token.end))

						elif self.breaks.get(token.string):
							self.tags['breaks'].append((token.start, token.end))

						else:
							self.tags['keywords'].append((token.start, token.end))

							# These below are used only to tag deflines with indentation information,
							# which is used to make finding scope limits faster for example in walk_scope.
							# --> if thinking this is not usable, these can simply be removed from here and
							# update_tokens, and fixing places were it was actually used
							if token.string == 'async':
								# line, col of tag start
								# save line of async for check, in elif below
								# (tokenizer starts at line number 1)
								flag_async, ind_depth = token.start
								tagname = f'defline{ind_depth}'
								self.tags[tagname].append((token.start, token.end))
								self.tags['deflin'].append((token.start, token.end))

							elif token.string in ('def', 'class'):
								if flag_async and flag_async == token.start[0]: pass
								else:
									ind_depth = token.start[1]
									tagname = f'defline{ind_depth}'
									try:
										self.tags[tagname].append((token.start, token.end))
										self.tags['deflin'].append((token.start, token.end))
									# Syntax error, just in middle of writing string etc.
									# (No need 10 level of nested func)
									except KeyError: pass

								flag_async = False


				# These three are only about 10% in total
				elif token.type == tokenize.STRING:
					self.tags['strings'].append((token.start, token.end))

				elif token.type == tokenize.COMMENT:
					self.tags['comments'].append((token.start, token.end))

				elif token.type == tokenize.NUMBER:
					self.tags['numbers'].append((token.start, token.end))

				else: continue

				##############


		except (IndentationError, tokenize.TokenError): pass


		#t1 = int(self.root.tk.eval('clock milliseconds'))
		for tag in self.tags:
			if len(self.tags[tag]) > 0:

				tk_command = patt + tag
				for ((s0,s1), (e0,e1)) in self.tags[tag]:
					tk_command += f' {s0}.{s1} {e0}.{e1}'

				try: self.tk.eval(tk_command)
				except tkinter.TclError as err: print(err)

		#t2 = int(self.root.tk.eval('clock milliseconds'))
		#print(t2-t1, t1-t0, 'ms')

		################## insert_tokens END ####################


	def update_tokens(self, start=None, end=None, line=None, tab=None):
		''' Update syntax highlighting after some change in contents.
		'''

		start_idx = start
		end_idx = end
		linecontents = line
		if not linecontents: linecontents = self.text_widget.get( start_idx, end_idx )

		linenum,_ = self.get_line_col_as_int(index=start_idx)


		if not tab:
			tab = self.tabs[self.tabindex]


		###### START ###########
		g = iter( linecontents.splitlines(keepends=True) )
		tokens = tokenize.generate_tokens( g.__next__ )

		# Remove old tags:
		for tag in self.tagnames:
			tab.text_widget.tag_remove( tag, start_idx, end_idx )


		patt = f'{tab.tcl_name_of_contents} tag add '
		flag_err = False
		par_err = None
		check_pars = False
		flag_async = False
		last_token = self.LastToken()
		last_name = self.LastToken()

		for tag in self.tagnames: self.tags[tag].clear()
		try:
			for token in tokens:

				last_token = token

				# Over 30% of all tokens
				if token.type == tokenize.OP:

					if token.exact_type != tokenize.LPAR: continue

					# Calls
					else:
						# Need to know if absolutely last token was NAME:
						if token.start == last_name.end:
							self.tags['calls'].append((last_name.start, last_name.end))

				# 30% of all tokens
				elif token.type == tokenize.NAME:
					last_name = token

					if not self.keywords.get(token.string): continue
					else:

						if token.string == 'self':
							self.tags['selfs'].append((token.start, token.end))

						elif self.bools.get(token.string):
							self.tags['bools'].append((token.start, token.end))

##						elif self.tests.get(token.string):
##							self.tags['tests'].append((token.start, token.end))

						elif self.breaks.get(token.string):
							self.tags['breaks'].append((token.start, token.end))

						else:
							self.tags['keywords'].append((token.start, token.end))

							# These below are used only to tag deflines with indentation information,
							# which is used to make finding scope limits faster for example in walk_scope.
							# --> if thinking this is not usable, these can simply be removed from here and
							# update_tokens, and fixing places were it was actually used
							if token.string == 'async':
								# line, col of tag start
								# save line of async for check, in elif below
								# (tokenizer starts at line number 1)
								flag_async, ind_depth = token.start
								tagname = f'defline{ind_depth}'
								self.tags[tagname].append((token.start, token.end))
								self.tags['deflin'].append((token.start, token.end))

							elif token.string in ('def', 'class'):
								if flag_async and flag_async == token.start[0]: pass
								else:
									ind_depth = token.start[1]
									tagname = f'defline{ind_depth}'
									try:
										self.tags[tagname].append((token.start, token.end))
										self.tags['deflin'].append((token.start, token.end))
									# Syntax error, just in middle of writing string etc.
									# (No need 10 level of nested func)
									except KeyError: pass

								flag_async = False


				# These three are only about 10% in total
				elif token.type == tokenize.STRING:
					self.tags['strings'].append((token.start, token.end))

				elif token.type == tokenize.COMMENT:
					self.tags['comments'].append((token.start, token.end))

				elif token.type == tokenize.NUMBER:
					self.tags['numbers'].append((token.start, token.end))

				else: continue

				##############



		except IndentationError as e:
##			for attr in ['args', 'filename', 'lineno', 'msg', 'offset', 'text']:
##				item = getattr( e, attr)
##				print( attr,': ', item )
##
##			print( e.args[0], '\nIndentation errline: ',
##			self.text_widget.index(tkinter.INSERT) )

			flag_err = True
			tab.check_scope = True
			#print('update_tokens: indent_err')


		except tokenize.TokenError as ee:

			if 'EOF in multi-line statement' in ee.args[0]:
				idx_start = str(last_token.start[0] +linenum -1) + '.0'
				check_pars = idx_start


			elif 'multi-line string' in ee.args[0]:
				flag_err = True
				tab.check_scope = True

			#print('update_tokens: other_err')



		for tag in self.tags:
			if len(self.tags[tag]) > 0:

				tk_command = patt + tag
				for ((s0,s1), (e0,e1)) in self.tags[tag]:
					tk_command += f' {s0 +linenum -1}.{s1} {e0 +linenum -1}.{e1}'

				try: self.tk.eval(tk_command)
				except tkinter.TclError as err: print(err)

		##### Check parentheses ####
		if check_pars:
			start_line = check_pars
			par_err = self.checkpars(start_line, tab)

		# From backspace_override:
		elif tab.par_err:
			start_line = False
			par_err = self.checkpars(start_line, tab)

		tab.par_err = par_err


		if not par_err:
			# Not always checking whole file for par mismatches, so clear
			self.text_widget.tag_remove('mismatch', '1.0', tkinter.END)

			###### Check parentheses end ###########

		if not flag_err:
			#print('ok')
			tab.check_scope = False

			###### update_tokens end ###########


	def checkpars(self, idx_start, tab):
		''' idx_start: Text-index or False
		'''
		# Possible par mismatch may be caused from another line,
		# so find current block: find first empty line before and after curline
		# then count pars in it.

		if not idx_start:
			# line had nothing but brace in it and it were deleted
			idx_start = 'insert'

		startline, lines = self.find_empty_lines(tab, index=idx_start)
		startline,_ = self.get_line_col_as_int(tab=tab, index=startline)
		err_indexes = self.count_pars(startline, lines, tab)

		err = False

		if err_indexes:
			err = True
			err_line = startline + err_indexes[0]
			err_col = err_indexes[1]
			err_idx = '%i.%i' % (err_line, err_col)

			tab.text_widget.tag_remove('mismatch', '1.0', tkinter.END)
			tab.text_widget.tag_add('mismatch', err_idx, '%s +1c' % err_idx)

		return err


	def count_pars(self, startline, lines, tab):

		pars = list()
		bras = list()
		curls = list()

		opening  = '([{'
		closing  = ')]}'

		tags = None

		# Populate lists and return at first extra closer:
		for i in range(len(lines)):

			for j in range(len(lines[i])):
				c = lines[i][j]
				patt = '%i.%i' % (startline+i, j)
				tags = tab.text_widget.tag_names(patt)

				# Skip if string or comment:
				if tags:
					if 'strings' in tags or 'comments' in tags:
						tags = None
						continue

				if c in closing:
					if c == ')':
						if len(pars) > 0:
							pars.pop(-1)
						else:
							return (i,j)

					elif c == ']':
						if len(bras) > 0:
							bras.pop(-1)
						else:
							return (i,j)

					# c == '}'
					else:
						if len(curls) > 0:
							curls.pop(-1)
						else:
							return (i,j)


				elif c in opening:
					if c == '(':
						pars.append((i,j))

					elif c == '[':
						bras.append((i,j))

					# c == '{':
					else:
						curls.append((i,j))


		# no extra closer in block.
		# Return first extra opener:
		idxlist = list()

		for item in [ pars, bras, curls ]:
			if len(item) > 0:
				idx =  item.pop(-1)
				idxlist.append(idx)


		if len(idxlist) > 0:
			if len(idxlist) > 1:
				maxidx = max(idxlist)
				return idxlist[idxlist.index(maxidx)]
			else:
				return idxlist[0]
		else:
			return False


	def find_empty_lines(self, tab, index='insert'):
		'''	Finds first empty lines before and after current line

			returns
				linenumber of start and end of the block
				and list of lines.

			Called from check_pars()
		'''

		startline = '1.0'
		patt = r'^[[:blank:]]*$'
		pos = index

		try:
			pos = tab.text_widget.search(patt, pos, stopindex='1.0', regexp=True, backwards=True)
		except tkinter.TclError as e:
			print(e)
			self.bell()

		if pos: startline = pos


		endline = 'end'
		pos = index

		try:
			pos = tab.text_widget.search(patt, pos, stopindex='end', regexp=True)
		except tkinter.TclError as e:
			print(e)
			self.bell()

		if pos: endline = pos


		lines = tab.text_widget.get('%s linestart' % startline, '%s lineend' % endline).splitlines()

		return startline, lines


########## Syntax highlight End
########## Theme Related Begin

	def editor_starts_fullscreen(self, value=None):
		if value == None: pass
		elif value: self.start_fullscreen = True
		else: self.start_fullscreen = False
		print(self.start_fullscreen)


	def get_geometry(self):
		''' Get geometry-string, trying geometry() first,
			possibly falling back to winfos
			and reporting failures, for possible later fixes.
		'''
		tmp = self.geometry()
		# Not great check, better than nothing though
		if len(tmp.split('x')[0]) < 3:
			print('INFO: Geometry handling issue, got:', tmp)
			w = self.winfo_width()
			h = self.winfo_height()
			x = self.winfo_x()
			y = self.winfo_y()
			tmp = f'{w}x{h}+{x}+{y}'

		return tmp


	def use_geometry(self, geom_string):
		'''
			To let window-manager handle positioning and size of the editor,
			use one of: False, 0 or '' as geom_string

			To reset to default handling, (no size changing, only put editor
			to top-right corner), use 'default' as geom_string

			To save current geometry, use 'current' as geom_string


			A geometry string is a standard way of describing the size and location of a top-level window
			on a desktop. A geometry string has this general form:
				'wxh±x±y' where:
				The w and h parts give the window width and height in pixels.
				They are separated by the character 'x'.

			If the next part has the form +x,
			it specifies that the left side of the window should be x pixels from the left side of the desktop.
			If it has the form -x,
			the right side of the window is x pixels from the right side of the desktop.

			If the next part has the form +y,
			it specifies that the top of the window should be y pixels below the top of the desktop.
			If it has the form -y,
			the bottom of the window will be y pixels above the bottom edge of the desktop.

		'''

		def give_info_fullscreen():
			self.wait_for(100)
			self.bell()
			print('Can not set fullscreen-size as default size.')
			print('But editor can be set launch to fullscreen with:')
			print()
			print('start_fullscreen(True)')


		if geom_string in (False, 0, ''):
			self.geom = False
			print('Use geometry:', False)
			print('Geometry changes are applied at next restart')
			return
		elif type(geom_string) != str:
			self.bell()
			return
		elif geom_string == self.geom:
			self.bell()
			return
		elif geom_string == 'default':
			geom_string = self.geom = '+%d+0'
			if self.os_type == 'windows':
				geom_string = self.geom = '-0+0'
			diff = self.winfo_screenwidth() - self.winfo_width()
			tests = (self.os_type != 'windows', self.geom == '+%d+0', diff > 0)
			if all(tests): self.geometry('+%d+0' % diff )
			else: self.geometry(self.geom)
			print('Resetting to default geometry:', self.geom)
			print('Possible size change is reset to default at next restart')
			return

		# Used at first launch
		elif geom_string == 'current':
			if not self.is_fullscreen(): self.geom = self.get_geometry()
			else: give_info_fullscreen()
			return

		# Actually wanting to set some size and position to be used at startup
		# geom_string is 'wxh±x±y'
		try:
			self.geometry(geom_string)

			if self.is_fullscreen(): give_info_fullscreen()
			else: self.geom = geom_string

		except tkinter.TclError as e:
			print(e)


	def tabsize_change(self, width):
		''' width is integer between 1-8
		'''

		if type(width) != int:
			self.bell()
			return
		elif width == self.ind_depth:
			self.bell()
			return
		elif not 0 < width <= 8:
			self.bell()
			return


		self.ind_depth = width
		self.tab_width = self.textfont.measure(self.ind_depth * self.tab_char)
		for tab in self.tabs + [self.help_tab, self.err_tab]:
			tab.text_widget.config(tabs=(self.tab_width, ))
		print(self.ind_depth)


	def is_fullscreen(self):

		# last fallback
		width_editor = self.winfo_width()
		width_screen = self.winfo_screenwidth()
		res = width_editor == width_screen

		# preferring wm attributes
		if self.wm_attributes().count('-fullscreen') != 0:
			res = self.wm_attributes('-fullscreen') == 1

		# first fallback
		elif self.wm_attributes().count('-zoomed') != 0:
			res = self.wm_attributes('-zoomed') == 1

		return res


	def apply_left_margin(self, ln_kwargs, just_kwargs):

		self.ln_widget.config(**ln_kwargs)
		self.ln_widget.tag_config('justright', **just_kwargs)


	def left_margin_set(self, width_normal=None, width_fullscreen=None):
		'''	Set total distance from left edge of editor window to start of text,
			for normal window, and possible separate width for fullscreen.

			Without arguments, print current setting.

			to reset both to defaults:
			left_margin_set(0)

			reset only margin of normal window:
			left_margin_set(0, self.margin_fullscreen)

			see also: left_margin_gap_set
		'''

		if type(width_normal) != int:
			print('normal:', self.margin, 'fullscreen:', self.margin_fullscreen)
			return

		if width_normal <= self.default_margin: width_normal = self.default_margin

		self.margin, self.margin_fullscreen = width_normal, width_normal

		if type(width_fullscreen) == int:
			if width_fullscreen <= self.default_margin: width_fullscreen = self.default_margin
			self.margin_fullscreen = width_fullscreen

		if self.is_fullscreen(): kwargs={'width':self.margin_fullscreen}
		else: kwargs={'width':self.margin}

		print('normal:', self.margin, 'fullscreen:', self.margin_fullscreen)
		self.ln_widget.config(**kwargs)


	def left_margin_gap_set(self, gap_normal=None, gap_fullscreen=None):
		'''	Set distance(length of empty space) from linenumbers to start of text,
			for normal window, and possible separate width for fullscreen.

			This does not change total distance of left_margin, which can
			be done with left_margin_set. After using this, one can increase
			lenght of total margin, with left_margin_set, if necessary.

			Without arguments, print current setting.

			Reset both to defaults:
			left_margin_gap_set(0)

			Reset only gap of normal window:
			left_margin_gap_set(0, self.gap_fullscreen)

			distance can be int --> pixels
			or string like 1c --> note, this adds much space

			Example: left_margin_gap_set(10, '2c')

		'''

		if type(gap_normal) not in (int, str):
			print('normal:', self.gap, 'fullscreen:', self.gap_fullscreen)
			return

		if type(gap_normal) == str: pass
		else:
			if gap_normal <= 0: gap_normal = 0
		try: self.ln_widget.tag_config('justright', rmargin=gap_normal)
		except tkinter.TclError as e:
			print(e)
			return

		self.gap, self.gap_fullscreen = gap_normal, gap_normal


		if type(gap_fullscreen) in (int, str):
			if type(gap_fullscreen) == str: pass
			else:
				if gap_fullscreen <= 0: gap_fullscreen = 0
			try:
				self.ln_widget.tag_config('justright', rmargin=gap_fullscreen)
				self.gap_fullscreen = gap_fullscreen
			except tkinter.TclError as e:
				print(e)
				return

		print('normal:', self.gap, 'fullscreen:', self.gap_fullscreen)

		gap = self.gap
		if self.is_fullscreen(): gap = self.gap_fullscreen
		self.ln_widget.tag_config('justright', rmargin=gap)


	def scrollbar_widths_set(self, width=None, elementborderwidth=None):
		'''	Change widths of scrollbar
		'''

		if width is None and elementborderwidth is None: pass
		elif type(width) != int or type(elementborderwidth) != int:
			self.bell()
			return

		print(width, elementborderwidth)
		self.scrollbar_width = width
		self.elementborderwidth = elementborderwidth

		self.set_fdialog_widths()

		self.scrollbar.config(width=self.scrollbar_width,
							elementborderwidth=self.elementborderwidth)


##	def highlight_line(self, index='insert', color=None):
##		''' color is tk color, which can be
##
##			A: System named color. For example, one has Entry-widget with default
##				foreground color. To get name of the color:
##
##					entry_widget.cget('fg')
##
##			B: tk named color. For example: 'red'
##
##			C: Hexadecimal number with any of the following forms,
##				in case of color white(using 4, 8, 12 and 16 bits):
##
##			#fff
##			#ffffff
##			#fffffffff
##			#ffffffffffff
##		'''
##
##		if not color: color = r'#303030'
##
##		safe_idx = self.get_safe_index(index)
##		s = '%s display linestart' % safe_idx
##
##		if not self.line_is_elided(safe_idx):
##			e = '%s display lineend' % safe_idx
##		else:
##			e = '%s display lineend -1 display char' % safe_idx
##
##		self.text_widget.tag_remove('highlight_line', '1.0', 'end')
##
##		self.text_widget.tag_config('highlight_line', background=color)
##		self.text_widget.tag_add('highlight_line', s, e)


	def set_text_widget_colors(self, tab):

		tab.text_widget.config(foreground=self.fgcolor,
							background=self.bgcolor,
							insertbackground=self.fgcolor)


	def set_other_frame_colors(self):
		bg = self.bgcolor
		fg = self.fgcolor

		kwargs = {
		'bg':fg,
		'fg':bg,
		'disabledforeground':fg,
		'selectbackground':'blue',
		'selectforeground':'white',
		}

		self.comp_frame.listbox.config(**kwargs)


	def set_ln_widget_colors(self):
		# Linenumbers use same color with comments
		bg, fg = self.themes[self.curtheme]['comments'][:]
		self.ln_widget.config(foreground=fg, background=self.bgcolor,
							selectbackground=self.bgcolor,
							selectforeground=fg,
							inactiveselectbackground=self.bgcolor )


	def toggle_color(self, event=None):

		if self.curtheme == 'day':
			self.curtheme = 'night'
		else:
			self.curtheme = 'day'

		self.bgcolor, self.fgcolor = self.themes[self.curtheme]['normal_text'][:]

		for tab in self.tabs + [self.help_tab, self.err_tab]:
			self.update_syntags_colors(tab)
			self.set_text_widget_colors(tab)

		self.text_frame.config(bg=self.bgcolor)
		self.set_ln_widget_colors()
		self.set_other_frame_colors()

		return 'break'


	def update_syntags_colors(self, tab):

		for tagname in self.themes[self.curtheme]:
			bg, fg = self.themes[self.curtheme][tagname][:]
			tab.text_widget.tag_config(tagname, background=bg, foreground=fg)


	def get_lineheights(self):
		''' Returns lineheight of normal_text
		'''
		f = self.measure_frame

		# It needs to be mapped during measuring
		if not f.winfo_ismapped():
			f.place_configure(relx=0.1, rely=0.1)

		# It needs to be updated before measuring
		f.t.update_idletasks()

##		line_heights = a,b,c = 1,1,1

		# 'normal_text':
		a = f.t.dlineinfo('3.0')[3]
##		# 'keywords':
##		b = f.t.dlineinfo('2.0')[3]
##		# 'comments':
##		c = f.t.dlineinfo('1.0')[3]

		f.place_forget()

		return a


	def handle_diff_lineheights(self):
		''' Called from init when for example missing font or conf
			and from on_fontchange.
		'''

		# 1: Compare to linenum_font
		self.ln_widget.tag_config('justright', spacing1=0)

		linespace_textfont = self.textfont.metrics()['linespace']
		linespace_linenumfont = self.linenum_font.metrics()['linespace']
		diff = linespace_textfont - linespace_linenumfont
		size = self.linenum_font.cget('size')

		# Linenumbers can't be higher than text
		while diff < 0:
			size -= 1
			self.linenum_font.config(size=size)
			linespace_linenumfont = self.linenum_font.metrics()['linespace']
			diff = linespace_textfont - linespace_linenumfont

		self.ln_widget.tag_config('justright', spacing1=diff)
		self.spacing_linenums = diff

		# Now, count diff of, descent value, between linenum_font and textfont
		descent_textfont = self.textfont.metrics()['descent']
		descent_linenumfont = self.linenum_font.metrics()['descent']
		diff_descent = descent_linenumfont - descent_textfont
		self.offset_comments = diff_descent

		# Apply it to comments-tag
		for tab in self.tabs + [self.help_tab, self.err_tab]:
			tab.text_widget.tag_config('comments', offset=self.offset_comments)


		# 2: Compare to keyword_font
		linespace_textfont = self.textfont.metrics()['linespace']
		linespace_keywordfont = self.keyword_font.metrics()['linespace']
		diff = linespace_textfont - linespace_keywordfont
		size = self.keyword_font.cget('size')

		# Keywords can't be higher than text
		while diff < 0:
			size -= 1
			self.keyword_font.config(size=size)
			linespace_keywordfont = self.keyword_font.metrics()['linespace']
			diff = linespace_textfont - linespace_keywordfont

		# Now, count diff of, descent value, between keyword_font and textfont
		descent_textfont = self.textfont.metrics()['descent']
		descent_keywordfont = self.keyword_font.metrics()['descent']
		diff_descent = descent_keywordfont - descent_textfont
		self.offset_keywords = diff_descent

		# If diff_descent, apply it to keywords-tag
		if diff_descent:
			for tab in self.tabs + [self.help_tab, self.err_tab]:
				tab.text_widget.tag_config('keywords', offset=self.offset_keywords)


	def on_fontchange(self, fontname=None):
		''' fontname: String in self.fonts.keys

			Check is made so that linenum_font or keyword_font does not get bigger than textfont.
		'''

		# A: changing linenum_font, no need to update anything related to text_widget
		# just check lineheights
		if fontname and fontname == 'linenum_font':

			res = True
			# Want this:
			# lineheight text_widget >= lineheight ln_widget
			#########################################
			# count diff linespace
			oldspacing = self.ln_widget.tag_cget('justright', 'spacing1')
			self.ln_widget.tag_config('justright', spacing1=0)
			spacing = 0

			linespace_textfont = self.textfont.metrics()['linespace']
			linespace_linenumfont = self.linenum_font.metrics()['linespace']
			diff = linespace_textfont - linespace_linenumfont

			# Linenumbers can't be higher than text
			if diff < 0:
				res =  False
				self.bell()
				print('Lineheight of linenumbers cant be bigger than lineheight of text-window.')
				print('If want bigger linenumbers, increase textfont size first or choose different font for linenumbers.')
				self.ln_widget.tag_config('justright', spacing1=oldspacing)
			else:
				spacing = diff

			if res:
				self.ln_widget.tag_config('justright', spacing1=spacing)
				self.spacing_linenums = spacing

				# Now, count diff of, descent value, between linenum_font and textfont
				linespace_textfont = self.textfont.metrics()['descent']
				linespace_linenumfont = self.linenum_font.metrics()['descent']
				diff_descent = linespace_linenumfont - linespace_textfont
				self.offset_comments = diff_descent

				# Apply it to comments-tag
				for tab in self.tabs + [self.help_tab, self.err_tab]:
					tab.text_widget.tag_config('comments', offset=self.offset_comments)

			# No further action is required so return
			return res


		# B: changing keyword_font --> no need to update anything related to text_widget
		# just check lineheights
		elif fontname and fontname == 'keyword_font':

			res = True
			linespace_textfont = self.textfont.metrics()['linespace']
			linespace_keywordfont = self.keyword_font.metrics()['linespace']
			diff = linespace_textfont - linespace_keywordfont
			#print(diff)

			# Keywords can't be higher than text
			if diff < 0:
				res =  False
				self.bell()
				print('Lineheight of keywords cant be bigger than lineheight of text-window.')
				print('If want bigger keywords, increase textfont size first or choose different font for keywords.')

			if res:
				# Now, count diff of, descent value, between keyword_font and textfont
				linespace_textfont = self.textfont.metrics()['descent']
				linespace_keywordfont = self.keyword_font.metrics()['descent']
				diff_descent = linespace_keywordfont - linespace_textfont
				self.offset_keywords = diff_descent

				# Apply it to keywords-tag
				for tab in self.tabs + [self.help_tab, self.err_tab]:
					tab.text_widget.tag_config('keywords', offset=self.offset_keywords)

			return res


		# textfont
		elif fontname and fontname == 'textfont':
			self.handle_diff_lineheights()


		self.line_height = self.get_lineheights()


		# There could be a geometry change, so:
		if self.geom: self.flag_check_geom_at_exit = True

		self.boldfont.config(**self.textfont.config())
		self.boldfont.config(weight='bold')

		self.tab_width = self.textfont.measure(self.ind_depth * self.tab_char)
		pad_x =  self.tab_width // self.ind_depth // 3
		self.pad = pad_y = pad_x


		# Used in show_completions
		self.comp_frame.char_width = self.pad*3


		self.scrollbar_width = self.tab_width // self.ind_depth
		self.elementborderwidth = max(self.scrollbar_width // 6, 1)
		if self.elementborderwidth == 1: self.scrollbar_width = 9
		self.scrollbar.config(width=self.scrollbar_width,
							elementborderwidth=self.elementborderwidth)

		self.set_fdialog_widths()


		for tab in self.tabs + [self.help_tab, self.err_tab]:
			tab.text_widget.config(tabs=(self.tab_width, ), padx=self.pad, pady=self.pad)


		# btn_git
		width_text = self.menufont.measure('123456')
		width_img = 8
		width_total = width_text + width_img + self.pad*4
		self.btn_git.config(image=self.img_name, width=width_total)


		self.ln_widget.config(padx=self.pad, pady=self.pad)
		# Likely not necessary:
		self.y_extra_offset = self.text_widget['highlightthickness'] + self.text_widget['bd'] + self.text_widget['pady']


		return True

		## on_fontchange End ######


	def font_choose(self, event=None):
		if self.state != 'normal' or self.is_fullscreen():
			self.bell()
			return 'break'

		fonttop = tkinter.Toplevel()
		fonttop.title('Choose Font')

		big = False
		shortcut = "<Alt-f>"

		if self.os_type == 'mac_os':
			big = True
			shortcut = "<function>"


		fonttop.protocol("WM_DELETE_WINDOW", lambda: ( fonttop.grab_release(),
				fonttop.destroy(), self.text_widget.focus_force(),
				self.text_widget.bind( shortcut, self.font_choose)) )

		changefont.FontChooser( fonttop, [self.textfont, self.menufont, self.keyword_font, self.linenum_font], big,
			sb_widths=(self.scrollbar_width, self.elementborderwidth),
			on_fontchange=self.on_fontchange )
		self.text_widget.bind( shortcut, self.do_nothing)


		fonttop.grab_set()
		fonttop.attributes('-topmost', 1)

		self.to_be_closed.append(fonttop)

		return 'break'


	def enter2(self, args, event=None):
		''' When mousecursor enters hyperlink tagname in colorchooser.
		'''
		wid = args[0]
		tagname = args[1]

		t = wid.textwid

		# Maybe left as lambda-example?
		#wid.after(200, lambda kwargs={'cursor':'hand2'}: t.config(**kwargs) )

		t.config(cursor="hand2")
		wid.after(50, lambda args=[tagname],
				kwargs={'underline':1, 'font':self.boldfont}: t.tag_config(*args, **kwargs) )


	def leave2(self, args, event=None):
		''' When mousecursor leaves hyperlink tagname in colorchooser.
		'''
		wid = args[0]
		tagname = args[1]

		t = wid.textwid

		t.config(cursor=self.name_of_cursor_in_text_widget)
		wid.after(50, lambda args=[tagname],
				kwargs={'underline':0, 'font':self.menufont}: t.tag_config(*args, **kwargs) )


	def lclick2(self, args, event=None):
		'''	When clicked hyperlink in colorchooser.
		'''
		wid = args[0]
		tagname = args[1]

		syntags = [
		'normal_text',
		'keywords',
		'numbers',
		'bools',
		'strings',
		'comments',
		'breaks',
		'calls',
		'selfs',
		'match',
		'focus',
		'replaced',
		'mismatch',
		'selected'
		]

		modetags = [
		'Day',
		'Night',
		'Text',
		'Background'
		]

		savetags = [
		'Save_TMP',
		'TMP',
		'Start',
		'Defaults'
		]

		onlyfore = [
		'keywords',
		'numbers',
		'bools',
		'strings',
		'comments',
		'breaks',
		'calls',
		'selfs'
		]


		if tagname in syntags:

			if tagname == 'selected':
				tagname = 'sel'


			elif wid.frontback_mode == 'foreground':
				initcolor = self.text_widget.tag_cget(tagname, 'foreground')
				patt = 'Choose fgcolor for: %s' % tagname

			else:
				initcolor = self.text_widget.tag_cget(tagname, 'background')
				patt = 'Choose bgcolor for: %s' % tagname

			try:
				res = self.tk.call('tk_chooseColor', '-initialcolor', initcolor, '-title', patt)

			except tkinter.TclError as e:
				self.bell()
				print(e)
				return 'break'


			tmpcolor = str(res)

			if tmpcolor in [None, '']:
				wid.focus_set()
				return 'break'


			try:
				if wid.frontback_mode == 'foreground':
					self.themes[self.curtheme][tagname][1] = tmpcolor
				else:
					self.themes[self.curtheme][tagname][0] = tmpcolor

				self.bgcolor, self.fgcolor = self.themes[self.curtheme]['normal_text'][:]

				for tab in self.tabs + [self.help_tab, self.err_tab]:
					self.update_syntags_colors(tab)
					self.set_text_widget_colors(tab)

				self.text_frame.config(bg=self.bgcolor)
				self.set_ln_widget_colors()
				self.set_other_frame_colors()

			# if closed editor and still pressing ok in colorchooser:
			except (tkinter.TclError, AttributeError) as e:
				# because if closed editor, this survives
				pass


		elif tagname in modetags:

			t = wid.textwid

			if tagname == 'Day' and self.curtheme != 'day':
				r1 = t.tag_nextrange('Day', 1.0)
				r2 = t.tag_nextrange('Night', 1.0)

				t.delete(r1[0], r1[1])
				t.insert(r1[0], '[X] Day-mode	', 'Day')
				t.delete(r2[0], r2[1])
				t.insert(r2[0], '[ ] Night-mode	', 'Night')

				self.toggle_color()


			elif tagname == 'Night' and self.curtheme != 'night':
				r1 = t.tag_nextrange('Day', 1.0)
				r2 = t.tag_nextrange('Night', 1.0)

				t.delete(r1[0], r1[1])
				t.insert(r1[0], '[ ] Day-mode	', 'Day')
				t.delete(r2[0], r2[1])
				t.insert(r2[0], '[X] Night-mode	', 'Night')

				self.toggle_color()


			elif tagname == 'Text':
				if wid.frontback_mode != 'foreground':
					r1 = t.tag_nextrange('Text', 1.0)
					r2 = t.tag_nextrange('Background', 1.0)

					t.delete(r1[0], r1[1])
					t.insert(r1[0], '[X] Text color\n', 'Text')

					t.delete(r2[0], r2[1])
					t.insert(r2[0], '[ ] Background color\n', 'Background')
					wid.frontback_mode = 'foreground'

					t.tag_remove('disabled', 1.0, tkinter.END)

					for tag in onlyfore:
						r3 = wid.tag_idx.get(tag)
						t.tag_add(tag, r3[0], r3[1])


			elif tagname == 'Background':
				if wid.frontback_mode != 'background':
					r1 = t.tag_nextrange('Text', 1.0)
					r2 = t.tag_nextrange('Background', 1.0)

					t.delete(r1[0], r1[1])
					t.insert(r1[0], '[ ] Text color\n', 'Text')

					t.delete(r2[0], r2[1])
					t.insert(r2[0], '[X] Background color\n', 'Background')
					wid.frontback_mode = 'background'

					for tag in onlyfore:
						r3 = t.tag_nextrange(tag, 1.0)
						wid.tag_idx.setdefault(tag, r3)
						t.tag_remove(tag, 1.0, tkinter.END)
						t.tag_add('disabled', r3[0], r3[1])


		elif tagname in savetags:

			t = wid.textwid

			if tagname == 'Save_TMP':
				wid.tmp_theme = copy.deepcopy(self.themes)
				wid.flag_tmp = True
				self.flash_tag(t, tagname)

			elif tagname == 'TMP' and wid.flag_tmp:
				self.themes = copy.deepcopy(wid.tmp_theme)
				self.flash_tag(t, tagname)

			elif tagname == 'Start':
				self.themes = copy.deepcopy(wid.start_theme)
				self.flash_tag(t, tagname)

			elif tagname == 'Defaults':
				self.themes = copy.deepcopy(self.default_themes)
				self.flash_tag(t, tagname)


			if (tagname in ['Defaults', 'Start']) or (tagname == 'TMP' and wid.flag_tmp):

				self.bgcolor, self.fgcolor = self.themes[self.curtheme]['normal_text'][:]

				for tab in self.tabs + [self.help_tab, self.err_tab]:
					self.update_syntags_colors(tab)
					self.set_text_widget_colors(tab)

				self.text_frame.config(bg=self.bgcolor)
				self.set_ln_widget_colors()
				self.set_other_frame_colors()


		wid.focus_set()


	def flash_tag(self, widget, tagname):
		''' Flash save_tag when clicked in colorchooser.
			widget is tkinter.Text -widget
		'''
		w = widget

		w.after(50, lambda args=[tagname],
				kwargs={'background':'green'}: w.tag_config(*args, **kwargs) )

		w.after(600, lambda args=[tagname],
				kwargs={'background':w.cget('background')}: w.tag_config(*args, **kwargs) )


	def color_choose(self, event=None):
		if self.state != 'normal' or self.is_fullscreen():
			self.bell()
			return 'break'

		colortop = tkinter.Toplevel()
		c = colortop
		c.title('Choose Color')
		c.start_theme = copy.deepcopy(self.themes)
		c.tmp_theme = copy.deepcopy(self.themes)
		c.flag_tmp = False

		shortcut_color = "<Alt-s>"
		shortcut_toggl = "<Alt-t>"

		if self.os_type == 'mac_os':
			shortcut_color = "<ssharp>"
			shortcut_toggl = "<dagger>"


		c.protocol("WM_DELETE_WINDOW", lambda: ( c.grab_release(), c.destroy(),
				self.text_widget.bind( shortcut_color, self.color_choose),
				self.text_widget.bind( shortcut_toggl, self.toggle_color),
				self.text_widget.focus_force()) )

		self.text_widget.bind( shortcut_color, self.do_nothing)
		self.text_widget.bind( shortcut_toggl, self.do_nothing)

		#c.textfont = tkinter.font.Font(family='TkDefaulFont', size=10)

		size_title = 12
		if self.os_type == 'mac_os': size_title = 16
		c.titlefont = tkinter.font.Font(family='TkDefaulFont', size=size_title)

		c.textwid = tkinter.Text(c, blockcursor=True, highlightthickness=0,
							bd=4, pady=4, padx=10, tabstyle='wordprocessor', font=self.menufont)

		c.scrollbar = tkinter.Scrollbar(c, orient=tkinter.VERTICAL, highlightthickness=0,
							bd=0, command = c.textwid.yview)


		c.textwid['yscrollcommand'] = c.scrollbar.set
		c.scrollbar.config(width=self.scrollbar_width)
		c.scrollbar.config(elementborderwidth=self.elementborderwidth)

		t = c.textwid

		t.tag_config('title', font=c.titlefont)
		t.tag_config('disabled', foreground='#a6a6a6')

		tags = [
		'Day',
		'Night',
		'Text',
		'Background',
		'normal_text',
		'keywords',
		'numbers',
		'bools',
		'strings',
		'comments',
		'breaks',
		'calls',
		'selfs',
		'match',
		'focus',
		'replaced',
		'mismatch',
		'selected',
		'Save_TMP',
		'TMP',
		'Start',
		'Defaults'
		]




		for tag in tags:
			t.tag_config(tag, font=self.menufont)
			t.tag_bind(tag, "<Enter>",
				lambda event, arg=[c, tag]: self.enter2(arg, event))
			t.tag_bind(tag, "<Leave>",
				lambda event, arg=[c, tag]: self.leave2(arg, event))
			t.tag_bind(tag, "<ButtonRelease-1>",
					lambda event, arg=[c, tag]: self.lclick2(arg, event))



		c.rowconfigure(1, weight=1)
		c.columnconfigure(1, weight=1)

		t.grid_configure(row=0, column = 0)
		c.scrollbar.grid_configure(row=0, column = 1, sticky='ns')


		i = tkinter.INSERT

		t.insert(i, 'Before closing, load setting from: Start\n', 'title')
		t.insert(i, 'if there were made unwanted changes.\n', 'title')
		t.insert(i, '\nChanging color for:\n', 'title')


		c.frontback_mode = None
		c.tag_idx = dict()

		if self.curtheme == 'day':

			t.insert(i, '[X] Day-mode	', 'Day')
			t.insert(i, '[X] Text color\n', 'Text')

			t.insert(i, '[ ] Night-mode	', 'Night')
			t.insert(i, '[ ] Background color\n', 'Background')

			c.frontback_mode = 'foreground'


		else:
			t.insert(i, '[ ] Day-mode	', 'Day')
			t.insert(i, '[X] Text color\n', 'Text')

			t.insert(i, '[X] Night-mode	', 'Night')
			t.insert(i, '[ ] Background color\n', 'Background')

			c.frontback_mode = 'foreground'



		t.insert(i, '\nSelect tag you want to modify\n', 'title')
		t.insert(i, 'normal text\n', 'normal_text')


		t.insert(i, '\nSyntax highlight tags\n', 'title')
		t.insert(i, 'keywords\n', 'keywords')
		t.insert(i, 'numbers\n', 'numbers')
		t.insert(i, 'bools\n', 'bools')
		t.insert(i, 'strings\n', 'strings')
		t.insert(i, 'comments\n', 'comments')
		t.insert(i, 'breaks\n', 'breaks')
		t.insert(i, 'calls\n', 'calls')
		t.insert(i, 'selfs\n', 'selfs')


		t.insert(i, '\nSearch tags\n', 'title')
		t.insert(i, 'match\n', 'match')
		t.insert(i, 'focus\n', 'focus')
		t.insert(i, 'replaced\n', 'replaced')


		t.insert(i, '\nParentheses\n', 'title')
		t.insert(i, 'mismatch\n', 'mismatch')

		t.insert(i, '\nSelection\n', 'title')
		t.insert(i, 'selected\n', 'selected')


		t.insert(i, '\nSave current setting to template,\n', 'title')
		t.insert(i, 'to which you can revert later:\n', 'title')
		t.insert(i, 'Save TMP\n', 'Save_TMP')

		t.insert(i, '\nLoad setting from:\n', 'title')
		t.insert(i, 'TMP\n', 'TMP')
		t.insert(i, 'Start\n', 'Start')
		t.insert(i, 'Defaults\n', 'Defaults')


		t.state = 'disabled'
		t.config(insertontime=0)


		c.grab_set()
		c.attributes('-topmost', 1)

		self.to_be_closed.append(c)

		return 'break'


########## Theme Related End
########## Run file Related Begin

	def enter(self, tagname, event=None):
		''' Used in error-page, when mousecursor enters hyperlink tagname.
		'''
		self.text_widget.config(cursor="hand2")
		self.text_widget.tag_config(tagname, underline=1)


	def leave(self, tagname, event=None):
		''' Used in error-page, when mousecursor leaves hyperlink tagname.
		'''
		self.text_widget.config(cursor=self.name_of_cursor_in_text_widget)
		self.text_widget.tag_config(tagname, underline=0)


	def lclick(self, tagname, event=None):
		'''	Used in error-page, when hyperlink tagname is clicked.
		'''
		self.tag_link(tagname)
		return 'break'


	def tag_link(self, tagname, event=None):
		''' Used in error-page, executed when hyperlink tagname is clicked.
		'''
		# Currently, error-tab is open and is about to be closed
		err_tab_index = self.tabindex
		# Index of tab to be opened
		new_index = False

		i = int(tagname.split("-")[1])
		filepath, errline = self.errlines[i]

		# stdin: runned tab without filename
		if filepath != "<stdin>": filepath = pathlib.Path(filepath)
		openfiles = [tab.filepath for tab in self.tabs]

		# Clicked activetab
		if filepath == self.tabs[self.oldindex].filepath or filepath == "<stdin>":
			new_index = self.oldindex

		# Clicked file that is open, switch activetab
		elif filepath in openfiles:
			for i,tab in enumerate(self.tabs):
				if tab.filepath == filepath:
					new_index = i
					break

		# else: open file in newtab
		else:
			try:
				with open(filepath, 'r', encoding='utf-8') as f:
					tmp = f.read()


					newtab = Tab(self.create_textwidget())

					self.set_textwidget(newtab)
					self.set_syntags(newtab)

					self.tabs.append(newtab)
					new_index = self.tabindex


					newtab.oldcontents = tmp

					if '.py' in filepath.suffix:
						indentation_is_alien, indent_depth = self.check_indent_depth(tmp)

						if indentation_is_alien:
							tmp = newtab.oldcontents.splitlines(True)
							tmp[:] = [self.tabify(line, width=indent_depth) for line in tmp]
							tmp = ''.join(tmp)
							newtab.contents = tmp

						else:
							newtab.contents = newtab.oldcontents

					else:
						newtab.contents = newtab.oldcontents


					newtab.filepath = filepath
					newtab.type = 'normal'
					newtab.text_widget.insert('1.0', newtab.contents)

					if self.can_do_syntax(newtab):
						self.update_lineinfo(newtab)

						a = self.get_tokens(newtab)
						self.insert_tokens(a, tab=newtab)


					self.set_bindings(newtab)

					newtab.text_widget.edit_reset()
					newtab.text_widget.edit_modified(0)


			except (EnvironmentError, UnicodeDecodeError) as e:
				print(e.__str__())
				print(f'\n Could not open file: {filepath}')
				self.bell()
				return



		line = errline + '.0'
		self.tabs[new_index].position = line
		self.tabs[new_index].text_widget.mark_set('insert', line)

		# Rest of here should be as close to stop_show_errors as possible
		self.state = 'normal'
		self.text_widget.config(state='normal')
		self.cursor_frame.place_forget()

		self.tab_close(self.tabs[err_tab_index])
		self.tabs.pop(err_tab_index)
		self.tab_open(self.tabs[new_index])
		self.tabindex = new_index

		self.err_tab.text_widget.delete('1.0', 'end')

		self.bind("<Escape>", self.esc_override)
		self.unbind( "<ButtonRelease-1>", funcid=self.bid_mouse)
		self.bind("<Button-%i>" % self.right_mousebutton_num,
			lambda event: self.popup_raise(event))
		self.update_title()

		### tag_link End ######


	def update_popup_run_action(self):

		options = dict()

		if self.popup_run_action == 1:
			options['label'] = "  run module"
			options['command'] = lambda kwargs={'module':True}: self.run(**kwargs)

		else:
			options['label'] = "  run custom"
			options['command'] = lambda kwargs={'custom':True}: self.run(**kwargs)

		self.popup.delete(self.popup_run_action_idx)
		self.popup.insert_command(self.popup_run_action_idx, **options)


	def popup_run_action_set(self, choice=None):
		'''	Set run-action to be executed from popup-menu.
			Choices are: False: default run-file
			1: run-module
			2: run-custom
		'''
		if not choice: pass
		elif type(choice) != int:
			self.bell()
			return
		elif choice == 1: self.popup_run_action = 1
		else: self.popup_run_action = 2
		self.update_popup_run_action()

		if self.popup_run_action == 1:
			print('run module')
			print('currently: ', self.module_run_name )
		else:
			print('run custom')
			print('currently: ', self.custom_run_cmd )

		return


	def custom_run_cmd_set(self, cmd=None):
		'''	Set command to be executed from popup-menu.
			Command must be list.
			Setting doesn't do test-run to verify cmd.
		'''
		if cmd is None: pass
		elif not cmd: self.custom_run_cmd = None
		elif type(cmd) != list:
			self.bell()
			return
		else: self.custom_run_cmd = cmd
		print(self.custom_run_cmd)
		return


	def run_module_set(self, cmd=None):
		'''	Set name of module (and possible arguments), to be used on test-runs.
			Command must be list: ['modulename', 'arg1', 'arg2'..]
			This is then added after: [sys.executable, '-m']
			Setting doesn't do test-run to verify cmd
		'''
		if cmd is None: pass
		elif not cmd: self.module_run_name = None
		elif type(cmd) != list:
			self.bell()
			return
		else:
			self.module_run_name = [sys.executable, '-m']
			self.module_run_name.extend(cmd)
		print(self.module_run_name)
		return


	def timeout_set(self, timeout=None):
		'''	Set timeout for test-runs,
			default is 2 (seconds)
		'''
		if timeout is None: pass
		elif not timeout: self.timeout = None
		elif type(timeout) != int:
			self.bell()
			return
		else: self.timeout = timeout
		print(self.timeout)
		return


	def run(self, module=False, custom=False):
		'''	Do Test-run with timeout
		'''
		curtab = self.tabs[self.tabindex]
		if (self.state != 'normal'):
			self.bell()
			return 'break'

		if not self.save_forced():
			self.bell()
			return 'break'


		source = curtab.filepath
		d = dict(stderr=subprocess.PIPE)
		if self.os_type == 'mac_os' and not self.in_mainloop and self.mac_print_fix:
			d = dict(capture_output=True)

		# Enable running code without filename
		if (curtab.type != 'normal'):
			tmp = self.text_widget.get('1.0', 'end')
			tmp = bytes(tmp, 'utf-8')
			d['input'] = tmp
			source = '-'

		d['timeout'] = self.timeout


		# Normal
		cmd = [sys.executable, source]

		# Run module
		if module:
			if self.module_run_name:
				cmd = self.module_run_name
			else:
				self.bell()
				return

		# Run custom
		elif custom:
			if self.custom_run_cmd:
				cmd = self.custom_run_cmd
			else:
				self.bell()
				return

		self.wait_for(200)
		print('TESTRUN, START')
		self.wait_for(800)


		has_err = False
		err = ''


		# First check for timeout
		try: p = subprocess.run(cmd, **d)
		except subprocess.TimeoutExpired as e:
			print('TIMED OUT after %ds' % self.timeout)
			return

		# For example: executable does not exist
		except Exception as e:
			print(e)
			return

		# Real errors
		try: p.check_returncode()

		except subprocess.CalledProcessError:
			has_err = True


		# fix for macos printing issue
		if self.os_type == 'mac_os' and not self.in_mainloop and self.mac_print_fix:
			out = p.stdout.decode()
			if len(out) > 0: print(out)

		if has_err:
			# Error
			err = p.stderr.decode()
		else:
			# Stuff possibly put to stderr
			print(p.stderr.decode())


		self.err = False
		self.wait_for(500)

		if len(err) != 0:
			self.err = err.splitlines()
			print('\nTESTRUN, FAIL')
		else: print('\nTESTRUN, OK')
		print(30*'-')

		self.show_errors()


	def show_errors(self):
		''' Show traceback from last run with added hyperlinks.
		'''
		if not self.err: return

		self.bind("<Button-%i>" % self.right_mousebutton_num, self.do_nothing)
		self.bind("<Escape>", self.stop_show_errors)


		self.state = 'error'

		self.tab_close(self.tabs[self.tabindex])
		self.tabs.append(self.err_tab)
		self.oldindex = self.tabindex
		self.tabindex = len(self.tabs) -1
		self.tab_open(self.err_tab)


		self.errlines = list()
		openfiles = [tab.filepath for tab in self.tabs]

		self.auto_update_syntax_stop()


		for tag in self.text_widget.tag_names():
			if 'hyper' in tag:
				self.text_widget.tag_delete(tag)


		for line in self.err:
			tmp = line

			tagname = "hyper-%s" % len(self.errlines)
			self.text_widget.tag_config(tagname)

			# Why ButtonRelease instead of just Button-1:
			# https://stackoverflow.com/questions/24113946

			self.text_widget.tag_bind(tagname, "<ButtonRelease-1>",
				lambda event, arg=tagname: self.lclick(arg, event))

			self.text_widget.tag_bind(tagname, "<Enter>",
				lambda event, arg=tagname: self.enter(arg, event))

			self.text_widget.tag_bind(tagname, "<Leave>",
				lambda event, arg=tagname: self.leave(arg, event))

			# Parse filepath and linenums from errors
			if 'File ' in line and 'line ' in line:
				self.text_widget.insert(tkinter.INSERT, '\n')

				data = line.split(',')[:2]
				linenum = data[1][6:]
				path = data[0][8:-1]

				# Running tab without filename
				if self.tabs[self.oldindex].type != 'normal':
					if "<stdin>" in path:
						filepath = "<stdin>"
						path = "<stdin>"
						pathlen = len(path) + 2

				# Normal case
				else:
					path = data[0][8:-1]
					pathlen = len(path) + 2
					filepath = pathlib.Path(path)


				self.errlines.append((filepath, linenum))

				self.text_widget.insert(tkinter.INSERT, tmp)
				s0 = tmp.index(path) - 1
				s = self.text_widget.index('insert linestart +%sc' % s0 )
				e = self.text_widget.index('%s +%sc' % (s, pathlen) )

				self.text_widget.tag_add(tagname, s, e)

				if filepath in openfiles:
					self.text_widget.tag_config(tagname, foreground='brown1')
					self.text_widget.tag_raise(tagname)

				self.text_widget.insert(tkinter.INSERT, '\n')

			else:
				self.text_widget.insert(tkinter.INSERT, tmp +"\n")

				# Make it look bit nicer
				if self.syntax:
					# -1 lines because linebreak has been added already
					start = self.text_widget.index('insert -1 lines linestart')
					end = self.text_widget.index('insert -1 lines lineend')

					self.update_lineinfo(self.err_tab)
					self.update_tokens(start=start, end=end, line=line,
										tab=self.err_tab)


		self.err_tab.position = '1.0'
		self.err_tab.text_widget.mark_set('insert', self.err_tab.position)
		self.err_tab.text_widget.see(self.err_tab.position)
		self.err_tab.text_widget.focus_set()
		self.text_widget.config(state='disabled')

		# Show 'insertion cursor' while text_widget is disabled
		self.bid_mouse = self.bind( "<ButtonRelease-1>", func=self.cursor_frame_set, add=True)

		self.text_widget.edit_reset()
		self.text_widget.edit_modified(0)

		self.auto_update_syntax_continue()


	def stop_show_errors(self, event=None):
		self.state = 'normal'
		self.text_widget.config(state='normal')
		self.cursor_frame.place_forget()

		self.tab_close(self.tabs[self.tabindex])
		self.tabs.pop()
		self.tabindex = self.oldindex
		self.tab_open(self.tabs[self.tabindex])
		self.err_tab.text_widget.delete('1.0', 'end')

		self.bind("<Escape>", self.esc_override)
		self.unbind( "<ButtonRelease-1>", funcid=self.bid_mouse)
		self.bind("<Button-%i>" % self.right_mousebutton_num,
			lambda event: self.popup_raise(event))

		return 'break'


########## Run file Related End
########## Select and move Begin

	def line_is_defline(self, line):
		''' line: string

			Check if line is definition line of function or class.

			On success, returns string: name of function
			On fail, returns False

			Called from: walk_scope, get_scope_start, get_scope_path
		'''

		tmp = line.split()
		res = False

		try:
			if tmp[0] in [ 'async', 'class', 'def']:
				patt_end = ':'
				if tmp[0] == 'async':
					tmp = tmp[2]
				else:
					tmp = tmp[1]

				if '(' in tmp: patt_end = '('

				try:
					e = tmp.index(patt_end)
					res = tmp[:e]

				except ValueError: pass
		except IndexError: pass

		return res


	def get_deflines(self, tab):
		''' Get definition lines

			Creates list: linenums,
			which consist of tuples: (ind_lvl, idx_as_float, defname)
			Example, for 'defline1'-tag:
			(indentation level 1) -->(1, 1234.1, 'some_func')

			That would mean there is definition line in line 1234 and it has
			indentation level 1, and name of the function is 'some_func'.

			Called from: get_absolutely_next_defline, goto_def
		'''

		# Get non empty ranges
		tagnames = [ tag for tag in self.tagnames if 'defline' in tag ]
		tagnames.sort(key=lambda s: int(s.split('defline')[1]) )
		linenums = list()
		for tag in tagnames:
			# [::2] get first item then every other item
			# --> get only range start -indexes
			if r := tab.text_widget.tag_ranges(tag)[::2]:
				# defline_info is stored as tuples: (ind_lvl, idx, func_name)
				# example: 'defline2'-tag (indentation level 2)
				# -->(2, 1234.2, 'some_func')
				for idx in r:
					idx_as_str = str(idx)
					idx_as_float = float(idx_as_str)
					ind_lvl = int(tag.split('defline')[1])

					s, e = f'{idx_as_str} linestart', f'{idx_as_str} lineend'
					defline_content = tab.text_widget.get(s, e)
					defname = self.line_is_defline(defline_content)
					if not defname: defname = '-1'

					defline_info = (ind_lvl, idx_as_float, defname)
					linenums.append(defline_info)

			else: break

		#print(linenums)

		return linenums


	def get_absolutely_next_defline(self, index='insert', down=False, maxind=9, update=True):
		''' Get (possibly absolutely) next defline

			maxind: search only deflines with indentation <= maxind
			default:maxind=9 --> efectively: search absolutely next defline

			if maxind is set to same indentation than current defline
			--> search next defline (with rising tendency)

			update: update self.deflines,
			which holds deflinenums and indentation

			Called from walk_scope

			On success, returns tuple (1, 1234.1, 'some_func')
			(indentation, index, funcname)

			else: False
		'''

		if update:
			self.deflines = self.get_deflines(self.tabs[self.tabindex])
		curlinenum = float(self.text_widget.index(index))
		linenums = self.deflines[:]

		if down:
			linenums.sort(key=lambda t: t[1])
			for i in range(len(linenums)):
				if linenums[i][1] > curlinenum and linenums[i][0] <= maxind:
					return linenums[i]
			else: return False

		else:
			linenums.sort(reverse=True, key=lambda t: t[1])
			for i in range(len(linenums)):
				if linenums[i][1] < curlinenum and linenums[i][0] <= maxind:
					return linenums[i]
			else: return False


	def walk_scope(self, event=None, down=False, absolutely_next=False):
		''' Walk definition lines up or down.

			Walking has a rising tendency: if walking up
			from the first function definition line of a class,
			cursor is moved to the class definition line. If
			continuing there, walking up or down, one now walks
			class definition lines. Same happens when walking
			down from last function definition of a class.
			( And for nested functions )

			When walking with absolutely_next-flag,
			Cursor is moved to absolutely next defline.


			Note: Puts insertion-cursor on defline, for example selection purposes

		'''
		# Why can_do_syntax? Because tag: 'strings' is
		# used while parsing. Tag exists only if synxtax-highlighting is on.
		# This means one can not walk_scope without syntax-highlight.
		if (not self.can_do_syntax()) or (self.state not in ['normal', 'search', 'goto_def']):
			self.bell()
			return 'break'


		# lines of interest ends with: ### pos

		idx = self.get_safe_index()
		line = self.text_widget.get('%s linestart' % idx, '%s lineend' % idx)

		update = True
		if idx == self.cur_defline: update = False
		else: self.cur_defline = '-1.-1'


		if absolutely_next:
			if t := self.get_absolutely_next_defline(down=down, update=update):
				ind_lvl, next_deflinenum_as_float, _ = t
				self.cur_defline = pos = str(next_deflinenum_as_float) ### pos
			else:
				self.bell()
				return 'break'

		# is cursor already at defline?
		elif self.line_is_defline(line):

			# use defline tag:
			# find next defline that has same or smaller indentation
			ind = 0
			for char in line:
				if char in ['\t']: ind += 1
				else: break

			if t := self.get_absolutely_next_defline(down=down, maxind=ind, update=update):
				ind_lvl, next_deflinenum_as_float, _ = t
				self.cur_defline = pos = str(next_deflinenum_as_float) ### pos
			else:
				self.bell()
				return 'break'

		elif not down:
			(scope_line, ind_defline,
			idx_scope_start) = self.get_scope_start()
			if scope_line == '__main__()':
				self.bell()
				return 'break'

			pos = idx_scope_start ### pos

		else:
			pos = 'insert' ### pos

			(scope_line, ind_defline,
			idx_scope_start) = self.get_scope_start(index=pos)

			if scope_line != '__main__()':
				idx_scope_end = pos = self.get_scope_end(ind_defline, idx_scope_start)
			# Q: Why not: else: return here, after if?
			# A: 'insert' could be before(more up) than first defline


			# Now have idx_scope_start, idx_scope_end of current scope.
			# Below, searching for: idx_scope_start of next defline(down)
			#####################################
			blank_range = '{0,%d}' % ind_defline
			p1 = r'^[[:blank:]]%s' % blank_range
			p2  = r'[acd]'

			patt = p1 + p2

			while pos:
				try:
					pos = self.text_widget.search(patt, pos, stopindex='end', regexp=True)

				except tkinter.TclError as e:
					print(e)
					self.bell()
					return 'break'

				if not pos:
					self.bell()
					return 'break'

				if 'strings' in self.text_widget.tag_names(pos):
					#print('strings3', pos)
					if pos == 'end':
						self.bell()
						return 'break'
					pos = self.text_widget.tag_prevrange('strings', pos)[1] + ' +1 lines linestart'
					continue

				lineend = '%s lineend' % pos
				linestart = '%s linestart' % pos
				line = self.text_widget.get( linestart, lineend )
				if res := self.line_is_defline(line):
					pos = self.idx_linestart(pos)[0]
					break

				pos = '%s +1 lines' % pos
				##################################

		# Put cursor on defline
		try:
			self.text_widget.mark_set('insert', pos)
			self.wait_for(100)
			self.ensure_idx_visibility(pos)

		except tkinter.TclError as e:
			print(e)

		return 'break'


	def select_scope(self, event=None, index='insert'):
		''' Select current scope, function or class.

			Function can be selected if cursor is:
				1: At definition line

				2: Below such line that directly belongs to scope
					of a function (== does not belong to nested function).

				Function can be selected even after return line

			Same is true for class but, since there usually is not
			code at the end of class that does not belong to method:
			When trying to select class at the end of class
			--> get last method selected instead
			--> goto class definition line, try again

		'''
		# Why can_do_syntax? Because tag: 'strings' is
		# used while parsing. Tag exists only if synxtax-highlighting is on.
		# This means one can not walk_scope without syntax-highlight.
		if (not self.can_do_syntax()) or (self.state not in ['normal', 'search', 'goto_def']):
			self.bell()
			return 'break'

		pos = index

		(scope_line, ind_defline,
		idx_scope_start) = self.get_scope_start(index=pos)

		if scope_line != '__main__()':
			idx_scope_end = self.get_scope_end(ind_defline, idx_scope_start)
		else:
			self.bell()
			return 'break'

		self.text_widget.tag_remove('sel', '1.0', tkinter.END )
		self.wait_for(20)

		# Is start of selection not viewable?
		if not self.text_widget.bbox(idx_scope_start):
			self.wait_for(121)
			self.ensure_idx_visibility(idx_scope_start, back=4)
			self.wait_for(100)
		else:
			self.text_widget.mark_set('insert', idx_scope_start)

		self.text_widget.mark_set(self.anchorname, idx_scope_end)
		self.text_widget.tag_add('sel', idx_scope_start, idx_scope_end )

		return 'break'


	def move_many_lines(self, event=None):
		''' Move or select 10 lines from cursor.
			Called from linux or windows.
			Mac stuff is in mac_cmd_overrides()
		'''

		if self.state not in  ['normal', 'search', 'goto_def']:
			self.bell()
			return 'break'

		if event.widget != self.text_widget:
			return


		# Check if: not only ctrl (+shift) down, then return
		if self.os_type == 'linux':
			if event.state not in  [4, 5]: return

		elif self.os_type == 'windows':
			if event.state not in [262148, 262149, 262156, 262157 ]: return



		# Pressed Control + Shift + arrow up or down.
		# Want: select 10 lines from cursor.

		# Pressed Control + arrow up or down.
		# Want: move 10 lines from cursor.


		# Taken from center_view:
		num_lines = self.text_widget_height // self.line_height
		# Lastline of visible window
		lastline_screen = int(float(self.text_widget.index('@0,65535')))
		firstline_screen = lastline_screen - num_lines
		# Lastline of file would be:
		#last = int(float(self.text_widget.index('end'))) - 1
		curline = int(float(self.text_widget.index('insert')))
		# This seems not to work (not in view/sync):
		#curline = self.tabs[self.tabindex].oldlinenum
		to_up = curline - firstline_screen
		to_down = lastline_screen - curline


		# Using Tcl-script here doesn't seem to improve speed much
		cmd = '''
		set ww %s
		set ee %s
		set sd %s
		set near %s
		set n 1

		while {$n < 11} {
			if {$near > 0} {
						after %s {
						$ww yview scroll $sd units
						event generate $ww $ee
						}
			} else {
				after %s {event generate $ww $ee}
				}

			incr n 1

		}
		'''
		### %s are:
		### tcl_name_of_contents, event_name/e, scroll_direction
		### near, wait_time, wait_time

		w = self.tcl_name_of_contents

		if event.keysym == 'Up':
			e = '<<SelectPrevLine>>'

			if event.state not in [ 5, 262157, 262149 ]:
				e = '<<PrevLine>>'

			# Add some delay to get visual feedback
			near = '0'
			if to_up < 10: near = '1'
			# Slow down when only moving, to see cursor movement 'animation'
			wait_time = '[expr 17*$n]'
			scroll_direction = '-1'
			update_idle = '$ww update idletasks'
			if 'Select' in e: wait_time = '5'
			try:	self.tk.eval( cmd % ( w, e, scroll_direction, near, wait_time, wait_time ) )
			except tkinter.TclError as err: print(err)
			return 'break'


		elif event.keysym == 'Down':
			e = '<<SelectNextLine>>'

			if event.state not in [ 5, 262157, 262149 ]:
				e = '<<NextLine>>'

			near = '0'
			if to_down < 10: near = '1'
			wait_time = '[expr 17*$n]'
			scroll_direction = '+1'
			if 'Select' in e: wait_time = '5'
			try:	self.tk.eval( cmd % ( w, e, scroll_direction, near, wait_time, wait_time ) )
			except tkinter.TclError as err: print(err)
			return 'break'
		else:
			return


	def center_view(self, event=None, up=False):
		''' Raise insertion-line
		'''
		if self.state not in ['normal', 'help', 'error', 'search', 'replace', 'replace_all', 'goto_def']:
			self.bell()
			return 'break'

		self.wait_for(60)
		# If pressed Control-Shift-j/u, move one line at time
		if filter_keys_in(event, ['Control', 'Shift']):
			n=1
			if up: n=-1
			self.text_widget.yview_scroll(n, 'units')
			return 'break'


		num_lines = self.text_widget_height // self.line_height
		num_scroll = num_lines // 3
		pos = self.text_widget.index('insert')
		#posint = int(float(self.text_widget.index('insert')))
		# Lastline of visible window
		lastline_screen = int(float(self.text_widget.index('@0,65535')))

		# Lastline
		last = int(float(self.text_widget.index('end'))) - 1
		curline = int(float(self.text_widget.index('insert'))) - 1

		if up: num_scroll *= -1

		# Near fileend
		elif curline + 2*num_scroll + 2 > last:
			self.text_widget.insert(tkinter.END, num_scroll*'\n')
			self.text_widget.mark_set('insert', pos)


		# Near screen end
		#elif curline + 2*num_scroll + 2 > lastline_screen:
		self.text_widget.yview_scroll(num_scroll, 'units')


		# No ensure_view, enable return to cursor by arrow keys
		return 'break'


	def idx_lineend(self, index='insert'):
		return  self.text_widget.index( '%s display lineend' % index )


	def line_is_empty(self, index='insert'):

		safe_index = self.get_safe_index(index)

		s = '%s linestart' % safe_index
		e = '%s lineend' % safe_index

		patt = r'%s get -displaychars {%s} {%s}' % (self.tcl_name_of_contents, s, e )

		try:	line = self.text_widget.tk.eval(patt)
		except tkinter.TclError as err:
			print('INFO: line_is_empty:\n', err, 'index:', index, 'safe_index:', safe_index,
			's:', s, 'e:', e, 'patt:', patt,'tcl_name_of_contents:', self.tcl_name_of_contents )
			self.bell()
			# or False?
			return True

		return line.strip() == ''


	def idx_linestart(self, index='insert'):
		'''	Returns: pos, line_starts_from_curline

			Where pos is tkinter.Text -index:

				if line starts from curline:
					pos = end of indentation if there is such --> pos != indent0
					(if there is no indentation, pos == indent0)
				else:
					pos = start of display-line == indent0


			If line is empty, pos = start of line == indent0


			indent0 definition, When:
				1: Cursor is not at the first line of file
				2: User presses arrow-left

				If then: Cursor moves up one line,
				it means the cursor was at indent0 before key-press.

		'''
		safe_index = self.get_safe_index(index)

		pos = self.text_widget.index( '%s linestart' % safe_index)
		s1 = '%s display linestart' % safe_index
		s2 = '%s linestart' % safe_index
		line_starts_from_curline = self.text_widget.compare( s1,'==',s2 )

		if not line_starts_from_curline:
			pos = self.text_widget.index( '%s display linestart' % safe_index)


		elif not self.line_is_empty(safe_index):
			s = '%s linestart' % safe_index
			e = '%s lineend' % safe_index

##			patt = r'%s get -displaychars {%s} {%s}' % (self.tcl_name_of_contents, s, e )
##			try: line_contents = self.text_widget.tk.eval(patt)
##			except tkinter.TclError as err:
##				print('INFO: idx_linestart:' , err)

			stop = '%s lineend' % safe_index
			if r := self.line_is_elided(safe_index): stop = r[0]

			patt = r'^[[:blank:]]*[^[:blank:]]'

			pos = self.text_widget.search(patt, s, stopindex=stop, regexp=True,
					count=self.search_count_var)

			# self.search_count_var.get() == indentation level +1
			# because pattern matches: not blank at end of patt
			ind = '%s +%d chars' % (pos, self.search_count_var.get()-1)
			pos = self.text_widget.index(ind)


		return pos, line_starts_from_curline


	def set_selection(self, ins_new, ins_old, have_selection, selection_started_from_top,
					sel_start, sel_end, direction=None):
		''' direction is 'up' or 'down'

			Called from: select_by_words(), goto_linestart()
		'''
		###########################################
		# Get marknames: self.text_widget.mark_names()
		# It gives something like this if there has been or is a selection:
		# 'insert', 'current', 'tk::anchor1'.
		# This: 'tk::anchor1' is name of the selection-start-mark
		# used here as in self.anchorname below.
		# This is done because adjusting only 'sel' -tags
		# is not sufficient in selection handling, when not using
		# builtin-events, <<SelectNextWord>> and <<SelectPrevWord>>.
		###########################################

		if direction == 'down':
			if have_selection:
				self.text_widget.tag_remove('sel', '1.0', tkinter.END)

				if selection_started_from_top:
					self.text_widget.mark_set(self.anchorname, sel_start)
					self.text_widget.tag_add('sel', sel_start, ins_new)
				else:
					# Check if selection is about to be closed
					# (selecting towards selection-start)
					# to avoid one char selection -leftovers.
					if self.text_widget.compare( '%s +1 chars' % ins_new, '>=' , sel_end ):
						self.text_widget.mark_set('insert', sel_end)
						self.text_widget.mark_set(self.anchorname, sel_end)
						return

					self.text_widget.mark_set(self.anchorname, sel_end)
					self.text_widget.tag_add('sel', ins_new, sel_end)

			# No selection,
			# no need to check direction of selection:
			else:
				self.text_widget.mark_set(self.anchorname, ins_old)
				self.text_widget.tag_add('sel', ins_old, ins_new)


		elif direction == 'up':
			if have_selection:
				self.text_widget.tag_remove('sel', '1.0', tkinter.END)

				if selection_started_from_top:
					# Check if selection is about to be closed
					# (selecting towards selection-start)
					# to avoid one char selection -leftovers.
					if self.text_widget.compare( '%s -1 chars' % ins_new, '<=' , sel_start ):
						self.text_widget.mark_set('insert', sel_start)
						self.text_widget.mark_set(self.anchorname, sel_start)
						return

					self.text_widget.mark_set(self.anchorname, sel_start)
					self.text_widget.tag_add('sel', sel_start, ins_new)

				else:
					self.text_widget.mark_set(self.anchorname, sel_end)
					self.text_widget.tag_add('sel', ins_new, sel_end)

			# No selection,
			# no need to check direction of selection:
			else:
				self.text_widget.mark_set(self.anchorname, ins_old)
				self.text_widget.tag_add('sel', ins_new, ins_old)


	def get_sel_info(self):
		''' Called from select_by_words, goto_linestart
		'''
		have_selection = len(self.text_widget.tag_ranges('sel')) > 0
		ins_old = self.text_widget.index('insert')
		selection_started_from_top = False
		sel_start = False
		sel_end = False


		# tkinter.SEL_FIRST is always before tkinter.SEL_LAST
		# no matter if selection started from top or bottom:
		if have_selection:
			sel_start = self.text_widget.index(tkinter.SEL_FIRST)
			sel_end = self.text_widget.index(tkinter.SEL_LAST)
			if ins_old == sel_end:
				selection_started_from_top = True


		return [ins_old, have_selection, selection_started_from_top,
				sel_start, sel_end ]


	def select_by_words(self, event=None):
		'''	Pressed ctrl (or Alt in mac) + shift and arrow left or right.
			Make <<SelectNextWord>> and <<SelectPrevWord>> to stop at lineends.
		'''
		if self.state not in ['normal', 'help', 'error', 'search', 'replace', 'replace_all', 'goto_def']:
			self.bell()
			return 'break'

		# Check if: ctrl + shift down.
		# MacOS event is already checked.
		if self.os_type == 'linux':
			if event.state != 5: return

		elif self.os_type == 'windows':
			# with or without numlock
			if event.state not in [ 262157, 262149 ]: return


		[ ins_old, have_selection, selection_started_from_top,
		sel_start, sel_end ] = args = self.get_sel_info()


		if event.keysym == 'Right':
			ins_new = self.move_by_words_right()
			args.insert(0, ins_new)
			self.set_selection(*args, direction='down')


		elif event.keysym == 'Left':
			ins_new = self.move_by_words_left()
			args.insert(0, ins_new)
			self.set_selection(*args, direction='up')


		return 'break'


	def move_by_words_left(self):
		''' Returns tkinter.Text -index: pos
			and moves cursor to it.
		'''

		idx_linestart, line_started_from_curline = self.idx_linestart()
		i_orig = self.text_widget.index('insert')

		if self.line_is_empty():
			# Go over empty space first
			self.text_widget.event_generate('<<PrevWord>>')

			# And put cursor to line end
			i_new = self.idx_lineend()
			self.text_widget.mark_set('insert', i_new)


		elif not line_started_from_curline:

			# At indent0, put cursor to line end of previous line
			if self.text_widget.compare('insert', '==', idx_linestart):
				self.text_widget.event_generate('<<PrevWord>>')
				self.text_widget.mark_set('insert', 'insert display lineend')

			# Not at indent0, just check cursor not go over indent0
			else:
				self.text_widget.event_generate('<<PrevWord>>')
				if self.text_widget.compare('insert', '<', idx_linestart):
					self.text_widget.mark_set('insert', idx_linestart)


		# Below this line is non empty and not wrapped
		############
		# Most common scenario:
		# Is cursor after idx_linestart?
		# i_orig > idx_linestart
		elif self.text_widget.compare( i_orig, '>', idx_linestart ):
			self.text_widget.event_generate('<<PrevWord>>')

			# Check that cursor did not go over idx_linestart
			i_new = self.text_widget.index(tkinter.INSERT)
			if self.text_widget.compare( i_new, '<', idx_linestart):
				self.text_widget.mark_set('insert', idx_linestart)


		## Below this i_orig <= idx_linestart
		############
		# At idx_linestart
		elif i_orig == idx_linestart:

			# No indentation?
			if self.get_line_col_as_int(index=idx_linestart)[1] == 0:
				# At filestart?
				if self.text_widget.compare( i_orig, '==', '1.0'):
					pos = i_orig
					return pos

				# Go over empty space first
				self.text_widget.event_generate('<<PrevWord>>')

				# And put cursor to line end
				i_new = self.idx_lineend()
				self.text_widget.mark_set('insert', i_new)

			# Cursor is at idx_linestart (end of indentation)
			# of line that has indentation.
			else:
				# Put cursor at indent0 (start of indentation)
				self.text_widget.mark_set('insert', 'insert linestart')


		# Below this only lines that has indentation
		############
		# 1: Cursor is not after idx_linestart
		#
		# 2: Nor at idx_linestart == end of indentation, if line has indentation
		# 							start of line, (indent0), if line has no indentation
		#
		# --> Cursor is in indentation

		# At indent0 of line that has indentation
		elif self.get_line_col_as_int(index=i_orig)[1] == 0:
			# At filestart?
			if self.text_widget.compare( i_orig, '==', '1.0'):
				pos = i_orig
				return pos

			# Go over empty space first
			self.text_widget.event_generate('<<PrevWord>>')

			# And put cursor to line end
			i_new = self.idx_lineend()
			self.text_widget.mark_set('insert', i_new)


		# Cursor is somewhere between (exclusively) indent0 and idx_linestart
		# on line that has indentation.
		else:
			# Put cursor at indent0
			self.text_widget.mark_set('insert', 'insert linestart')


		pos = self.text_widget.index('insert')
		return pos


	def move_by_words_right(self):
		''' Returns tkinter.Text -index: pos
			and moves cursor to it.
		'''

		# Get some basic indexes first
		idx_linestart, line_started_from_curline = self.idx_linestart()
		i_orig = self.text_widget.index('insert')
		e = self.idx_lineend()


		if self.line_is_empty():
			# Go over empty space first
			self.text_widget.event_generate('<<NextWord>>')

			# And put cursor to idx_linestart
			i_new = self.idx_linestart()[0]

			# Check not at fileend, if not then proceed
			if i_new:
				self.text_widget.mark_set('insert', i_new)


		# Below this line is not empty
		##################
		# Cursor is at lineend, goto idx_linestart of next non empty line
		elif i_orig == e:

			# Check if at fileend
			if self.text_widget.compare('%s +1 chars' % i_orig, '==', tkinter.END):
				pos = i_orig
				return pos

			self.text_widget.event_generate('<<NextWord>>')
			idx_linestart = self.idx_linestart()[0]
			self.text_widget.mark_set('insert', idx_linestart)


		# Below this line cursor is before line end
		############
		# Most common scenario
		# Cursor is at or after idx_linestart
		# idx_lineend > i_orig >= idx_linestart
		elif self.text_widget.compare(i_orig, '>=', idx_linestart):

			self.text_widget.event_generate('<<NextWord>>')

			# Check not over lineend
			if self.text_widget.compare('insert', '>', e):
				self.text_widget.mark_set('insert', e)


		############
		# Below this line has indentation and is not wrapped
		# Cursor is at
		# indent0 <= i_orig < idx_linestart

		# --> put cursor to idx_linestart
		############
		else:
			self.text_widget.mark_set('insert', idx_linestart)


		pos = self.text_widget.index('insert')
		return pos


	def move_by_words2(self, event=None):
		''' Move two words by time with Control-period or comma
		'''

		direction = 'Left'
		if event.keysym == 'period': direction = 'Right'


		# There is no MacOS event check in move_by_words
		# --> Choosing linux state as default
		# These don't really matter so much, only to pass the state-checks
		# This likely should be done with masks
		f = self.move_by_words
		event_state = 4
		if self.os_type == 'windows': event_state = 262156


		event = FakeEvent(keysym=direction, state=event_state)

		f(event=event)

		if direction == 'Right': idx = self.idx_lineend()
		else: idx = self.idx_linestart()[0]
		if self.text_widget.compare( idx, '!=', 'insert'):
			f(event=event)

		return 'break'


	def move_by_words(self, event=None):
		'''	Pressed ctrl or Alt and arrow left or right.
			Make <<NextWord>> and <<PrevWord>> to handle lineends.
		'''
		if self.state not in ['normal', 'help', 'error', 'search', 'replace', 'replace_all', 'goto_def']:
			self.bell()
			return 'break'

		# Check if: not only ctrl down, then return
		# MacOS event is already checked.
		if self.os_type == 'linux':
			if event.state != 4: return

		elif self.os_type == 'windows':
			# With numlock +8 or without
			if event.state not in [ 262156, 262148 ]: return


		if event.keysym == 'Right':
			pos = self.move_by_words_right()

		elif event.keysym == 'Left':
			pos = self.move_by_words_left()

		else:
			return


		return 'break'


	def handle_updown(self, event=None):
		if self.comp_frame.winfo_ismapped():
			self.comp_frame.place_forget()
			return 'break'
		return


	def check_sel(self, event=None):
		'''	Pressed arrow left or right.
			If have selection, put cursor on the wanted side of selection.
		'''

		if self.state in [ 'filedialog' ]:
			self.bell()
			return 'break'

		if self.state in [ 'search', 'replace' ]:
			pos = self.search_focus[0]
			# If cur match viewable
			if self.text_widget.bbox(pos):
				self.message_frame2.place_forget()
			# Else:
			# keep gotodef banner on


		# self.text_widget or self.entry
		wid = event.widget

		# Check if have shift etc. pressed. If is, return to default bindings.
		# macOS event is already handled in mac_cmd_overrides.
		# macOS event here is only plain arrow left or right and has selection.
		if self.os_type != 'mac_os':
			if self.os_type == 'linux' and event.state != 0: return
			# With numlock +8 or without
			if self.os_type == 'windows' and event.state not in [ 262152, 262144 ]: return

			# This also has been already done for macOS
			if self.cursor_frame.winfo_ismapped():
				self.cursor_frame.place_forget()

			have_selection = False

			if wid == self.entry:
				have_selection = self.entry.selection_present()

			elif wid == self.text_widget:
				have_selection = len(self.text_widget.tag_ranges('sel')) > 0

			else:
				return


			if not have_selection: return
			##############################


		# SEL_FIRST is always before SEL_LAST
		s = wid.index(tkinter.SEL_FIRST)
		e = wid.index(tkinter.SEL_LAST)
		i = wid.index(tkinter.INSERT)

		if wid == self.text_widget:

			# Leave cursor where it is if have selected all
			if s == self.text_widget.index('1.0') and e == self.text_widget.index(tkinter.END):
				self.text_widget.tag_remove('sel', '1.0', tkinter.END)


			# When long selection == index not visible:
			# at first keypress, show wanted end of selection
			elif event.keysym == 'Right':
				if self.text_widget.dlineinfo(e):
					self.text_widget.tag_remove('sel', '1.0', tkinter.END)
				else:
					# selection_started_from_top == False
					self.text_widget.mark_set(self.anchorname, s)

				self.text_widget.mark_set('insert', e)
				self.ensure_idx_visibility(e)


			elif event.keysym == 'Left':

				if self.text_widget.dlineinfo(s):
					self.text_widget.tag_remove('sel', '1.0', tkinter.END)
				else:
					# selection_started_from_top == True
					self.text_widget.mark_set(self.anchorname, e)

				self.text_widget.mark_set('insert', s)
				self.ensure_idx_visibility(s)

			else:
				return



		if wid == self.entry:
			self.entry.selection_clear()

			if event.keysym == 'Right':
				self.entry.icursor(e)
				self.entry.xview_moveto(1.0)

			elif event.keysym == 'Left':

				if self.state in ['search', 'replace', 'replace_all']:
					tmp = self.entry.get()
					s = tmp.index(':') + 2

				self.entry.icursor(s)
				self.entry.xview_moveto(0)

			else:
				return


		return 'break'


	def yank_line(self, event=None):
		'''	Copy current line to clipboard
		'''

		if self.state not in [
					'normal', 'help', 'error', 'search', 'replace', 'replace_all', 'goto_def']:
			self.bell()
			return 'break'


		self.wait_for(12)

		if not self.line_is_empty():
			s = self.idx_linestart()[0]
			e = '%s lineend' % s

			# Elided line check
			idx = self.get_safe_index(s)
			if r := self.line_is_elided(idx):
				e = '%s lineend' % self.text_widget.index(r[1])


			tmp = self.text_widget.get(s,e)
			self.text_widget.clipboard_clear()

			bg, fg = self.themes[self.curtheme]['sel'][:]
			self.text_widget.tag_config('animate', background=bg, foreground=fg)
			self.text_widget.tag_raise('animate')
			self.text_widget.tag_remove('animate', '1.0', tkinter.END)
			self.text_widget.tag_add('animate', s, e)

			if self.os_type != 'windows':
				self.text_widget.clipboard_append(tmp)
			else:
				self.copy_windows(selection=tmp)

			self.after(600, lambda args=['animate', '1.0', tkinter.END]:
					self.text_widget.tag_remove(*args) )


		return 'break'


	def goto_lineend(self, event=None):
		if self.state in [ 'filedialog' ]:
			self.bell()
			return 'break'


		if filter_keys_out(event, ['Control']): return


		wid = event.widget
		if wid == self.entry:
			wid.selection_clear()
			idx = tkinter.END
			wid.icursor(idx)
			wid.xview_moveto(1.0)
			return 'break'


		want_selection = False

		# win, linux
		# Alt-a/e
		# Alt-shift-left/right

		# mac
		# cmd-a/e
		# cmd-shift-left/right
		# Note: command-shift-a or e not binded.

		# all
		# (shift)?-Home/End


		# If want selection:
		# Pressed also shift, so adjust selection
		if filter_keys_in(event, ['Shift']):
			want_selection = True

			[ ins_old, have_selection, from_top, s, e ] = args = self.get_sel_info()

		# Alt/Cmd-a/e, Home/End
		else: self.text_widget.tag_remove('sel', '1.0', tkinter.END)


		ins_new = self.idx_lineend()
		self.text_widget.mark_set('insert', ins_new)


		if want_selection:
			args.insert(0, ins_new)
			self.set_selection(*args, direction='down')


		return 'break'


	def goto_linestart(self, event=None):
		if self.state in [ 'filedialog' ]:
			self.bell()
			return 'break'


		if filter_keys_out(event, ['Control']): return


		wid = event.widget
		if wid == self.entry:
			wid.selection_clear()
			idx = 0
			if self.state in ['search', 'replace', 'replace_all']:
				tmp = wid.get()
				idx = tmp.index(':') + 2

			wid.icursor(idx)
			wid.xview_moveto(0)
			return 'break'


		want_selection = False

		# win, linux
		# Alt-a/e
		# Alt-shift-left/right

		# mac
		# cmd-a/e
		# cmd-shift-left/right
		# Note: command-shift-a or e not binded.

		# all
		# (shift)?-Home/End


		# If want selection:
		# Pressed also shift, so adjust selection
		if filter_keys_in(event, ['Shift']):
			want_selection = True

			[ ins_old, have_selection, from_top, s, e ] = args = self.get_sel_info()

		# Alt/Cmd-a/e, Home/End
		else: self.text_widget.tag_remove('sel', '1.0', tkinter.END)


		if self.line_is_empty():
			ins_new = self.text_widget.index( 'insert display linestart' )
		else:
			ins_new = self.idx_linestart()[0]



		self.text_widget.mark_set('insert', ins_new)

		if want_selection:
			args.insert(0, ins_new)
			self.set_selection(*args, direction='up')


		return 'break'

########## Select and move End
########## Overrides Begin

	def mac_cmd_overrides(self, event=None):
		'''	Used to catch key-combinations like Alt-shift-Right
			in macOS, which are difficult to bind.
		'''
		match event.state:
			# Pressed Cmd + Shift + arrow left or right.
			# Want: select line from cursor.

			# Pressed Cmd + Shift + arrow up or down.
			# Want: select 10 lines from cursor.
			case 105:

				# self.text_widget or self.entry
				wid = event.widget

				# Enable select from in entry
				if wid == self.entry: return

				# Enable select from in contents
				elif wid == self.text_widget:

					if event.keysym == 'Right':
						self.goto_lineend(event=event)

					elif event.keysym == 'Left':

						# Want Cmd-Shift-left to:
						# Select indentation on line that has indentation
						# When: at idx_linestart
						# same way than Alt-Shift-Left

						# At idx_linestart of line that has indentation?
						idx = self.idx_linestart()[0]
						tests = [not self.line_is_empty(),
								self.text_widget.compare(idx, '==', 'insert' ),
								self.get_line_col_as_int(index=idx)[1] != 0,
								not len(self.text_widget.tag_ranges('sel')) > 0
								]

						if all(tests):
							pos = self.text_widget.index('%s linestart' % idx )
							self.text_widget.mark_set(self.anchorname, 'insert')
							self.text_widget.tag_add('sel', pos, 'insert')

						else:
							self.goto_linestart(event=event)


					elif event.keysym == 'Up':
						# As in move_many_lines()
						# Add some delay to get visual feedback
						for i in range(10):
							self.after(i*5, lambda args=['<<SelectPrevLine>>']:
								self.text_widget.event_generate(*args) )

					elif event.keysym == 'Down':
						for i in range(10):
							self.after(i*5, lambda args=['<<SelectNextLine>>']:
								self.text_widget.event_generate(*args) )

					else: return

				return 'break'


			# Pressed Cmd + arrow left or right.
			# Want: walk tabs.

			# Pressed Cmd + arrow up or down.
			# Want: move cursor 10 lines from cursor.
			case 104:

				if event.keysym == 'Right':
					self.walk_tabs(event=event)

				elif event.keysym == 'Left':
					self.walk_tabs(event=event, **{'back':True})

				elif event.keysym == 'Up':
					# As in move_many_lines()
					# Add some delay to get visual feedback
					for i in range(10):
						self.after(i*7, lambda args=['<<PrevLine>>']:
							self.text_widget.event_generate(*args) )

				elif event.keysym == 'Down':
					for i in range(10):
						self.after(i*7, lambda args=['<<NextLine>>']:
							self.text_widget.event_generate(*args) )

				else: return

				return 'break'


			# Pressed Alt + arrow left or right.
			case 112:

				if event.keysym in ['Up', 'Down']: return

				# self.text_widget or self.entry
				wid = event.widget

				if wid == self.entry:

					if event.keysym == 'Right':
						self.entry.event_generate('<<NextWord>>')

					elif event.keysym == 'Left':
						self.entry.event_generate('<<PrevWord>>')

					else: return

				else:
					res = self.move_by_words(event=event)
					return res

				return 'break'


			# Pressed Alt + Shift + arrow left or right.
			case 113:

				if event.keysym in ['Up', 'Down']: return

				# self.text_widget or self.entry
				wid = event.widget

				if wid == self.entry:

					if event.keysym == 'Right':
						self.entry.event_generate('<<SelectNextWord>>')

					elif event.keysym == 'Left':
						self.entry.event_generate('<<SelectPrevWord>>')

					else: return

				else:
					res = self.select_by_words(event=event)
					return res

				return 'break'


			# Pressed arrow left or right.
			# If have selection, put cursor on the wanted side of selection.

			# Pressed arrow up or down: return event.
			# +shift: 97: return event.
			case 97: return

			case 96:
				if self.state in [ 'search', 'replace' ]:
					pos = self.search_focus[0]
					# If cur match viewable
					if self.text_widget.bbox(pos):
						self.message_frame2.place_forget()
					# Else:
					# keep gotodef banner on

				if self.cursor_frame.winfo_ismapped():
					self.cursor_frame.place_forget()


				if event.keysym in ['Up', 'Down']:
					if self.comp_frame.winfo_ismapped():
						self.comp_frame.place_forget()
						return 'break'

					return


				# self.text_widget or self.entry
				wid = event.widget
				have_selection = False

				if wid == self.entry:
					have_selection = self.entry.selection_present()

				elif wid == self.text_widget:
					have_selection = len(self.text_widget.tag_ranges('sel')) > 0

				else: return

				if have_selection:
					if event.keysym == 'Right':
						self.check_sel(event=event)

					elif event.keysym == 'Left':
						self.check_sel(event=event)

					else: return


				else: return

				return 'break'


			# Pressed Fn
			case 64:

				# fullscreen
				if event.keysym == 'f':
					# prevent inserting 'f' when doing fn-f:
					return 'break'

				# Some shortcuts does not insert.
				# Like fn-h does not insert h.
				else:
					return

		return

		######### mac_cmd_overrides End #################


	def popup_raise(self, event=None):
		if self.state != 'normal':
			self.bell()
			return 'break'

		root_y = self.text_widget.winfo_rooty()
		root_x = self.text_widget.winfo_rootx()

		# Pressed mouse-right, check widget is text_widget
		if event.keysym not in ['rightsinglequotemark', 'm']:
			# Disable popup when not clicked inside Text-widget
			max_y = self.text_widget.winfo_rooty() + self.text_widget_height
			max_x = self.text_widget.winfo_rootx() + self.text_widget.winfo_width()

			tests = (root_x <= event.x_root <= max_x,
					root_y <= event.y_root <= max_y)

			if not all(tests): return 'break'


			self.popup.post(event.x_root +self.pad*5, event.y_root +self.pad*3)

		# Shortcut, try placing to center of text_widget
		else:
			x = root_x + self.text_widget.winfo_width()//3 - self.ln_widget.winfo_width()
			y = root_y + self.text_widget_height//3 -self.entry.winfo_height()

			self.popup.post(x, y)


		self.popup.focus_set() # Needed to remove popup when clicked outside.
		return 'break'


	def popup_focusOut(self, event=None):
		self.popup.unpost()
		return 'break'


	def copy_fallback(self, selection=None, flag_cut=False):

		if self.os_type == 'windows':
			self.copy_windows(selection=selection)

		else:
			try:
				self.clipboard_clear()
				self.clipboard_append(self.text_widget.get('sel.first', 'sel.last'))

			except tkinter.TclError:
				# is empty
				pass


		if flag_cut:
			self.text_widget.delete(tkinter.SEL_FIRST, tkinter.SEL_LAST)

		return 'break'


	def copy(self, event=None, flag_cut=False):
		''' When selection started from start of block,
				for example: cursor is before if-word,
			and
				selected at least one whole line below firsline

			Then
				preserve indentation
				of all lines in selection.

			This is done in paste()
			if self.flag_fix_indent is True.
			If not, paste_fallback() is used instead.
		'''
		self.indent_selstart = 0
		self.indent_nextline = 0
		self.indent_diff = 0
		self.flag_fix_indent = False
		self.checksum_fix_indent = False


		# Check if have_selection
		have_selection = len(self.text_widget.tag_ranges('sel')) > 0
		if not have_selection:
			#print('copy fail 1, no selection')
			return 'break'

		# self.text_widget.selection_get() would not get elided text
		t_orig = self.text_widget.get('sel.first', 'sel.last')


		# Check if num selection lines > 1
		startline, startcol = map(int, self.text_widget.index(tkinter.SEL_FIRST).split(sep='.'))
		endline = int(self.text_widget.index(tkinter.SEL_LAST).split(sep='.')[0])
		numlines = endline - startline
		if not numlines > 1:
			#print('copy fail 2, numlines not > 1')
			return self.copy_fallback(selection=t_orig, flag_cut=flag_cut)


		# Selection start indexes:
		line, col = startline, startcol

		self.indent_selstart = col


		# Check if selstart line not empty
		tmp = self.text_widget.get('%s.0' % str(line),'%s.0 lineend' % str(line))
		if len(tmp.strip()) == 0:
			#print('copy fail 4, startline empty')
			return self.copy_fallback(selection=t_orig, flag_cut=flag_cut)

		# Check if cursor not at idx_linestart
		for i in range(len(tmp)):
			if not tmp[i].isspace():
				break

		if i > self.indent_selstart:
			# Cursor is inside indentation or indent0
			#print('copy fail 3, Cursor in indentation')
			return self.copy_fallback(selection=t_orig, flag_cut=flag_cut)

		elif i < self.indent_selstart:
			#print('copy fail 3, SEL_FIRST after idx_linestart')
			return self.copy_fallback(selection=t_orig, flag_cut=flag_cut)

		# Check if two nextlines below selstart not empty
		t = t_orig.splitlines(keepends=True)
		tmp = t[1]

		if len(tmp.strip()) == 0:

			if numlines > 2:
				tmp = t[2]

				if len(tmp.strip()) == 0:
					#print('copy fail 6, two nextlines empty')
					return self.copy_fallback(selection=t_orig, flag_cut=flag_cut)

			# numlines == 2:
			else:
				#print('copy fail 5, numlines == 2, nextline is empty')
				return self.copy_fallback(selection=t_orig, flag_cut=flag_cut)

		for i in range(len(tmp)):
			if not tmp[i].isspace():
				self.indent_nextline = i
				break

		# Indentation difference of first line and next nonempty line
		self.indent_diff = self.indent_nextline - self.indent_selstart

		# Continue checks
		if self.indent_diff < 0:
			# For example:
			#
			#			self.indent_selstart
			#		self.indent_nextline
			#indent0
			#print('copy fail 7, indentation decreasing on first non empty line')
			return self.copy_fallback(selection=t_orig, flag_cut=flag_cut)


		# Check if indent of any line in selection < self.indent_selstart
		min_ind = self.indent_selstart
		for i in range(1, numlines):
			tmp = t[i]

			if len(tmp.strip()) == 0:
				# This will skip rest of for-loop contents below
				# and start next iteration.
				continue

			for j in range(len(tmp)):
				if not tmp[j].isspace():
					if j < min_ind:
						min_ind = j
					# This will break out from this for-loop only.
					break

		if self.indent_selstart > min_ind:
			#print('copy fail 8, indentation of line in selection < self.indent_selstart')
			return self.copy_fallback(selection=t_orig, flag_cut=flag_cut)


		###################
		self.flag_fix_indent = True
		self.checksum_fix_indent = t_orig

		return self.copy_fallback(selection=t_orig, flag_cut=flag_cut)
		###################


	def paste(self, event=None):
		''' When selection started from start of block,
				for example: cursor is before if-word,
			and
				selected at least one whole line below firsline

			Then
				preserve indentation
				of all lines in selection.


			This is done if self.flag_fix_indent is True.
			If not, paste_fallback() is used instead.
			self.flag_fix_indent is set in copy()
		'''

		try:
			t = self.text_widget.clipboard_get()
			if len(t) == 0:
				return 'break'

		# Clipboard empty
		except tkinter.TclError:
			return 'break'

		if not self.flag_fix_indent or t != self.checksum_fix_indent:
			self.paste_fallback(event=event)
			self.text_widget.edit_separator()
			#print('paste normal')
			return 'break'

		#print('paste override')


		[ ins_old, have_selection, selection_started_from_top,
		sel_start, sel_end ] = args = self.get_sel_info()


		# Count indent diff of pasteline and copyline
		idx_ins, col = self.get_line_col_as_int(index=ins_old)
		indent_cursor = col
		indent_diff_cursor = indent_cursor - self.indent_selstart


		# Split selection from clipboard to list
		# and build string to be pasted.
		tmp_orig = t.splitlines(keepends=True)
		s = ''
		# First line
		s += tmp_orig[0]

		for line in tmp_orig[1:]:

			if line.isspace():
				pass

			elif indent_diff_cursor > 0:
				# For example:
				#
				#	self.indent_selstart
				#			indent_cursor
				#indent0

				line = indent_diff_cursor*'\t' + line

			elif indent_diff_cursor < 0:
				# For example:
				#
				#			self.indent_selstart
				#		indent_cursor
				#indent0

				# This is one reason to cancel in copy()
				# if indentation of any line in selection < self.indent_selstart
				line = line[-1*indent_diff_cursor:]

			#else:
			#line == line
			# same indentation level,
			# so do nothing.
			s += line


		# Do paste string
		# Put mark --> can get end index of new string
		self.auto_update_syntax_stop()
		self.text_widget.mark_set('paste', ins_old)
		self.text_widget.insert(ins_old, s)


		start = self.text_widget.index( '%s linestart' % ins_old)
		end = self.text_widget.index( 'paste lineend')


		tab = self.tabs[self.tabindex]
		in_string = False
		if self.cursor_is_in_multiline_string(tab=tab): in_string = True


		if self.can_do_syntax() and not in_string:
			self.update_lineinfo()
			self.update_tokens( start=start, end=end)

		if not have_selection:
			self.ensure_idx_visibility(ins_old)
			self.wait_for(100)
			self.text_widget.tag_add('sel', ins_old, 'paste')
			self.text_widget.mark_set(self.anchorname, 'paste')

		elif selection_started_from_top:
				self.ensure_idx_visibility(ins_old)
		else:
			self.ensure_idx_visibility('insert')


		self.text_widget.edit_separator()
		self.auto_update_syntax_continue()

		return 'break'


	def paste_fallback(self, event=None):
		''' Fallback from paste
		'''

		try:
			tmp = self.clipboard_get()
			tmp = tmp.splitlines(keepends=True)


		except tkinter.TclError:
			# is empty
			return 'break'

		self.auto_update_syntax_stop()
		have_selection = False

		if len( self.text_widget.tag_ranges('sel') ) > 0:
			selstart = self.text_widget.index( '%s' % tkinter.SEL_FIRST)
			selend = self.text_widget.index( '%s' % tkinter.SEL_LAST)

			self.text_widget.tag_remove('sel', '1.0', tkinter.END)
			have_selection = True


		idx_ins = self.text_widget.index(tkinter.INSERT)
		self.text_widget.event_generate('<<Paste>>')


		tab = self.tabs[self.tabindex]
		in_string = False
		if self.cursor_is_in_multiline_string(tab=tab): in_string = True


		# Selected many lines or
		# one line and cursor is not at the start of next line:
		if len(tmp) > 1:

			s = self.text_widget.index( '%s linestart' % idx_ins)
			e = self.text_widget.index( 'insert lineend')
			t = self.text_widget.get( s, e )

			if self.can_do_syntax() and not in_string:
				self.update_lineinfo()
				self.update_tokens( start=s, end=e, line=t )

			if have_selection:
				self.text_widget.tag_add('sel', selstart, selend)

			else: self.text_widget.tag_add('sel', idx_ins, tkinter.INSERT)


			self.text_widget.mark_set('insert', idx_ins)

			self.wait_for(100)
			self.ensure_idx_visibility(idx_ins)


		# Selected one line and cursor is at the start of next line:
		elif len(tmp) == 1 and tmp[-1][-1] == '\n':
			s = self.text_widget.index( '%s linestart' % idx_ins)
			e = self.text_widget.index( '%s lineend' % idx_ins)
			t = self.text_widget.get( s, e )

			if self.can_do_syntax() and not in_string:
				self.update_lineinfo()
				self.update_tokens( start=s, end=e, line=t )

			if have_selection:
				self.text_widget.tag_add('sel', selstart, selend)

			else: self.text_widget.tag_add('sel', idx_ins, tkinter.INSERT)

			self.text_widget.mark_set('insert', idx_ins)


		else:
			s = self.text_widget.index( '%s linestart' % idx_ins)
			e = self.text_widget.index( 'insert lineend')
			t = self.text_widget.get( s, e )

			if self.can_do_syntax() and not in_string:
				self.update_lineinfo()
				self.update_tokens( start=s, end=e, line=t )

			if have_selection:
				self.text_widget.tag_add('sel', selstart, selend)
				self.text_widget.mark_set('insert', idx_ins)


		self.auto_update_syntax_continue()

		return 'break'


	def undos(self, func1, func2):
		if self.state != 'normal':
			self.bell()
			return 'break'

##			Undo and indexes:
##			1: Redoing an action will put cursor to end of action, that got redoed,
##			just like when anything is normally being done
##			(example: after inserting letter, cursor is at end of letter)
##
##			2: Undoing an action will put cursor to start, where action, that got
##			undoed, would have started.
##			(example: after undoing insert letter,
##			cursor is at start of letter that no longer exist)
##
##			##########################################
##
##			Original issue
##			When undoing normally, if action was offscreen,
##			action was undoed but user did not see what was undoed.
##			This override tries to fix that.
##			Now, if undoed action was offscreen, undo/redo is canceled
##				( index-logic described above in mind )
##			with the opposite action. --> Nothing is changed,
##			only cursor is moved to correct line.
##			--> One can see what is going to be undoed next time one does undo.
##
##
##			Issue after fix
##			Because it could be a multiline action, like replace_all,
##				( most likely just indent, comment )
##			And because there is this "is action visible on screen" -test:
##				top_line <= ins_line <= bot_line
##			--> If trying to apply this fix to long action, there is problem
##
##			For example if trying to undo long indentation action: At first try
##			it notices that after undoing action, cursor is not on original screen
##			and so it redoes the action to fix the "no can see undo" -issue told above.
##			But if action, the one one wants to undo, is long, cursor will not ever be visible on screen
##				(after func1)
##			--> redo(func2) always happen and so long actions are never undoed.
##
##
##			To fix this, original insertion cursor position and position after fix
##			(with opposite action) is compared,
##				ins_after_func2 == ins_orig
##
##			if cursor was not moved when trying to move it for visibilitys sake,
##			it means the start/end of action is always not on screen
##			--> action is long
##			--> just appply normal undo/redo (func1) without visibility-check


		self.auto_update_syntax_stop()

		try:

			ins_orig = self.text_widget.index('insert')
			# Linenumbers of top and bottom lines currently displayed on screen
			top_line,_ = self.get_line_col_as_int(index='@0,0')
			bot_line,_ = self.get_line_col_as_int(index='@0,65535')
			self.wait_for(33)

			func1()

			# Was action func1 not viewable?
			# Then just move the cursor, with opposite action, func2
			ins_line,_ = self.get_line_col_as_int()
			if not ( top_line <= ins_line <= bot_line ):

				func2()

				bot_line_after_func2,_ = self.get_line_col_as_int(index='@0,65535')


				# Check for long actions, like indent. Info is above
				ins_after_func2 = self.text_widget.index('insert')
				if ins_after_func2 == ins_orig:

					func1()

					# This seems to fix 'screen jumping'
					bot_line_after,_ = self.get_line_col_as_int(index='@0,65535')
					diff = bot_line_after - bot_line_after_func2
					if diff != 0: self.text_widget.yview_scroll(-diff, 'units')

			else:
				# This seems to fix 'screen jumping'
				bot_line_after,_ = self.get_line_col_as_int(index='@0,65535')
				diff = bot_line_after - bot_line
				if diff != 0: self.text_widget.yview_scroll(-diff, 'units')



			if self.can_do_syntax():
				( scope_line, ind_defline, idx_scope_start) = self.get_scope_start()
				idx_scope_end = self.get_scope_end(ind_defline, idx_scope_start)

				s = '%s linestart' % idx_scope_start
				e = '%s lineend' % idx_scope_end

				self.update_lineinfo()
				self.update_tokens(start=s, end=e)

		except tkinter.TclError:
			self.bell()

		self.auto_update_syntax_continue()

		return 'break'


	def undo_override(self, event=None):
		return self.undos(self.text_widget.edit_undo, self.text_widget.edit_redo)


	def redo_override(self, event=None):
		return self.undos(self.text_widget.edit_redo, self.text_widget.edit_undo)


	def select_all(self, event=None):
		self.text_widget.tag_remove('sel', '1.0', tkinter.END)
		self.text_widget.tag_add('sel', 1.0, tkinter.END)
		return 'break'


	def put_editor_fullscreen(self, delay):
		ln_kwargs={'width':self.margin_fullscreen}
		just_kwargs = {'rmargin':self.gap_fullscreen}

		self.do_maximize(1)
		self.after(delay, lambda args=(ln_kwargs, just_kwargs): self.apply_left_margin(*args) )


	def do_maximize(self, want_maximize):
		''' fullscreen option seems to exist now on all win/linux/mac
			didn't use to, so:
		'''

		if self.wm_attributes().count('-fullscreen') != 0:
			self.wm_attributes('-fullscreen', want_maximize)

		elif self.wm_attributes().count('-zoomed') != 0:
			self.wm_attributes('-zoomed', want_maximize)

		elif want_maximize:
			width_screen = self.winfo_screenwidth()
			height_screen = self.winfo_screenheight()
			self.geometry('%dx%d+0+0' % (width_screen, height_screen) )

		else:
			self.geometry(self.geom)


	def esc_override(self, event=None):
		'''	Enable toggle fullscreen with Esc
			And cancel completion
		'''
		# Safe escing, if mistakenly pressed during search_next
		if self.state in ['normal']:
			if len(self.text_widget.tag_ranges('sel')) > 0:
				self.text_widget.tag_remove('sel', '1.0', tkinter.END)
				return 'break'

			elif self.expander.cancel_completion(event=event):
				self.comp_frame.place_forget()
				return 'break'


		delay = 300
		want_maximize = 1
		ln_kwargs={'width':self.margin_fullscreen}
		just_kwargs = {'rmargin':self.gap_fullscreen}

		if self.is_fullscreen():
			delay = 200
			want_maximize = 0
			ln_kwargs={'width':self.margin}
			just_kwargs = {'rmargin':self.gap}


		if self.margin != self.margin_fullscreen or (self.os_type == 'windows' and not want_maximize):
			if self.margin != self.margin_fullscreen:
				self.wait_for(100)
				self.apply_left_margin(ln_kwargs, just_kwargs)
				self.wait_for(200)

			# Prevent flashing 1&2/3
			if want_maximize or self.os_type == 'windows':
				self.orig_bg_color = self.cget('bg')
				self.config(bg=self.bgcolor)

			if self.os_type == 'windows': self.wait_for(100)
			self.do_maximize(want_maximize)
			if self.os_type == 'windows': self.wait_for(100)


			# Prevent flashing 3/3
			if want_maximize or self.os_type == 'windows':
				self.config(bg=self.orig_bg_color)

			return 'break'


		self.do_maximize(want_maximize)
		# Show cursor when back to normal window
		if not want_maximize and self.tabs[self.tabindex].type != 'help':
			self.ensure_idx_visibility('insert')

		self.after(delay, lambda args=(ln_kwargs, just_kwargs): self.apply_left_margin(*args) )

		return 'break'


	def space_override(self, event):
		'''	Used to bind Space-key when searching or replacing.
		'''
		# Safe spacing, if mistakenly pressed during search_next
		if self.state in ['normal', 'error', 'help']:
			if len(self.text_widget.tag_ranges('sel')) > 0:
				self.text_widget.tag_remove('sel', '1.0', tkinter.END)
				return 'break'
			else:
				return


		if self.state not in ['search', 'replace', 'replace_all']:
			return

		# self.search_focus marks range of focus-tag:
		self.save_pos = self.search_focus[1]

		# Help enabling: "exit to goto_def func with space" while searching
		if self.goto_def_pos:
			self.save_pos = self.goto_def_pos

		self.stop_search()

		return 'break'


	def insert_tab(self, event):
		'''	Used to insert tab in self.text_widget or self.entry
		'''

		w = event.widget
		tests = ( w is self.text_widget,
				self.state in ['search', 'replace', 'replace_all', 'goto_def']
				)
		if all(tests): return 'break'


		# self.text_widget / self.entry
		w.insert(tkinter.INSERT, '\t')

		return 'break'


	def tab_over_indent(self):
		'''	Called from indent()

			If at indent0 of empty line or non empty line:
			move line and/or cursor to closest indentation
		'''

		# There should not be selection
		ins = tkinter.INSERT
		line_ins, col_ins = self.get_line_col_as_int(index=ins)

		# Cursor is not at indent0
		if col_ins != 0: return False

		res = self.text_widget.count(
				'insert linestart', 'insert +1 lines', 'displaylines')

		# Line is wrapped
		if res[0] > 1: return False

		empty = self.line_is_empty()
		tests = [not empty,
				self.text_widget.get('insert', 'insert +1c').isspace()
				]

		# Line already has indentation
		if all(tests): return False

		if empty:
			self.text_widget.delete('insert linestart', 'insert lineend')


		patt = r'^[[:blank:]]+[^[:blank:]]'

		(ind_prev, ind_next, pos_prev, pos_next,
		line_prev, line_next, diff_prev, diff_next) = (
			False, False, False, False, False, False, False, False)


		# Indentation of previous
		pos_prev = self.text_widget.search(patt, ins, stopindex='1.0',
			regexp=True, backwards=True, count=self.search_count_var)

		# self.search_count_var.get() == indentation level +1
		# because pattern matches: not blank and not comment at end of patt
		if pos_prev:
			ind_prev = self.search_count_var.get() -1
			line_prev,_ = self.get_line_col_as_int(index=pos_prev)
			diff_prev = line_ins - line_prev


		# Indentation of next
		pos_next = self.text_widget.search(patt, ins, stopindex='end',
			regexp=True, count=self.search_count_var)

		if pos_next:
			ind_next = self.search_count_var.get() -1
			line_next,_ = self.get_line_col_as_int(index=pos_next)
			diff_next = line_next - line_ins


		if pos_next and pos_prev:
			# Equal distance, prefer next
			if diff_prev == diff_next: return ind_next

			elif min(diff_prev, diff_next) == diff_prev:
				return ind_prev

			else: return ind_next

		elif pos_prev: return ind_prev
		elif pos_next: return ind_next
		else: return False


	def del_to_dot(self, event):
		''' Delete previous word
		'''
		# No need to check event.state?
		if self.state != 'normal': return
		if len( self.text_widget.tag_ranges('sel') ) > 0:
			self.text_widget.tag_remove('sel', '1.0', tkinter.END)

		self.text_widget.delete('%s -1c wordstart' % 'insert', 'insert')
		return 'break'


	def backspace_override(self, event):
		''' For syntax highlight
			This is executed *before* actual deletion
		'''

		# plain backspace, with +8 or without numlock
		if self.state != 'normal' or event.state not in [0, 8]:
			return
		tab=self.tabs[self.tabindex]
		pars = '()[]{}'
		triples = ["'''", '"""']

		# Is there a selection?
		if len(self.text_widget.tag_ranges('sel')) > 0:
			tmp = self.text_widget.selection_get()

			if not tab.check_scope:
				for triple in triples:
					if triple in tmp:
						tab.check_scope = True
						break

			if not tab.check_scope and self.cursor_is_in_multiline_string(tab=tab):
				tab.check_scope = True

			for char in tmp:
				if char in pars:
					tab.par_err = True
					break

			self.text_widget.delete( tkinter.SEL_FIRST, tkinter.SEL_LAST )
			return 'break'


		else:
			# Deleting one letter

			# Multiline string check
			line = self.text_widget.get( 'insert linestart', 'insert lineend')
			ins_col = self.get_line_col_as_int()[1]
			prev_char = line[ins_col-1:ins_col]

			if not tab.check_scope:
				for triple in triples:
					if triple in line:
						tab.check_scope = True
						break

			# Trigger parcheck
			if not tab.par_err and ( prev_char in pars): tab.par_err = True


		return


	def return_override(self, event):
		if self.state != 'normal':
			self.bell()
			return 'break'


		# Cursor indexes when pressed return:
		line, col = self.get_line_col_as_int()

		def finish_return():
			self.text_widget.see(f'{line+1}.0')
			self.text_widget.edit_separator()
			return 'break'


		tab = self.tabs[self.tabindex]
		if self.cursor_is_in_multiline_string(tab=tab):
			tab.check_scope = True


		# First an easy case:
		if col == 0:
			self.text_widget.insert(tkinter.INSERT, '\n')
			return finish_return()


		tmp = self.text_widget.get('%s.0' % str(line),'%s.0 lineend' % str(line))

		# Then one special case: check if cursor is inside indentation,
		# and line is not empty.
		if tmp[:col].isspace() and not tmp[col:].isspace():
			self.text_widget.insert(tkinter.INSERT, '\n')
			self.text_widget.insert('%s.0' % str(line+1), tmp[:col])
			return finish_return()

		else:
			# rstrip space to prevent indentation sailing.
			if tmp[col:].isspace():
				self.text_widget.delete(tkinter.INSERT, 'insert lineend')

			for i in range(len(tmp[:col]) + 1):
				if tmp[i] != '\t':
					break

			# Manual newline because return is overrided.
			self.text_widget.insert(tkinter.INSERT, '\n')
			self.text_widget.insert(tkinter.INSERT, i*'\t')
			return finish_return()


	def sbset_override(self, *args):
		'''	update_linenums whenever position of scrollbar knob changes
		'''
		self.scrollbar.set(*args)

		if self.want_ln == 2: self.update_linenums()

########## Overrides End
########## Utilities Begin

	def mac_print_fix_use(self, use=None):
		''' Setting, should alternative print-function be used
			to fix possible printing issue when using macOS.
			default is False
		'''
		if self.os_type != 'mac_os':
			print('This is for macOS only')
			self.bell()
			return
		if use == None: print(self.mac_print_fix)
		elif use:
			if self.mac_print_fix != True:
				self.mac_print_fix = True
				self.change_printer_to(FIIXED_PRINTER)
				print('Using mac_print_fix now')
			else:
				print('Using mac_print_fix already')
		else:
			if self.mac_print_fix != False:
				self.mac_print_fix = False
				self.change_printer_to(DEFAUL_PRINTER)
				print('Using normal print now')
			else:
				print('Using normal print already')


	def change_printer_to(self, printer):
		global print
		print = printer
		importflags.PRINTER['current'] = printer


	def view_module(self):
		''' Open module to new Tab. Uses selection as name of module.

			Tab can be safely closed after reading, or saved with new filename.

			Note: calls importlib.import_module() on selection.

		'''
		try:
			target = self.text_widget.selection_get()
		except tkinter.TclError:
			self.bell()
			return 'break'

		target = target.strip()

		if not len(target) > 0:
			self.bell()
			return 'break'

		self.auto_update_syntax_stop()


		try:
			mod = importlib.import_module(target)
			filepath = inspect.getsourcefile(mod)

			if not filepath:
				# For example: readline
				self.bell()
				print('Could not inspect:', target, '\nimport and use help()')
				return 'break'

			try:
				with open(filepath, 'r', encoding='utf-8') as f:
					fcontents = f.read()

					# new_tab() calls tab_close()
					# and updates self.tabindex
					self.new_tab()

					curtab = self.tabs[self.tabindex]

					if '.py' in filepath:
						indentation_is_alien, indent_depth = self.check_indent_depth(fcontents)

						tmp = fcontents.splitlines(True)
						tmp[:] = [self.tabify(line, width=indent_depth) for line in tmp]
						tmp = ''.join(tmp)
						curtab.contents = tmp
					else:
						curtab.contents = fcontents


					curtab.text_widget.insert('1.0', curtab.contents)
					curtab.text_widget.mark_set('insert', curtab.position)
					curtab.text_widget.see(curtab.position)


					if self.can_do_syntax(curtab):
						self.update_lineinfo(curtab)
						a = self.get_tokens(curtab)
						self.insert_tokens(a, tab=curtab)


					curtab.text_widget.focus_set()
					self.text_widget.edit_reset()
					self.text_widget.edit_modified(0)


			except (EnvironmentError, UnicodeDecodeError) as e:
				print(e.__str__())
				print(f'\n Could not open file: {filepath}')
				self.bell()

		except ModuleNotFoundError as err:
			print(err.__str__())
		except TypeError as ee:
			print(ee.__str__())
			self.bell()


		self.auto_update_syntax_continue()

		return 'break'


	def strip_first_char(self, event=None):
		''' Remove first char of every line of selection

			is popup-menu item

			intention: fix for pasted diff-output lines

			After paste from diff, use this first,
			then tabify with ctrl-t


			This assumes that addition indicator character,
			like "+" in git diff,
			is not inside indentation
		'''

		if self.state != 'normal':
			self.bell()
			return 'break'


		self.auto_update_syntax_stop()

		tab = self.tabs[self.tabindex]

		try:
			start = 'sel.first linestart'
			end = 'sel.last lineend'

			startline,_ = self.get_line_col_as_int(tab=tab, index=start)
			endline,_ = self.get_line_col_as_int(tab=tab, index=end)

			for line in range(startline, endline+1):
				idx = '%d.0' % line
				if tab.text_widget.get(idx) == '\n': continue
				tab.text_widget.delete(idx)


			if self.can_do_syntax(tab):
				self.update_lineinfo(tab)
				self.update_tokens(start=start, end=end, tab=tab)

			tab.text_widget.edit_separator()

		except tkinter.TclError as e:
			print(e)


		self.auto_update_syntax_continue()

		return 'break'


	def tabify_lines(self, event=None):
		tab = self.tabs[self.tabindex]

		self.auto_update_syntax_stop()

		try:
			start = tab.text_widget.index('sel.first linestart')
			end = tab.text_widget.index('sel.last lineend')
			tmp = tab.text_widget.get(start, end)

			indentation_is_alien, indent_depth = self.check_indent_depth(tmp)

			tmp = tmp.splitlines()

			if indentation_is_alien:
				tmp[:] = [self.tabify(line, width=indent_depth) for line in tmp]
			else:
				tmp[:] = [self.tabify(line) for line in tmp]


			tmp = ''.join(tmp)


			tab.text_widget.delete(start, end)
			tab.text_widget.insert(start, tmp)

			if self.can_do_syntax(tab):
				self.update_lineinfo(tab)
				self.update_tokens(start=start, end=end, tab=tab)

			tab.text_widget.edit_separator()


		except tkinter.TclError as e:
			print(e)


		self.auto_update_syntax_continue()

		return 'break'


	def tabify(self, line, width=None):

		if width:
			ind_width = width
		else:
			ind_width = self.ind_depth

		indent_stop_index = 0

		for char in line:
			if char in [' ', '\t']: indent_stop_index += 1
			else: break


		if line.isspace(): return '\n'


		if indent_stop_index == 0:
			# remove trailing space
			if not line.isspace():
				line = line.rstrip() + '\n'
			return line


		indent_string = line[:indent_stop_index]
		line = line[indent_stop_index:]

		# Remove trailing space
		line = line.rstrip() + '\n'


		count = 0
		for char in indent_string:
			if char == '\t':
				count = 0
				continue
			if char == ' ': count += 1
			if count == ind_width:
				indent_string = indent_string.replace(ind_width * ' ', '\t', True)
				count = 0

		tabified_line = ''.join([indent_string, line])

		return tabified_line


	def restore_btn_git(self):
		''' Put Git-branch name back if on one
		'''

		if self.branch:
			branch = self.branch[:5]
			# Set branch name lenght to 5

			if len(branch) < 5:
				diff = 5-len(branch)
				t=1
				for i in range(diff):
					if t > 0:
						branch += ' '
					else:
						branch = ' ' + branch
					t *= -1

			# Add one space to start to get some space from bitmap
			branch = ' ' + branch

			self.btn_git.config(text=branch, disabledforeground='')

			if 'main' in self.branch or 'master' in self.branch:
				self.btn_git.config(disabledforeground='brown1')

		else:
			self.btn_git.config(text=' jou  ', disabledforeground='')


	def flash_btn_git(self):
		''' Flash text and enable canceling flashing later.
		'''

		bg, fg = self.themes[self.curtheme]['normal_text'][:]

##		For some times:
##			wait 300
##		 	change btn_git text to spaces
##		 	again wait 300
##		 	change btn_git text to CAPS

		def get_wait_time(lap, delay, position, num_waiters):
			''' all ints
				lap: how many laps have been completed
				delay: delay between waiters
				position: position among waiters, first, second etc
				num_waiters: number of waiters

				Time of a waiter at position position after lap laps:
					time spend with passed laps + time spend on current lap
					(lap * delay * num_waiters) + (position * delay)
			'''

			return (lap * delay * num_waiters) + (position * delay)


		for i in range(4):
			t1 = get_wait_time(i, 300, 1, 2)
			t2 = get_wait_time(i, 300, 2, 2)

			l1 = lambda kwargs={'text': 6*' ', 'disabledforeground': 'brown1'}: self.btn_git.config(**kwargs)
			l2 = lambda kwargs={'text': ' CAPS '}: self.btn_git.config(**kwargs)

			l3 = lambda kwargs={'bg':fg, 'fg':bg}: self.text_widget.config(**kwargs)
			l4 = lambda kwargs={'bg':bg, 'fg':fg}: self.text_widget.config(**kwargs)

			c3 = self.after(t1, l3)
			c4 = self.after(t2, l4)
			self.to_be_cancelled['flash_btn_git'].append(c3)
			self.to_be_cancelled['flash_btn_git'].append(c4)

			c1 = self.after(t1, l1)
			c2 = self.after(t2, l2)
			self.to_be_cancelled['flash_btn_git'].append(c1)
			self.to_be_cancelled['flash_btn_git'].append(c2)


	def check_caps(self, event=None):
		'''	Check if CapsLock is on.
		'''

		e = event.state
		# 0,2	macos, linux
		# 8,10	win11

		# event.keysym == Motion
		# Bind to Motion is for: checking CapsLock -state when starting editor,
		# (this assumes user moves mouse)
		# and checking if CapsLock -state changes when focus is not in editor
		if event.keysym != 'Caps_Lock':

			# CapsLock is on but self.capslock is not True:
			if e in [2, 10] and self.capslock in [False, 'init']:
				self.capslock = True
				self.bell()
				self.flash_btn_git()


			# CapsLock is off but self.capslock is True:
			elif e in [0, 8] and self.capslock in [True, 'init']:
				if self.capslock == 'init':
					self.capslock = False
					return 'break'

				self.capslock = False

				# If quickly pressed CapsLock off,
				# cancel flashing started at the end of this callback.
				for item in self.to_be_cancelled['flash_btn_git'][:]:
					self.after_cancel(item)
					self.to_be_cancelled['flash_btn_git'].remove(item)


				# Put Git-branch name back if on one
				self.restore_btn_git()
				bg, fg = self.themes[self.curtheme]['normal_text'][:]
				self.text_widget.config(bg=bg, fg=fg)

		# event.keysym == Caps_Lock
		# Check if CapsLock -state changes when focus is in editor
		else:

			# CapsLock is being turned off
			# macOS -state
			event_state = 0

			if self.os_type == 'linux': event_state = 2

			if e in [event_state, 10]:
				self.capslock = False

				# If quickly pressed CapsLock off,
				# cancel flashing started at the end of this callback.
				for item in self.to_be_cancelled['flash_btn_git'][:]:
					self.after_cancel(item)
					self.to_be_cancelled['flash_btn_git'].remove(item)

				# Put Git-branch name back if on one
				self.restore_btn_git()
				bg, fg = self.themes[self.curtheme]['normal_text'][:]
				self.text_widget.config(bg=bg, fg=fg)


			# CapsLock is being turned on
			else:
				self.capslock = True
				self.bell()
				self.flash_btn_git()

		return 'break'


	def flash_line(self, pos='insert', delay=600):
		'''	Flash line for 600ms
			Called from goto_def()
		'''

		if self.state not in [
					'normal', 'waiting', 'help', 'error', 'search', 'replace', 'replace_all', 'goto_def']:
			self.bell()
			return 'break'

		s = self.idx_linestart(pos)[0]
		e = '%s lineend' % s

		# Elided line check
		idx = self.get_safe_index(s)
		if r := self.line_is_elided(idx):
			e = '%s lineend' % self.text_widget.index(r[1])

		bg, fg = self.themes[self.curtheme]['sel'][:]
		self.text_widget.tag_config('animate', background=bg, foreground=fg)
		self.text_widget.tag_raise('animate')
		self.text_widget.tag_remove('animate', '1.0', tkinter.END)
		self.text_widget.tag_add('animate', s, e)

		self.after(delay, lambda args=['animate', '1.0', tkinter.END]:
				self.text_widget.tag_remove(*args) )

		return 'break'


	def handle_search_entry(self, search_pos, index):
		''' Handle entry when searching/replacing

			Called from: show_next() and show_prev()

			Search_pos is position of current focus among search matches.
			For example, if current search position would be
			' 2/20' then search_pos would be 2.

			index is tkinter.Text -index of current search position,
			for example, '100.1'
		'''

		self.entry.config(validate='none')

		# 1. Delete from 0 to Se/Re*: check ':' always in prompt
		entry_contents = self.entry.get()
		patt_e = 'Re'
		if self.state == 'search': patt_e = 'Se'

		idx_s = entry_contents.index(':')
		idx_e = entry_contents.rindex(patt_e, 0, idx_s)
		self.entry.delete(0, idx_e)

		# Prompt is now '^Se.*' / '^Re.*'


		# 2. Build string to be inserted in the beginning of entry
		# a: Add scope_path
		# Search backwards and get function/class names.
		patt = ' '

		if self.can_do_syntax():
			if scope_name := self.get_scope_path(index):
				patt = ' @' + scope_name + ' @'


		# b: Add search position
		idx = search_pos
		lenght_of_search_position_index = len(str(idx))
		lenght_of_search_matches = len(str(self.search_matches))
		diff = lenght_of_search_matches - lenght_of_search_position_index

		tmp = f'{diff*" "}{idx}/{self.search_matches}'
		patt = tmp + patt


		# 3. Insert string
		self.entry.insert(0, patt)


		# 4. Show as banner also
		patt = tmp
		if self.can_do_syntax(): patt += ' @@' +scope_name
		self.show_message(patt, 2500)


	def get_scope_path_using_defline_tag(self, index, ind_depth, scope_path='', get_idx_linestart=False):
		''' Speed up getting scope path by using defline -tag
			Called from get_scope_path, get_scope_start
		'''

		ind = ind_depth
		pos = index

		while ind+1:

			r = self.text_widget.tag_prevrange(f'defline{ind}', pos)
			if r:

				pos = r[0]

				tmp = self.text_widget.get( pos, '%s lineend' % pos)
				if scope_name := self.line_is_defline(tmp):
					if scope_path != '':
						scope_path = scope_name +'.'+ scope_path
					else:
						scope_path = scope_name

				ind -= 1

			else:
				break


		if not scope_path: scope_path = '__main__()'
		# If called from get_scope_start:
		if get_idx_linestart:
			return scope_path, pos

		return scope_path

	#@debug
	def get_scope_path(self, index):
		''' Get info about function or class where insertion-cursor is in.

			Index is tkinter.Text -index

			Called from handle_search_entry()

			Search backwards from index up to filestart and build scope-path
			of current position: index.

			on success:
				returns string: scope_path
			else:
				returns '__main__()'
		'''

		pos = index
		scope_path = ''
		ind_last_line = 0
		index_line_contents = self.text_widget.get( '%s linestart' % pos,
			'%s lineend' % pos )


		# If posline is empty,
		# Find next(up) non empty, uncommented line
		#############################################
		if index_line_contents.isspace() or index_line_contents == '' \
			or index_line_contents.strip().startswith('#') \
			or 'strings' in self.text_widget.tag_names(pos):

			blank_range = '{0,}'
			p1 = r'^[[:blank:]]%s' % blank_range
			# Not blank and not comment
			p2 = r'[^[:blank:]#]'

			p = p1 + p2


			while pos:
				try:
					pos = self.text_widget.search(p, pos, stopindex='1.0',
							backwards=True, regexp=True)

				except tkinter.TclError as e:
					print(e)
					pos = False
					break

				if not pos: break

				if 'strings' in self.text_widget.tag_names(pos):
					#print('strings1', pos)
					if pos == '1.0':
						# It seems that stopindex is sometimes not stopping,
						# when searching in linenumber 1 in multiline string,
						# for word that ends first displayline of this string
						# See wordexpand.py for example
						scope_path = '__main__()'
						return scope_path

					pos = self.text_widget.tag_prevrange('strings', pos)[0] + ' linestart'
					continue

				break
				#####

			if not pos:
				scope_path = '__main__()'
				return scope_path

			index_line_contents = self.text_widget.get( '%s linestart' % pos,
				'%s lineend' % pos )
			#########################


		for char in index_line_contents:
			if char in ['\t']: ind_last_line += 1
			else: break



		# Check possible early defline
		##################################################
		if scope_name := self.line_is_defline(index_line_contents):
			scope_path = scope_name

		# If reached indent0
		# --> exit
		if ind_last_line == 0:
			if not scope_path: scope_path = '__main__()'
			return scope_path

		elif ind_last_line == 1:
			return self.get_scope_path_using_defline_tag(pos, 0, scope_path)



		############################
		# Find first defline using just regexp
		# After getting it, one can build rest of scope_path faster
		# by using defline_tag

		# Why: [^[:blank:]#] instead of: [acd], as from: (a)sync, (c)lass, (d)ef?
		# Reason: need to update indentation level of pos line or else path
		# would be corrupted by possible nested function definitions (function in function).
		patt = r'^[[:blank:]]{1,%d}[^[:blank:]#]' % (ind_last_line-1)

		while pos:
			try:
				# Count is tkinter.IntVar which is used to
				# count indentation level of matched line.
				pos = self.text_widget.search(patt, pos, stopindex='1.0',
					backwards=True, regexp=True, count=self.search_count_var)

			except tkinter.TclError as e:
				print(e)
				break

			if not pos: break

			elif 'strings' in self.text_widget.tag_names(pos):
				#print('strings2', pos)
				if pos == '1.0':
					return '__main__()'
				pos = self.text_widget.tag_prevrange('strings', pos)[0] + ' linestart'
				continue

			# -1: remove terminating char(not blank not #) from matched char count
			# Check patt if interested.
			ind_curline = self.search_count_var.get() - 1


			# Find previous line that:
			# Has one (or more) indentation level smaller indentation than ind_last_line
			# 	Then if it also is definition line --> add to scopepath
			# 	update ind_last_line
			def_line_contents = tmp = self.text_widget.get( pos, '%s lineend' % pos )


			########
			if scope_name := self.line_is_defline(def_line_contents):
				if scope_path != '':
					scope_path = scope_name +'.'+ scope_path
				else:
					scope_path = scope_name

				# SUCCESS
				return self.get_scope_path_using_defline_tag(pos, ind_curline-1, scope_path)
			########


			# Update search pattern and indentation of matched pos line
			ind_last_line = ind_curline
			patt = r'^[[:blank:]]{0,%d}[^[:blank:]#]' % (ind_curline-1)

			# Question: Why not:
			# 	pos = '%s -1c' % pos
			# 	To avoid rematching same line?
			#
			# Answer:
			#	Search is backwards, so even if there is a match at pos,
			#	(where search 'starts' every round), it is not taken as match,
			#	because it is considered to be completely outside of search-range,
			#	which 'ends' at pos, when searching backwards.
			#
			# For more info about searching, backwards, and indexes:
			#	search_help_print()
			#
			#### END OF WHILE #########


		# FAIL
		return '__main__()'


	#@debug
	def get_scope_start(self, index='insert'):
		''' Find next(up) function or class definition

			On success returns:
				definition line:		string
				indentation_of_defline:	int
				idx_linestart(defline):	text-index

			On fail returns:
				'__main__()', 0, '1.0'


			Called from walk_scope, select_scope, self.expander.getwords
		'''


		# Stage 1: Search backwards(up) from index for:
		# pos = Uncommented line with 0 blank or more
		blank_range = '{0,}'
		p1 = r'^[[:blank:]]%s' % blank_range
		# Not blank, not comment
		p2 = r'[^[:blank:]#]'

		patt = p1 + p2

		# Skip possible first defline at index
		# +1 lines: Because cursor could be at defline,
		# start at next line(down) to catch that defline
		# ( For example, select_scope, elide_scope )
		index += ' +1 lines'
		safe_index = self.get_safe_index(index)
		pos = '%s linestart' % safe_index

		while pos:
			try:
				pos = self.text_widget.search(patt, pos, stopindex='1.0',
						regexp=True, backwards=True)

			except tkinter.TclError as e:
				print(e)
				break

			# Empty or just comments
			if not pos:
				return '__main__()', 0, '1.0'

			if 'strings' in self.text_widget.tag_names(pos):
				#print('strings3', pos)
				if pos == '1.0':
					return '__main__()', 0, '1.0'
				pos = self.text_widget.tag_prevrange('strings', pos)[0]
				continue

			break
			###################


		s, e = '%s linestart' % pos, '%s lineend' % pos

		if r := self.line_is_elided(pos): e = r[0]

		pos_line_contents = self.text_widget.get(s, e)


		ind_last_line = 0
		for char in pos_line_contents:
			if char in ['\t']: ind_last_line += 1
			else: break

		# Check if defline already
		if res := self.line_is_defline(pos_line_contents):
			idx = self.idx_linestart(pos)[0]
			return pos_line_contents.strip(), ind_last_line, idx

		elif ind_last_line == 0:
			return '__main__()', 0, pos

		### Stage 1 End ########


		# Stage 2: Search backwards(up) from pos updating indentation level until:
		# defline with ind_last_line-1 blanks or less
		if ind_last_line == 1:
			# note the added '^' at start, this is important to anchor
			# match to linestart. Without it this would match:
			# not blank not comment, which makes A LOT of matches on every line
			patt = p2 = r'^[^[:blank:]#]'

		else:
			# ind_last_line > 1
			blank_range = '{0,%d}' % (ind_last_line - 1)
			p1 = r'^[[:blank:]]%s' % blank_range
			# Not blank, not comment
			p2 = r'[^[:blank:]#]'
			patt = p1 + p2

		#print(ind_last_line, 'before while')

		while pos:
			try:
				pos = self.text_widget.search(patt, pos, stopindex='1.0',
						regexp=True, backwards=True, count=self.search_count_var)

			except tkinter.TclError as e:
				print(e)
				break

			if not pos:
				return '__main__()', 0, '1.0'

			elif 'strings' in self.text_widget.tag_names(pos):
				#print('strings4', pos)
				if pos == '1.0':
					return '__main__()', 0, '1.0'
				pos = self.text_widget.tag_prevrange('strings', pos)[0]
				continue

			################
			# -1: remove terminating char(not blank not #) from matched char count
			# Check patt if interested.
			ind_curline = self.search_count_var.get() - 1

			# Find previous line that:
			# Has one (or more) indentation level smaller indentation than ind_last_line
			# 	Then if it also is definition line --> success
			# 	update ind_last_line
			def_line_contents = self.text_widget.get( pos, '%s lineend' % pos )

			#####
			if res := self.line_is_defline(def_line_contents):
				idx = self.idx_linestart(pos)[0]

				# SUCCESS
				#print(def_line_contents, ind_curline, idx)
				return def_line_contents.strip(), ind_curline, idx
			#####


			# Update search pattern and indentation of matched pos line
			elif ind_curline > 1:
				patt = r'^[[:blank:]]{0,%d}[^[:blank:]#]' % (ind_curline-1)

			elif ind_curline == 1:
				patt = r'^[^[:blank:]#]'

			else:
				# ind_curline == 0
				return '__main__()', 0, pos

			### Stage 2 End ###

		# FAIL
		return '__main__()', 0, '1.0'


	def get_scope_end(self, ind_def_line, index='insert'):
		''' Called from: self.expander.getwords, walk_scope, select_scope

			ind_def_line is int which is supposed to tell indentation of function
			or class -definition line, where insertion-cursor is currently in.
			This ind_def_line can be getted with calling:

				get_scope_start(index='insert')


		 	Goal is to get positions of function start and end.

			On success:
				Returns string: index of end of function or class
			Else:
				Returns 'end'

			NOTE: One needs to check that after get_scope_start-call:
				if scope_path == '__main__()':
					do not call get_scope_end()
		'''

		# Scope is elided
		idx = self.get_safe_index(index)
		if r := self.line_is_elided(idx):
			return self.text_widget.index(r[1])


		# Stage 1: Search forwards(down) from index for:
		# pos = Uncommented line with ind_def_line blanks or less (== next defline/wanderin line)
		blank_range = '{0,%d}' % ind_def_line
		p1 = r'^[[:blank:]]%s' % blank_range
		# Not blank, not comment
		p2 = r'[^[:blank:]#]'

		patt = p1 + p2

		# Skip possible defline at index
		pos = '%s lineend' % index
		flag_at_file_end = False

		while pos:
			try:
				pos = self.text_widget.search(patt, pos, stopindex='end', regexp=True)

			except tkinter.TclError as e:
				print(e)
				pos = 'end'
				break

			if not pos:
				pos = 'end'
				break

			if 'strings' in self.text_widget.tag_names(pos):
				#print('strings5', pos)
				if pos == 'end':
					break
				pos = self.text_widget.tag_prevrange('strings', pos)[1] + ' +1 lines linestart'
				continue

			break
			### Stage 1 End ###


		# Some fixes
		scope_end_fallback = pos + ' -1 lines lineend'
		if pos == 'end':
			scope_end_fallback = index + ' lineend'
			flag_at_file_end = True


		# Stage 2: Search backwards(up) from pos up to index for:
		# Line with ind_def_line+1 blanks or more (== idx_scope_end)
		blank_range = '{%d,}' % (ind_def_line + 1)

		# Get line with any indentation
		if flag_at_file_end: blank_range = '{0,}'

		p1 = r'^[[:blank:]]%s' % blank_range
		# Not blank
		p2 = r'[^[:blank:]]'

		# Not blank not comment
		if flag_at_file_end: p2 = r'[^[:blank:]#]'

		patt = p1 + p2


		#print(patt, pos)
		while pos:
			try:
				pos = self.text_widget.search(patt, pos, stopindex=index,
						regexp=True, backwards=True)

			except tkinter.TclError as e:
				print(e)
				pos = 'end'
				break

			if not pos:
				pos = 'end'
				break

			if 'strings' in self.text_widget.tag_names(pos):
				#print('strings4', pos)
				if pos == 'end':
					break
				# This won't work if for example returning
				# multiline string
				pos = self.text_widget.tag_prevrange('strings', pos)[0]
				continue

			# ON SUCCESS
			break
			### Stage 2 End ###


		# Quick fix for: Function could return multiline string
		if pos == 'end': pos = scope_end_fallback

		pos = self.text_widget.index('%s lineend' % pos)
		return pos


########## Utilities End
########## Gotoline etc Begin

	def stop_goto_def(self, event=None):

		self.bind("<Escape>", self.esc_override)
		self.unbind( "<Button-1>", funcid=self.bid_mouse)
		self.text_widget.unbind( "<Double-Button-1>", funcid=self.bid )

		self.text_widget.config(state='normal')
		self.state = 'normal'

		# Don't leave selection --> esc_override works right away
		if len(self.text_widget.tag_ranges('sel')) > 0:
			self.text_widget.tag_remove('sel', '1.0', tkinter.END)

		self.cursor_frame.place_forget()
		self.message_frame2.place_forget()


		# Space is on hold for extra 200ms, released below
		self.text_widget.unbind( "<space>", funcid=self.bid4 )
		bid_tmp = self.text_widget.bind( "<space>", self.do_nothing_without_bell)

		# Stopping by space while goto_def started from 'normal' -state
		if event:
			if event.keysym == "space" and self.goto_def_pos:
				self.save_pos = self.goto_def_pos

		self.goto_def_pos = False

		# Set cursor pos
		curtab = self.tabs[self.tabindex]
		try:
			if self.save_pos:
				line = self.save_pos
				curtab.position = line
				self.save_pos = ''
			else:
				line = curtab.position

			self.text_widget.focus_set()
			self.text_widget.mark_set('insert', line)
			self.wait_for(100)
			self.ensure_idx_visibility(line)

		except tkinter.TclError:
			curtab.position = self.text_widget.index(tkinter.INSERT)

		# Release space
		self.wait_for(200)
		self.text_widget.unbind( "<space>", funcid=bid_tmp )
		curtab.bid_space = self.text_widget.bind( "<space>", self.space_override)

		return 'break'


	def goto_def(self, event=None):
		''' Get word under cursor or use selection and
			go to function definition

			Example: search definition of method: line_is_elided()

			A: Using selection:
			 self.line_is_elided
			 lf.line_is_elided
			 line_is_elided

			B: Using shortcut without selection when (easiest way)
			cursor is at or in between

			self.l<INS>ine_is_elided<INS>

			Works also when searching/replacing, just press Alt-g on match.

			One can also select other function of interest while searching
			or just click the function name and press Alt-g

			Arrow key or Control-np --> back to search matches
		'''

		if (not self.can_do_syntax()) or (self.state not in ['normal', 'goto_def', 'search', 'replace']):
			self.bell()
			return 'break'

		c = self.text_widget
		have_selection = len(c.tag_ranges('sel')) > 0


		p = 'insert'

		if have_selection:
			word_at_cursor = c.selection_get()
		else:
			word_at_cursor = c.get(f'{p} -1c wordstart', f'{p} -1c wordend')

		word_at_cursor = word_at_cursor.strip()
		if '.' in word_at_cursor:
			word_at_cursor = word_at_cursor.split('.')[-1]

		if word_at_cursor == '':
			return 'break'


		# Reduce greatly search time, compared to re-aproach
		self.deflines = self.get_deflines(self.tabs[self.tabindex])

		for item in self.deflines:
			if item[2] == word_at_cursor:
				pos = str(item[1])
				break
		else:
			print('Could not find:', word_at_cursor)
			self.bell()
			return 'break'


		if pos:
			# Help enabling: "exit to goto_def func with space" while searching
			self.goto_def_pos = pos
			self.text_widget.focus_set()
			self.wait_for(100)
			self.ensure_idx_visibility(pos)

			if have_selection:
				self.text_widget.tag_remove( 'sel', '1.0', tkinter.END )

			self.wait_for(150)
			self.flash_line(pos)

			# Give reminder
			self.show_message2(' GOTO DEF ', 20000)


			# NOTE: If searching, this gets passed
			if self.state == 'normal':
				# Save cursor position to self.save_pos to be restored
				# when pressing Esc to quit goto_def
				tab = self.tabs[self.tabindex]
				try: tab.position = self.text_widget.index(tkinter.INSERT)
				except tkinter.TclError: pass
				self.save_pos = ''

				self.bind("<Escape>", self.stop_goto_def)
				self.bid = self.text_widget.bind("<Double-Button-1>",
					func=lambda event: self.update_curpos(event, **{'on_stop':self.stop_goto_def}), add=True )

				# Show 'insertion cursor' while text_widget is disabled
				self.bid_mouse = self.bind( "<Button-1>", func=self.cursor_frame_set, add=True)

				self.text_widget.unbind( "<space>", funcid=self.tabs[self.tabindex].bid_space )
				self.bid4 = self.text_widget.bind( "<space>", self.stop_goto_def )


				self.text_widget.config(state='disabled')
				self.state = 'goto_def'

			else: pass

		else:
			self.bell()

		return 'break'


	def goto_bookmark(self, event=None, back=False):
		''' Walk bookmarks
		'''

		if self.state != 'normal':
			self.bell()
			return 'break'


		def get_mark(start_idx, markfunc):
			pos = False
			mark_name = markfunc(start_idx)

			while mark_name:
				if 'bookmark' in mark_name:
					pos_mark = self.text_widget.index(mark_name)
					if self.text_widget.compare(pos_mark, '!=', 'insert' ):
						pos = pos_mark
						break

				mark_name = markfunc(mark_name)

			return pos, mark_name

		# Start
		mark_func = self.text_widget.mark_next

		if back:
			mark_func = self.text_widget.mark_previous

		pos, mark = get_mark('insert', mark_func)

		# At file_startend, try again from beginning of other end
		if not pos:
			start = '1.0'
			if back: start = tkinter.END
			pos, mark = get_mark(start, mark_func)

		# No bookmarks in this tab
		if not pos:
			self.wait_for(100)
			self.bell()
			return 'break'


		# get position among bookmarks and build info message
		marks = self.text_widget.mark_names()
		bookmarks = marks[:]
		l = sorted([ (mark, self.text_widget.index(mark)) for mark in bookmarks if 'bookmark' in mark], key=lambda x:float(x[1]) )
		for i,item in enumerate(l):
			if item[0] == mark: break

		a = len(str(i+1))
		b = len(str(len(l)))
		diff = b - a
		head = diff*' ' + f'{i+1}/{len(l)} '

		scope = self.get_scope_path(pos)
		msg = head + scope
		######################


		try:
			self.text_widget.mark_set('insert', pos)
			self.wait_for(100)
			self.show_message(msg, 1200)
			self.ensure_idx_visibility(pos)

		except tkinter.TclError as e:
			print(e)

		return 'break'


	def do_gotoline(self, event=None):
		''' If tkinter.END is linenumber of last line:
			When linenumber given is positive and between 0 - tkinter.END,
			go to start of that line, if greater, go to tkinter.END.

			When given negative number between -1 - -tkinter.END or so,
			start counting from tkinter.END towards beginning and
			go to that line. -1 and empty: go to end.


			If there is comma ",", then do select range, like:

			1,3(normal) or ,33 (from ins, to 33) or 1, (from 1, to ins )
			or ,+2 (from ins, to ins+2) or -2,end-2 (from ins-2, to end-2)
			empty means then insert and -+ is counted from it
		'''

		try:
			# Get stuff after prompt
			tmp = self.entry.get()
			idx = self.entry.len_prompt
			tmp = tmp[idx:].strip()

			# Enable select range Begin
			def get_index(index_string):
				s = index_string.strip()
				if s == '': return 'insert'
				elif 'end' in s:
					if '-' in s:
						s = s.split('-')[1]
						return 'end -%s lines' % s
					else: return 'end'

				elif '-' in s: return 'insert -%s lines' % s[1:]
				elif '+' in s: return 'insert +%s lines' % s[1:]
				else: return s + '.0'


			if ',' in tmp:
				tmp = tmp.split(',')
				s,e = tmp[:2]
				if s == e == '': return self.stop_gotoline()
				s,e = map(get_index, [s,e])

				self.text_widget.tag_remove('sel', '1.0', 'end')
				self.text_widget.tag_add('sel', s, e)
				self.tabs[self.tabindex].position = e
				return self.stop_gotoline(select=True)
			## Enable select range End

			if tmp in ['-1', '']:
				line = tkinter.END

			elif '-' not in tmp:
				line = tmp + '.0'

			elif tmp[0] == '-' and '-' not in tmp[1:] and len(tmp) > 1:

				if int(tmp[1:]) < int(self.entry.endline):
					line = self.entry.endline + '.0 -%s lines' % tmp[1:]
				else: line = tkinter.END
			else: line = tkinter.INSERT

			self.tabs[self.tabindex].position = line


		except tkinter.TclError as e:
			print(e)

		self.stop_gotoline()
		return 'break'


	def stop_gotoline(self, event=None, select=False):
		self.state = 'normal'
		self.bind("<Escape>", self.esc_override)

		self.entry.config(validate='none')

		self.entry.bid_ret = self.entry.bind("<Return>", self.load)
		self.entry.delete(0, tkinter.END)
		curtab = self.tabs[self.tabindex]

		if curtab.filepath:
			self.entry.insert(0, curtab.filepath)
			self.entry.xview_moveto(1.0)


		# Set cursor pos
		try:
			line = curtab.position
			self.text_widget.focus_set()
			self.text_widget.mark_set('insert', line)
			self.wait_for(100)
			self.ensure_idx_visibility(line)

			if not select:
				self.text_widget.tag_remove('sel', '1.0', tkinter.END)

		except tkinter.TclError:
			curtab.position = '1.0'

		return 'break'


	def gotoline(self, event=None):
		''' Go or select lines
		'''
		if self.state not in ['normal']:
			self.bell()
			return 'break'

		self.state = 'gotoline'

		try:
			pos = self.text_widget.index(tkinter.INSERT)
		except tkinter.TclError:
			pos = '1.0'

		self.tabs[self.tabindex].position = pos

		# Remove extra line, this is number of lines in contents
		self.entry.endline = str(self.get_line_col_as_int(index=tkinter.END)[0] - 1)
		self.entry.unbind("<Return>", funcid=self.entry.bid_ret)
		self.entry.bind("<Return>", self.do_gotoline)
		self.bind("<Escape>", self.stop_gotoline)

		self.entry.delete(0, tkinter.END)
		self.entry.focus_set()

		patt = 'Go to line, 1-%s: ' % self.entry.endline
		self.entry.len_prompt = len(patt)
		self.entry.insert(0, patt)
		self.entry.config(validate='key', validatecommand=self.validate_gotoline)

		return 'break'


	def do_validate_gotoline(self, i, S, P):
		'''	i is index of action,
			S is new string to be validated,
			P is all content of entry.
		'''

		#print(i,S,P)
		max_idx = self.entry.len_prompt + 2*len(self.entry.endline) + 9
		# if lastline = 1234 --> 2*4
		# end-1234,end-1232 --> 2*end- == 2*4
		# ',' == 1

		if int(i) < self.entry.len_prompt:
			self.entry.selection_clear()
			self.entry.icursor(self.entry.len_prompt)

			return S == ''

		elif len(P) > max_idx:
			return S == ''

		elif S.isdigit() or S in '-+,end':
			return True

		else:
			return S == ''


########## Gotoline etc End
########## Save and Load Begin

	def filedialog_sorting_order_set(self, dir_reverse=None, file_reverse=None):
		''' Set sorting order of both "normal" directories and files
			True means: use reversed order.
			Default uses reverse for dirs and normal for files.
			Example, set both to normal: filedialog_sorting_order_set(1,1)
		'''

		if dir_reverse is None and file_reverse is None: pass
		else:
			if dir_reverse: self.dir_reverse = True
			else: self.dir_reverse = False
			if file_reverse: self.file_reverse = True
			else: self.file_reverse = False

			# See fdialog.py
			f = self.fdialog_frame
			f.dialog.dir_reverse = self.dir_reverse
			f.dialog.file_reverse = self.file_reverse


		print(self.dir_reverse, self.file_reverse)


	def trace_filename(self, *args):

		# Canceled
		if self.tracevar_filename.get() == '':
			self.entry.delete(0, tkinter.END)

			if self.tabs[self.tabindex].filepath != None:
				self.entry.insert(0, self.tabs[self.tabindex].filepath)
				self.entry.xview_moveto(1.0)

		else:
			# Update self.lastdir
			filename = pathlib.Path().cwd() / self.tracevar_filename.get()
			self.lastdir = pathlib.Path(*filename.parts[:-1])

			self.loadfile(filename)


		self.tracevar_filename.trace_remove('write', self.tracefunc_name)
		self.tracefunc_name = None

		if self.os_type == 'mac_os':
			self.text_widget.bind( "<Mod1-Key-Return>", self.load)
		else:
			self.text_widget.bind( "<Alt-Return>", self.load)

		self.state = 'normal'


		for widget in [self.entry, self.btn_open, self.btn_save, self.text_widget]:
			widget.config(state='normal')


		self.stop_fdialog()
		self.text_widget.focus_force()

		return 'break'


	def loadfile(self, filepath):
		''' filepath is pathlib.Path
			If filepath is python-file, convert indentation to tabs.

			File is always opened to *current* tab
		'''

		filename = filepath
		openfiles = [tab.filepath for tab in self.tabs]
		curtab = self.tabs[self.tabindex]

		for widget in [self.entry, self.btn_open, self.btn_save, self.text_widget]:
			widget.config(state='normal')


		if filename in openfiles:
			print(f'file: {filename} is already open')
			self.bell()
			self.entry.delete(0, tkinter.END)

			if curtab.filepath != None:
				self.entry.insert(0, curtab.filepath)
				self.entry.xview_moveto(1.0)

			return False


		self.auto_update_syntax_stop()


		# Using *same* tab:
		try:
			with open(filename, 'r', encoding='utf-8') as f:
				tmp = f.read()
				curtab.oldcontents = tmp

				if '.py' in filename.suffix:
					indentation_is_alien, indent_depth = self.check_indent_depth(tmp)

					if indentation_is_alien:
						tmp = curtab.oldcontents.splitlines(True)
						tmp[:] = [self.tabify(line, width=indent_depth) for line in tmp]
						tmp = ''.join(tmp)
						curtab.contents = tmp

					else:
						curtab.contents = curtab.oldcontents
				else:
					curtab.contents = curtab.oldcontents


				curtab.filepath = filename
				curtab.type = 'normal'
				curtab.position = '1.0'
				self.bookmarks_remove(all_tabs=False)


				self.entry.delete(0, tkinter.END)
				if curtab.filepath != None:
					self.entry.insert(0, curtab.filepath)
					self.entry.xview_moveto(1.0)

				self.text_widget.delete('1.0', tkinter.END)
				self.text_widget.insert(tkinter.INSERT, curtab.contents)
				self.text_widget.mark_set('insert', '1.0')
				self.text_widget.see('1.0')

				if self.can_do_syntax(curtab):
					self.update_lineinfo(curtab)
					self.insert_tokens(self.get_tokens(curtab), tab=curtab)

				self.text_widget.edit_reset()
				self.text_widget.edit_modified(0)


		except (EnvironmentError, UnicodeDecodeError) as e:
			print(e.__str__())
			print(f'\n Could not open file: {filename}')
			self.entry.delete(0, tkinter.END)

			if curtab.filepath != None:
				self.entry.insert(0, curtab.filepath)
				self.entry.xview_moveto(1.0)

			self.text_widget.focus_set()
			self.auto_update_syntax_continue()
			return False


		self.text_widget.focus_set()
		self.auto_update_syntax_continue()
		return True


	def map_filedialog(self, use_tracefunc=True):
		self.state = 'filedialog'
		self.bind("<Escape>", self.stop_fdialog)

		for widget in [self.entry, self.btn_open, self.btn_save, self.text_widget]:
			widget.config(state='disabled')


		wid = self.fdialog_frame

		# Give more lines when in fullscreen
		if self.is_fullscreen():
			wid.dialog.files.config(height=15)
			wid.dialog.dirs.config(height=15)
			kwargs = {'relx':0.1, 'rely':0.1}
		else:
			wid.dialog.files.config(height=10)
			wid.dialog.dirs.config(height=10)
			kwargs = {'x':wid.old_x, 'y':wid.old_y}


		self.tracevar_filename.set('empty')
		if use_tracefunc:
			self.tracefunc_name = self.tracevar_filename.trace_add('write', self.trace_filename)

		wid.place_configure(**kwargs)
		wid.dialog.update_view()


	def load(self, event=None):
		'''	Get just the filename,
			on success, pass it to loadfile()

			File is always opened to *current* tab
		'''

		if self.state != 'normal':
			self.bell()
			return 'break'

		curtab = self.tabs[self.tabindex]

		# Prevent loosing bookmarks mistakenly
		# --> Ask confirmation if tab have bookmarks
		tests = ( len(curtab.bookmarks) > 0,
				curtab.type == 'normal'
				)
		if all(tests):
			msg_options = dict(message='Current tab has bookmarks',
				detail='Will loose those bookmarks if choose to continue, continue anyway?')
			res = self.msgbox.show(**msg_options)
			if res == 'cancel':
				self.entry.delete(0, tkinter.END)

				if curtab.filepath != None:
					self.entry.insert(0, curtab.filepath)
					self.entry.xview_moveto(1.0)

				self.text_widget.focus_set()
				return 'break'


		if curtab.type == 'normal':
			if not self.save(activetab=True):
				self.bell()
				return 'break'


		if len(self.text_widget.tag_ranges('sel')) > 0:
			self.text_widget.tag_remove('sel', '1.0', 'end')


		# Called by: Open-button(event==None) or keyboard-shortcut
		if (not event) or (event.widget != self.entry):

			shortcut = "<Mod1-Key-Return>"
			if self.os_type != 'mac_os':
				shortcut = "<Alt-Return>"

			self.text_widget.bind( shortcut, self.do_nothing_without_bell)


			self.map_filedialog()

			return 'break'


		# Entered filename to be opened in entry:
		else:
			tmp = self.entry.get().strip()

			if not isinstance(tmp, str) or tmp.isspace():
				self.bell()
				return 'break'

			filename = pathlib.Path().cwd() / tmp

			self.loadfile(filename)

			return 'break'


	def load_tags(self, tab_list):
		''' load tags from cache-file at startup
			Called from __init__()
		'''
		# When have little over 10k lines(all lines counted, also empty)
		# tagging syntax with rpi1 using
		# A: normal insert_tokens() takes 21-24s
		# B: cache with tcl load_tags() takes 1.6s
		# --> use cache, Benefit is over 1:10

		# On faster/normal machine
		# A: normal insert_tokens() takes about 250ms
		# B: cache with tcl load_tags() takes about 70ms
		# --> Benefit is not as great but still about 1:3

		p = pathlib.Path(self.env) / self.cachepath

		# In Tcl, need to enclose strings with possible '\'s inside curlies {}
		# set cache_path {%s} % string_with_possible_\

		# build tcl-dict: {key1 value1 key2 value2}
		# {myfile.py .!editor.!frame.!text2..}
		filedict = '{'
		for tab in tab_list:
			fpath = tab.filepath.resolve()
			tk_wid = tab.tcl_name_of_contents
			filedict += '{%s} %s ' % (fpath, tk_wid)
		# remove trailing space just in case
		filedict = filedict[:-1]
		filedict += '}'
		res = True

		try:
			self.tk.eval('''
			set cache_path {%s}
			set ch [open $cache_path r]
			set taginfo [read $ch]
			close $ch
			set filedict %s
			foreach fpath [dict keys $filedict] {
				set wid [dict get $filedict $fpath]
				set tag_dict [dict get $taginfo $fpath]
				foreach tag [dict keys $tag_dict] {
					set tag_list [dict get $tag_dict $tag]
					set taglen [llength $tag_list]
					if {$taglen > 0} {eval "$wid tag add $tag $tag_list"}
				}
			}
			''' % (p, filedict) )

		except tkinter.TclError as e:
			res = False
			print(e)

		return res


	def save_tags(self):
		''' save tags to cache-file
			Called from save_forced()
		'''
		have_py_files = False
		p = pathlib.Path(self.env) / self.cachepath

		# save tags at exit
		###############
		# build tcl-dict: {key1 value1 key2 value2}
		# {myfile.py .!editor.!frame.!text2..}
		filedict = '{'
		for tab in self.tabs:
			if tab.filepath:
				if '.py' in tab.filepath.suffix:
					have_py_files = True
					tab.chk_sum = len(tab.contents)
					fpath = tab.filepath.resolve()
					tk_wid = tab.tcl_name_of_contents
					filedict += '{%s} %s ' % (fpath, tk_wid)
		# remove trailing space just in case
		filedict = filedict[:-1]
		filedict += '}'

		if not have_py_files: return

		tags = ' '.join(self.tagnames)
		try:
			self.tk.eval('''
			set cache_path {%s}
			set taginfo {}
			set filedict %s
			foreach fpath [dict keys $filedict] {
				set wid [dict get $filedict $fpath]
				set tag_dict {}
				foreach tag {%s} {dict set tag_dict $tag [$wid tag ranges $tag]}
				dict set taginfo $fpath $tag_dict
				}
			set ch [open $cache_path w]
			puts $ch $taginfo
			close $ch
			''' % (p, filedict, tags) )

		except tkinter.TclError as e:
			print(e)


	def save_forced(self, curtab=False):
		''' Called from run() or quit_me()

			If python-file, convert indentation to tabs.
		'''
		# Dont do anything when widget is not alive
		if not self.__class__.alive: raise ValueError

		# Dont want contents to be replaced with errorlines or help.
		last_state = self.state

		while self.state != 'normal':
			self.text_widget.event_generate('<Escape>')

			# Is state actually changing, or is it stuck == there is a bug
			# --> cancel
			if self.state == last_state:
				print(r'\nState is not changing, currently: ', self.state)

				return False

			last_state = self.state


		if curtab: tabs = [self.tabs[self.tabindex]]
		else: tabs = self.tabs


		res = True
		for tab in tabs:
			if tab.type == 'normal':

				try:
					pos = tab.text_widget.index(tkinter.INSERT)
				except tkinter.TclError:
					pos = '1.0'

				tab.position = pos
				tab.contents = tab.text_widget.get('1.0', tkinter.END)[:-1]


				if '.py' in tab.filepath.suffix:
					# Check indent (tabify) and rstrip:
					tmp = tab.contents.splitlines(True)
					tmp[:] = [self.tabify(line) for line in tmp]
					tmp = ''.join(tmp)
				else:
					tmp = tab.contents

				tab.contents = tmp

				if tab.contents == tab.oldcontents:
					continue

				try:
					with open(tab.filepath, 'w', encoding='utf-8') as f:
						f.write(tab.contents)
						tab.oldcontents = tab.contents

				except EnvironmentError as e:
					print(e.__str__())
					print(f'\n Could not save file: {tab.filepath}')
					res = False
			else:
				tab.position = '1.0'


		if not curtab and not self.one_time_conf: self.save_tags()
		return res


	def save(self, activetab=False):
		''' Called for example when pressed Save-button.

			activetab=True from load() and del_tab()

			If python-file, convert indentation to tabs.
		'''
		# Have to check if activetab because
		# state is filedialog in loadfile()
		if self.state != 'normal' and not activetab:
			self.bell()
			return 'break'


		def update_entry():
			self.entry.delete(0, tkinter.END)
			self.entry.insert(0, self.tabs[self.tabindex].filepath)
			self.entry.xview_moveto(1.0)


		def set_cursor_pos():
			try:
				line = self.tabs[self.tabindex].position
				self.text_widget.focus_set()
				self.text_widget.mark_set('insert', line)
				self.ensure_idx_visibility(line)

			except tkinter.TclError:
				self.tabs[self.tabindex].position = '1.0'


		tmp_entry = self.entry.get().strip()
		tests = (isinstance(tmp_entry, str),
				not tmp_entry.isspace(),
				not tmp_entry == ''
				)

		if not all(tests):
			print('Give a valid filename')
			self.bell()
			return False


		fpath_in_entry = (pathlib.Path().cwd() / tmp_entry).resolve()
		##############

		try:
			pos = self.text_widget.index(tkinter.INSERT)
		except tkinter.TclError:
			pos = '1.0'


		oldtab = self.tabs[self.tabindex]
		oldtab.position = pos

		# Update oldtabs contents
		# [:-1]: text widget adds dummy newline at end of file when editing
		cur_contents = oldtab.contents = self.text_widget.get('1.0', tkinter.END)[:-1]
		##############################


		openfiles = [tab.filepath for tab in self.tabs]


		# Creating a new file
		if fpath_in_entry != oldtab.filepath and not activetab:

			if fpath_in_entry in openfiles:
				self.bell()
				print(f'\nFile: {fpath_in_entry} already opened')

				if oldtab.filepath != None:
					update_entry()

				return False

			if fpath_in_entry.exists():
				self.bell()
				print(f'\nCan not overwrite file: {fpath_in_entry}')

				if oldtab.filepath != None:
					update_entry()

				return False

			if oldtab.type == 'newtab':

				# Avoiding disk-writes, just checking filepath:
				try:
					with open(fpath_in_entry, 'w', encoding='utf-8') as f:
						oldtab.filepath = fpath_in_entry
						oldtab.type = 'normal'
				except EnvironmentError as e:
					print(e.__str__())
					print(f'\n Could not create file: {fpath_in_entry}')
					return False


				set_cursor_pos()

				if oldtab.filepath != None:
					update_entry()
					self.auto_update_syntax_stop()

					if self.can_do_syntax(tab=oldtab):
						self.update_lineinfo(tab=oldtab)
						self.insert_tokens(self.get_tokens(oldtab), tab=oldtab)
					else:
						# Remove tags
						for tag in self.tagnames:
							self.text_widget.tag_remove(tag, '1.0', 'end')

					self.auto_update_syntax_continue()

				oldtab.text_widget.edit_reset()
				oldtab.text_widget.edit_modified(0)



			# Want to create new file with same contents
			# (bookmarks are not copied)
			elif oldtab.type == 'normal':
				try:
					with open(fpath_in_entry, 'w', encoding='utf-8') as f:
						pass
				except EnvironmentError as e:
					print(e.__str__())
					print(f'\n Could not create file: {fpath_in_entry}')

					if oldtab.filepath != None:
						update_entry()

					return False


				self.auto_update_syntax_stop()

				# new_tab() calls tab_close()
				# and updates self.tabindex
				self.new_tab()
				newtab = self.tabs[self.tabindex]

				newtab.filepath = fpath_in_entry
				# Q: Why not newtab.oldcontents = cur_contents?
				# A: Because not writing to disk now, want to keep difference, for
				#    forced save to work with this tab.
				newtab.contents = cur_contents
				newtab.position = pos
				newtab.type = 'normal'

				update_entry()
				newtab.text_widget.insert(tkinter.INSERT, newtab.contents)
				set_cursor_pos()

				if self.can_do_syntax(tab=newtab):
					self.update_lineinfo(tab=newtab)
					self.insert_tokens(self.get_tokens(newtab), tab=newtab)
				else:
					# Remove tags
					for tag in self.tagnames:
						self.text_widget.tag_remove(tag, '1.0', 'end')

				self.auto_update_syntax_continue()

				newtab.text_widget.edit_reset()
				newtab.text_widget.edit_modified(0)


			# Should not happen
			else:
				print('Error in save() while saving tab:')
				print(oldtab.filepath)
				return False


		# Not creating a new file
		else:
			# Q: When this happens?
			# A: Pressing Save and fpath_in_entry == oldtab.filepath
			#    that is, file exist already on disk
			if not activetab:
				# --> enable sync tab to disk (=='intuitive save-button behaviour')
				res = self.save_forced(curtab=True)
				if res: self.show_message(' OK ', 1100)

				return res

			# NOTE: oldtab.contents is updated at beginning.
			# Closing tab or loading file
			if '.py' in oldtab.filepath.suffix:
				# Check indent (tabify) and strip
				tmp = oldtab.contents.splitlines(True)
				tmp[:] = [self.tabify(line) for line in tmp]
				tmp = ''.join(tmp)
			else:
				tmp = oldtab.contents
				tmp = tmp


			if tmp == oldtab.oldcontents:
				return True


			try:
				with open(oldtab.filepath, 'w', encoding='utf-8') as f:
					f.write(tmp)

			except EnvironmentError as e:
				print(e.__str__())
				print(f'\n Could not save file: {oldtab.filepath}')
				return False


		return True
		############# Save End #######################################

########## Save and Load End
########## Bookmarks and Help Begin

##	Note: goto_bookmark() is in Gotoline etc -section
	#@debug
	def bookmarks_print(self):

		def get_and_print_books(book_list, filter_word):
			book_list = sorted([ self.text_widget.index(mark) for mark in book_list if filter_word in mark], key=float )
			if not book_list: return
			book_list = [ (self.get_scope_path(pos), pos) for pos in book_list ]

			max_len = max( map(lambda item: len(str(item[1])), book_list) )
			patt = '{0:%s}\t{1}' % max_len
			for (path, pos) in book_list:
				print(patt.format(pos, path))


		self.wait_for(100)

		marks = self.text_widget.mark_names()
		bookmarks = marks[:]
		print('\nBookmarks:')
		get_and_print_books(bookmarks, 'bookmark')

		stashed = marks[:]
		for mark in stashed:
			if 'stashed' in mark: break
		else: return

		print('\nHided bookmarks:')
		get_and_print_books(stashed, 'stashed')


	def line_is_bookmarked(self, index, tab=None, mark_patt='bookmark'):
		''' index:	tkinter.Text -index

			mark_patt can also be 'stashed'

			On success, returns: markname
		'''

		curtab = tab
		if not tab:
			curtab = self.tabs[self.tabindex]

		# Find first mark in line
		s = curtab.text_widget.index('%s display linestart' % index)
		mark_name = curtab.text_widget.mark_next(s)

		# Find first bookmark at or after s
		while mark_name:
			if mark_patt not in mark_name:
				mark_name = curtab.text_widget.mark_next(mark_name)
			else:
				break

		if mark_name:
			if mark_patt in mark_name:
				mark_line,_ = self.get_line_col_as_int(tab=curtab, index=mark_name)
				pos_line,_ = self.get_line_col_as_int(tab=curtab, index=s)

			if mark_line == pos_line:
				return mark_name

		return False


	def clear_bookmarks(self):
		''' Unsets bookmarks from current tab.

			Does NOT do: tab.bookmarks.clear()
		'''
		for mark in self.text_widget.mark_names():
			if 'bookmark' in mark:
				self.text_widget.mark_unset(mark)


	def save_bookmarks(self, tab, also_stashed=False):
		''' tab: Tab
		'''
		tab.bookmarks = list({ tab.text_widget.index(mark) for mark in tab.bookmarks })
		tab.bookmarks.sort()

		if also_stashed:
			tab.bookmarks_stash = list({ tab.text_widget.index(mark) for mark in tab.bookmarks_stash })
			tab.bookmarks_stash.sort()


	def restore_bookmarks(self, tab, also_stashed=False):
		''' tab: Tab

			When bookmarks are saved, only their index position, not names, are saved.

			Bookmarks are restored here and tab.bookmarks holds again the names of bookmarks.
		'''

		for i, pos in enumerate(tab.bookmarks):
			tab.text_widget.mark_set('bookmark%d' % i, pos)

		tab.bookmarks.clear()

		[ tab.bookmarks.append(mark) for mark in tab.text_widget.mark_names() if 'bookmark' in mark ]


		if also_stashed:
			for i, pos in enumerate(tab.bookmarks_stash):
				tab.text_widget.mark_set('stashed%d' % i, pos)

			tab.bookmarks_stash.clear()

			[ tab.bookmarks_stash.append(mark) for mark in tab.text_widget.mark_names() if 'stashed' in mark ]


	def bookmarks_import(self):
		''' update (add not already existing bookmarks),
			update opened tabs bookmarks from file

			Also stashed bookmarks
		'''

		if self.state != 'normal':
			self.bell()
			return 'break'

		# Just waiting
		self.map_filedialog(use_tracefunc=False)

		# Editor remains responsive while doing wait_variable()
		# but widgets have been disabled
		self.wait_variable(self.tracevar_filename)
		data, p = False, False

		# Canceled
		if self.tracevar_filename.get() == '': pass
		else:
			p = pathlib.Path().cwd() / self.tracevar_filename.get()
			if p.exists():
				try:
					with open(p, 'r', encoding='utf-8') as f:
						string_representation = f.read()
						data = json.loads(string_representation)

				except EnvironmentError as e:
					print(e.__str__())
					print('\nCould not export bookmarks')

		if data:
			total_books = 0
			total_stash = 0

			for fpath in data.keys():
				for tab in self.tabs:
					if tab.filepath.__str__() == fpath and tab.type == 'normal':

						bookmarks, bookmarks_stashed = data[fpath]

						for idx in bookmarks:
							if not self.line_is_bookmarked(idx, tab=tab):
								new_mark = 'bookmark' + str(len(tab.bookmarks))
								tab.text_widget.mark_set( new_mark, idx )
								tab.bookmarks.append(new_mark)
								total_books += 1

						for idx in bookmarks_stashed:
							if not self.line_is_bookmarked(idx, tab=tab, mark_patt='stashed'):
								new_mark = 'stashed' + str(len(tab.bookmarks_stash))
								tab.text_widget.mark_set( new_mark, idx )
								tab.bookmarks_stash.append(new_mark)
								total_stash += 1

			print('\nImported total of %i new bookmarks and %i new hided bookmarks from:\n%s' % (total_books, total_stash, p))


		# This has to be after tracevar_filename.get()
		self.stop_fdialog()

		self.state = 'normal'
		for widget in [self.entry, self.btn_open, self.btn_save, self.text_widget]:
			widget.config(state='normal')


	def bookmarks_export(self):
		''' Also stashed bookmarks are saved
		'''
		import tkinter.filedialog
		fname_as_string = p = tkinter.filedialog.asksaveasfilename()

		data = dict()

		for tab in self.tabs:
			if tab.filepath:
				filepath = tab.filepath.__str__()
				bookmark_index_list = list({ tab.text_widget.index(mark) for mark in tab.bookmarks })
				bookmark_stash_list = list({ tab.text_widget.index(mark) for mark in tab.bookmarks_stash })
				data[filepath] = bookmark_index_list, bookmark_stash_list


		string_representation = json.dumps(data)

		try:
			with open(p, 'w', encoding='utf-8') as f:
				f.write(string_representation)
				print('\nExported bookmarks to:\n%s' % p)

		except EnvironmentError as e:
			print(e.__str__())
			print('\nCould not export bookmarks')


	def bookmarks_unstash(self, all_tabs=False):
		''' Restore hided bookmarks
		'''
		if self.state != 'normal': return
		tabs = [self.tabs[self.tabindex]]
		if all_tabs: tabs = self.tabs

		for tab in tabs:
			if tab.type != 'normal': continue
			total = 0

			for mark in tab.text_widget.mark_names():
				if 'stashed' in mark:
					pos = tab.text_widget.index(mark)
					tab.text_widget.mark_unset(mark)

					if not self.line_is_bookmarked(pos, tab=tab):
						new_mark = 'bookmark' + str(len(tab.bookmarks))
						tab.text_widget.mark_set( new_mark, pos )
						tab.bookmarks.append(new_mark)
						total += 1

			if total > 0:
				print('\nRestored from stash total of %i new bookmarks to:\n%s' % (total, tab.filepath))

			tab.bookmarks_stash.clear()


	def stash_bookmark(self, event=None):
		''' Move mark to other collection so
			it is not browsable until later un-stashed

			Use when have too many bookmarks
		'''
		if self.state != 'normal':
			self.bell()
			return 'break'

		if old_idx := self.remove_single_bookmark():
			curtab = self.tabs[self.tabindex]
			new_mark = 'stashed' + str(len(curtab.bookmarks_stash))
			pos = self.text_widget.index('%s display linestart' % old_idx)
			self.text_widget.mark_set( new_mark, pos )
			curtab.bookmarks_stash.append(new_mark)

			self.bookmark_animate(pos, remove=True, tagname='animate_stash')

		return 'break'


	def bookmarks_remove(self, all_tabs=False):
		''' Removes bookmarks from current tab/all tabs
		'''

		tabs = [self.tabs[self.tabindex]]
		if all_tabs: tabs = self.tabs

		for tab in tabs:
			tab.bookmarks.clear()

		self.clear_bookmarks()


	def remove_single_bookmark(self):

		if mark_name := self.line_is_bookmarked('insert'):

			old_idx = self.text_widget.index(mark_name)
			self.text_widget.mark_unset(mark_name)
			tab = self.tabs[self.tabindex]
			tab.bookmarks.remove(mark_name)

			# Keeping right naming of bookmarks in tab.bookmarks is quite tricky
			# when removing and adding bookmarks in the same tab, without changing view.
			# Seems like the line: self.clear_bookmarks solves the issue.
			# Bookmarks where working right, but if doing self.bookmarks_print
			# after removing and adding bookmarks, it would look odd with ghost duplicates.
			self.save_bookmarks(tab)
			self.clear_bookmarks()
			self.restore_bookmarks(tab)

			return old_idx

		else:
			return False


	def toggle_bookmark(self, event=None, index='insert'):
		''' Add/Remove bookmark at cursor position

			Bookmark is string, name of tk text mark like: 'bookmark11'
			It is appended to tab.bookmarks

			Adding bookmark to line which has stashed bookmark will
			remove that stashed mark

		'''
		tests = (
				self.state not in [ 'normal', 'search', 'replace', 'goto_def' ],
				not self.text_widget.bbox('insert')
				)

		if any(tests):
			self.bell()
			return 'break'

		pos = self.text_widget.index('%s display linestart' % index)
		tab = self.tabs[self.tabindex]

		# Remove possible stashed bookmark,
		# if this is unwanted behaviour, this block should be removed
		if mark := self.line_is_bookmarked(pos, tab=tab, mark_patt='stashed'):
			pos = tab.text_widget.index(mark)
			tab.text_widget.mark_unset(mark)
			tab.bookmarks_stash.remove(mark)


		# If there is bookmark, remove it
		if self.remove_single_bookmark():
			self.bookmark_animate(pos, remove=True)
			return 'break'


		new_mark = 'bookmark' + str(len(tab.bookmarks))
		self.text_widget.mark_set( new_mark, pos )
		tab.bookmarks.append(new_mark)

		self.bookmark_animate(pos)
		return 'break'


	def bookmark_animate(self, index, remove=False, tagname='animate'):
		''' Animate on Add/Remove bookmark

			Called from: toggle_bookmark, stash_bookmark
		'''

		s = self.text_widget.index( '%s display linestart' % index)

		self.text_widget.edit_separator()

		try:
			e0 = self.idx_lineend()
			col = self.get_line_col_as_int(index=e0)[1]


			# Time to spend with marking-animation on line
			time_wanted = 400
			# Time to spend with marking-animation on char
			step = 8

			# Removing animation is 'doubled' --> need to reduce time
			if remove:
				time_wanted = 300
				step = 6

			# Want to animate on this many chars
			wanted_num_chars = want = time_wanted // step

			# Check not over screen width 1
			width_char = self.textfont.measure('A')
			width_scr = self.text_widget.winfo_width()
			num_chars = width_scr // width_char

			if wanted_num_chars > num_chars:
				wanted_num_chars = want = num_chars



			flag_added_space = False
			flag_changed_contents_state = False


			# If line has not enough characters
			if (diff := want - col) > 0:

				# Check not over screen width 2
				if (self.text_widget.bbox(e0)[0] + diff * width_char) < (width_scr - width_char):

					# Add some space so we can tag more estate from line. It is later removed.
					flag_added_space = True

					# Searching, Replacing
					if self.text_widget.cget('state') == 'disabled':

						self.text_widget.config(state='normal')
						flag_changed_contents_state = True

					self.text_widget.insert(e0, diff * ' ')


				# Some deep indentation and small screen size combo
				# --> Line has enough characters, just update step
				else:
					wanted_num_chars = 0
					t = self.text_widget.get(s, e0)
					for char in t:
						wanted_num_chars += 1

					# Recalculate step
					step = time_wanted // wanted_num_chars
					want = wanted_num_chars



			e = self.idx_lineend()

			bg, fg = self.themes[self.curtheme]['sel'][:]
			if tagname == 'animate':
				self.text_widget.tag_config(tagname, background=bg, foreground=fg)
			self.text_widget.tag_raise(tagname)
			self.text_widget.tag_remove(tagname, '1.0', tkinter.END)


			# Animate removing bookmark
			if remove:
				# 1: Tag wanted_num_chars from start. In effect this, but in loop
				# to enable use of after(), to get animating effect.
				# self.text_widget.tag_add('sel', s, '%s +%d chars' % (s, wanted_num_chars) )

				for i in range(wanted_num_chars):
					p0 = '%s +%d chars' % (s, wanted_num_chars - i-1 )
					p1 = '%s +%d chars' % (s, wanted_num_chars - i )

					self.after( (i+1)*step, lambda args=[tagname, p0, p1]:
							self.text_widget.tag_add(*args) )

				# 2: Same story as when adding, just note some time has passed
				for i in range(wanted_num_chars):
					p0 = '%s +%d chars' % (s, wanted_num_chars - i-1 )
					p1 = '%s +%d chars' % (s, wanted_num_chars - i )

					self.after( ( time_wanted + (i+1)*step ), lambda args=[tagname, p0, p1]:
							self.text_widget.tag_remove(*args) )


				if flag_added_space:
					self.after( (2*time_wanted + 30), lambda args=[e0, '%s display lineend' % e0]:
							self.text_widget.delete(*args) )

					if flag_changed_contents_state:
						self.after( (2*time_wanted + 40), lambda kwargs={'state':'disabled'}:
								self.text_widget.config(**kwargs) )



			# Animate adding bookmark
			else:
				# Info is in remove-section above
				for i in range(wanted_num_chars):
					p0 = '%s +%d chars' % (s, i)
					p1 = '%s +%d chars' % (s, i+1)

					self.after( (i+1)*step, lambda args=[tagname, p0, p1]:
							self.text_widget.tag_add(*args) )


				self.after( (time_wanted + 300), lambda args=[tagname, '1.0', tkinter.END]:
						self.text_widget.tag_remove(*args) )


				if flag_added_space:
					self.after( (time_wanted + 330), lambda args=[e0, '%s display lineend' % e0]:
							self.text_widget.delete(*args) )

					if flag_changed_contents_state:
						self.after( (time_wanted + 340), lambda kwargs={'state':'disabled'}:
								self.text_widget.config(**kwargs) )



		except tkinter.TclError as ee:
			print(ee)


		self.text_widget.edit_separator()

		######## bookmark_animate End #######


	def stop_help(self, event=None):

		self.state = 'normal'

		self.entry.config(state='normal')
		self.text_widget.config(state='normal')
		self.btn_open.config(state='normal')
		self.btn_save.config(state='normal')

		self.cursor_frame.place_forget()


		self.tab_close(self.tabs[self.tabindex])

		self.tabs.pop()
		self.tabindex = self.oldindex

		self.tab_open(self.tabs[self.tabindex])


		self.bind("<Escape>", self.esc_override)
		self.unbind( "<Button-1>", funcid=self.bid_mouse)
		self.bind("<Button-%i>" % self.right_mousebutton_num,
			lambda event: self.popup_raise(event))


	def enter_help(self, tagname, event=None):
		''' Used in help-page, when mousecursor enters hyperlink tagname.
		'''
		self.text_widget.config(cursor="hand2")
		self.text_widget.tag_config(tagname, underline=1)


	def leave_help(self, tagname, event=None):
		''' Used in help-page, when mousecursor leaves hyperlink tagname.
		'''
		self.text_widget.config(cursor=self.name_of_cursor_in_text_widget)
		self.text_widget.tag_config(tagname, underline=0)


	def lclick_help(self, tagname, event=None):
		'''	Used in help-page, when hyperlink tagname is clicked.
		'''
		return self.goto_help_title(tagname)


	def goto_help_title(self, tagname):
		# "help_tag-%d"
		title_idx = int(tagname.split('-')[1])
		w = self.help_tab.text_widget
		patt = '[%d]' % title_idx
		pos = '1.0'
		try: pos = w.search(patt, pos, stopindex='end')
		except tkinter.TclError: pos = 'insert'

		self.wait_for(100)
		w.see(pos)
		self.wait_for(120)
		self.flash_line(pos=pos)

		return 'break'


	def init_help_tags(self):
		help_title_string = '''
	Shortcuts


	Searching in general
	General about editor
	About buttons

	Executing program
	Doing Test-run
	Fix syntax-highlighting
	Check syntax

	Bookmarks
	Goto definition

	Set editor size and position
	Set editor to launch fullscreen
	Set command to fetch current version control branch

	Tab-completion
	Inspecting modules
	Pasting diff output to editor
	Fix possible printing issue with macOS
	Selecting range of lines
	Guides
	Elide(folding)

	Search and Replace in more detail
	Substitution with Regexp

	Set left margin
	Set scrollbar width
	Set filedialog sorting order (directories, files)
	Change tabsize
	Export configuration


	Developing
'''

		w = self.help_tab.text_widget

		w.mark_set('insert', '1.0')

		i = 1
		for line in help_title_string.splitlines(keepends=True):
			if line.isspace():
				w.insert('insert', '\n')
				continue

			tagname = "help_tag-%d" % i
			w.tag_config(tagname)

			w.tag_bind(tagname, "<ButtonRelease-1>",
				lambda event, arg=tagname: self.lclick_help(arg, event))

			w.tag_bind(tagname, "<Enter>",
				lambda event, arg=tagname: self.enter_help(arg, event))

			w.tag_bind(tagname, "<Leave>",
				lambda event, arg=tagname: self.leave_help(arg, event))

			w.insert('insert', line, tagname)
			i += 1


	def help(self, event=None):
		if self.state != 'normal':
			self.bell()
			return 'break'

		self.state = 'help'


		self.tab_close(self.tabs[self.tabindex])

		self.tabs.append(self.help_tab)
		self.oldindex = self.tabindex
		self.tabindex = len(self.tabs) -1

		self.tab_open(self.tabs[self.tabindex])
		self.help_tab.text_widget.focus_set()


		self.entry.config(state='disabled')
		self.text_widget.config(state='disabled')
		self.btn_open.config(state='disabled')
		self.btn_save.config(state='disabled')


		# Show 'insertion cursor' while text_widget is disabled
		self.bid_mouse = self.bind( "<Button-1>", func=self.cursor_frame_set, add=True)
		self.bind("<Button-%i>" % self.right_mousebutton_num, self.do_nothing)
		self.bind("<Escape>", self.stop_help)


########## Bookmarks and Help End
########## Indent and Comment Begin

	def check_indent_depth(self, contents):
		'''Contents is contents of py-file as string.'''

		words = [
				'def ',
				'if ',
				'for ',
				'while ',
				'class '
				]

		tmp = contents.splitlines()

		for word in words:

			for i in range(len(tmp)):
				line = tmp[i]
				if word in line:

					# Trying to check if at the beginning of new block:
					if line.strip()[-1] == ':':
						# Offset is num of empty lines between this line and next
						# non empty line
						nextline = None

						for offset in range(1, len(tmp)-i):
							nextline = tmp[i+offset]
							if nextline.strip() == '': continue
							else: break


						if not nextline:
							continue


						# Now should have next non empty line,
						# so start parsing it:
						flag_space = False
						indent_0 = 0
						indent_1 = 0

						for char in line:
							if char in [' ', '\t']: indent_0 += 1
							else: break

						for char in nextline:
							# Check if indent done with spaces:
							if char == ' ':
								flag_space = True

							if char in [' ', '\t']: indent_1 += 1
							else: break


						indent = indent_1 - indent_0
						#print(indent)
						tests = [
								indent <= 0,
								(not flag_space) and (indent > 1)
								]

						if any(tests):
							#print('indent err')
							#skipping
							continue


						# All is good, do nothing:
						if not flag_space:
							return False, 0

						# Found one block with spaced indentation,
						# assuming it is used in whole file.
						else:
							if indent != self.ind_depth:
								return True, indent

							else:
								return False, 0

		return False, 0


	def can_expand_word(self, event=None):
		'''	Called from indent() and unindent()
		'''

		if not self.text_widget.bbox('insert'):
			self.bell()
			return False

		# Check previous char
		curinsert = self.text_widget.index('insert')
		line_as_int, ins_as_int = self.get_line_col_as_int()

		if ins_as_int > 0:
			prev_char = self.text_widget.get( ('%s -1 char') % curinsert, '%s' % curinsert )

			if prev_char in self.expander.wordchars:
				return True

			# There already are completions and previous completion was callable
			elif prev_char in '(':
				if event.widget != self.expander.text_widget or not self.expander.state:
					return False

				curline = self.text_widget.get("insert linestart", "insert lineend")

				_, _, insert, line = self.expander.state

				if insert == curinsert and line == curline:
					return True


		return False

	#@debug
	def indent(self, event=None):
		if self.state in [ 'search', 'replace', 'replace_all', 'goto_def' ]:
			return 'break'

		self.auto_update_syntax_stop()


		if len(self.text_widget.tag_ranges('sel')) == 0:

			if self.can_expand_word(event=event):
				self.show_completions(event=event)
				# can_expand_word called before indent and unindent

				# Reason is that before commit 5300449a75c4826
				# when completing with Tab word1_word2 at word1:
				# first, pressing Shift down to enter underscore '_'
				# then fast pressing Tab after that.

				# Now, Shift might still be pressed down
				# --> get: word1_ and unindent line but no completion

				# Want: indent, unindent one line (no selection) only when:
				# cursor_index <= idx_linestart

				# Solution
				# Tab-completion also with Shift-Tab,
				# which is intended to help tab-completing with slow/lazy fingers

				self.auto_update_syntax_continue()
				return 'break'

			# If at start of line: move line to match indent of previous line.
			elif indentation_level := self.tab_over_indent():
				self.text_widget.insert(tkinter.INSERT, indentation_level * '\t')

				self.auto_update_syntax_continue()
				return 'break'

			else:
				self.auto_update_syntax_continue()

				# Check if tab-completing outside screen, if so, don't insert tab
				if event.widget != self.expander.text_widget or not self.expander.state: return

				curline = self.text_widget.get("insert linestart", "insert lineend")
				curinsert = self.text_widget.index('insert')
				_, _, insert, line = self.expander.state

				# Don't insert tab
				if insert == curinsert and line == curline:
					self.ensure_idx_visibility('insert')
					return 'break'

				return


		try:
			startline = int(self.text_widget.index(tkinter.SEL_FIRST).split(sep='.')[0])
			endline = int(self.text_widget.index(tkinter.SEL_LAST).split(sep='.')[0])
			i = self.text_widget.index(tkinter.INSERT)


			if len(self.text_widget.tag_ranges('sel')) != 0:

				# Is start of selection not viewable?
				if not self.text_widget.bbox(tkinter.SEL_FIRST):

					self.wait_for(150)
					self.ensure_idx_visibility(tkinter.SEL_FIRST, back=4)
					self.wait_for(100)


			for linenum in range(startline, endline+1):
				self.text_widget.mark_set(tkinter.INSERT, '%s.0' % linenum)
				self.text_widget.insert(tkinter.INSERT, '\t')


			if startline == endline:
				self.text_widget.mark_set(tkinter.INSERT, '%s +1c' %i)

			elif self.text_widget.compare(tkinter.SEL_FIRST, '<', tkinter.INSERT):
				self.text_widget.mark_set(tkinter.INSERT, tkinter.SEL_FIRST)

			self.ensure_idx_visibility('insert', back=4)
			self.text_widget.edit_separator()

		except tkinter.TclError:
			pass


		self.auto_update_syntax_continue()

		return 'break'


	def unindent(self, event=None):
		if self.state in [ 'search', 'replace', 'replace_all', 'goto_def' ]:
			return 'break'

		self.auto_update_syntax_stop()


		if len(self.text_widget.tag_ranges('sel')) == 0:

			if self.can_expand_word(event=event):

				self.show_completions(event=event, back=True)

				# can_expand_word called before indent and unindent

				# Reason is that before commit 5300449a75c4826
				# when completing with Tab word1_word2 at word1:
				# first, pressing Shift down to enter underscore '_'
				# then fast pressing Tab after that.

				# Now, Shift might still be pressed down
				# --> get: word1_ and unindent line but no completion

				# Want: indent, unindent one line (no selection) only when:
				# cursor_index <= idx_linestart

				# Solution
				# Tab-completion also with Shift-Tab,
				# which is intended to help tab-completing with slow/lazy fingers

				self.auto_update_syntax_continue()
				return 'break'

			# Check if tab-completing outside screen, if so, don't insert tab
			elif event.widget == self.expander.text_widget and self.expander.state:

				curline = self.text_widget.get("insert linestart", "insert lineend")
				curinsert = self.text_widget.index('insert')
				_, _, insert, line = self.expander.state

				# Don't insert tab
				if insert == curinsert and line == curline:
					self.ensure_idx_visibility('insert')
					return 'break'


		try:
			# Unindenting curline only:
			if len(self.text_widget.tag_ranges('sel')) == 0:
				startline = int(self.text_widget.index(tkinter.INSERT).split(sep='.')[0])
				endline = startline

			else:
				startline = int(self.text_widget.index(tkinter.SEL_FIRST).split(sep='.')[0])
				endline = int(self.text_widget.index(tkinter.SEL_LAST).split(sep='.')[0])

			i = self.text_widget.index(tkinter.INSERT)

			# Check there is enough space in every line:
			flag_continue = True

			for linenum in range(startline, endline+1):
				tmp = self.text_widget.get('%s.0' % linenum, '%s.0 lineend' % linenum)

				# Check that every *non empty* line has tab-char at beginning of line
				if len(tmp) != 0 and tmp[0] != '\t':
					flag_continue = False
					break

			if flag_continue:

				if len(self.text_widget.tag_ranges('sel')) != 0:

					# Is start of selection not viewable?
					if not self.text_widget.bbox(tkinter.SEL_FIRST):

						self.wait_for(150)
						self.ensure_idx_visibility('insert', back=4)
						self.wait_for(100)


				for linenum in range(startline, endline+1):
					tmp = self.text_widget.get('%s.0' % linenum, '%s.0 lineend' % linenum)

					if len(tmp) != 0:
						if len(self.text_widget.tag_ranges('sel')) != 0:
							self.text_widget.mark_set(tkinter.INSERT, '%s.0' % linenum)
							self.text_widget.delete(tkinter.INSERT, '%s+%dc' % (tkinter.INSERT, 1))

						else:
							self.text_widget.delete( '%s.0' % linenum, '%s.0 +1c' % linenum)


				# Is selection made from down to top or from right to left?
				if len(self.text_widget.tag_ranges('sel')) != 0:

					if startline == endline:
						self.text_widget.mark_set(tkinter.INSERT, '%s -1c' %i)

					elif self.text_widget.compare(tkinter.SEL_FIRST, '<', tkinter.INSERT):
						self.text_widget.mark_set(tkinter.INSERT, tkinter.SEL_FIRST)

					# Is start of selection not viewable?
					if not self.text_widget.bbox(tkinter.SEL_FIRST):
						self.ensure_idx_visibility('insert', back=4)

				self.text_widget.edit_separator()

		except tkinter.TclError:
			pass


		self.auto_update_syntax_continue()

		return 'break'


	def comment(self, event=None):
		if self.state != 'normal':
			self.bell()
			return 'break'

		self.auto_update_syntax_stop()

		try:
			s = self.text_widget.index(tkinter.SEL_FIRST)
			e = self.text_widget.index(tkinter.SEL_LAST)

			startline,_ = self.get_line_col_as_int(index=s)
			startpos = self.text_widget.index( '%s -1l linestart' % s )

			endline,_ = self.get_line_col_as_int(index=e)
			endpos = self.text_widget.index( '%s +1l lineend' % e )

			for linenum in range(startline, endline+1):
				self.text_widget.insert('%d.0' % linenum, '##')

			if self.can_do_syntax():
				self.update_lineinfo()
				self.update_tokens(start=startpos, end=endpos)


		# No selection, comment curline
		except tkinter.TclError as e:
			startpos = self.text_widget.index( 'insert -1l linestart' )
			endpos = self.text_widget.index( 'insert +1l lineend' )
			self.text_widget.insert('%s linestart' % tkinter.INSERT, '##')

			if self.can_do_syntax():
				self.update_lineinfo()
				self.update_tokens(start=startpos, end=endpos)


		self.text_widget.edit_separator()
		self.auto_update_syntax_continue()

		return 'break'


	def uncomment(self, event=None):
		''' Should work even if there are uncommented lines between commented lines.
		'''

		if self.state != 'normal':
			self.bell()
			return 'break'

		idx_ins = self.text_widget.index(tkinter.INSERT)
		self.auto_update_syntax_stop()

		try:
			s = self.text_widget.index(tkinter.SEL_FIRST)
			e = self.text_widget.index(tkinter.SEL_LAST)

			startline,_ = self.get_line_col_as_int(index=s)
			endline,_ = self.get_line_col_as_int(index=e)
			startpos = self.text_widget.index('%s -1l linestart' % s)
			endpos = self.text_widget.index('%s +1l lineend' % e)
			changed = False


			for linenum in range(startline, endline+1):
				tmp = self.text_widget.get('%d.0' % linenum,'%d.0 lineend' % linenum)

				if tmp[:2] == '##':
					self.text_widget.delete('%d.0' % linenum,
						'%d.0 +2c' % linenum)

					changed = True


			if changed:
				if self.can_do_syntax():
					self.update_lineinfo()
					self.update_tokens(start=startpos, end=endpos)

				self.text_widget.edit_separator()


		# No selection, uncomment curline
		except tkinter.TclError as e:
			self.auto_update_syntax_continue()

			tmp = self.text_widget.get('%s linestart' % idx_ins,
				'%s lineend' % idx_ins)

			if tmp[:2] == '##':
				self.text_widget.delete('%s linestart' % idx_ins,
					'%s linestart +2c' % idx_ins)

				self.text_widget.edit_separator()


		self.auto_update_syntax_continue()

		return 'break'

########## Indent and Comment End
################ Elide Begin

	def get_safe_index(self, index='insert'):
		''' If at display lineend and line is not empty:

			Return index that is moved one char left,
			else: return index
		'''

		res = index
		left = '%s -1 display char' % index

		# Index is after(right) display linestart
		# Index is not before(left) from display lineend
		tests = [self.text_widget.compare( '%s display linestart' % index, '<', index),
				not self.text_widget.compare('%s display lineend' % index, '>', index)
				]


		if all(tests): res = left

		return self.text_widget.index(res)


	def line_is_elided(self, index='insert'):

		r = self.text_widget.tag_nextrange('elIdel', index)

		if len(r) > 0:
			# Is cursor at elided defline?
			if self.get_line_col_as_int(index=r[0])[0] == self.get_line_col_as_int(index=index)[0]:
				return r

		return False


	def elide_scope(self, event=None, index='insert'):
		''' Fold/Unfold function or class if cursor is at
			definition line
		'''
		if (not self.can_do_syntax()) or (self.state not in ['normal']):
			self.bell()
			return 'break'

		ref = self.text_widget.index(index)
		idx = self.get_safe_index(index)


		# Show scope
		if r := self.line_is_elided(idx):
			self.text_widget.tag_remove('sel', '1.0', tkinter.END)
			self.wait_for(50)

			# Protect cursor from being pushed down
			self.text_widget.mark_set('insert', idx)

			self.text_widget.tag_remove('elIdel', r[0], r[1])

		else:
			patt = r'%s get {%s linestart} {%s lineend}' \
					% (self.tcl_name_of_contents, idx, idx)

			try: line = self.text_widget.tk.eval(patt)
			except tkinter.TclError as err:
				print('INFO: elide_scope: ', err)

			if not self.line_is_defline(line):
				return 'break'

			# Hide scope
			pos = idx

			(scope_line, ind_defline,
			idx_scope_start) = self.get_scope_start(index=pos)

			idx_scope_end = self.get_scope_end(ind_defline, idx_scope_start)


			s = '%s lineend' % idx_scope_start
			e = idx_scope_end

			self.text_widget.tag_remove('sel', '1.0', tkinter.END)
			self.wait_for(50)

			# Protect cursor from being elided
			self.text_widget.mark_set('insert', idx)

			self.text_widget.tag_add('elIdel', s, e)


		# If cursor was at defline lineend, it was moved one char left,
		# put it back to lineend
		if self.text_widget.compare(idx, '!=', ref):
			# 	Q: Why not '%s lineend' % idx ?
			#
			# 	A:	s = '%s lineend' % idx_scope_start
			#		self.text_widget.tag_add('elIdel', s, e)
			#
			# That says, the first index inside elided text is:
			# 	'lineend' of definition line
			#
			# --> if cursor is put there, at 'lineend', it will be elided.
			# --> in a way it is correct to say that definition line has now no end.
			#		(the index is there but not visible)
			#
			# But lines always have 'display lineend', And putting cursor
			# there works.
			#
			# Q2: Were is cursor exactly if put there?
			# A2: with some repetition
			#	s = '%s lineend' % idx_scope_start
			#	e = idx_scope_end
			#
			#	self.text_widget.tag_add('elIdel', s, e)
			#
			# One has to think what is the first display index after elided
			# text. That is first index after 'e' and since one knows that
			# 'idx_scope_end' is 'lineend' of the last line of scope:
			#
			# --> cursor is there, since text-ranges excludes out ending index if
			# one remembers right, cursor is exactly at 'idx_scope_end'.
			#
			# Or more general, if elided part would end in the middle of line,
			# then, current line would be extended with rest of that remaining line.
			# Then if doing 'display lineend', cursor would just go to end of that line.


			self.text_widget.mark_set('insert', '%s display lineend' % idx)

		return 'break'


################ Elide End
################ Search Begin

	def search_next(self, event=None, back=False):
		'''	Search with selection from cursor position,
			show and select next/previous match.

			If there is no selection, search-word from
			last real search is used.

			Shortcut: Ctrl-np
		'''
		search_word = False
		using_selection = False

		if self.state == 'waiting':
			return 'break'

		elif self.state not in ['normal', 'error', 'help']:
			self.bell()
			return 'break'

		# No selection
		elif len(self.text_widget.tag_ranges('sel')) == 0:
			if self.old_word: search_word = self.old_word
			else:
				self.bell()
				return 'break'

		else:
			tmp = self.selection_get()

			# Allow one linebreak
			if 80 > len(tmp) > 0 and len(tmp.splitlines()) < 3:
				search_word = tmp
				using_selection = True

			# Too large selection
			else:
				self.bell()
				return 'break'


		# Info: search 'def search(' in module: tkinter
		# https://www.tcl.tk/man/tcl9.0/TkCmd/text.html#M147
		# Note: '-all' is needed in counting position among all matches
		search_args = [ self.tcl_name_of_contents, 'search', '-all',
						search_word, '1.0' ]
		try:
			res = self.tk.call(tuple(search_args))

		except tkinter.TclError as e:
			print(e)
			self.bell()
			return 'break'


		# If no match, res == '' --> False
		if not res:
			self.bell()
			return 'break'

		# Start-indexes of matches
		m = [ str(x) for x in res ]

		num_all_matches = len(m)

		if num_all_matches == 1 and using_selection:
			self.bell()
			return 'break'

		# Get current index among search matches
		if using_selection:
			start = self.text_widget.index(tkinter.SEL_FIRST)

		else:
			start = self.text_widget.search(search_word, 'insert')


		idx = m.index(start)
		# Get current index among search matches End

		# Next, get 'index among search matches' of next match,
		# or previous if searching backwards
		if not using_selection:
			if back: idx -= 1

		else:
			# Update index with limit check
			if back:
				if idx == 0:
					idx = len(m)
				idx -= 1

			else:
				if idx == len(m) - 1:
					idx = -1
				idx += 1


		# Start-index of search_word of next/previous match
		pos = m[idx]


		# Build info-message: "match idx/len(m)" etc.
		a = len(str(idx+1))
		b = len(str(len(m)))
		diff = b - a
		head = diff*' ' + f'{idx+1}/{len(m)} '

		scope = self.get_scope_path(pos)
		msg = head + scope
		######################


		wordlen = len(search_word)
		word_end = "%s + %dc" % (pos, wordlen)

		self.wait_for(33)
		self.text_widget.tag_remove('sel', '1.0', tkinter.END)
		self.text_widget.mark_set(self.anchorname, pos)
		self.wait_for(12)
		self.text_widget.tag_add('sel', pos, word_end)
		self.text_widget.mark_set('insert', word_end)

		# Is it not viewable?
		if not self.text_widget.bbox(pos):
			self.wait_for(100)
			self.ensure_idx_visibility(pos)

		self.show_message(msg, 1000)

		return 'break'


	def show_next(self, event=None):
		''' Note: side-effect, alters insert-mark
				self.text_widget.mark_set('insert')
		'''

		if self.state not in [ 'search', 'replace', 'replace_all' ]:
			return

		# self.search_index is int telling: on what match-mark focus is now at.
		# If self.search_index == 2, then focus is at mark named 'match2' etc.

		# idx counts from 0 until at next match-mark. One can not just iterate marks
		# and get idx from mark-name because marks get 'deleted' if replacing.
		# --> 'match2' is not necessarily second (or whatever) in list.

		# idx is used to get current index position among all current matches.
		# For example: If now have 10 matches left,
		# and last position was 1/11, but then one match got replaced,
		# so focus is now at 1/10 and after this show_next-call it should be at 2/10.

		# self.mark_indexes is list holding ints of still remaining match-marks.
		# These ints are sorted from small to big.


		idx = 0
		for index in self.mark_indexes:
			idx += 1

			if index > self.search_index:
				self.search_index = index

				break

		# There was no bigger int in list:
		# --> focus is at last match, or at last match that was replaced.
		# --> Wrap focus to first match-mark.
		else:
			idx = 1
			self.search_index = self.mark_indexes[0]


		mark_name = 'match%d' % self.search_index

		self.text_widget.tag_remove('focus', '1.0', tkinter.END)

		# match-mark marks start of the match
		start = mark_name


		# Make zero lenght matches visible
		if 'match_zero_lenght' in self.text_widget.tag_names(start):
			end = '%s +1c' % mark_name

		else:
			end = '%s +%dc' % ( mark_name, self.match_lenghts[self.search_index] )

		# self.search_focus is range of focus-tag.
		self.search_focus = (start, end)

		# idx: int
		# start: tkinter.Text -index
		#t0 = int(self.root.tk.eval('clock milliseconds'))
		self.handle_search_entry(idx, start)
		#t1 = int(self.root.tk.eval('clock milliseconds'))
		#print(t1-t0, 'ms')

		# Is it not viewable?
		if not self.text_widget.bbox(start):
			self.wait_for(100)

		self.ensure_idx_visibility(start)


		# Until next line of code explanation for
		# Intention: use goto_def while searching/replacing

		# This need to be 'end', so that in goto_def(), one could use 'insert'
		# as base-index 'p' to get word_at_cursor.
		# Now when that is possible, it enables the following:
		#
		# While searching, one can click a function name, other than on match,
		# (clicking sets new 'insert' -position to that position clicked)
		# and press Alt-g to get there.
		#
		# Or just press Alt-g while on match to get that function definition
		# if searching for function.
		# (this works because 'insert' is set here correctly)
		# Before, this was done in goto_def by checking if state was 'search'
		# and then using self.search_focus[1] as base-index 'p'
		self.text_widget.mark_set('insert', end)


		if self.entry.flag_start:
			if self.state == 'search':
				self.wait_for(100)
				bg, fg = self.themes[self.curtheme]['match'][:]
				self.text_widget.tag_config('match', background=bg, foreground=fg)
			self.wait_for(200)
			self.entry.flag_start = False


		self.message_frame2.place_forget()

		# Change color
		# self.search_focus is range of focus-tag.
		self.text_widget.tag_add('focus', self.search_focus[0], self.search_focus[1])



		self.entry.config(validate='key')

		if self.search_matches == 1:
			self.bind("<Control-n>", self.do_nothing)
			self.bind("<Control-p>", self.do_nothing)


		self.entry.xview_moveto(0)

		return 'break'


	def show_prev(self, event=None):
		''' Note: side-effect, alters insert-mark
				self.text_widget.mark_set('insert')
		'''


		if self.state not in [ 'search', 'replace', 'replace_all' ]:
			return

		# self.search_index is int telling: on what match-mark focus is now at.
		# If self.search_index == 2, then focus is at mark named 'match2' etc.

		# idx counts down from len(self.mark_indexes) until at previous match-mark.
		# One can not just iterate marks
		# and get idx from mark-name because marks get 'deleted' if replacing.
		# --> 'match2' is not necessarily second (or whatever) in list.

		# idx is used to get current index position among all current matches.
		# For example: If now have 10 matches left,
		# and last position was 3/11, but then one match got replaced,
		# so focus could now be at say: 2/10 and after this show_prev-call it should be at 1/10.

		# self.mark_indexes is list holding ints of still remaining match-marks.
		# These ints are sorted from small to big.

		idx = len(self.mark_indexes) + 1
		for index in self.mark_indexes[::-1]:
			idx -= 1

			if index < self.search_index:
				self.search_index = index

				break

		# There was no smaller int in list:
		# --> focus is at first match, or at first match that was replaced.
		# --> Wrap focus to last match-mark.
		else:
			idx = len(self.mark_indexes)
			self.search_index = self.mark_indexes[-1]


		mark_name = 'match%d' % self.search_index

		self.text_widget.tag_remove('focus', '1.0', tkinter.END)

		# match-mark marks start of the match
		start = mark_name


		# Make zero lenght matches visible
		if 'match_zero_lenght' in self.text_widget.tag_names(start):
			end = '%s +1c' % mark_name

		else:
			end = '%s +%dc' % ( mark_name, self.match_lenghts[self.search_index] )

		# self.search_focus is range of focus-tag.
		self.search_focus = (start, end)


		# idx: int
		# start: tkinter.Text -index
		self.handle_search_entry(idx, start)

		# Is it not viewable?
		if not self.text_widget.bbox(start):
			self.wait_for(100)

		self.ensure_idx_visibility(start)


		# Until next line of code explanation for
		# Intention: use goto_def while searching/replacing

		# This need to be 'end', so that in goto_def(), one could use 'insert'
		# as base-index 'p' to get word_at_cursor.
		# Now when that is possible, it enables the following:
		#
		# While searching, one can click a function name, other than on match,
		# (clicking sets new 'insert' -position to that position clicked)
		# and press Alt-g to get there.
		#
		# Or just press Alt-g while on match to get that function definition
		# if searching for function.
		# (this works because 'insert' is set here correctly)
		# Before, this was done in goto_def by checking if state was 'search'
		# and then using self.search_focus[1] as base-index 'p'
		self.text_widget.mark_set('insert', end)

		if self.entry.flag_start:
			if self.state == 'search':
				self.wait_for(100)
				bg, fg = self.themes[self.curtheme]['match'][:]
				self.text_widget.tag_config('match', background=bg, foreground=fg)
			self.wait_for(200)
			self.entry.flag_start = False


		self.message_frame2.place_forget()

		# Change color
		# self.search_focus is range of focus-tag.
		self.text_widget.tag_add('focus', self.search_focus[0], self.search_focus[1])

		self.entry.config(validate='key')


		if self.search_matches == 1:
			self.bind("<Control-n>", self.do_nothing)
			self.bind("<Control-p>", self.do_nothing)


		self.entry.xview_moveto(0)

		return 'break'


	def search_setting_reset(self):

		defaults = [
				'search',
				'-all',
				'-count',
				self.match_lenghts_var
				]

		self.search_settings = defaults
		self.search_starts_at = '1.0'
		self.search_ends_at = False


	def search_setting_print(self):

		if not self.search_settings:
			self.search_setting_reset()

		print(
			self.search_settings[4:],
			'\n'
			'start:', self.search_starts_at,
			'\n'
			'end:', self.search_ends_at
			)


	def search_help_print(self):

		helptxt = r'''
Search-options

-backwards
The search will proceed backward through the text, finding the matching range
closest to index whose first character is before index (it is not allowed to be at index).
Note that, for a variety of reasons, backwards searches can be substantially slower
than forwards searches (particularly when using -regexp), so it is recommended that
performance-critical code use forward searches.

-regexp
Treat pattern as a regular expression and match it against the text using the
rules for regular expressions (see the regexp command and the re_syntax page for details).
The default matching automatically passes both the -lineanchor and -linestop options
to the regexp engine (unless -nolinestop is used), so that ^$ match beginning and
end of line, and ., [^ sequences will never match the newline character \n.

-nolinestop
This allows . and [^ sequences to match the newline character \n, which they will
otherwise not do (see the regexp command for details). This option is only meaningful
if -regexp is also given, and error will be thrown otherwise. For example, to
match the entire text, use "-nolinestop -regexp" as search setting
and ".*" as search word.

-nocase
Ignore case differences between the pattern and the text.

-overlap
The normal behaviour is that matches which overlap
an already-found match will not be returned. This switch changes that behaviour so that
all matches which are not totally enclosed within another match are returned. For example,
doing -overlap search with pattern “\w+” against “hello there” will just match
twice (same as without -overlap), but matching “B[a-z]+B” against “BooBooBoo” will
now match twice.
Replacing is disabled while this setting is on. Searching works.
Consider this using only -regexp and no -overlap:
If have string ABABABABA, where boundary is A and contents is B and
want change contents B: use regexp B(?=A) to match contents.
(It also matches BBA etc, so check every match --> don't use replace_all)
To change boundary A, search for A.

-strictlimits
When performing any search, the normal behaviour is that the start and stop limits
are checked with respect to the start of the matching text. With the -strictlimits flag,
the entire matching range must lie inside the start and stop limits specified
for the match to be valid.

-elide
Find elided (hidden) text as well. By default only displayed text is searched.

If stopIndex is specified, the search stops at that index: for forward searches,
no match at or after stopIndex will be considered; for backward searches, no match
earlier in the text than stopIndex will be considered. If stopIndex is omitted,
the entire text will be searched: when the beginning or end of the text is reached,
the search continues at the other end until the starting location is reached again;
if stopIndex is specified, no wrap-around will occur. This means that, for example,
if the search is -forwards but stopIndex is earlier in the text than startIndex,
nothing will ever be found.

https://www.tcl.tk/man/tcl9.0/TkCmd/text.html#M147

		'''

		print(helptxt)


	def search_setting_edit(self, search_setting):
		''' search_setting is string of options below separated by spaces.

			If also setting -start and -end:
			-start and -end must be last, and -start before -end.
			If -end is given, also -start must have been given.

			When both -start and -end is given:
			If search is not -backwards: -start-index must be such that, it is before
			-end-index in contents. If search is -backwards: -start-index must be such
			that, it is after -end-index in contents.

			If want to search all content, it is safest always to give only -start
			so that search would wrap at fileends. If no -start is given, old
			indexes are used. If only -start is given, old -end-index is deleted.


			Special indexes:
			(note that there is no index called 'start'):
			filestart: 1.0
			fileend: end
			insertion cursor: insert


			Example1, use regexp and old indexes:

				search_setting_edit( '-regexp' )


			Example2, search backwards, give start-index if not sure what were old ones:

				search_setting_edit( '-backwards -start end' )


			Example3, use regexp, include elided text, search only from cursor to fileend:

				my_settings = "-regexp -elide -start insert -end end"

				search_setting_edit( my_settings )


			Example4, exact(==default==not regexp) search, backwards from cursor to 50 lines up:

				my_settings = "-backwards -start insert -end insert -50 lines"


			Options:
			-backwards
			-regexp
			-nocase
			-overlap
			-nolinestop
			-strictlimits
			-elide
			-start	idx
			-end	idx


			Replacing does not work while -overlap -setting is on. Searching works.

			More help about these options:
			search_help_print()

			Print current search settings:
			search_setting_print()

			Reset search settings:
			search_setting_reset()

			https://www.tcl.tk/man/tcl9.0/TkCmd/text.html#M147
		'''

		if not self.search_settings:
			self.search_setting_reset()


		defaults = [
				'search',
				'-all',
				'-count',
				self.match_lenghts_var,
				]

		settings = defaults[:]
		user_options = search_setting.split()


		options = [
			'-backwards',
			'-regexp',
			'-nocase',
			'-overlap',
			'-nolinestop',
			'-strictlimits',
			'-elide'
			]


		for option in user_options:
			if option in options:
				settings.append(option)


		search_start_idx = self.search_starts_at
		search_end_idx = self.search_ends_at


		if '-start' in user_options:
			idx_start = user_options.index('-start') + 1

			if len(user_options) > idx_start:

				# Also changing StopIndex part1
				if '-end' in user_options[idx_start:]:
					idx_end = user_options.index('-end')
					search_start_idx = user_options[idx_start:idx_end]

				# Changing only StartIndex
				else:
					search_start_idx = user_options[idx_start:]

				# Also changing StopIndex part2
				if '-end' in user_options:
					idx_start = user_options.index('-end') + 1

					if len(user_options) > idx_start:
						search_end_idx = user_options[idx_start:]


		# With s = settings one gets reference to original list.
		# If want copy(dont want to mess original), and one likely does, one writes:
		s = settings[:]
		# Because tabs have their own text-widgets, which act as tcl-command,
		# tcl-name of current widget/command is added here.
		# See Tcl/Tk -literature for more info about this
		s.insert(0, self.tcl_name_of_contents)
		s.append( '--' )
		tmp = self.text_widget.get('1.0', '1.1')

		flag = False
		if not tmp:
			self.text_widget.insert('1.0', 'A')
			tmp = 'A'
			flag = True

		s.append(tmp)

		if not '-backwards' in user_options:
			s.append('1.0')
			s.append('1.0 lineend')
		else:
			s.append('1.0 lineend')
			s.append('1.0')


		try:
			res = self.tk.call(tuple(s))

			self.search_settings = settings

			# Start changed
			if type(search_start_idx) == list:
				if tmp := ' '.join(x for x in search_start_idx):
					self.search_starts_at = tmp

					# End changed
					if type(search_end_idx) == list:
						if tmp := ' '.join(x for x in search_end_idx):
							self.search_ends_at = tmp

					# Start changed but End not changed
					else: self.search_ends_at = False

		except tkinter.TclError as e:
			print(e)


		if flag: self.text_widget.delete('1.0', '1.1')

		#### search_setting_edit End ##############

	#@debug
	def do_search(self, search_word):
		''' Search contents for search_word
			with self.search_settings and tk text search
			https://www.tcl.tk/man/tcl9.0/TkCmd/text.html#M147

			returns number of search matches

			if at least one match:
				tags 'match' with list match_ranges

			called from start_search()
		'''

		def handle_search_start():
			''' When search-setting: -start == 'insert' and search_word == selection_get:
				ensure search starts from selection.
			'''

			if self.search_starts_at == 'insert':
				have_selection = len(self.text_widget.tag_ranges('sel')) > 0
				if have_selection:
					tmp = self.selection_get()
					if tmp == search_word:
						if '-backwards' not in self.search_settings:
							idx_sel_start = self.text_widget.index(tkinter.SEL_FIRST)
							return idx_sel_start
						else:
							idx_sel_end = self.text_widget.index(tkinter.SEL_LAST)
							return idx_sel_end
			# else:
			return self.search_starts_at
			##############################


		s = self.search_settings[:]
		# Because tabs have their own text-widgets, which act as tcl-command,
		# tcl-name of current widget/command is added here.
		# See Tcl/Tk -literature for more info about this
		s.insert(0, self.tcl_name_of_contents)
		s.append( '--' )
		s.append(search_word)
		s.append( handle_search_start() )
		if self.search_ends_at: s.append(self.search_ends_at)
		try:
			res = self.tk.call(tuple(s))
		except tkinter.TclError as e:
			self.bell()
			print('INFO: do_search:', e)
			return False

		if not res: return False

		start_indexes = [ str(x) for x in res ]


		# s holds lenghts of matches
		# lenghts can vary
		s = eval( self.match_lenghts_var.get() )
		# eval( '(8, 8, 8, 8)' )  -->  (8, 8, 8, 8)

		# With list one can deal with single matches (single tuples):
		# (8,) --> [8]
		s = self.match_lenghts = list(s)

		# self.search_matches
		num_matches = len(start_indexes)

		if not num_matches: return False



		for mark in self.text_widget.mark_names():
			if 'match' in mark:
				self.text_widget.mark_unset(mark)

		match_ranges = list()
		match_zero_ranges = list()
		self.mark_indexes = list()

		# Tag matches, add mark to start of every match
		for i in range( len(start_indexes) ):

			mark_name = 'match%d' % i
			start_idx = start_indexes[i]
			self.text_widget.mark_set(mark_name, start_idx)
			self.mark_indexes.append(i)

			match_lenght = s[i]

			# Used in making zero lenght matches visible
			if match_lenght == 0 and 'elIdel' not in self.text_widget.tag_names(start_idx):
				end_idx = '%s +1c' % start_idx
				match_zero_ranges.append(mark_name)
				match_zero_ranges.append(end_idx)

			else:
				end_idx = '%s +%dc' % (mark_name, match_lenght)


			match_ranges.append(mark_name)
			match_ranges.append(end_idx)


		self.text_widget.tag_add('match', *match_ranges)
		if len(match_zero_ranges) > 0:
			self.text_widget.tag_add('match_zero_lenght', *match_zero_ranges)

		return num_matches


	def start_search(self, event=None):

		# Get stuff after prompt
		tmp_orig = self.entry.get()

		idx = tmp_orig.index(':') + 2
		tmp = tmp_orig[idx:]

		if len(tmp) == 0:
			self.bell()
			return 'break'

		search_word = tmp


		self.text_widget.tag_remove('match', '1.0', tkinter.END)
		self.text_widget.tag_remove('focus', '1.0', tkinter.END)
		self.text_widget.tag_config('match', background='', foreground='')

		self.search_matches = self.do_search(search_word)
		# 'match' is tagged in do_search()


		if self.search_matches > 0:

			self.search_index = -1
			self.old_word = search_word

			# search_history_walk
			if not self.flag_appended_tmp_word_to_search_history:
				if self.old_word not in self.search_history[0]:
					self.search_history[0].append(self.old_word)

			self.flag_appended_tmp_word_to_search_history = False


			self.bind("<Button-%i>" % self.right_mousebutton_num, self.do_nothing)
			self.entry.config(validate='none')


			if self.state == 'search':

				self.bid_show_next = self.bind("<Control-n>", self.show_next )
				self.bid_show_prev = self.bind("<Control-p>", self.show_prev )
				self.entry.flag_start = True
				self.search_history_index = len(self.search_history[0])
				self.flag_use_replace_history = False

				self.text_widget.focus_set()
				self.wait_for(100)
				#print(self.search_matches)
				self.show_next()


			else:
				patt = 'Replace %s matches with: ' % str(self.search_matches)
				idx = tmp_orig.index(':') + 2
				self.entry.delete(0, idx)
				self.entry.insert(0, patt)

				self.entry.select_from(len(patt))
				self.entry.select_to(tkinter.END)
				self.entry.icursor(len(patt))
				self.entry.xview_moveto(0)

				self.search_history_index = len(self.search_history[1])
				self.flag_use_replace_history = True


				bg, fg = self.themes[self.curtheme]['match'][:]
				self.text_widget.tag_config('match', background=bg, foreground=fg)


				self.entry.bind("<Return>", self.start_replace)
				self.entry.focus_set()
				self.entry.config(validate='key')

		else:
			self.bell()
			bg, fg = self.themes[self.curtheme]['match'][:]
			self.text_widget.tag_config('match', background=bg, foreground=fg)
			self.bind("<Control-n>", self.do_nothing)
			self.bind("<Control-p>", self.do_nothing)



		return 'break'


	def cursor_frame_init(self):
		''' Mark insertion cursor while text_widget is disabled
		'''
		self.cursor_frame = tkinter.Frame(self)
		self.cursor_frame.place_configure(x=30, y=30, width=1, height=1)
		self.cursor_frame.place_forget()


	def cursor_frame_set(self, event=None):
		''' Mark insertion cursor while text_widget is disabled
			Helps seeing cursor position
		'''

		self.wait_for(30)
		if event.widget != self.text_widget: return

		bg, fg = self.themes[self.curtheme]['sel'][:]
		self.cursor_frame.config(bg=bg)
		self.cursor_frame.place_forget()

		# Why _ inplace of w: bbox-width can be
		# for example, in case of empty line, lenght of whole line
		# and don't want so wide cursor
		x, y, _, h = self.text_widget.bbox('current')

		idx_ins = self.text_widget.index('insert') # real index of insert
		idx = self.text_widget.index('@%d,%d' % (x, y) )
		#print(idx_cur, idx)

		# These are offsets of text_widget, relative to root.
		# They have to be added, because cursor_frame is in root
		offset_x = self.ln_widget.winfo_width()
		if self.want_ln == 0: offset_x = 0
		offset_y = self.entry.winfo_height()

		w = self.pad -1
		x = x + offset_x
		y = y + offset_y

		# Sometimes this happens, like when clicking at linestart:
		# 'insert'-index is one char greater than what is about to be marked
		if self.text_widget.compare(idx_ins, '>', idx):
			prev_bbox_w = self.text_widget.bbox('%s -1c' % idx_ins)[2]
			# This fixes it
			x = x + prev_bbox_w

		self.cursor_frame.place_configure(x=x, y=y, width=w, height=h)

		return


	def update_curpos(self, event=None, on_stop=None):
		''' on_stop: function to be executed on doubleclick
		'''

		self.save_pos = self.text_widget.index(tkinter.INSERT)

		on_stop()

		return 'break'


	def search_history_remove_duplicates(self):
		for i in (0,1):
			for item in self.search_history[i][:]:
				num_items = self.search_history[i].count(item)
				while num_items > 1:
					# Leave first item
					idx0 = self.search_history[i].index(item)
					idx = self.search_history[i].index(item, idx0+1)
					self.search_history[i].pop(idx)
					num_items = self.search_history[i].count(item)

	#@debug
	def search_history_walk(self, event=None, direction='up'):
		''' Walk search-history in entry with arrow up/down
			while searching/replacing
		'''

		is_replace_history = x = 0
		if self.flag_use_replace_history:
			x = 1

		index = self.search_history_index
		h = self.search_history

		if len(h[x]) == 0: return 'break'


		# Get history item
		if direction == 'up':
			index -= 1

			if index < 0:
				index += 1
				return 'break'
		else:
			index += 1

			if index > len(h[x]) -1:
				index -= 1
				return 'break'


		# Update self.search_history_index
		self.search_history_index = index
		history_item = h[x][index]


		# Get prompt-lenght and remove text after it
		self.entry.config(validate='none')
		tmp_orig = self.entry.get()
		idx = tmp_orig.index(':') + 2
		self.entry.delete(idx, 'end')

		# Insert and select history_item
		self.entry.insert(idx, history_item)

		self.entry.select_from(idx)
		self.entry.select_to('end')
		self.entry.icursor(idx)
		self.entry.xview_moveto(0)

		self.entry.config(validate='key')

		return 'break'


	def clear_search_tags(self, event=None):
		if self.state != 'normal':
			return 'break'

		self.text_widget.tag_remove('replaced', '1.0', tkinter.END)
		self.bind("<Escape>", self.esc_override)


	def stop_search(self, event=None):
		if self.state == 'waiting':
			return 'break'

		self.text_widget.config(state='normal')
		self.entry.config(state='normal')
		self.btn_open.config(state='normal')
		self.btn_save.config(state='normal')
		self.bind("<Button-%i>" % self.right_mousebutton_num,
			lambda event: self.popup_raise(event))

		#self.wait_for(200)
		self.text_widget.tag_remove('focus', '1.0', tkinter.END)
		self.text_widget.tag_remove('match', '1.0', tkinter.END)
		self.text_widget.tag_remove('match_zero_lenght', '1.0', tkinter.END)
		self.text_widget.tag_remove('sel', '1.0', tkinter.END)

		self.cursor_frame.place_forget()


		# Leave marks on replaced areas, Esc clears.
		if len(self.text_widget.tag_ranges('replaced')) > 0:
			self.bind("<Escape>", self.clear_search_tags)
		else:
			self.bind("<Escape>", self.esc_override)


		self.entry.config(validate='none')


		self.entry.bid_ret = self.entry.bind("<Return>", self.load)
		self.entry.delete(0, tkinter.END)

		curtab = self.tabs[self.tabindex]

		if curtab.filepath:
			self.entry.insert(0, curtab.filepath)
			self.entry.xview_moveto(1.0)


		# Set cursor pos
		try:
			if self.save_pos:

				# Unfinished replace_all call
				if self.state == 'replace_all' and len(self.mark_indexes) != 0:
					self.save_pos = ''
					# This will pass until focus_set
					pass

				line = self.save_pos
				curtab.position = line
				self.save_pos = ''
			else:
				line = curtab.position

			self.text_widget.focus_set()
			self.text_widget.mark_set('insert', line)

		except tkinter.TclError:
			curtab.position = self.text_widget.index(tkinter.INSERT)


		# Help enabling: "exit to goto_def func with space" while searching
		# This has to be after: Set cursor pos
		self.goto_def_pos = False

		self.new_word = ''
		self.search_matches = 0
		flag_all = False


		if self.state in ['replace_all']:
			flag_all = True
			if self.can_do_syntax():
				self.update_lineinfo()
				self.insert_tokens(self.get_tokens(curtab, update=True))


		self.auto_update_syntax_continue()


		self.state = 'normal'


		if self.bid_show_next:
			self.unbind( "<Control-n>", funcid=self.bid_show_next )
			self.unbind( "<Control-p>", funcid=self.bid_show_prev )
			self.bid_show_next = None
			self.bid_show_prev = None

		self.text_widget.unbind( "<Control-n>", funcid=self.bid1 )
		self.text_widget.unbind( "<Control-p>", funcid=self.bid2 )
		self.text_widget.unbind( "<Double-Button-1>", funcid=self.bid3 )
		self.unbind( "<Button-1>", funcid=self.bid_mouse)

		# Space is on hold for extra 200ms, released below
		self.text_widget.unbind( "<space>", funcid=self.bid4 )
		bid_tmp = self.text_widget.bind( "<space>", self.do_nothing_without_bell)


		self.text_widget.bind( "<Control-n>", self.search_next)
		self.text_widget.bind( "<Control-p>",
				lambda event: self.search_next(event, **{'back':True}) )

		self.text_widget.bind("<Return>", self.return_override)
		self.entry.bind("<Control-n>", self.do_nothing_without_bell)
		self.entry.bind("<Control-p>", self.do_nothing_without_bell)


		self.entry.unbind("<Up>", funcid=self.bidup )
		self.entry.unbind("<Down>", funcid=self.biddown )
		if self.flag_appended_tmp_word_to_search_history:
			self.flag_appended_tmp_word_to_search_history = False
			self.search_history[0].pop()

		self.bind( "<Return>", self.do_nothing_without_bell)


		if not flag_all: self.ensure_idx_visibility(line)

		# Possible gotodef_banner
		self.message_frame2.place_forget()

		# Release space
		self.wait_for(200)
		self.search_history_remove_duplicates()
		self.text_widget.unbind( "<space>", funcid=bid_tmp )
		curtab.bid_space = self.text_widget.bind( "<space>", self.space_override)

		return 'break'

		### stop_search End ######


	def toggle_search_setting_regexp(self, event=None):
		''' self.search_settings is a list
		'''
		if self.state not in ['search', 'replace_all', 'replace']: return 'break'

		my_settings = "-regexp"
		if my_settings not in self.search_settings:
			self.search_settings.insert(4, my_settings)
			self.show_message('Regexp ON', 1000)
		else:
			idx = self.search_settings.index(my_settings)
			self.search_settings.pop(idx)
			self.show_message('Regexp OFF', 1000)

		return 'break'


	def toggle_search_setting_starts_from_insert(self, event=None):
		if self.state not in ['search', 'replace_all', 'replace']: return 'break'

		if self.search_starts_at == 'insert':
			self.search_starts_at = '1.0'
			self.show_message('From: START', 1000)
		else:
			self.search_starts_at = 'insert'
			self.show_message('From: INSERT', 1000)

		self.search_ends_at = False

		return 'break'


	def search(self, event=None):
		'''	Ctrl-f --> search --> start_search --> show_next / show_prev --> stop_search
		'''

		if self.state not in ['normal']:
			self.bell()
			return 'break'

		if not self.search_settings:
			self.search_setting_reset()

		# Save cursor pos
		try:
			self.tabs[self.tabindex].position = self.text_widget.index(tkinter.INSERT)

		except tkinter.TclError:
			pass


		self.state = 'search'
		self.btn_open.config(state='disabled')
		self.btn_save.config(state='disabled')

		self.bidup = self.entry.bind("<Up>", func=lambda event: self.search_history_walk(event, **{'direction':'up'}), add=True )
		self.biddown = self.entry.bind("<Down>", func=lambda event: self.search_history_walk(event, **{'direction':'down'}), add=True )

		self.entry.unbind("<Return>", funcid=self.entry.bid_ret)
		self.entry.bind("<Return>", self.start_search)
		self.bind("<Escape>", self.stop_search)

		self.bid1 = self.text_widget.bind("<Control-n>", func=self.skip_bindlevel )
		self.bid2 = self.text_widget.bind("<Control-p>", func=self.skip_bindlevel )
		self.entry.bind("<Control-n>", self.skip_bindlevel)
		self.entry.bind("<Control-p>", self.skip_bindlevel)
		self.bid_show_next = None
		self.bid_show_prev = None

		# Show 'insertion cursor' while text_widget is disabled
		self.bid_mouse = self.bind( "<Button-1>", func=self.cursor_frame_set, add=True)

		self.bid3 = self.text_widget.bind("<Double-Button-1>",
			func=lambda event: self.update_curpos(event, **{'on_stop':self.stop_search}),
				add=True )

		self.text_widget.unbind( "<space>", funcid=self.tabs[self.tabindex].bid_space )
		self.bid4 = self.text_widget.bind( "<space>", self.space_override )

		self.entry.delete(0, tkinter.END)


		tmp = False
		self.flag_appended_tmp_word_to_search_history = False
		# Suggest selection as search_word if appropiate, else old_word.
		try:
			tmp = self.selection_get()

			# Allow one linebreak
			if not (80 > len(tmp) > 0 and len(tmp.splitlines()) < 3):
				tmp = False
				raise tkinter.TclError

			self.search_history[0].append(tmp) ####
			self.flag_appended_tmp_word_to_search_history = True


		# No selection
		except tkinter.TclError:
			tmp = self.old_word


		if tmp:
			self.entry.insert(tkinter.END, tmp)
			self.entry.xview_moveto(1.0)
			self.entry.select_to(tkinter.END)
			self.entry.icursor(tkinter.END)


		# search_history_walk
		self.search_history_index = len(self.search_history[0]) -1 ###
		self.flag_use_replace_history = False

		self.text_widget.tag_remove('sel', '1.0', tkinter.END)
		patt = 'Search: '
		self.entry.insert(0, patt)
		self.entry.config(validate='key', validatecommand=self.validate_search)

		self.text_widget.config(state='disabled')
		self.entry.focus_set()

		return 'break'


	def do_validate_search(self, i, s, S):
		'''	i is index of action,
			s is string before action,
			S is new string to be validated
		'''

		idx = s.index(':') + 2

		if int(i) < idx:
			self.entry.selection_clear()
			self.entry.icursor(idx)

			return S == ''

		else:
			return True

################ Search End
################ Replace Begin

	def replace(self, event=None, state='replace'):
		'''	Ctrl-r --> replace --> start_search --> start_replace
			--> show_next / show_prev / do_single_replace --> stop_search
		'''

		if not self.search_settings:
			self.search_setting_reset()

		if self.state != 'normal':
			self.bell()
			return 'break'

		elif '-overlap' in self.search_settings:
			self.wait_for(100)
			print('\nError: Can not replace while "-overlap" in search_settings')
			self.bell()
			return 'break'


		# Save cursor pos
		try:
			self.tabs[self.tabindex].position = self.text_widget.index(tkinter.INSERT)
			if state == 'replace_all':
				self.save_pos = self.text_widget.index(tkinter.INSERT)

		except tkinter.TclError:
			pass

		self.state = state
		self.btn_open.config(state='disabled')
		self.btn_save.config(state='disabled')

		self.bidup = self.entry.bind("<Up>", func=lambda event: self.search_history_walk(event, **{'direction':'up'}), add=True )
		self.biddown = self.entry.bind("<Down>", func=lambda event: self.search_history_walk(event, **{'direction':'down'}), add=True )

		self.entry.unbind("<Return>", funcid=self.entry.bid_ret)
		self.entry.bind("<Return>", self.start_search)
		self.bind("<Escape>", self.stop_search)
		self.bid1 = self.text_widget.bind("<Control-n>", func=self.skip_bindlevel )
		self.bid2 = self.text_widget.bind("<Control-p>", func=self.skip_bindlevel )
		self.entry.bind("<Control-n>", self.skip_bindlevel)
		self.entry.bind("<Control-p>", self.skip_bindlevel)
		self.bid_show_next = None
		self.bid_show_prev = None

		# Show 'insertion cursor' while text_widget is disabled
		self.bid_mouse = self.bind( "<Button-1>", func=self.cursor_frame_set, add=True)

		self.bid3 = self.text_widget.bind("<Double-Button-1>",
			func=lambda event: self.update_curpos(event, **{'on_stop':self.stop_search}),
				add=True )

		self.text_widget.unbind( "<space>", funcid=self.tabs[self.tabindex].bid_space )
		self.bid4 = self.text_widget.bind("<space>", func=self.space_override )


		self.entry.delete(0, tkinter.END)


		tmp = False
		self.flag_appended_tmp_word_to_search_history = False
		# Suggest selection as search_word if appropiate, else old_word.
		try:
			tmp = self.selection_get()
			if not (80 > len(tmp) > 0):
				tmp = False
				raise tkinter.TclError

			self.search_history[0].append(tmp) ####
			self.flag_appended_tmp_word_to_search_history = True


		# No selection
		except tkinter.TclError:
			tmp = self.old_word


		if tmp:
			self.entry.insert(tkinter.END, tmp)
			self.entry.xview_moveto(1.0)
			self.entry.select_to(tkinter.END)
			self.entry.icursor(tkinter.END)


		# search_history_walk, want search_words here
		self.search_history_index = len(self.search_history[0])
		self.flag_use_replace_history = False

		patt = 'Replace this: '
		self.entry.insert(0, patt)
		self.entry.config(validate='key', validatecommand=self.validate_search)

		self.wait_for(400)
		self.text_widget.tag_remove('replaced', '1.0', tkinter.END)

		self.text_widget.config(state='disabled')
		self.entry.focus_set()
		return 'break'


	def replace_all(self, event=None):

		if not self.search_settings:
			self.search_setting_reset()

		if self.state != 'normal':
			self.bell()
			return 'break'

		elif '-overlap' in self.search_settings:
			self.wait_for(100)
			print('\nError: Can not replace_all while "-overlap" in search_settings')
			self.bell()
			return 'break'


		self.replace(event, state='replace_all')

	#@debug
	def do_single_replace(self, event=None):

		# Enable changing newword between replaces Begin
		#################
		# Get stuff after prompt
		tmp_orig = self.entry.get()
		idx = tmp_orig.index(':') + 2
		tmp = tmp_orig[idx:]

		# Replacement-string has changed
		if tmp != self.new_word:

			# Not allowed to do this:
			if tmp == self.old_word:

				self.wait_for(100)
				self.bell()
				self.wait_for(100)
				self.entry.config(validate='none')
				self.entry.delete(idx, tkinter.END)

				self.wait_for(200)
				self.entry.insert(tkinter.END, self.new_word)
				self.entry.config(validate='key')

				return 'break'

			else:
				self.new_word = tmp

				# search_history_walk
				if self.new_word not in self.search_history[1]:
					self.search_history[1].append(self.new_word)
				self.search_history_index = len(self.search_history[1])
				self.flag_use_replace_history = True

		# Enable changing newword between replaces End
		#################



		# Apply normal 'Replace and proceed to next by pressing Return' -behaviour.
		# If last replace was done by pressing Return, there is currently no focus-tag.
		# Check this and get focus-tag with show_next() if this is the case, and break.
		# This means that the actual replacing happens only when have focus-tag.
		c = self.text_widget.tag_nextrange('focus', 1.0)

		if not len(c) > 0:
			self.show_next()
			return 'break'



		# Start of actual replacing
		self.text_widget.config(state='normal')

		wordlen_new = len(self.new_word)


		####
		mark_name = 'match%d' % self.search_index

		start = self.text_widget.index(mark_name)
		end_old = '%s +%dc' % ( start, self.match_lenghts[self.search_index] )
		end_new = "%s +%dc" % ( start, wordlen_new )


		# Regexp
		if ('-regexp' in self.search_settings):
			cont = r'[%s get {%s} {%s}]' \
					% (self.tcl_name_of_contents, start, end_old)

			search_re = self.old_word
			substit = r'"%s"' % self.new_word
			patt = r'regsub -line {%s} %s %s' % (search_re, cont, substit)

			try: new_word = self.text_widget.tk.eval(patt)
			except tkinter.TclError as err:
				print('INFO: do_single_replace:', err)

			len_new_word = len(new_word)
			end_new = "%s +%dc" % ( start, len_new_word )

		# Normal
		else: new_word = self.new_word


		self.text_widget.replace(start, end_old, new_word)

		if self.can_do_syntax():
			self.update_tokens(start='%s linestart' % start, end='%s lineend' % end_new)


		self.text_widget.tag_add('replaced', start, end_new)
		self.text_widget.tag_remove('focus', '1.0', tkinter.END)

		# Fix for use of non existing mark in self.save_pos
		self.search_focus = (start, end_new)
		# Mark gets here deleted

		self.text_widget.mark_unset(mark_name)
		self.mark_indexes.remove(self.search_index)
		####


		self.text_widget.config(state='disabled')

		self.search_matches -= 1

		if self.search_matches == 0:
			self.wait_for(700)
			self.stop_search()


	def do_replace_all(self, event=None):

		# Start of actual replacing
		self.text_widget.tag_config('match', background='', foreground='')
		self.text_widget.tag_remove('focus', '1.0', tkinter.END)
		self.text_widget.config(state='normal')
		wordlen_new = len(self.new_word)


		####
		i = self.mark_indexes[-1]
		last_mark = 'match%d' % i
		idx_last_mark = self.text_widget.index(last_mark)

		for index in self.mark_indexes[::-1]:

			mark_name = 'match%d' % index
			start = self.text_widget.index(mark_name)
			end_old = '%s +%dc' % ( start, self.match_lenghts[index] )
			end_new = "%s +%dc" % ( start, wordlen_new )


			# Regexp
			if ('-regexp' in self.search_settings):
				cont = r'[%s get {%s} {%s}]' \
						% (self.tcl_name_of_contents, start, end_old)
				search_re = self.old_word
				substit = r'"%s"' % self.new_word
				patt = r'regsub -line {%s} %s %s' % (search_re, cont, substit)
				try:	new_word = self.text_widget.tk.eval(patt)
				except tkinter.TclError as err:
					print('INFO: do_replace_all:', err)

				len_new_word = len(new_word)
				end_new = "%s +%dc" % ( start, len_new_word )


			# Normal
			else: new_word = self.new_word


			self.text_widget.replace(start, end_old, new_word)


			self.text_widget.tag_add('replaced', start, end_new)
			self.text_widget.mark_unset(mark_name)
			self.mark_indexes.pop(-1)
		####


		# Is it not viewable?
		if not self.text_widget.bbox(idx_last_mark):
			self.wait_for(300)

		# Show last match that got replaced
		self.ensure_idx_visibility(idx_last_mark)
		self.wait_for(200)

		bg, fg = self.themes[self.curtheme]['replaced'][:]
		self.text_widget.tag_config('replaced', background=bg, foreground=fg)

		self.stop_search()
		###################


	def start_replace(self, event=None):

		# Get stuff after prompt
		tmp_orig = self.entry.get()
		idx = tmp_orig.index(':') + 2
		tmp = tmp_orig[idx:]
		self.new_word = tmp

		# No check for empty newword to enable deletion.

		if self.old_word == self.new_word:
			self.bell()
			return 'break'

		# search_history_walk
		if self.new_word not in self.search_history[1]:
			self.search_history[1].append(self.new_word)
		self.search_history_index = len(self.search_history[1])
		self.flag_use_replace_history = True


		self.entry.config(validate='none')

		lenght_of_search_matches = len(str(self.search_matches))
		diff = lenght_of_search_matches - 1
		idx = tmp_orig.index(':')
		self.entry.delete(0, idx)

		patt = f'{diff*" "}1/{self.search_matches} Replace with'

		if self.state == 'replace_all':
			patt = f'{diff*" "}1/{self.search_matches} ReplaceALL with'

		self.entry.insert(0, patt)


		self.entry.flag_start = True
		self.auto_update_syntax_stop()


		self.wait_for(100)
		self.show_next()


		self.bid_show_next = self.bind("<Control-n>", self.show_next )
		self.bid_show_prev = self.bind("<Control-p>", self.show_prev )

		self.entry.bind("<Return>", self.skip_bindlevel)
		self.text_widget.bind("<Return>", self.skip_bindlevel)
		self.text_widget.focus_set()

		if self.state == 'replace':
			self.bind( "<Return>", self.do_single_replace)

		elif self.state == 'replace_all':
			self.bind( "<Return>", self.do_replace_all)

		return 'break'


################ Replace End
########### Class Editor End


def main():

	# Do something with errors raising from Editor.__new__()
	try:
		Editor.in_mainloop = True
		debug = False
		e = False

		try:
			args = sys.argv[1:]
			first_arg = args[0]
			# Note: debug-session in Windows should be started using script
			# found under /dev
			if first_arg == '--debug': debug = True
			# Use one time conf(original conf remains untouched) to enable 'adhoc behaviour' editor
			# like normal editor: python -m henxel filepath1 filepath2
			else: Editor.files_to_be_opened = args

		except IndexError: pass


		e=Editor(debug=debug)
		e.mainloop()

	except Exception as new_err:

		if debug:
			traceback.print_exception(new_err)
			sys.exit(1)
		else:
			raise new_err



















