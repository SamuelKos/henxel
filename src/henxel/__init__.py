############ Stucture briefing Begin

# Stucture briefing
# TODO
# Imports
# Module Utilities
# Class Tab

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
import tkinter.font
import tkinter
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

# From current directory
from . import wordexpand
from . import changefont
from . import fdialog

# For executing edited file in the same env than this editor, which is nice:
# It means you have your installed dependencies available. By self.run()
import subprocess

# For making paste to work in Windows
import threading


# https://stackoverflow.com/questions/3720740/pass-variable-on-import/39360070#39360070
# These are currently used only when debugging, and even then only when doing test-launch.
# Look in: build_launch_test()
import importflags
FLAGS = importflags.FLAGS

############ Imports End
############ Module Utilities Begin

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
			'edit_search_setting',
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
			'is_pyfile',
			'line_is_bookmarked',
			'line_is_defline',
			'line_is_elided',
			'line_is_empty',
			'package_has_syntax_error',
			'print_bookmarks',
			'print_search_help',
			'print_search_setting',
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
############ Class Tab Begin

class Tab:
	'''	Represents a tab-page of an Editor-instance
	'''

	def __init__(self, **entries):
		''' active		Bool
			filepath	pathlib.Path

			contents,
			oldcontents,
			position,
			type		String
			text_widget tkinter.Text
			bookmarks	List
		'''

		self.active = False
		self.filepath = None
		self.contents = ''
		self.oldcontents = ''
		self.position = '1.0'
		self.type = 'newtab'
		self.bookmarks = list()
		self.text_widget = None
		self.tcl_name_of_contents = ''

		self.__dict__.update(entries)


	def __str__(self):

		return	'\nfilepath: %s\nactive: %s\ntype: %s\nposition: %s' % (
				str(self.filepath),
				str(self.active),
				self.type,
				self.position
				)


############ Class Tab End
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
CONFPATH = 'editor.cnf'
ICONPATH = 'editor.png'
HELPPATH = 'help.txt'
HELP_MAC = 'help_mac.txt'
START_MAC = 'restart_editor.scpt'
START_WIN = 'restart_editor_todo.bat'
START_LINUX = 'restart_editor_todo.sh'


VERSION = importlib.metadata.version(__name__)


TAB_WIDTH = 4
TAB_WIDTH_CHAR = 'A'

SLIDER_MINSIZE = 66


GOODFONTS = [
			'Andale Mono',
			'FreeMono',
			'Bitstream Vera Sans Mono',
			'DejaVu Sans Mono',
			'Liberation Mono',
			'Inconsolata',
			'Consolas',
			'Courier 10 Pitch',
			'Courier New',
			'Courier',
			'Noto Mono',
			'Noto Sans Mono'
			]

############ Constants End
############ Init etc. Begin

class Editor(tkinter.Toplevel):

	# import flags
	flags = FLAGS
	restart_script = None

	# Normal stuff
	alive = False

	pkg_contents = None
	no_icon = True
	pic = None
	helptxt = None

	root = None
	font = None
	menufont = None
	boldfont = None

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
			# Q: Does launch-test have its own root? A: Yes:
##			if flags and flags.get('launch_test') == True:
##				print('BBBB')
			# Was earlier v.0.2.2 in init:

			# self.root = tkinter.Tk().withdraw()

			# wich worked in Debian 11, but not in Debian 12,
			# resulted error msg like: class str has no some attribute etc.
			# After changing this line in init to:

			# self.root = tkinter.Tk()
			# self.root.withdraw()

			# Editor would launch, but after closing and reopening in the same python-console-instance,
			# there would be same kind of messages but about icon, and also fonts would change.
			# This is why that stuff is now here to keep those references.

			cls.root = tkinter.Tk()
			cls.root.withdraw()


		if not cls.font:
			cls.font = tkinter.font.Font(family='TkDefaulFont', size=12, name='textfont')
			cls.menufont = tkinter.font.Font(family='TkDefaulFont', size=10, name='menufont')
			cls.boldfont = cls.font.copy()


		if not cls.pkg_contents:
			cls.pkg_contents = importlib.resources.files(__name__)


		if cls.pkg_contents:

			if debug and not cls.restart_script:
				startfile = False
				if cls.os_type == 'mac_os': startfile = START_MAC
				elif cls.os_type == 'windows': startfile = START_WIN
				else: startfile = START_LINUX

				if not startfile: pass
				else:
					for item in cls.pkg_contents.iterdir():
						if item.name == startfile:
							cls.restart_script = item.resolve()
							break

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
				for item in cls.pkg_contents.iterdir():

					helpfile = HELPPATH
					if cls.os_type == 'mac_os': helpfile = HELP_MAC

					if item.name == helpfile:
						try:
							cls.helptxt = item.read_text()
							break

						except Exception as e:
							print(e.__str__())


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
			self.restart_script = self.__class__.restart_script
			self.debug = debug

			super().__init__(self.root, *args, class_='Henxel', bd=4, **kwargs)
			self.protocol("WM_DELETE_WINDOW",
				lambda kwargs={'quit_debug':True}: self.quit_me(**kwargs))


			# Get original background, which is returned at end of init
			# after editor gets mapped
			self.orig_bg_color = self.cget('bg')
			self.config(bg='black')
			# Dont map too early to prevent empty windows at startup
			# when init is taking long
			self.withdraw()


			# Other widgets
			self.to_be_closed = list()

			# Used in check_caps
			self.to_be_cancelled = list()

			self.ln_string = ''
			self.want_ln = True
			self.syntax = True
			self.oldconf = None
			self.tab_char = TAB_WIDTH_CHAR

			if sys.prefix != sys.base_prefix:
				self.env = sys.prefix
			else:
				self.env = None

			self.tabs = list()
			self.tabindex = None
			self.branch = None
			self.version = VERSION
			self.os_type = self.__class__.os_type


			self.font = self.__class__.font
			self.menufont = self.__class__.menufont
			self.boldfont = self.__class__.boldfont


			if self.flags and self.flags.get('launch_test') == True: pass
			else:
				# Get current git-branch
				try:
					self.branch = subprocess.run('git branch --show-current'.split(),
							check=True, capture_output=True).stdout.decode().strip()
				except Exception as e:
					pass


			# Search related variables Begin
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

			# Used for counting indentation
			self.search_count_var = tkinter.IntVar()
			# Search related variables End

			self.errlines = list()
			self.err = False

			# When clicked with mouse button 1 while searching
			# to set cursor position to that position clicked.
			self.save_pos = None

			# Used in load()
			self.tracevar_filename = tkinter.StringVar()
			self.tracefunc_name = None
			self.lastdir = None

			self.par_err = False

			# Used in copy() and paste()
			self.flag_fix_indent = False
			self.checksum_fix_indent = False

			self.waitvar = tkinter.IntVar()
			self.fullscreen = False
			self.state = 'normal'


			self.helptxt = 'Could not load help-file. Press ESC to return.'

			if self.__class__.helptxt:
				self.helptxt = self.__class__.helptxt

			try:
				self.tk.call('wm','iconphoto', self._w, self.__class__.pic)
			except tkinter.TclError as e:
				print(e)


			# Initiate widgets
			####################################
			self.btn_git = tkinter.Button(self, takefocus=0, relief='flat',
										highlightthickness=0, padx=0, state='disabled')
			self.restore_btn_git() # Show git-branch if on one

			self.entry = tkinter.Entry(self, highlightthickness=0, takefocus=0)
			if self.os_type != 'mac_os': self.entry.config(bg='#d9d9d9')

			self.btn_open = tkinter.Button(self, takefocus=0, text='Open',
										highlightthickness=0, command=self.load)
			self.btn_save = tkinter.Button(self, takefocus=0, text='Save',
										highlightthickness=0, command=self.save)

			self.ln_widget = tkinter.Text(self, width=4, highlightthickness=0, relief='flat')
			self.ln_widget.tag_config('justright', justify=tkinter.RIGHT)


			self.text_widget_basic_config = dict(undo=True, maxundo=-1, autoseparators=True,
											tabstyle='wordprocessor', highlightthickness=0,
											relief='flat')
			#############
			self.frame = tkinter.Frame(self, bd=0, padx=0, pady=0, highlightthickness=0,
									bg='black')

			self.scrollbar = tkinter.Scrollbar(self, orient=tkinter.VERTICAL,
											highlightthickness=0, bd=0, takefocus=0)

			# Tab-completion, used in indent() and unindent()
			self.expander = wordexpand.ExpandWord(self)


			self.popup = tkinter.Menu(self, tearoff=0, bd=0, activeborderwidth=0)


			if self.debug:
				self.popup.add_command(label="test", command=lambda: self.after_idle(self.quit_me))
				self.popup.add_command(label="     restart",
						command=lambda: self.after_idle(self.restart_editor))
				self.popup.add_command(label="         run", command=self.run)

				# Next lines left as example of what does not work if doing restart in quit_me
				#self.popup.add_command(label="test", command=self.quit_me)
				#self.popup.add_command(label="     restart", command=self.restart_editor)

				if self.flags and self.flags.get('test_fake_error'): this_func_no_exist()
				#this_func_no_exist()

			else:
				self.popup.add_command(label="         run", command=self.run)
				self.popup.add_command(label="        copy", command=self.copy)
				self.popup.add_command(label="       paste", command=self.paste)
				self.popup.add_command(label="##   comment", command=self.comment)
				self.popup.add_command(label="   uncomment", command=self.uncomment)

			self.popup.add_command(label="  select all", command=self.select_all)
			self.popup.add_command(label="     inspect", command=self.insert_inspected)
			self.popup.add_command(label="      errors", command=self.show_errors)
			self.popup.add_command(label="        help", command=self.help)


			# Get conf
			string_representation = None
			data, p = None, None

			if self.flags and self.flags.get('test_skip_conf') == True: pass
			else:
				if self.env: p = pathlib.Path(self.env) / CONFPATH

				if p and p.exists():
					try:
						with open(p, 'r', encoding='utf-8') as f:
							string_representation = f.read()
							data = json.loads(string_representation)

					except EnvironmentError as e:
						print(e.__str__())	# __str__() is for user (print to screen)
						#print(e.__repr__())	# __repr__() is for developer (log to file)
						print(f'\n Could not load existing configuration file: {p}')

			if data:
				self.oldconf = string_representation
				self.load_config(data)



			# Colors Begin #######################

			red = r'#c01c28'
			cyan = r'#2aa1b3'
			magenta = r'#a347ba'
			green = r'#26a269'
			orange = r'#e95b38'
			gray = r'#508490'
			black = r'#000000'
			white = r'#d3d7cf'


			self.default_themes = dict()
			self.default_themes['day']   = d = dict()
			self.default_themes['night'] = n = dict()

			# self.default_themes[self.curtheme][tagname] = [backgroundcolor, foregroundcolor]
			d['normal_text'] = [white, black]
			n['normal_text'] = [black, white]

			d['keywords'] = ['', orange]
			n['keywords'] = ['', 'deep sky blue']
			d['numbers'] = ['', red]
			n['numbers'] = ['', red]
			d['bools'] = ['', magenta]
			n['bools'] = ['', magenta]
			d['strings'] = ['', green]
			n['strings'] = ['', green]
			d['comments'] = ['', gray]
			n['comments'] = ['', gray]
			d['calls'] = ['', cyan]
			n['calls'] = ['', cyan]
			d['breaks'] = ['', orange]
			n['breaks'] = ['', orange]
			d['selfs'] = ['', gray]
			n['selfs'] = ['', gray]

			d['match'] = ['lightyellow', 'black']
			n['match'] = ['lightyellow', 'black']
			d['focus'] = ['lightgreen', 'black']
			n['focus'] = ['lightgreen', 'black']

			d['replaced'] = ['yellow', 'black']
			n['replaced'] = ['yellow', 'black']

			d['mismatch'] = ['brown1', 'white']
			n['mismatch'] = ['brown1', 'white']

			d['sel'] = ['#c3c3c3', black]
			n['sel'] = ['#c3c3c3', black]


			## No conf Begin ########
			if self.tabindex == None:

				self.curtheme = 'night'
				self.themes = copy.deepcopy(self.default_themes)
				self.bgcolor, self.fgcolor = self.themes[self.curtheme]['normal_text'][:]

				# Set Font
				fontname = None

				fontfamilies = [f for f in tkinter.font.families()]

				for font in GOODFONTS:
					if font in fontfamilies:
						fontname = font
						break

				if not fontname:
					fontname = 'TkDefaulFont'


				size0, size1 = 12, 10
				# There is no font-scaling in macOS?
				if self.os_type == 'mac_os': size0, size1 = 22, 16

				self.font.config(family=fontname, size=size0)
				self.menufont.config(family=fontname, size=size1)


				self.ind_depth = TAB_WIDTH
				self.tab_width = self.font.measure(self.ind_depth * self.tab_char)
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

				## No conf End ########



			#################
			self.apply_config()


			# Needed in leave() taglink in: Run file Related
			self.name_of_cursor_in_text_widget = self.contents['cursor']

			self.scrollbar.config(command=self.contents.yview,
								width=self.scrollbar_width,
								elementborderwidth=self.elementborderwidth)

			for widget in [self.entry, self.btn_open, self.btn_save, self.ln_widget]:
				widget.config(bd=self.pad)

			self.entry.config(font=self.menufont)
			self.btn_open.config(font=self.menufont)
			self.btn_save.config(font=self.menufont)
			self.popup.config(font=self.menufont)
			self.btn_git.config(font=self.menufont)

			# Hide selection in linenumbers
			self.ln_widget.config(font=self.font, foreground=self.fgcolor, background=self.bgcolor, selectbackground=self.bgcolor, selectforeground=self.fgcolor, inactiveselectbackground=self.bgcolor, state='disabled', padx=self.pad, pady=self.pad)





			# In apply_conf now

##			# Get anchor-name of selection-start.
##			# Used in for example select_by_words():
##			self.contents.insert(1.0, 'asd')
##			# This is needed to get some tcl-objects created,
##			# ::tcl::WordBreakRE and self.anchorname
##			self.contents.event_generate('<<SelectNextWord>>')
##			# This is needed to clear selection
##			# otherwise left at the end of file:
##			self.contents.event_generate('<<PrevLine>>')
##
##			# Now also this array is created which is needed
##			# in RE-fixing ctrl-leftright behaviour in Windows below.
##			# self.tk.eval('parray ::tcl::WordBreakRE')
##
##			self.anchorname = None
##			for item in self.contents.mark_names():
##				if 'tk::' in item:
##					self.anchorname = item
##					break
##
##			self.contents.delete('1.0', '1.3')


			# In Win11 event: <<NextWord>> does not work (as supposed) but does so in Linux and macOS
			# https://www.tcl.tk/man/tcl9.0/TclCmd/tclvars.html
			# https://www.tcl.tk/man/tcl9.0/TclCmd/library.html

			if self.os_type == 'windows':

				# To fix: replace array ::tcl::WordBreakRE contents with newer version, and
				# replace proc tk::TextNextWord with newer version which was looked in Debian 12
				# Need for some reason generate event: <<NextWord>> before this,
				# because array ::tcl::WordBreakRE does not exist yet,
				# but after this event it does. This was done above.

				self.tk.eval(r'set l3 [list previous {\W*(\w+)\W*$} after {\w\W|\W\w} next {\w*\W+\w} end {\W*\w+\W} before {^.*(\w\W|\W\w)}] ')
				self.tk.eval('array set ::tcl::WordBreakRE $l3 ')
				self.tk.eval('proc tk::TextNextWord {w start} {TextNextPos $w $start tcl_endOfWord} ')




			# Widgets are initiated, now more configuration
			################################################
			# Needed in update_linenums(), there is more info.
			self.update_idletasks()

			# if self.y_extra_offset > 0, it needs attention
			self.y_extra_offset = self.contents['highlightthickness'] + self.contents['bd'] + self.contents['pady']
			# Needed in update_linenums() and sbset_override()
			self.bbox_height = self.contents.bbox('@0,0')[3]
			self.text_widget_height = self.scrollbar.winfo_height()


			# Register validation-functions, note the tuple-syntax:
			self.validate_gotoline = (self.register(self.do_validate_gotoline), '%i', '%S', '%P')
			self.validate_search = (self.register(self.do_validate_search), '%i', '%s', '%S')


			self.helptxt = f'{self.helptxt}\n\nHenxel v. {self.version}'

			# Widgets are configured
			###############################


##			# Widget visibility-check
##			if self.flags and self.flags.get('launch_test'):
##				a = self.contents.winfo_ismapped()
##				b = self.contents.winfo_viewable()# checks also if ancestors are mapped
##				print(a,b) # 0 0
##
##			# Note also this
##			if self.flags and self.flags.get('launch_test'):
##				print(self.bbox_height,  self.text_widget_height)
##				# self.bbox_height == 1,  self.text_widget_height == 1
##				# --> self.contents is not yet 'packed' by (grid) geometry-manager


			# Layout Begin
			################################
			self.rowconfigure(1, weight=1)
			self.columnconfigure(1, weight=1)

			# It seems that widget is shown on screen when doing grid_configure
			self.btn_git.grid_configure(row=0, column = 0, sticky='nsew')
			self.entry.grid_configure(row=0, column = 1, sticky='nsew')
			self.btn_open.grid_configure(row=0, column = 2, sticky='nsew')
			self.btn_save.grid_configure(row=0, column = 3, columnspan=2,
										sticky='nsew')



			self.ln_widget.grid_configure(row=1, column = 0, sticky='nsew')

			self.frame.rowconfigure(0, weight=1)
			self.frame.columnconfigure(0, weight=1)
			self.contents.grid_configure(row=0, column=0, sticky='nsew')



			# If want linenumbers:
			if self.want_ln:
				self.frame.grid_configure(row=1, column=1, columnspan=3,
										sticky='nswe')

			else:
				self.frame.grid_configure(row=1, column=0, columnspan=4,
										sticky='nswe')
				self.ln_widget.grid_remove()

			self.scrollbar.grid_configure(row=1,column=4, sticky='nse')
			#################


			self.line_can_update = False

			self.boldfont.config(**self.font.config())
			self.boldfont.config(weight='bold')

			self.init_syntags()



			# Create tabs for help and error pages
			newtab = Tab()
			self.set_textwidget(newtab)
			self.set_syntags(newtab)
			self.help_tab = newtab
			self.help_tab.type = 'help'
			self.help_tab.position = '1.0'
			self.help_tab.text_widget.insert('insert', self.helptxt)
			self.help_tab.text_widget.mark_set('insert', newtab.position)
			self.help_tab.text_widget.see(newtab.position)
			self.set_bindings(newtab)
			self.help_tab.text_widget['yscrollcommand'] = lambda *args: self.sbset_override(*args)


			newtab = Tab()
			self.set_textwidget(newtab)
			self.set_syntags(newtab)
			self.err_tab = newtab
			self.err_tab.type = 'error'
			self.err_tab.position = '1.0'
			self.err_tab.text_widget.mark_set('insert', newtab.position)
			self.err_tab.text_widget.see(newtab.position)
			self.set_bindings(newtab)
			self.err_tab.text_widget['yscrollcommand'] = lambda *args: self.sbset_override(*args)
			###



			for tab in self.tabs:

				self.set_syntags(tab)

				if tab.type == 'normal':
					tab.text_widget.insert('1.0', tab.contents)
					self.restore_bookmarks(tab)

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

						a = self.get_tokens(tab)
						#t1 = int(self.root.tk.eval('clock seconds'))
						self.insert_tokens(a, tab=tab) ##### this takes times
						#t2 = int(self.root.tk.eval('clock seconds'))
						#print(t2-t1, 's')


				self.set_bindings(tab)
				tab.text_widget['yscrollcommand'] = lambda *args: self.sbset_override(*args)
				tab.text_widget.edit_reset()
				tab.text_widget.edit_modified(0)



			curtab = self.tabs[self.tabindex]

			self.scrollbar.set(*self.contents.yview())
			self.anchorname = curtab.anchorname
			self.tcl_name_of_contents = curtab.tcl_name_of_contents
			self.line_can_update = True

			if curtab.filepath:
				self.entry.insert(0, curtab.filepath)
				self.entry.xview_moveto(1.0)



			############
			# Bindings #
			############
			self.set_bindings_other()
			############


			############
			# Get window positioning with geometry call to work below
			self.update_idletasks()
			# Sticky top right corner, to get some space for console on left
			# This geometry call has to be before deiconify
			diff = self.winfo_screenwidth() - self.winfo_width()
			if self.os_type == 'windows':
				self.geometry('-0+0')
			elif diff > 0:
				self.geometry('+%d+0' % diff )

			############
			# map Editor, restore original background, which was set to black
			# during init to prevent flashing when init takes long
			if self.flags and not self.flags.get('test_is_visible'): pass
			else: self.deiconify()

			# Focus has to be after deiconify if on Windows
			if self.os_type == 'windows':
				self.contents.focus_force()
			else:
				self.contents.focus_set()


			self.config(bg=self.orig_bg_color)

			self.__class__.alive = True
			self.update_title()

##			# Widget visibility-check
##			if self.flags and self.flags.get('launch_test'):
##				a = self.contents.winfo_ismapped()
##				b = self.contents.winfo_viewable()#check also if ancestors ar mapped
##				print(a,b)
##
##			# Note also this
##			if self.flags and self.flags.get('launch_test'):
##				print(self.bbox_height,  self.text_widget_height)
##				# self.bbox_height == 25,  self.text_widget_height == 616
##				# --> self.contents is now 'packed' by (grid) geometry-manager

		except Exception as init_err:

			doing_launchtest = False
			if self.flags and self.flags.get('launch_test'): doing_launchtest = True

			if doing_launchtest: pass
			else:
				try: self.cleanup()
				except Exception as err:
					# Some object, that cleanup tried to delete,
					# did not yet had been created.
					print(err)

				# Give info about recovering from unlaunchable state
				msg = '''
################################################
Editor did not Launch!

Below is printed help(henxel.stash_pop), read and follow.
################################################
help(henxel.stash_pop) Begin

'''

				ending = '''
################################################
Error messages Begin
'''

				print(msg + stash_pop.__doc__.replace('\t', '  ') + ending)

			raise init_err

			############################# init End ##########################


	def update_title(self, event=None):
		tail = len(self.tabs) - self.tabindex - 1
		self.title( f'Henxel {"0"*self.tabindex}@{"0"*(tail)}' )


	def handle_window_resize(self, event=None):
		'''	In case of size change, like maximize etc. viewsync-event is not
			generated in such situation so need to bind to <Configure>-event.

			Just update self.fullscreen here, not actually setting fullscreen,
			which is done in esc_override
		'''
		# Handle fullscreen toggles
		self.update_idletasks()

		# Check if setting attribute '-fullscreen' is supported
		# type(self.wm_attributes()) == tuple
		# Not used because this interferes with esc_override when
		# using slow machine.
##		if self.wm_attributes().count('-fullscreen') != 0:
##			if self.wm_attributes('-fullscreen') == 1:
##				if self.fullscreen == False:
##					self.fullscreen = True
##			else:
##				if self.fullscreen == True:
##					self.fullscreen = False


		self.text_widget_height = self.scrollbar.winfo_height()
##		# Not used, left as example on how to always know the current number of screenlines.
##		# Count number of screen-lines,
##		# from text-widgets (internal) x,y-position x=0 and y=0-65535.
##		# End y-position could be something more realistic, like:
##		#       self.text_widget_height = self.scrollbar.winfo_height(),
##		# but with this magic number 65535, one possible winfo_height()-call
##		# is avoided. But Still, if dont want magics:
##		# self.contents.count('@0,0', '@0,%s' % self.text_widget_height, 'displaylines')[0]
##		#       or if in doubt is that up-to-date(it is, see above):
##		# self.contents.count('@0,0', '@0,%s' % self.scrollbar.winfo_height(), 'displaylines')[0]
##
##		# Note that result is None if widget is not yet fully started, below is solution to that.
##		if tmp := self.contents.count('@0,0', '@0,65535', 'displaylines')[0]:
##			# Here one can do things like find the maximum number of screen lines etc
##			# if tmp > self.max_screen_lines: self.max_screen_lines = tmp
##			self.screen_lines = tmp
##
##		else:
##			# Geometry manager hasn't run yet, most likely doing still init
##			# Note that this is not realistic value, but a future value if everything wents ok.
##			# Correct value would be 0
##			self.screen_lines = int(self.contents['height'])

		#self.update_linenums()


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


	def test_bind(self, event=None):
		print('jou')


	def skip_bindlevel(self, event=None):
		return 'continue'


	def ensure_idx_visibility(self, index, tab=None, back=None):
		''' Ensures index is visible on screen.

			Does not set insert-mark to index.
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
			self.contents.see( '%s - %i lines' % (index, b) )
		elif not lineno_ins + 4 < lineno_end:
			self.contents.see( '%s + 4 lines' % index )


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
		# When one makes changes here, and does launch-test or restart
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
		# when editing conf-related stuff, for example, one would:
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
		# In __init__ one could use real error instead, to see effect.
		# just git commit first, then put this line someplace:
		# 	this_func_no_exist()
		# Then dont restart, but quit editor and console, and restart python and editor
		# --> see effect
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

			tmp = self.build_launch_test(mode)
			d = dict(capture_output=True)
			p = subprocess.run(['python','-'], input=tmp, **d)

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


	def package_has_syntax_error(self):
		flag_cancel = False

		for item in self.__class__.pkg_contents.iterdir():
			if item.is_file() and '.py' in item.suffix:

				try:
					file_contents = item.read_text()
					ast.parse(file_contents, filename=item.resolve())

				except Exception as e:
					err = '\t' +  e.__str__() + '\n'
					print( '\nIn: ', item.resolve().__str__() )
					print(err)
					flag_cancel = True
					continue

		return flag_cancel


	def restart_editor(self, event=None):
		self.quit_me(restart=True)
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
		del self.contents
		del self.scrollbar
		del self.expander
		del self.popup
		del self.frame


	def quit_me(self, event=None, quit_debug=False, restart=False):

		def delayed_break(delay):
			self.wait_for(delay)
			self.bell()
			return 'break'

		# For example, called from incomplete, or zombie Editor.
		# And for preventing recursion if doing test-launch
		if (self.flags and self.flags.get('launch_test')) or not self.__class__.alive:
			raise ValueError


		if not self.save_forced(): return delayed_break(33)


		if self.debug:
			if self.package_has_syntax_error():
				self.activate_terminal()
				return delayed_break(33)
			# Close-Button, quit_debug=True
			# pass tests if closing editor or restarting
			elif quit_debug or restart: pass
			elif not self.test_launch_is_ok():
				self.activate_terminal()
				return delayed_break(33)
			else: return 'break'


		# Below this line, 1: debug=False (normal mode) or 2: quit_debug or restart
		# --> cleanup is reasonable

		for tab in self.tabs: self.save_bookmarks(tab)
		self.save_config()

		self.config(bg='black') # Prevent flashing if slow machine
		self.cleanup()


		self.__class__.alive = False


		# quit_debug: Allow quitting debug-session without closing
		# Python console, by clicking close-button.
		tests = [not quit_debug, self.debug, restart, self.restart_script]

		if all(tests):
			tmp = [self.restart_script]
			subprocess.run(tmp)

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
		# 'strings' in self.contents.tag_names('insert')
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
			on_oldline:			bool	(self.oldlinenum == linenum curline)
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
			( scope_line, ind_defline, idx_scope_start) = self.get_scope_start()

			idx_scope_end = self.get_scope_end(ind_defline, idx_scope_start)

			s = '%s linestart' % idx_scope_start
			e = idx_scope_end

		else:
			s = 'insert linestart'
			e = 'insert lineend'


		# Remove old tags:
		for tag in self.tagnames:
			self.contents.tag_remove( tag, s, e)


		if tab.check_scope:
			self.update_tokens(start=s, end=e)
		else:
			self.update_tokens(start=s, end=e, line=newline)

		###### check_line End ##########


	def update_lineinfo(self, tab=None):
		''' Update info about current line, which is used to determine if
			tokens of the line has to be updated for syntax highlight.

			When this is called, the info is up to date and thus
			prevents update for the line (in update_line() ), which is the purpose.
		'''

		if not tab:
			tab = self.tabs[self.tabindex]

		linestart = 'insert linestart'
		lineend = 'insert lineend'
		tab.oldline = tab.text_widget.get( linestart, lineend )
		tab.oldlinenum,_ = self.get_line_col_as_int(tab=tab)


	def update_line(self, event=None):
		'''	Triggers after event: <<WidgetViewSync>>

			Used to update linenumbers and syntax highlighting of current line

			The event itself is generated *after* when inserting, deleting
			or on screen geometry change, but not when just scrolling (like yview).
			Almost all font-changes also generate this event.

		'''

		tab = self.tabs[self.tabindex]
		# More info in update_linenums()
		self.bbox_height = tab.text_widget.bbox('@0,0')[3]
		self.text_widget_height = self.scrollbar.winfo_height()
		self.update_linenums()


		if self.can_do_syntax(tab) and self.line_can_update:

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

				self.check_line( oldline=tab.oldline, newline=curline,
								on_oldline=on_oldline, tab=tab)

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
		else:
			w.bind( "<Shift-Tab>", self.unindent)

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

			w.bind( "<Control-Up>", self.move_many_lines)
			w.bind( "<Control-Down>", self.move_many_lines)
			w.bind( "<Control-Shift-Up>", self.move_many_lines)
			w.bind( "<Control-Shift-Down>", self.move_many_lines)

			w.bind( "<Control-8>", self.walk_scope)
			w.bind( "<Control-Shift-8>",
				lambda event: self.walk_scope(event, **{'absolutely_next':True}) )
			w.bind( "<Control-9>",
				lambda event: self.walk_scope(event, **{'down':True}) )
			w.bind( "<Control-Shift-9>",
				lambda event: self.walk_scope(event, **{'down':True, 'absolutely_next':True}) )

			w.bind( "<Alt-Shift-F>", self.select_scope)
			w.bind( "<Alt-Shift-E>", self.elide_scope)

			w.bind("<Left>", self.check_sel)
			w.bind("<Right>", self.check_sel)

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
			w.bind( "<Mod1-Key-8>", self.walk_scope)
			w.bind( "<Mod1-Shift-(>",
				lambda event: self.walk_scope(event, **{'absolutely_next':True}) )
			w.bind( "<Mod1-Key-9>",
				lambda event: self.walk_scope(event, **{'down':True}) )
			w.bind( "<Mod1-Shift-)>",
				lambda event: self.walk_scope(event, **{'down':True, 'absolutely_next':True}) )

			w.bind( "<Mod1-Shift-F>", self.select_scope)
			w.bind( "<Mod1-Shift-E>", self.elide_scope)

			w.bind( "<Mod1-Key-y>", self.yank_line)
			w.bind( "<Mod1-Key-n>", self.new_tab)

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

			w.bind( "<Mod1-Key-BackSpace>", self.del_to_dot)
			w.bind( "<Mod1-Key-Return>", self.load)


		#######################################################

		# self.os_type == any:
		w.bind( "<Control-a>", self.goto_linestart)
		w.bind( "<Control-e>", self.goto_lineend)
		w.bind( "<Control-A>", self.goto_linestart)
		w.bind( "<Control-E>", self.goto_lineend)

		w.bind( "<Control-j>", self.center_view)
		w.bind( "<Control-u>",
			lambda event: self.center_view(event, **{'up':True}) )

		w.bind( "<Control-d>", self.del_tab)
		w.bind( "<Control-Q>",
			lambda event: self.del_tab(event, **{'save':False}) )

		w.bind( "<Shift-Return>", self.comment)
		w.bind( "<Shift-BackSpace>", self.uncomment)
		w.bind( "<Tab>", self.indent)

		w.bind( "<Control-Tab>", self.insert_tab)

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


		w.bind( "<<WidgetViewSync>>", self.update_line)
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

		if self.os_type == 'mac_os':
			self.right_mousebutton_num = 2



		# Binds with ID Begin
		self.entry.bid_ret = self.entry.bind("<Return>", self.load)
		# Binds with ID End



		self.bind( "<Button-%i>" % self.right_mousebutton_num, self.raise_popup)
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

			# Default cmd-q does not trigger quit_me
			# Override Cmd-Q:
			# https://www.tcl.tk/man/tcl8.6/TkCmd/tk_mac.html
			self.root.createcommand("tk::mac::Quit", self.quit_me)
			#self.root.createcommand("tk::mac::OnHide", self.test_hide)


		else:
			self.bind( "<Alt-n>", self.new_tab)
			self.bind( "<Control-q>", self.quit_me)

			self.bind( "<Control-R>", self.replace_all)
			self.bind( "<Control-r>", self.replace)

			self.bind( "<Alt-w>", self.walk_tabs)
			self.bind( "<Alt-q>", lambda event: self.walk_tabs(event, **{'back':True}) )

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

		# if dont want linenumbers:
		if self.want_ln:
			# remove remembers grid-options
			self.ln_widget.grid_remove()
			self.frame.grid_configure(column=0, columnspan=4)
			self.want_ln = False
		else:
			self.frame.grid_configure(column=1, columnspan=3)
			self.ln_widget.grid()

			self.want_ln = True

		return 'break'


	def get_linenums(self):

		x = 0
		line = '0'
		col= ''
		ln = ''

		# line-height is used as step, it depends on font
		step = self.bbox_height

		nl = '\n'
		lineMask = '%s\n'

		# @x,y is tkinter text-index -notation:
		# The character that covers the (x,y) -coordinate within the text's window.
		indexMask = '@0,%d'

		# stepping lineheight at time, checking index of each lines first cell, and splitting it.

		for i in range(0, self.text_widget_height, step):

			ll, cc = self.contents.index( indexMask % i).split('.')

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

			# 1 - 3 : adjust linenumber-lines with text-lines

			# 1:
			# @0,0 is currently visible first character at
			# x=0 y=0 in text-widget.

			# 2: bbox returns this kind of tuple: (3, -9, 19, 38)
			# (bbox is cell that holds a character)
			# (x-offset, y-offset, width, height) in pixels
			# Want y-offset of first visible line, and reverse it:

			# NOTE ABOUT BBOX
			# if used normal index like bbox('insert +2lines') or bbox('12.1')
			# THen, if that index is not currently visible on screen,
			# bbox returns: None

			# index like '@0,0' are different by definition, they do not refer
			# to content of Text-widget, but structure of widget window.

			y_offset = self.contents.bbox('@0,0')[1]

			y_offset *= -1

			# if self.y_extra_offset > 0, this is needed:
			if y_offset != 0:
				y_offset += self.y_extra_offset

			tt.config(state='normal')
			tt.delete('1.0', tkinter.END)
			tt.insert('1.0', self.ln_string)
			tt.tag_add('justright', '1.0', tkinter.END)

			# 3: Then scroll lineswidget same amount to fix offset
			# compared to text-widget:
			tt.yview_scroll(y_offset, 'pixels')

			tt.config(state='disabled')


############## Linenumbers End
############## Tab Related Begin

	def new_tab(self, event=None):

		if self.state != 'normal':
			self.bell()
			return 'break'


		newtab = Tab()

		self.set_textwidget(newtab)
		self.set_syntags(newtab)
		self.set_bindings(newtab)
		newtab.text_widget['yscrollcommand'] = lambda *args: self.sbset_override(*args)
		newtab.position = '1.0'
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
			self.contents.delete('1.0', tkinter.END)
			self.bell()
			return 'break'


		if oldtab.type == 'normal' and save:
			if not self.save(activetab=True):
				self.bell()
				return 'break'



		if len(self.tabs) == 1:
			newtab = Tab()

			self.set_textwidget(newtab)
			self.set_syntags(newtab)
			self.set_bindings(newtab)
			newtab.text_widget['yscrollcommand'] = lambda *args: self.sbset_override(*args)
			newtab.position = '1.0'
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
			new_tab		also calls tab_close() before this
			walk_tabs	also calls tab_close() before this
			tag_link
			stop_help
			stop_show_errors
			loadfile	also calls remove_bookmarks() before this

		'''

		tab.active = True

		self.anchorname = tab.anchorname
		self.tcl_name_of_contents = tab.tcl_name_of_contents

		if tab.filepath:
			self.entry.insert(0, tab.filepath)
			self.entry.xview_moveto(1.0)

		self.contents = tab.text_widget
		self.scrollbar.config(command=self.contents.yview)
		self.scrollbar.set(*self.contents.yview())
		self.update_linenums()
		self.contents.grid_configure(row=0, column=0, sticky='nswe')
		self.contents.focus_set()

		# This is needed for some reason to prevent flashing
		# when using fast machine
		self.update_idletasks()


	def tab_close(self, tab):
		''' Called from:
			new_tab		also calls tab_open() after this
			walk_tabs	also calls tab_open() after this
			show_errors
			run
			help
		'''

		tab.active = False

		self.entry.delete(0, tkinter.END)
		self.scrollbar.config(command='')
		self.contents.grid_forget()

		if len(self.contents.tag_ranges('sel')) > 0:
			self.contents.tag_remove('sel', '1.0', 'end')


	def walk_tabs(self, event=None, back=False):

		if self.state != 'normal' or len(self.tabs) < 2:
			self.bell()
			return 'break'


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


		self.tab_close(self.tabs[old_idx])
		self.tab_open(self.tabs[new_idx])
		self.update_title()

		return 'break'

########## Tab Related End
########## Configuration Related Begin

	def save_config(self):
		data = self.get_config()

		string_representation = json.dumps(data)

		if string_representation == self.oldconf:
			return

		if self.env:
			p = pathlib.Path(self.env) / CONFPATH
			try:
				with open(p, 'w', encoding='utf-8') as f:
					f.write(string_representation)
			except EnvironmentError as e:
				print(e.__str__())
				print('\nCould not save configuration')
		else:
			print('\nNot saving configuration when not in venv.')


	def load_config(self, data):

		font, menufont = self.fonts_exists(data)
		self.set_config(data, font, menufont)


	def fonts_exists(self, dictionary):

		res = True
		fontfamilies = [f for f in tkinter.font.families()]

		font = dictionary['font']['family']

		if font not in fontfamilies:
			print(f'Font {font.upper()} does not exist.')
			font = False

		menufont = dictionary['menufont']['family']

		if dictionary['menufont']['family'] not in fontfamilies:
			print(f'Font {menufont.upper()} does not exist.')
			menufont = False

		return font, menufont


	def get_config(self):
		dictionary = d = dict()
		d['curtheme'] = self.curtheme
		d['lastdir'] = self.lastdir.__str__()

		# Replace possible Tkdefaulfont as family with real name,
		# if not mac_os, because tkinter.font.Font does not recognise
		# this: .APPLESYSTEMUIFONT

		if self.os_type == 'mac_os':

			if self.font.cget('family') == 'TkDefaulFont':
				d['font'] = self.font.config()

			else:
				d['font'] = self.font.actual()

			if self.menufont.cget('family') == 'TkDefaulFont':
				d['menufont'] = self.menufont.config()

			else:
				d['menufont'] = self.menufont.actual()

		else:
			d['font'] = self.font.actual()
			d['menufont'] = self.menufont.actual()


		d['scrollbar_width'] = self.scrollbar_width
		d['elementborderwidth'] = self.elementborderwidth
		d['want_ln'] = self.want_ln
		d['syntax'] = self.syntax
		d['ind_depth'] = self.ind_depth
		d['themes'] = self.themes

		for tab in self.tabs:
			# Convert tab.filepath to string for serialization
			if tab.filepath:
				tab.filepath = tab.filepath.__str__()
			else:
				tab.bookmarks.clear()


		whitelist = (
					'active',
					'filepath',
					'position',
					'type',
					'bookmarks'
					)


		d['tabs'] = [ dict([
							(key, tab.__dict__.get(key)) for key in whitelist
							]) for tab in self.tabs ]


		return dictionary


	def set_config(self, dictionary, font, menufont):
		d = dictionary
		# Set Font Begin ##############################

		# Both missing:
		if not font and not menufont:
			fontname = None

			fontfamilies = [f for f in tkinter.font.families()]

			for font in GOODFONTS:
				if font in fontfamilies:
					fontname = font
					break

			if not fontname:
				fontname = 'TkDefaulFont'

			d['font']['family'] = fontname
			d['menufont']['family'] = fontname

		# One missing, copy existing:
		elif bool(font) ^ bool(menufont):
			if font:
				d['menufont']['family'] = font
			else:
				d['font']['family'] = menufont


		self.font.config(**d['font'])
		self.menufont.config(**d['menufont'])
		self.scrollbar_width 	= d['scrollbar_width']
		self.elementborderwidth	= d['elementborderwidth']
		self.want_ln = d['want_ln']
		self.syntax = d['syntax']
		self.ind_depth = d['ind_depth']
		self.themes = d['themes']
		self.curtheme = d['curtheme']

		self.bgcolor, self.fgcolor = self.themes[self.curtheme]['normal_text'][:]

		###
		self.tab_width = self.font.measure(self.ind_depth * TAB_WIDTH_CHAR)

		pad_x =  self.tab_width // self.ind_depth // 3
		pad_y = pad_x
		self.pad = pad_x ###################################
		###

		self.lastdir = d['lastdir']

		if self.lastdir != None:
			self.lastdir = pathlib.Path(d['lastdir'])
			if not self.lastdir.exists():
				self.lastdir = None

		self.tabs = [ Tab(**item) for item in d['tabs'] ]

		# To avoid for-loop breaking, while removing items from the container being iterated,
		# one can iterate over container[:], that is: self.tabs[:],
		# which returns a shallow copy of the list --> safe to remove items.

		# This is same as:
		# tmplist = self.tabs[:]
		# for tab in tmplist:
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


	def set_textwidget(self, tab):

		w = tab.text_widget = tkinter.Text(self.frame, **self.text_widget_basic_config)

		w.insert(1.0, 'asd')
		w.event_generate('<<SelectNextWord>>')
		w.event_generate('<<PrevLine>>')

		tab.anchorname = None
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


		w.config(font=self.font, tabs=(self.tab_width, ), bd=self.pad,
				padx=self.pad, pady=self.pad, foreground=self.fgcolor,
				background=self.bgcolor, insertbackground=self.fgcolor)


	def apply_config(self):

		if self.tabindex == None:

			if len(self.tabs) == 0:
				newtab = Tab()
				newtab.active = True
				self.tabindex = 0
				self.tabs.insert(self.tabindex, newtab)

			# Recently active normal tab is gone
			else:
				self.tabindex = 0
				self.tabs[self.tabindex].active = True


		self.frame.config(bg=self.bgcolor)

		for tab in self.tabs:
			self.set_textwidget(tab)
			if tab.active: self.contents = tab.text_widget


########## Configuration Related End
########## Syntax highlight Begin

	def init_syntags(self):

		keywords = keyword.kwlist
		keywords.insert(0, 'self')
		self.keywords = dict()
		[self.keywords.setdefault(key, 1) for key in keywords]

		bools = [ 'False', 'True', 'None' ]
		self.bools = dict()
		[self.bools.setdefault(key, 1) for key in bools]

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
		[self.breaks.setdefault(key, 1) for key in breaks]

		tests = [
				'not',
				'or',
				'and',
				'in',
				'as'
				]
		self.tests = dict()
		[self.tests.setdefault(key, 1) for key in tests]

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
		self.tagnames = set(self.tagnames)


		self.tags = dict()
		for tag in self.tagnames: self.tags[tag] = list()


	def set_syntags(self, tab):
		''' This must be called after set_textwidget(tab)
			because most of tags are created there.

			This should be called only when creating text_widget
		'''

		w = tab.text_widget

		w.tag_config('keywords', font=self.boldfont)
		w.tag_config('numbers', font=self.boldfont)
		w.tag_config('comments', font=self.boldfont)
		w.tag_config('breaks', font=self.boldfont)
		w.tag_config('calls', font=self.boldfont)

		w.tag_config('focus', underline=True)
		w.tag_config('elIdel', elide=True)
		w.tag_config('animate')
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
			self.line_can_update = False

			for tab in self.tabs:
				for tag in self.tagnames:
					tab.text_widget.tag_remove( tag, '1.0', tkinter.END )

			return 'break'

		else:
			self.syntax = True
			self.line_can_update = False

			for tab in self.tabs:

				if self.can_do_syntax(tab):
					self.update_lineinfo(tab)

					a = self.get_tokens(tab)
					self.insert_tokens(a, tab=tab)


			self.line_can_update = True

			return 'break'


	def is_pyfile(self, tab=None):
		res = False

		if not tab:
			tab = self.tabs[self.tabindex]

		if tab.filepath:
			if '.py' in tab.filepath.suffix:
				res = True

		# This flag is set in insert_inspected()
		elif hasattr(tab, 'inspected'):
			res = True

		return res


	def can_do_syntax(self, tab=None):

		if not tab:
			tab = self.tabs[self.tabindex]

		return self.syntax and self.is_pyfile(tab)


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
		''' Dummy helper class, used in insert_tokens and update_tokens
			to prevent error with line:

				if last_token.type == tokenize.NAME:

			when brace-opener (,[ or { is first character of py-file

		'''
		type = 999


	def insert_tokens(self, tokens, tab=None):
		''' Syntax-highlight text

			syntax-tokens are from get_tokens()

			Called from: update_tokens, walk_tabs, etc
		'''

##		# If not viewchange(contents is not deleted)
##		# Remove old tags:
##		for tag in self.tagnames:
##			self.contents.tag_remove( tag, '1.0', 'end')


		if not tab:
			tab = self.tabs[self.tabindex]

		patt = f'{tab.tcl_name_of_contents} tag add '
		flag_err = False
		par_err = None
		check_pars = False
		last_token = self.LastToken()


		for tag in self.tagnames: self.tags[tag].clear()
		#t0 = int(self.root.tk.eval('clock milliseconds'))
		try:
			for token in tokens:

				if token.type == tokenize.NAME:

					if self.keywords.get(token.string):

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

				# Calls
				elif token.exact_type == tokenize.LPAR:
					# Need to know if last char before '(' was not empty.
					# token.line contains line as string which contains token.
					# Previously used test was:
					#prev_char_idx = token.start[1]-1
					#if prev_char_idx > -1 and token.line[prev_char_idx].isalnum():
					if last_token.type == tokenize.NAME:
						self.tags['calls'].append((last_token.start, last_token.end))

				elif token.type == tokenize.STRING:
					self.tags['strings'].append((token.start, token.end))

				elif token.type == tokenize.COMMENT:
					self.tags['comments'].append((token.start, token.end))

				elif token.type == tokenize.NUMBER:
					self.tags['numbers'].append((token.start, token.end))

				last_token = token

				################## END ####################



		except IndentationError as e:
##			for attr in ['args', 'filename', 'lineno', 'msg', 'offset', 'text']:
##				item = getattr( e, attr)
##				print( attr,': ', item )
##
##			print( e.args[0], '\nIndentation errline: ',
##			self.contents.index(tkinter.INSERT) )

			flag_err = True
			tab.check_scope = True


		except tokenize.TokenError as ee:

			if 'EOF in multi-line statement' in ee.args[0]:
				idx_start = str(last_token.start[0]) + '.0'
				check_pars = idx_start


			elif 'multi-line string' in ee.args[0]:
				flag_err = True
				tab.check_scope = True



		#t1 = int(self.root.tk.eval('clock milliseconds'))
		for tag in self.tags:
			if len(self.tags[tag]) > 0:

				tk_command = patt + tag
				for ((s0,s1), (e0,e1)) in self.tags[tag]:
					tk_command += f' {s0}.{s1} {e0}.{e1}'

				self.tk.eval(tk_command)

		#t2 = int(self.root.tk.eval('clock milliseconds'))
		#print(t2-t1, t1-t0, 'ms')



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
			tab.text_widget.tag_remove('mismatch', '1.0', tkinter.END)

			###### Check parentheses end ###########

		if not flag_err:
			#print('ok')
			tab.check_scope = False



	def update_tokens(self, start=None, end=None, line=None, tab=None):
		''' Update syntax highlighting after some change in contents.
		'''

		start_idx = start
		end_idx = end
		linecontents = line
		if not linecontents: linecontents = self.contents.get( start_idx, end_idx )

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
		last_token = self.LastToken()

		for tag in self.tagnames: self.tags[tag].clear()

		try:
			for token in tokens:

				if token.type == tokenize.NAME:

					if self.keywords.get(token.string):

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

				# Calls
				elif token.exact_type == tokenize.LPAR:
					# Need to know if last char before '(' was not empty.
					# token.line contains line as string which contains token.
					# Previously used test was:
					#prev_char_idx = token.start[1]-1
					#if prev_char_idx > -1 and token.line[prev_char_idx].isalnum():
					if last_token.type == tokenize.NAME:
						self.tags['calls'].append((last_token.start, last_token.end))

				elif token.type == tokenize.STRING:
					self.tags['strings'].append((token.start, token.end))

				elif token.type == tokenize.COMMENT:
					self.tags['comments'].append((token.start, token.end))

				elif token.type == tokenize.NUMBER:
					self.tags['numbers'].append((token.start, token.end))

				last_token = token

				################## END ####################



		except IndentationError as e:
##			for attr in ['args', 'filename', 'lineno', 'msg', 'offset', 'text']:
##				item = getattr( e, attr)
##				print( attr,': ', item )
##
##			print( e.args[0], '\nIndentation errline: ',
##			self.contents.index(tkinter.INSERT) )

			flag_err = True
			tab.check_scope = True


		except tokenize.TokenError as ee:

			if 'EOF in multi-line statement' in ee.args[0]:
				idx_start = str(last_token.start[0] +linenum -1) + '.0'
				check_pars = idx_start


			elif 'multi-line string' in ee.args[0]:
				flag_err = True
				tab.check_scope = True



		for tag in self.tags:
			if len(self.tags[tag]) > 0:

				tk_command = patt + tag
				for ((s0,s1), (e0,e1)) in self.tags[tag]:
					tk_command += f' {s0 +linenum -1}.{s1} {e0 +linenum -1}.{e1}'

				self.tk.eval(tk_command)


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
			self.contents.tag_remove('mismatch', '1.0', tkinter.END)

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

	def change_indentation_width(self, width):
		''' width is integer between 1-8
		'''

		if type(width) != int: return
		elif width == self.ind_depth: return
		elif not 0 < width <= 8: return


		self.ind_depth = width
		self.tab_width = self.font.measure(self.ind_depth * self.tab_char)
		self.contents.config(tabs=(self.tab_width, ))



	def set_scrollbar_widths(self, width, elementborderwidth):
		'''	Change widths of scrollbar
		'''

		self.scrollbar_width = width
		self.elementborderwidth = elementborderwidth

		self.scrollbar.config(width=self.scrollbar_width,
							elementborderwidth=self.elementborderwidth)


	def highlight_line(self, index='insert', color=None):
		''' color is tk color, which can be

			A: System named color. For example, one has Entry-widget with default
				foreground color. To get name of the color:

					entry_widget.cget('fg')

			B: tk named color. For example: 'red'

			C: Hexadecimal number with any of the following forms,
				in case of color white(using 4, 8, 12 and 16 bits):

			#fff
			#ffffff
			#fffffffff
			#ffffffffffff
		'''

		if not color: color = r'#303030'

		safe_idx = self.get_safe_index(index)
		s = '%s display linestart' % safe_idx

		if not self.line_is_elided(safe_idx):
			e = '%s display lineend' % safe_idx
		else:
			e = '%s display lineend -1 display char' % safe_idx

		self.contents.tag_remove('highlight_line', '1.0', 'end')

		self.contents.tag_config('highlight_line', background=color)
		self.contents.tag_add('highlight_line', s, e)


	def set_text_widget_colors(self, tab):
		tab.text_widget.config(foreground=self.fgcolor,
							background=self.bgcolor,
							insertbackground=self.fgcolor)


	def set_ln_widget_colors(self):
		self.ln_widget.config(foreground=self.fgcolor, background=self.bgcolor,
							selectbackground=self.bgcolor,
							selectforeground=self.fgcolor,
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

		self.frame.config(bg=self.bgcolor)
		self.set_ln_widget_colors()

		return 'break'


	def update_syntags_colors(self, tab):

		for tagname in self.themes[self.curtheme]:
			bg, fg = self.themes[self.curtheme][tagname][:]
			tab.text_widget.tag_config(tagname, background=bg, foreground=fg)


	def update_fonts(self):
		self.boldfont.config(**self.font.config())
		self.boldfont.config(weight='bold')

		self.tab_width = self.font.measure(self.ind_depth * self.tab_char)
		pad_x =  self.tab_width // self.ind_depth // 3
		self.pad = pad_y = pad_x

		self.scrollbar_width = self.tab_width // self.ind_depth
		self.elementborderwidth = max(self.scrollbar_width // 6, 1)
		if self.elementborderwidth == 1: self.scrollbar_width = 9
		self.scrollbar.config(width=self.scrollbar_width,
							elementborderwidth=self.elementborderwidth)



		for tab in self.tabs + [self.help_tab, self.err_tab]:
			tab.text_widget.tag_config('keywords', font=self.boldfont)
			tab.text_widget.tag_config('numbers', font=self.boldfont)
			tab.text_widget.tag_config('comments', font=self.boldfont)
			tab.text_widget.tag_config('breaks', font=self.boldfont)
			tab.text_widget.tag_config('calls', font=self.boldfont)
			tab.text_widget.config(tabs=(self.tab_width, ), padx=self.pad, pady=self.pad)


		self.ln_widget.config(padx=self.pad, pady=self.pad)
		self.y_extra_offset = self.contents['highlightthickness'] + self.contents['bd'] + self.contents['pady']
		#self.bbox_height = self.contents.bbox('@0,0')[3]



	def font_choose(self, event=None):
		if self.state != 'normal':
			self.bell()
			return 'break'

		fonttop = tkinter.Toplevel()
		fonttop.title('Choose Font')

		big = False
		shortcut = "<Alt-f>"

		if self.os_type == 'mac_os':
			big = True
			shortcut = "<function>"


		fonttop.protocol("WM_DELETE_WINDOW", lambda: ( fonttop.destroy(),
				self.contents.bind( shortcut, self.font_choose)) )

		changefont.FontChooser( fonttop, [self.font, self.menufont], big,
			sb_widths=(self.scrollbar_width, self.elementborderwidth),
			on_fontchange=self.update_fonts )
		self.contents.bind( shortcut, self.do_nothing)
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

			if wid.frontback_mode == 'foreground':
				initcolor = self.contents.tag_cget(tagname, 'foreground')
				patt = 'Choose fgcolor for: %s' % tagname

			else:
				initcolor = self.contents.tag_cget(tagname, 'background')
				patt = 'Choose bgcolor for: %s' % tagname

			res = self.tk.call('tk_chooseColor', '-initialcolor', initcolor, '-title', patt)

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

				self.frame.config(bg=self.bgcolor)
				self.set_ln_widget_colors()

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

				self.frame.config(bg=self.bgcolor)
				self.set_ln_widget_colors()


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
		if self.state != 'normal':
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


		c.protocol("WM_DELETE_WINDOW", lambda: ( c.destroy(),
				self.contents.bind( shortcut_color, self.color_choose),
				self.contents.bind( shortcut_toggl, self.toggle_color)) )

		self.contents.bind( shortcut_color, self.do_nothing)
		self.contents.bind( shortcut_toggl, self.do_nothing)

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


		self.to_be_closed.append(c)

		return 'break'


########## Theme Related End
########## Run file Related Begin

	def enter(self, tagname, event=None):
		''' Used in error-page, when mousecursor enters hyperlink tagname.
		'''
		self.contents.config(cursor="hand2")
		self.contents.tag_config(tagname, underline=1)


	def leave(self, tagname, event=None):
		''' Used in error-page, when mousecursor leaves hyperlink tagname.
		'''
		self.contents.config(cursor=self.name_of_cursor_in_text_widget)
		self.contents.tag_config(tagname, underline=0)


	def lclick(self, tagname, event=None):
		'''	Used in error-page, when hyperlink tagname is clicked.

			self.taglinks is dict with tagname as key
			and function (self.taglink) as value.
		'''

		# Passing tagname-string as argument to function self.taglink()
		# which in turn is a value of tagname-key in dictionary taglinks:
		self.taglinks[tagname](tagname)


	def tag_link(self, tagname, event=None):
		''' Used in error-page, executed when hyperlink tagname is clicked.
		'''
		# Currently, error-tab is open and is about to be closed
		err_tab_index = self.tabindex
		# Index of tab to be opened
		new_index = False

		i = int(tagname.split("-")[1])
		filepath, errline = self.errlines[i]

		filepath = pathlib.Path(filepath)
		openfiles = [tab.filepath for tab in self.tabs]

		# Clicked activetab
		if filepath == self.tabs[self.oldindex].filepath:
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


					newtab = Tab()

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



		self.tab_close(self.tabs[err_tab_index])
		self.tabs.pop(err_tab_index)

		line = errline + '.0'
		self.tabs[new_index].position = line
		self.tabs[new_index].text_widget.mark_set('insert', line)

		self.tab_open(self.tabs[new_index])
		self.tabindex = new_index
		self.err_tab.text_widget.delete('1.0', 'end')


		self.bind("<Escape>", self.esc_override)
		self.bind("<Button-%i>" % self.right_mousebutton_num,
			lambda event: self.raise_popup(event))
		self.state = 'normal'
		self.update_title()


	def run(self):
		'''	Run file currently being edited. This can not catch errlines of
			those exceptions that are catched. Like:

			try:
				code known sometimes failing with SomeError
				(but might also fail with other error-type)
			except SomeError:
				some other code but no raising error

			Note: 	Above code will raise an error in case
			 		code in try-block raises some other error than SomeError.
					In that case those errlines will be of course catched.

			What this means: If you self.run() with intention to spot possible
			errors in your program, you should use logging (in except-block)
			if you are not 100% sure about your code in except-block.
		'''
		curtab = self.tabs[self.tabindex]
		if (self.state != 'normal') or (curtab.type != 'normal'):
			self.bell()
			return 'break'

		if not self.save_forced():
			self.bell()
			return 'break'

		# https://docs.python.org/3/library/subprocess.html
		res = subprocess.run(['python', curtab.filepath], stderr=subprocess.PIPE).stderr

		err = res.decode()

		self.err = False
		if len(err) != 0:
			self.err = err.splitlines()

		self.show_errors()


	def show_errors(self):
		''' Show traceback from last run with added hyperlinks.
		'''
		if not self.err: return

		self.bind("<Escape>", self.stop_show_errors)
		self.bind("<Button-%i>" % self.right_mousebutton_num, self.do_nothing)

		self.state = 'error'

		self.tab_close(self.tabs[self.tabindex])
		self.tabs.append(self.err_tab)
		self.oldindex = self.tabindex
		self.tabindex = len(self.tabs) -1
		self.tab_open(self.err_tab)


		self.taglinks = dict()
		self.errlines = list()
		openfiles = [tab.filepath for tab in self.tabs]

		self.line_can_update = False

		for tag in self.contents.tag_names():
			if 'hyper' in tag:
				self.contents.tag_delete(tag)


		for line in self.err:
			tmp = line

			tagname = "hyper-%s" % len(self.errlines)
			self.contents.tag_config(tagname)

			# Why ButtonRelease instead of just Button-1:
			# https://stackoverflow.com/questions/24113946/unable-to-move-text-insert-index-with-mark-set-widget-function-python-tkint

			self.contents.tag_bind(tagname, "<ButtonRelease-1>",
				lambda event, arg=tagname: self.lclick(arg, event))

			self.contents.tag_bind(tagname, "<Enter>",
				lambda event, arg=tagname: self.enter(arg, event))

			self.contents.tag_bind(tagname, "<Leave>",
				lambda event, arg=tagname: self.leave(arg, event))

			self.taglinks[tagname] = self.tag_link

			# Parse filepath and linenums from errors
			if 'File ' in line and 'line ' in line:
				self.contents.insert(tkinter.INSERT, '\n')

				data = line.split(',')[:2]
				linenum = data[1][6:]
				path = data[0][8:-1]
				pathlen = len(path) + 2
				filepath = pathlib.Path(path)

				self.errlines.append((filepath, linenum))

				self.contents.insert(tkinter.INSERT, tmp)
				s0 = tmp.index(path) - 1
				s = self.contents.index('insert linestart +%sc' % s0 )
				e = self.contents.index('%s +%sc' % (s, pathlen) )

				self.contents.tag_add(tagname, s, e)

				if filepath in openfiles:
					self.contents.tag_config(tagname, foreground='brown1')
					self.contents.tag_raise(tagname)

				self.contents.insert(tkinter.INSERT, '\n')

			else:
				self.contents.insert(tkinter.INSERT, tmp +"\n")

				# Make it look bit nicer
				if self.syntax:
					# -1 lines because linebreak has been added already
					start = self.contents.index('insert -1 lines linestart')
					end = self.contents.index('insert -1 lines lineend')

					self.update_lineinfo(self.err_tab)
					self.update_tokens(start=start, end=end, line=line,
										tab=self.err_tab)

		self.err_tab.position = '1.0'
		self.err_tab.text_widget.mark_set('insert', self.err_tab.position)
		self.err_tab.text_widget.see(self.err_tab.position)

		self.err_tab.text_widget.focus_set()
		self.contents.edit_reset()
		self.contents.edit_modified(0)

		if self.syntax:
			self.line_can_update = True


	def stop_show_errors(self, event=None):
		self.state = 'normal'

		self.tab_close(self.tabs[self.tabindex])
		self.tabs.pop()
		self.tabindex = self.oldindex
		self.tab_open(self.tabs[self.tabindex])
		self.err_tab.text_widget.delete('1.0', 'end')

		self.bind("<Escape>", self.esc_override)
		self.bind("<Button-%i>" % self.right_mousebutton_num,
			lambda event: self.raise_popup(event))

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

		tmp = line.strip()
		res = False

		if len(tmp) < 8:
			pass

		elif tmp[:5] in [ 'async', 'class' ] or tmp[:3] == 'def':
			patt_end = ':'
			if '(' in tmp: patt_end = '('
			if tmp[:5] == 'async':
				tmp = tmp[5:].strip()
			if tmp[:3] == 'def':
				tmp = tmp[3:].strip()
			if tmp[:5] == 'class':
				tmp = tmp[5:].strip()
			try:
				e = tmp.index(patt_end)
				res = tmp[:e]

			except ValueError:
				pass

		return res


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
		# Why can_do_syntax, instead of is_pyfile? Because tag: 'strings' is
		# used while parsing. Tag exists only if synxtax-highlighting is on.
		# This means one can not walk_scope without syntax-highlight.
		if (not self.can_do_syntax()) or (self.state not in ['normal', 'search', 'goto_def']):
			self.bell()
			return 'break'


		if not down:
			(scope_line, ind_defline,
			idx_scope_start) = self.get_scope_start(absolutely_next=absolutely_next)

			if scope_line == '__main__()':
				self.bell()
				return 'break'

			pos = idx_scope_start

		else:
			# +1 lines: Because cursor could be at defline, start at next line(down)
			# to catch that defline
			pos = 'insert +1 lines'
			if not absolutely_next:
				(scope_line, ind_defline,
				idx_scope_start) = self.get_scope_start(index=pos)

				if scope_line != '__main__()':
					idx_scope_end = pos = self.get_scope_end(ind_defline, idx_scope_start)
				# Q: Why not: else: return here, after if?
				# A: 'insert' could be before(more up) than first defline


			# Now have idx_scope_start, idx_scope_end of current scope.
			# Below, searching for: idx_scope_start of next defline(down)
			#####################################
			if absolutely_next: blank_range = '{0,}'
			else: blank_range = '{0,%d}' % ind_defline
			p1 = r'^[[:blank:]]%s' % blank_range
			p2  = r'[acd]'

			patt = p1 + p2

			while pos:
				try:
					pos = self.contents.search(patt, pos, stopindex='end', regexp=True)

				except tkinter.TclError as e:
					print(e)
					self.bell()
					return 'break'

				if not pos:
					self.bell()
					return 'break'

				if 'strings' in self.contents.tag_names(pos):
					#print('strings3', pos)
					# Dont want rematch curline
					pos = '%s +1 lines' % pos
					continue

				lineend = '%s lineend' % pos
				linestart = '%s linestart' % pos
				line = self.contents.get( linestart, lineend )
				if res := self.line_is_defline(line):
					pos = self.idx_linestart(pos)[0]
					break

				pos = '%s +1 lines' % pos
				##################################

		# Put cursor on defline
		try:
			self.contents.mark_set('insert', pos)
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
		# Why can_do_syntax, instead of is_pyfile? Because tag: 'strings' is
		# used while parsing. Tag exists only if synxtax-highlighting is on.
		# This means one can not walk_scope without syntax-highlight.
		if (not self.can_do_syntax()) or (self.state not in ['normal', 'search', 'goto_def']):
			self.bell()
			return 'break'

		# +1 lines: Enable matching defline at insert
		pos = '%s +1 lines' % index
		(scope_line, ind_defline,
		idx_scope_start) = self.get_scope_start(index=pos)

		if scope_line != '__main__()':
			idx_scope_end = self.get_scope_end(ind_defline, idx_scope_start)
		else:
			self.bell()
			return 'break'

		self.contents.tag_remove('sel', '1.0', tkinter.END )
		self.wait_for(20)

		# Is start of selection not viewable?
		if not self.contents.bbox(idx_scope_start):
			self.wait_for(121)
			self.ensure_idx_visibility(idx_scope_start, back=4)
			self.wait_for(100)
		else:
			self.contents.mark_set('insert', idx_scope_start)

		self.contents.mark_set(self.anchorname, idx_scope_end)
		self.contents.tag_add('sel', idx_scope_start, idx_scope_end )

		return 'break'


	def move_many_lines(self, event=None):
		''' Move or select 10 lines from cursor.
			Called from linux or windows.
			Mac stuff is in mac_cmd_overrides()
		'''

		if self.state not in  ['normal', 'search', 'goto_def']:
			self.bell()
			return 'break'

		if event.widget != self.contents:
			return


		# Check if: not only ctrl (+shift) down, then return
		if self.os_type == 'linux':
			if event.state not in  [4, 5]: return

		elif self.os_type == 'windows':
			if event.state not in [ 262156, 262148, 262157, 262149 ]: return


		# Pressed Control + Shift + arrow up or down.
		# Want: select 10 lines from cursor.

		# Pressed Control + arrow up or down.
		# Want: move 10 lines from cursor.

		if event.keysym == 'Up':
			e = '<<SelectPrevLine>>'

			if event.state not in [ 5, 262157, 262149 ]:
				e = '<<PrevLine>>'

			for i in range(10):
				# Add some delay to get visual feedback
				if 'Select' in e:
					self.after(i*5, lambda args=[e]:
						self.contents.event_generate(*args) )
				else:
					self.after(i*7, lambda args=[e]:
						self.contents.event_generate(*args) )

			return 'break'


		elif event.keysym == 'Down':
			e = '<<SelectNextLine>>'

			if event.state not in [ 5, 262157, 262149 ]:
				e = '<<NextLine>>'

			for i in range(10):
				# Add some delay to get visual feedback
				if 'Select' in e:
					self.after(i*5, lambda args=[e]:
						self.contents.event_generate(*args) )
				else:
					self.after(i*7, lambda args=[e]:
						self.contents.event_generate(*args) )

			return 'break'

		else:
			return


	def center_view(self, event=None, up=False):
		''' Raise insertion-line
		'''
		if self.state != 'normal':
			self.bell()
			return 'break'


		num_lines = self.text_widget_height // self.bbox_height
		num_scroll = num_lines // 3
		pos = self.contents.index('insert')
		#posint = int(float(self.contents.index('insert')))
		# Lastline of visible window
		lastline_screen = int(float(self.contents.index('@0,65535')))

		# Lastline
		last = int(float(self.contents.index('end'))) - 1
		curline = int(float(self.contents.index('insert'))) - 1


		if up: num_scroll *= -1

		# Near fileend
		elif curline + 2*num_scroll + 2 > last:
			self.contents.insert(tkinter.END, num_scroll*'\n')
			self.contents.mark_set('insert', pos)


		# Near screen end
		#elif curline + 2*num_scroll + 2 > lastline_screen:
		self.contents.yview_scroll(num_scroll, 'units')


		# No ensure_view, enable return to cursor by arrow keys
		return 'break'


	def idx_lineend(self, index='insert'):
		return  self.contents.index( '%s display lineend' % index )


	def line_is_empty(self, index='insert'):

		safe_index = self.get_safe_index(index)

		s = '%s linestart' % safe_index
		e = '%s lineend' % safe_index

		patt = r'%s get -displaychars {%s} {%s}' % (self.tcl_name_of_contents, s, e )

		line = self.contents.tk.eval(patt)

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

		pos = self.contents.index( '%s linestart' % safe_index)
		s1 = '%s display linestart' % safe_index
		s2 = '%s linestart' % safe_index
		line_starts_from_curline = self.contents.compare( s1,'==',s2 )

		if not line_starts_from_curline:
			pos = self.contents.index( '%s display linestart' % safe_index)


		elif not self.line_is_empty(safe_index):
			s = '%s linestart' % safe_index
			e = '%s lineend' % safe_index

			patt = r'%s get -displaychars {%s} {%s}' % (self.tcl_name_of_contents, s, e )

			line_contents = self.contents.tk.eval(patt)

			stop = '%s lineend' % safe_index
			if r := self.line_is_elided(safe_index): stop = r[0]

			patt = r'^[[:blank:]]*[^[:blank:]]'

			pos = self.contents.search(patt, s, stopindex=stop, regexp=True,
					count=self.search_count_var)

			# self.search_count_var.get() == indentation level +1
			# because pattern matches: not blank at end of patt
			ind = '%s +%d chars' % (pos, self.search_count_var.get()-1)
			pos = self.contents.index(ind)


		return pos, line_starts_from_curline


	def set_selection(self, ins_new, ins_old, have_selection, selection_started_from_top,
					sel_start, sel_end, direction=None):
		''' direction is 'up' or 'down'

			Called from: select_by_words(), goto_linestart()
		'''
		###########################################
		# Get marknames: self.contents.mark_names()
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
				self.contents.tag_remove('sel', '1.0', tkinter.END)

				if selection_started_from_top:
					self.contents.mark_set(self.anchorname, sel_start)
					self.contents.tag_add('sel', sel_start, ins_new)
				else:
					# Check if selection is about to be closed
					# (selecting towards selection-start)
					# to avoid one char selection -leftovers.
					if self.contents.compare( '%s +1 chars' % ins_new, '>=' , sel_end ):
						self.contents.mark_set('insert', sel_end)
						self.contents.mark_set(self.anchorname, sel_end)
						return

					self.contents.mark_set(self.anchorname, sel_end)
					self.contents.tag_add('sel', ins_new, sel_end)

			# No selection,
			# no need to check direction of selection:
			else:
				self.contents.mark_set(self.anchorname, ins_old)
				self.contents.tag_add('sel', ins_old, ins_new)


		elif direction == 'up':
			if have_selection:
				self.contents.tag_remove('sel', '1.0', tkinter.END)

				if selection_started_from_top:
					# Check if selection is about to be closed
					# (selecting towards selection-start)
					# to avoid one char selection -leftovers.
					if self.contents.compare( '%s -1 chars' % ins_new, '<=' , sel_start ):
						self.contents.mark_set('insert', sel_start)
						self.contents.mark_set(self.anchorname, sel_start)
						return

					self.contents.mark_set(self.anchorname, sel_start)
					self.contents.tag_add('sel', sel_start, ins_new)

				else:
					self.contents.mark_set(self.anchorname, sel_end)
					self.contents.tag_add('sel', ins_new, sel_end)

			# No selection,
			# no need to check direction of selection:
			else:
				self.contents.mark_set(self.anchorname, ins_old)
				self.contents.tag_add('sel', ins_new, ins_old)


	def get_sel_info(self):
		''' Called from select_by_words, goto_linestart
		'''
		have_selection = len(self.contents.tag_ranges('sel')) > 0
		ins_old = self.contents.index('insert')
		selection_started_from_top = False
		sel_start = False
		sel_end = False


		# tkinter.SEL_FIRST is always before tkinter.SEL_LAST
		# no matter if selection started from top or bottom:
		if have_selection:
			sel_start = self.contents.index(tkinter.SEL_FIRST)
			sel_end = self.contents.index(tkinter.SEL_LAST)
			if ins_old == sel_end:
				selection_started_from_top = True


		return [ins_old, have_selection, selection_started_from_top,
				sel_start, sel_end ]


	def select_by_words(self, event=None):
		'''	Pressed ctrl or Alt + shift and arrow left or right.
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
		i_orig = self.contents.index('insert')

		if self.line_is_empty():
			# Go over empty space first
			self.contents.event_generate('<<PrevWord>>')

			# And put cursor to line end
			i_new = self.idx_lineend()
			self.contents.mark_set('insert', i_new)


		elif not line_started_from_curline:

			# At indent0, put cursor to line end of previous line
			if self.contents.compare('insert', '==', idx_linestart):
				self.contents.event_generate('<<PrevWord>>')
				self.contents.mark_set('insert', 'insert display lineend')

			# Not at indent0, just check cursor not go over indent0
			else:
				self.contents.event_generate('<<PrevWord>>')
				if self.contents.compare('insert', '<', idx_linestart):
					self.contents.mark_set('insert', idx_linestart)


		# Below this line is non empty and not wrapped
		############
		# Most common scenario:
		# Is cursor after idx_linestart?
		# i_orig > idx_linestart
		elif self.contents.compare( i_orig, '>', idx_linestart ):
			self.contents.event_generate('<<PrevWord>>')

			# Check that cursor did not go over idx_linestart
			i_new = self.contents.index(tkinter.INSERT)
			if self.contents.compare( i_new, '<', idx_linestart):
				self.contents.mark_set('insert', idx_linestart)


		## Below this i_orig <= idx_linestart
		############
		# At idx_linestart
		elif i_orig == idx_linestart:

			# No indentation?
			if self.get_line_col_as_int(index=idx_linestart)[1] == 0:
				# At filestart?
				if self.contents.compare( i_orig, '==', '1.0'):
					pos = i_orig
					return pos

				# Go over empty space first
				self.contents.event_generate('<<PrevWord>>')

				# And put cursor to line end
				i_new = self.idx_lineend()
				self.contents.mark_set('insert', i_new)

			# Cursor is at idx_linestart (end of indentation)
			# of line that has indentation.
			else:
				# Put cursor at indent0 (start of indentation)
				self.contents.mark_set('insert', 'insert linestart')


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
			if self.contents.compare( i_orig, '==', '1.0'):
				pos = i_orig
				return pos

			# Go over empty space first
			self.contents.event_generate('<<PrevWord>>')

			# And put cursor to line end
			i_new = self.idx_lineend()
			self.contents.mark_set('insert', i_new)


		# Cursor is somewhere between (exclusively) indent0 and idx_linestart
		# on line that has indentation.
		else:
			# Put cursor at indent0
			self.contents.mark_set('insert', 'insert linestart')


		pos = self.contents.index('insert')
		return pos


	def move_by_words_right(self):
		''' Returns tkinter.Text -index: pos
			and moves cursor to it.
		'''

		# Get some basic indexes first
		idx_linestart, line_started_from_curline = self.idx_linestart()
		i_orig = self.contents.index('insert')
		e = self.idx_lineend()


		if self.line_is_empty():
			# Go over empty space first
			self.contents.event_generate('<<NextWord>>')

			# And put cursor to idx_linestart
			i_new = self.idx_linestart()[0]

			# Check not at fileend, if not then proceed
			if i_new:
				self.contents.mark_set('insert', i_new)


		# Below this line is not empty
		##################
		# Cursor is at lineend, goto idx_linestart of next non empty line
		elif i_orig == e:

			# Check if at fileend
			if self.contents.compare('%s +1 chars' % i_orig, '==', tkinter.END):
				pos = i_orig
				return pos

			self.contents.event_generate('<<NextWord>>')
			idx_linestart = self.idx_linestart()[0]
			self.contents.mark_set('insert', idx_linestart)


		# Below this line cursor is before line end
		############
		# Most common scenario
		# Cursor is at or after idx_linestart
		# idx_lineend > i_orig >= idx_linestart
		elif self.contents.compare(i_orig, '>=', idx_linestart):

			self.contents.event_generate('<<NextWord>>')

			# Check not over lineend
			if self.contents.compare('insert', '>', e):
				self.contents.mark_set('insert', e)


		############
		# Below this line has indentation and is not wrapped
		# Cursor is at
		# indent0 <= i_orig < idx_linestart

		# --> put cursor to idx_linestart
		############
		else:
			self.contents.mark_set('insert', idx_linestart)


		pos = self.contents.index('insert')
		return pos


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
			if event.state not in [ 262156, 262148 ]: return


		if event.keysym == 'Right':
			pos = self.move_by_words_right()

		elif event.keysym == 'Left':
			pos = self.move_by_words_left()

		else:
			return


		return 'break'


	def check_sel(self, event=None):
		'''	Pressed arrow left or right.
			If have selection, put cursor on the wanted side of selection.
		'''

		if self.state in [ 'filedialog' ]:
			self.bell()
			return 'break'


		# self.contents or self.entry
		wid = event.widget

		# Check if have shift etc. pressed. If is, return to default bindings.
		# macOS event is already handled in mac_cmd_overrides.
		# macOS event here is only plain arrow left or right and has selection.
		if self.os_type != 'mac_os':
			if self.os_type == 'linux' and event.state != 0: return
			if self.os_type == 'windows' and event.state not in [ 262152, 262144 ]: return

			have_selection = False

			if wid == self.entry:
				have_selection = self.entry.selection_present()

			elif wid == self.contents:
				have_selection = len(self.contents.tag_ranges('sel')) > 0

			else:
				return

			if not have_selection: return


		s = wid.index(tkinter.SEL_FIRST)
		e = wid.index(tkinter.SEL_LAST)
		i = wid.index(tkinter.INSERT)

		if wid == self.contents:

			# Leave cursor where it is if have selected all
			if s == self.contents.index('1.0') and e == self.contents.index(tkinter.END):
				self.contents.tag_remove('sel', '1.0', tkinter.END)


			# When long selection == index not visible:
			# at first keypress, show wanted end of selection
			elif event.keysym == 'Right':
				if self.contents.dlineinfo(e):
					self.contents.tag_remove('sel', '1.0', tkinter.END)

				self.contents.mark_set('insert', e)
				self.ensure_idx_visibility(e)


			elif event.keysym == 'Left':

				if self.contents.dlineinfo(s):
					self.contents.tag_remove('sel', '1.0', tkinter.END)

				self.contents.mark_set('insert', s)
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
				e = '%s lineend' % self.contents.index(r[1])


			tmp = self.contents.get(s,e)
			self.contents.clipboard_clear()

			bg, fg = self.themes[self.curtheme]['sel'][:]
			self.contents.tag_config('animate', background=bg, foreground=fg)
			self.contents.tag_raise('animate')
			self.contents.tag_remove('animate', '1.0', tkinter.END)
			self.contents.tag_add('animate', s, e)

			if self.os_type != 'windows':
				self.contents.clipboard_append(tmp)
			else:
				self.copy_windows(selection=tmp)

			self.after(600, lambda args=['animate', '1.0', tkinter.END]:
					self.contents.tag_remove(*args) )


		return 'break'


	def goto_lineend(self, event=None):
		if self.state in [ 'filedialog' ]:
			self.bell()
			return 'break'


		wid = event.widget
		if wid == self.entry:
			wid.selection_clear()
			idx = tkinter.END
			wid.icursor(idx)
			wid.xview_moveto(1.0)
			return 'break'


		have_selection = False
		want_selection = False

		# ctrl-(shift)?-a or e
		# and cmd-a or e in macOS

		# If want selection:

		# Pressed also shift, so adjust selection
		# Linux, macOS state:
		# ctrl-shift == 5

		# Windows state:
		# ctrl-shift == 13

		# Also in mac_OS:
		# command-shift-arrowleft or right == 105
		# Note: command-shift-a or e not binded.

		# If want selection:
		if event.state in [ 5, 105, 13 ]:
			want_selection = True
			i = self.contents.index(tkinter.INSERT)

			if len( self.contents.tag_ranges('sel') ) > 0:
				# Need to know if selection started from top or bottom.


				have_selection = True
				s = self.contents.index(tkinter.SEL_FIRST)
				e = self.contents.index(tkinter.SEL_LAST)

				# Selection started from top
				from_top = False
				if self.contents.compare(s,'<',i):
					from_top = True

				# From bottom
				# else:	from_top = False


		# Dont want selection, ctrl/cmd-a/e:
		else:
			self.contents.tag_remove('sel', '1.0', tkinter.END)


		self.ensure_idx_visibility('insert')

		pos = self.idx_lineend()

		self.contents.see(pos)
		self.contents.mark_set('insert', pos)


		if want_selection:
			if have_selection:
				self.contents.tag_remove('sel', '1.0', tkinter.END)

				if from_top:
					self.contents.mark_set(self.anchorname, s)
					self.contents.tag_add('sel', s, 'insert')

				# From bottom:
				else:
					self.contents.mark_set(self.anchorname, e)
					self.contents.tag_add('sel', 'insert', e)

			else:
				self.contents.mark_set(self.anchorname, i)
				self.contents.tag_add('sel', i, 'insert')


		return 'break'


	def goto_linestart(self, event=None):
		if self.state in [ 'filedialog' ]:
			self.bell()
			return 'break'

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


		have_selection = False
		want_selection = False

		# ctrl-(shift)?-a or e
		# and cmd-a or e in macOS

		# If want selection:

		# Pressed also shift, so adjust selection
		# Linux, macOS state:
		# ctrl-shift == 5

		# Windows state:
		# ctrl-shift == 13

		# Also in mac_OS:
		# command-shift-arrowleft or right == 105
		# Note: command-shift-a or e not binded.

		if event.state in [ 5, 105, 13 ]:
			want_selection = True

		# Ctrl/Cmd-a/e
		else:
			self.contents.tag_remove('sel', '1.0', tkinter.END)


		[ ins_old, have_selection, from_top, s, e ] = args = self.get_sel_info()


		self.ensure_idx_visibility('insert')


		if self.line_is_empty():
			ins_new = self.contents.index( 'insert display linestart' )
		else:
			ins_new = self.idx_linestart()[0]

		self.contents.see(ins_new)
		self.contents.mark_set('insert', ins_new)


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


		# Pressed Cmd + Shift + arrow left or right.
		# Want: select line from cursor.

		# Pressed Cmd + Shift + arrow up or down.
		# Want: select 10 lines from cursor.
		if event.state == 105:

			# self.contents or self.entry
			wid = event.widget

			# Enable select from in entry
			if wid == self.entry:
				return

			# Enable select from in contents
			elif wid == self.contents:

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
							self.contents.compare(idx, '==', 'insert' ),
							self.get_line_col_as_int(index=idx)[1] != 0,
							not len(self.contents.tag_ranges('sel')) > 0
							]

					if all(tests):
						pos = self.contents.index('%s linestart' % idx )
						self.contents.mark_set(self.anchorname, 'insert')
						self.contents.tag_add('sel', pos, 'insert')

					else:
						self.goto_linestart(event=event)


				elif event.keysym == 'Up':
					# As in move_many_lines()
					# Add some delay to get visual feedback
					for i in range(10):
						self.after(i*5, lambda args=['<<SelectPrevLine>>']:
							self.contents.event_generate(*args) )

				elif event.keysym == 'Down':
					for i in range(10):
						self.after(i*5, lambda args=['<<SelectNextLine>>']:
							self.contents.event_generate(*args) )

				else:
					return

			return 'break'


		# Pressed Cmd + arrow left or right.
		# Want: walk tabs.

		# Pressed Cmd + arrow up or down.
		# Want: move cursor 10 lines from cursor.
		elif event.state == 104:

			if event.keysym == 'Right':
				self.walk_tabs(event=event)

			elif event.keysym == 'Left':
				self.walk_tabs(event=event, **{'back':True})

			elif event.keysym == 'Up':
				# As in move_many_lines()
				# Add some delay to get visual feedback
				for i in range(10):
					self.after(i*7, lambda args=['<<PrevLine>>']:
						self.contents.event_generate(*args) )

			elif event.keysym == 'Down':
				for i in range(10):
					self.after(i*7, lambda args=['<<NextLine>>']:
						self.contents.event_generate(*args) )

			else:
				return

			return 'break'


		# Pressed Alt + arrow left or right.
		elif event.state == 112:

			if event.keysym in ['Up', 'Down']: return

			# self.contents or self.entry
			wid = event.widget

			if wid == self.entry:

				if event.keysym == 'Right':
					self.entry.event_generate('<<NextWord>>')

				elif event.keysym == 'Left':
					self.entry.event_generate('<<PrevWord>>')

				else:
					return

			else:
				res = self.move_by_words(event=event)
				return res

			return 'break'


		# Pressed Alt + Shift + arrow left or right.
		elif event.state == 113:

			if event.keysym in ['Up', 'Down']: return

			# self.contents or self.entry
			wid = event.widget

			if wid == self.entry:

				if event.keysym == 'Right':
					self.entry.event_generate('<<SelectNextWord>>')

				elif event.keysym == 'Left':
					self.entry.event_generate('<<SelectPrevWord>>')

				else:
					return

			else:
				res = self.select_by_words(event=event)
				return res

			return 'break'


		# Pressed arrow left or right.
		# If have selection, put cursor on the wanted side of selection.

		# Pressed arrow up or down: return event.
		# +shift: 97: return event.
		elif event.state == 97: return

		elif event.state == 96:

			if event.keysym in ['Up', 'Down']: return

			# self.contents or self.entry
			wid = event.widget
			have_selection = False

			if wid == self.entry:
				have_selection = self.entry.selection_present()

			elif wid == self.contents:
				have_selection = len(self.contents.tag_ranges('sel')) > 0

			else:
				return

			if have_selection:
				if event.keysym == 'Right':
					self.check_sel(event=event)

				elif event.keysym == 'Left':
					self.check_sel(event=event)

				else:
					return

			else:
				return

			return 'break'


		# Pressed Fn
		elif event.state == 64:

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


	def raise_popup(self, event=None):
		if self.state != 'normal':
			self.bell()
			return 'break'

		# Disable popup when not clicked inside Text-widget
		root_y = self.contents.winfo_rooty()
		root_x = self.contents.winfo_rootx()
		max_y = self.contents.winfo_rooty() + self.text_widget_height
		max_x = self.contents.winfo_rootx() + self.contents.winfo_width()

		tests = (root_x <= event.x_root <= max_x,
				root_y <= event.y_root <= max_y)

		if not all(tests): return 'break'


		self.popup.post(event.x_root, event.y_root)
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
				self.clipboard_append(self.contents.get('sel.first', 'sel.last'))

			except tkinter.TclError:
				# is empty
				pass


		if flag_cut:
			self.contents.delete(tkinter.SEL_FIRST, tkinter.SEL_LAST)

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
		have_selection = len(self.contents.tag_ranges('sel')) > 0
		if not have_selection:
			#print('copy fail 1, no selection')
			return 'break'

		# self.contents.selection_get() would not get elided text
		t_orig = self.contents.get('sel.first', 'sel.last')


		# Check if num selection lines > 1
		startline, startcol = map(int, self.contents.index(tkinter.SEL_FIRST).split(sep='.'))
		endline = int(self.contents.index(tkinter.SEL_LAST).split(sep='.')[0])
		numlines = endline - startline
		if not numlines > 1:
			#print('copy fail 2, numlines not > 1')
			return self.copy_fallback(selection=t_orig, flag_cut=flag_cut)


		# Selection start indexes:
		line, col = startline, startcol

		self.indent_selstart = col


		# Check if selstart line not empty
		tmp = self.contents.get('%s.0' % str(line),'%s.0 lineend' % str(line))
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
			t = self.contents.clipboard_get()
			if len(t) == 0:
				return 'break'

		# Clipboard empty
		except tkinter.TclError:
			return 'break'

		if not self.flag_fix_indent or t != self.checksum_fix_indent:
			self.paste_fallback(event=event)
			self.contents.edit_separator()
			#print('paste norm')
			return 'break'

		#print('paste ride')


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
		# Put mark, so one can get end index of new string
		self.line_can_update = False
		self.contents.mark_set('paste', ins_old)
		self.contents.insert(ins_old, s)


		start = self.contents.index( '%s linestart' % ins_old)
		end = self.contents.index( 'paste lineend')

		if self.can_do_syntax():
			self.update_lineinfo()
			self.update_tokens( start=start, end=end)
			self.line_can_update = True


		if not have_selection:
			self.ensure_idx_visibility(ins_old)
			self.wait_for(100)
			self.contents.tag_add('sel', ins_old, 'paste')
			self.contents.mark_set(self.anchorname, 'paste')

		elif selection_started_from_top:
				self.ensure_idx_visibility(ins_old)
		else:
			self.ensure_idx_visibility('insert')


		self.contents.edit_separator()

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

		self.line_can_update = False
		have_selection = False

		if len( self.contents.tag_ranges('sel') ) > 0:
			selstart = self.contents.index( '%s' % tkinter.SEL_FIRST)
			selend = self.contents.index( '%s' % tkinter.SEL_LAST)

			self.contents.tag_remove('sel', '1.0', tkinter.END)
			have_selection = True


		idx_ins = self.contents.index(tkinter.INSERT)
		self.contents.event_generate('<<Paste>>')


		# Selected many lines or
		# one line and cursor is not at the start of next line:
		if len(tmp) > 1:

			s = self.contents.index( '%s linestart' % idx_ins)
			e = self.contents.index( 'insert lineend')
			t = self.contents.get( s, e )


			if self.can_do_syntax():
				self.update_lineinfo()
				self.update_tokens( start=s, end=e, line=t )
				self.line_can_update = True


			if have_selection:
				self.contents.tag_add('sel', selstart, selend)

			else:
				self.contents.tag_add('sel', idx_ins, tkinter.INSERT)

			self.contents.mark_set('insert', idx_ins)


			self.wait_for(100)
			self.ensure_idx_visibility(idx_ins)


		# Selected one line and cursor is at the start of next line:
		elif len(tmp) == 1 and tmp[-1][-1] == '\n':
			s = self.contents.index( '%s linestart' % idx_ins)
			e = self.contents.index( '%s lineend' % idx_ins)
			t = self.contents.get( s, e )


			if self.can_do_syntax():
				self.update_lineinfo()
				self.update_tokens( start=s, end=e, line=t )
				self.line_can_update = True


			if have_selection:
				self.contents.tag_add('sel', selstart, selend)

			else:
				self.contents.tag_add('sel', idx_ins, tkinter.INSERT)

			self.contents.mark_set('insert', idx_ins)


		else:
			s = self.contents.index( '%s linestart' % idx_ins)
			e = self.contents.index( 'insert lineend')
			t = self.contents.get( s, e )

			if self.can_do_syntax():
				self.update_lineinfo()
				self.update_tokens( start=s, end=e, line=t )
				self.line_can_update = True

			if have_selection:
				self.contents.tag_add('sel', selstart, selend)
				self.contents.mark_set('insert', idx_ins)


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
##			But if action one tries to undo is long, cursor will not ever be visible on screen
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



		try:

			ins_orig = self.contents.index('insert')
			# Linenumbers of top and bottom lines currently displayed on screen
			top_line,_ = self.get_line_col_as_int(index='@0,0')
			bot_line,_ = self.get_line_col_as_int(index='@0,65535')
			self.line_can_update = False
			self.wait_for(33)

			func1()

			# Was action func1 not viewable?
			# Then just move the cursor, with opposite action, func2
			ins_line,_ = self.get_line_col_as_int()
			if not ( top_line <= ins_line <= bot_line ):

				func2()

				bot_line_after_func2,_ = self.get_line_col_as_int(index='@0,65535')


				# Check for long actions, like indent. Info is above
				ins_after_func2 = self.contents.index('insert')
				if ins_after_func2 == ins_orig:

					func1()

					# This seems to fix 'screen jumping'
					bot_line_after,_ = self.get_line_col_as_int(index='@0,65535')
					diff = bot_line_after - bot_line_after_func2
					if diff != 0: self.contents.yview_scroll(-diff, 'units')

			else:
				# This seems to fix 'screen jumping'
				bot_line_after,_ = self.get_line_col_as_int(index='@0,65535')
				diff = bot_line_after - bot_line
				if diff != 0: self.contents.yview_scroll(-diff, 'units')



			if self.can_do_syntax():
				( scope_line, ind_defline, idx_scope_start) = self.get_scope_start()
				idx_scope_end = self.get_scope_end(ind_defline, idx_scope_start)

				s = '%s linestart' % idx_scope_start
				e = '%s lineend' % idx_scope_end

				self.update_lineinfo()
				self.update_tokens(start=s, end=e)
				self.line_can_update = True

		except tkinter.TclError:
			self.bell()

		return 'break'


	def undo_override(self, event=None):
		return self.undos(self.contents.edit_undo, self.contents.edit_redo)


	def redo_override(self, event=None):
		return self.undos(self.contents.edit_redo, self.contents.edit_undo)


	def select_all(self, event=None):
		self.contents.tag_remove('sel', '1.0', tkinter.END)
		self.contents.tag_add('sel', 1.0, tkinter.END)
		return 'break'


	def esc_override(self, event):
		'''	Enable toggle fullscreen with Esc.
		'''
		# Safe escing, if mistakenly pressed during search_next
		if self.state in ['normal']:
			if len(self.contents.tag_ranges('sel')) > 0:
				self.contents.tag_remove('sel', '1.0', tkinter.END)
				return 'break'


		if self.wm_attributes().count('-fullscreen') != 0:
			if self.state == 'normal':
				if self.wm_attributes('-fullscreen') == 1:
					self.wm_attributes('-fullscreen', 0)
				else:
					self.wm_attributes('-fullscreen', 1)
				return 'break'

		self.bell()
		return 'break'


	def space_override(self, event):
		'''	Used to bind Space-key when searching or replacing.
		'''
		# Safe spacing, if mistakenly pressed during search_next
		if self.state in ['normal', 'error', 'help']:
			if len(self.contents.tag_ranges('sel')) > 0:
				self.contents.tag_remove('sel', '1.0', tkinter.END)
				return 'break'
			else:
				return


		if self.state not in [ 'search', 'replace', 'replace_all' ]:
			return

		# self.search_focus marks range of focus-tag:
		self.save_pos = self.search_focus[1]
		self.stop_search()

		return 'break'


	def insert_tab(self, event):
		'''	Used to insert tab
		'''

		if self.state in [ 'search', 'replace', 'replace_all', 'goto_def' ]:
			return 'break'

		self.contents.insert(tkinter.INSERT, '\t')

		return 'break'


	def tab_over_indent(self):
		'''	Called from indent()

			If at indent0 of empty line or non empty line:
			move line and/or cursor to closest indentation
		'''
		self.line_can_update = False

		# There should not be selection
		ins = tkinter.INSERT
		line_ins, col_ins = self.get_line_col_as_int(index=ins)

		# Cursor is not at indent0
		if col_ins != 0: return False

		res = self.contents.count(
				'insert linestart', 'insert +1 lines', 'displaylines')

		# Line is wrapped
		if res[0] > 1: return False

		empty = self.line_is_empty()
		tests = [not empty,
				self.contents.get('insert', 'insert +1c').isspace()
				]

		# Line already has indentation
		if all(tests): return False

		if empty:
			self.contents.delete('insert linestart', 'insert lineend')


		patt = r'^[[:blank:]]+[^[:blank:]]'

		(ind_prev, ind_next, pos_prev, pos_next,
		line_prev, line_next, diff_prev, diff_next) = (
			False, False, False, False, False, False, False, False)


		# Indentation of previous
		pos_prev = self.contents.search(patt, ins, stopindex='1.0',
			regexp=True, backwards=True, count=self.search_count_var)

		# self.search_count_var.get() == indentation level +1
		# because pattern matches: not blank and not comment at end of patt
		if pos_prev:
			ind_prev = self.search_count_var.get() -1
			line_prev,_ = self.get_line_col_as_int(index=pos_prev)
			diff_prev = line_ins - line_prev


		# Indentation of next
		pos_next = self.contents.search(patt, ins, stopindex='end',
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
		if len( self.contents.tag_ranges('sel') ) > 0:
			self.contents.tag_remove('sel', '1.0', tkinter.END)

		self.contents.delete('%s -1c wordstart' % 'insert', 'insert')
		return 'break'


	def backspace_override(self, event):
		''' For syntax highlight
			This is executed *before* actual deletion
		'''

		# State is 8 in windows when no other keys are pressed
		if self.state != 'normal' or event.state not in [0, 8]:
			return
		tab=self.tabs[self.tabindex]
		pars = '()[]{}'
		triples = ["'''", '"""']

		# Is there a selection?
		if len(self.contents.tag_ranges('sel')) > 0:
			tmp = self.contents.selection_get()

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

			self.contents.delete( tkinter.SEL_FIRST, tkinter.SEL_LAST )
			return 'break'


		else:
			# Deleting one letter

			# Multiline string check
			line = self.contents.get( 'insert linestart', 'insert lineend')
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


		# First an easy case:
		if col == 0:
			self.contents.insert(tkinter.INSERT, '\n')
			self.contents.see(f'{line+1}.0')
			self.contents.edit_separator()
			return 'break'


		tmp = self.contents.get('%s.0' % str(line),'%s.0 lineend' % str(line))

		# Then one special case: check if cursor is inside indentation,
		# and line is not empty.
		if tmp[:col].isspace() and not tmp[col:].isspace():
			self.contents.insert(tkinter.INSERT, '\n')
			self.contents.insert('%s.0' % str(line+1), tmp[:col])
			self.contents.see(f'{line+1}.0')
			self.contents.edit_separator()
			return 'break'

		else:
			# rstrip space to prevent indentation sailing.
			if tmp[col:].isspace():
				self.contents.delete(tkinter.INSERT, 'insert lineend')

			for i in range(len(tmp[:col]) + 1):
				if tmp[i] != '\t':
					break

			# Manual newline because return is overrided.
			self.contents.insert(tkinter.INSERT, '\n')
			self.contents.insert(tkinter.INSERT, i*'\t')
			self.contents.see(f'{line+1}.0')
			self.contents.edit_separator()
			return 'break'


	def sbset_override(self, *args):
		'''	Fix for: not being able to config slider min-size
		'''
		self.scrollbar.set(*args)

##		h = self.text_widget_height
##
##		# Relative position (tuple on two floats) of
##		# slider-top (a[0]) and -bottom (a[1]) in scale 0-1, a[0] is smaller:
##		a = self.scrollbar.get()
##
##		# current slider size:
##		# (a[1]-a[0])*h
##
##		# want to set slider size to at least p (SLIDER_MINSIZE) pixels,
##		# by adding relative amount(0-1) of d to slider, that is: d/2 to both ends:
##		# ( a[1]+d/2 - (a[0]-d/2) )*h = p
##		# a[1] - a[0] + d = p/h
##		# d = p/h - a[1] + a[0]
##
##
##		d = SLIDER_MINSIZE/h - a[1] + a[0]
##
##		if h*(a[1] - a[0]) < SLIDER_MINSIZE:
##			self.scrollbar.set(a[0], a[1]+d)

		self.update_linenums()

########## Overrides End
########## Utilities Begin

	def insert_inspected(self):
		''' Tries to inspect selection. On success: opens new tab and pastes lines there.
			New tab can be safely closed with ctrl-d later, or saved with new filename.

			Note: calls importlib.import_module() on target

		'''
		try:
			target = self.contents.selection_get()
		except tkinter.TclError:
			self.bell()
			return 'break'

		target = target.strip()

		if not len(target) > 0:
			self.bell()
			return 'break'


		is_module = False

		try:
			mod = importlib.import_module(target)
			is_module = True
			filepath = inspect.getsourcefile(mod)

			if not filepath:
				# For example: readline
				self.bell()
				print('Could not inspect:', target, '\nimport and use help()')
				return 'break'

			try:
				with open(filepath, 'r', encoding='utf-8') as f:
					fcontents = f.read()

					self.line_can_update = False

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

						# This flag is used in handle_search_entry()
						curtab.inspected = True

					else:
						curtab.contents = fcontents


					curtab.text_widget.insert('1.0', curtab.contents)
					curtab.text_widget.mark_set('insert', curtab.position)
					curtab.text_widget.see(curtab.position)

					if self.can_do_syntax(curtab):
						self.update_lineinfo(curtab)
						a = self.get_tokens(curtab)
						self.insert_tokens(a, tab=curtab)
						self.line_can_update = True

					curtab.text_widget.focus_set()
					self.contents.edit_reset()
					self.contents.edit_modified(0)

					return 'break'


			except (EnvironmentError, UnicodeDecodeError) as e:
				print(e.__str__())
				print(f'\n Could not open file: {filepath}')
				self.bell()
				return 'break'

		except ModuleNotFoundError:
			print(f'\n Is not a module: {target}')
			# will continue to next try-block
		except TypeError as ee:
			print(ee.__str__())
			self.bell()
			return 'break'


		if not is_module:

			try:
				modulepart = target[:target.rindex('.')]
				object_part = target[target.rindex('.')+1:]
				mod = importlib.import_module(modulepart)
				target_object = getattr(mod, object_part)

				l = inspect.getsourcelines(target_object)
				t = ''.join(l[0])

				self.line_can_update = False

				# new_tab() calls tab_close()
				# and updates self.tabindex
				self.new_tab()

				curtab = self.tabs[self.tabindex]

				indentation_is_alien, indent_depth = self.check_indent_depth(t)

				tmp = t.splitlines(True)
				tmp[:] = [self.tabify(line, width=indent_depth) for line in tmp]
				tmp = ''.join(tmp)
				curtab.contents = tmp

				curtab.text_widget.insert('1.0', curtab.contents)
				curtab.text_widget.mark_set('insert', curtab.position)
				curtab.text_widget.see(curtab.position)


				# This flag is used in handle_search_entry()
				curtab.inspected = True

				if self.can_do_syntax(curtab):
					self.update_lineinfo(curtab)
					a = self.get_tokens(curtab)
					self.insert_tokens(a, tab=curtab)
					self.line_can_update = True

				curtab.text_widget.focus_set()
				self.contents.edit_reset()
				self.contents.edit_modified(0)

				return 'break'


			# from rindex()
			except ValueError:
				self.bell()
				return 'break'

			except Exception as e:
				self.bell()
				print(e.__str__())
				return 'break'

		return 'break'


	def tabify_lines(self, event=None):
		tab = self.tabs[self.tabindex]

		try:
			startline = self.contents.index(tkinter.SEL_FIRST).split(sep='.')[0]
			endline = self.contents.index(tkinter.SEL_LAST).split(sep='.')[0]

			start = '%s.0' % startline
			end = '%s.0 lineend' % endline
			tmp = self.contents.get(start, end)

			indentation_is_alien, indent_depth = self.check_indent_depth(tmp)

			tmp = tmp.splitlines()

			if indentation_is_alien:
				tmp[:] = [self.tabify(line, width=indent_depth) for line in tmp]

			else:
				tmp[:] = [self.tabify(line) for line in tmp]


			tmp = ''.join(tmp)


			self.line_can_update = False
			self.contents.delete(start, end)
			self.contents.insert(start, tmp)

			if self.can_do_syntax(tab):
				self.update_lineinfo(tab)
				self.update_tokens(start=start, end=end, tab=tab)
				self.line_can_update = True

			self.contents.edit_separator()


		except tkinter.TclError as e:
			print(e)

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
			# Set branch name lenght to 5.
			# Reason: avoid ln_widget geometry changes
			# when showing capslock-state in btn_git.
			if len(branch) < 5:
				diff = 5-len(branch)
				t=1
				for i in range(diff):
					if t > 0:
						branch += ' '
					else:
						branch = ' ' + branch
					t *= -1

			self.btn_git.config(text=branch, disabledforeground='')

			if 'main' in self.branch or 'master' in self.branch:
				self.btn_git.config(disabledforeground='brown1')

		else:
			self.btn_git.config(bitmap='info', disabledforeground='')


	def flash_btn_git(self):
		''' Flash text and enable canceling flashing later.
		'''

		self.btn_git.config(bitmap='')
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

			l1 = lambda kwargs={'text': 5*' ', 'disabledforeground': 'brown1'}: self.btn_git.config(**kwargs)
			l2 = lambda kwargs={'text': 'CAPS '}: self.btn_git.config(**kwargs)


			###
			l3 = lambda kwargs={'bg':fg, 'fg':bg}: self.contents.config(**kwargs)
			l4 = lambda kwargs={'bg':bg, 'fg':fg}: self.contents.config(**kwargs)

			c3 = self.after(t1, l3)
			c4 = self.after(t2, l4)
			self.to_be_cancelled.append(c3)
			self.to_be_cancelled.append(c4)
			###


			c1 = self.after(t1, l1)
			c2 = self.after(t2, l2)
			self.to_be_cancelled.append(c1)
			self.to_be_cancelled.append(c2)


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
				self.capslock = False

				# If quickly pressed CapsLock off,
				# cancel flashing started at the end of this callback.
				for item in self.to_be_cancelled[:]:
					self.after_cancel(item)
					self.to_be_cancelled.remove(item)


				# Put Git-branch name back if on one
				self.restore_btn_git()
				bg, fg = self.themes[self.curtheme]['normal_text'][:]
				self.contents.config(bg=bg, fg=fg)

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
				for item in self.to_be_cancelled[:]:
					self.after_cancel(item)
					self.to_be_cancelled.remove(item)


				# Put Git-branch name back if on one
				self.restore_btn_git()
				bg, fg = self.themes[self.curtheme]['normal_text'][:]
				self.contents.config(bg=bg, fg=fg)


			# CapsLock is being turned on
			else:
				self.capslock = True
				self.bell()
				self.flash_btn_git()

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

		if self.is_pyfile():
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
		index_line_contents = self.contents.get( '%s linestart' % pos,
			'%s lineend' % pos )


		# If posline is empty,
		# Find next(up) non empty, uncommented line
		#############################################
		if index_line_contents.isspace() or index_line_contents == '' \
			or index_line_contents.strip().startswith('#') \
			or 'strings' in self.contents.tag_names(pos):

			blank_range = '{0,}'
			p1 = r'^[[:blank:]]%s' % blank_range
			# Not blank and not comment
			p2 = r'[^[:blank:]#]'

			p = p1 + p2


			while pos:
				try:
					pos = self.contents.search(p, pos, stopindex='1.0',
							backwards=True, regexp=True)

				except tkinter.TclError as e:
					print(e)
					pos = False
					break

				if not pos: break

				if 'strings' in self.contents.tag_names(pos):
					#print('strings1', pos)
					continue

				break
				#####

			if not pos:
				scope_path = '__main__()'
				return scope_path

			index_line_contents = self.contents.get( '%s linestart' % pos,
				'%s lineend' % pos )
			#########################


		for char in index_line_contents:
			if char in ['\t']: ind_last_line += 1
			else: break


		# Check possible early defline
		##################################################
		if scope_name := self.line_is_defline(index_line_contents):
			scope_path = scope_name

		# Reached indent0,
		# Since not actually looking next defline but scope-path of index
		# --> exit
		if ind_last_line == 0:
			if not scope_path: scope_path = '__main__()'
			return scope_path
		############################
		# Below this, real start


		flag_finish = False

		if ind_last_line > 1:
			# Why: [^[:blank:]#] instead of: [acd], as from: (a)sync, (c)lass, (d)ef?
			# Reason: need to update indentation level of pos line or else path
			# would be corrupted by possible nested function definitions (function in function).
			patt = r'^[[:blank:]]{1,%d}[^[:blank:]#]' % (ind_last_line-1)

		# ind_last_line == 1
		# No need to update indentation level of pos line anymore.
		else:
			# Can now change pattern to:
			# From start of line, [acd], as from: (a)sync, (c)lass or (d)ef
			patt = r'^[acd]'
			flag_finish = True


		flag_match = False

		while pos:
			try:
				# Count is tkinter.IntVar which is used to
				# count indentation level of matched line.
				pos = self.contents.search(patt, pos, stopindex='1.0',
					backwards=True, regexp=True, count=self.search_count_var)

			except tkinter.TclError as e:
				print(e)
				break

			if not pos: break

			elif 'strings' in self.contents.tag_names(pos):
				#print('strings2', pos)
				continue

			# -1: remove terminating char(not blank not #) from matched char count
			# Check patt if interested.
			ind_curline = self.search_count_var.get() - 1


			# Find previous line that:
			# Has one (or more) indentation level smaller indentation than ind_last_line
			# 	Then if it also is definition line --> add to scopepath
			# 	update ind_last_line
			def_line_contents = tmp = self.contents.get( pos, '%s lineend' % pos )


			########
			if scope_name := self.line_is_defline(def_line_contents):
				if scope_path != '':
					scope_path = scope_name +'.'+ scope_path
				else:
					scope_path = scope_name

				flag_match = True
			########


			# Update search pattern and indentation of matched pos line
			if not flag_finish: ind_last_line = ind_curline


			# SUCCESS
			if flag_match and flag_finish:
				break


			flag_match = False


			if ind_curline > 1:
				patt = r'^[[:blank:]]{1,%d}[^[:blank:]#]' % (ind_curline-1)

			# ind_last_line == 1
			# No need to update indentation level of pos line anymore.
			else:
				patt = r'^[acd]'
				flag_finish = True

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
			#	print_search_help()
			#
			#### END OF WHILE #########


		if scope_path == '':
			scope_path = '__main__()'
			return scope_path
		else:
			return scope_path + '()'


	def get_scope_start(self, index='insert', absolutely_next=False):
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
		safe_index = self.get_safe_index(index)
		pos = '%s linestart' % safe_index

		while pos:
			try:
				pos = self.contents.search(patt, pos, stopindex='1.0',
						regexp=True, backwards=True)

			except tkinter.TclError as e:
				print(e)
				break

			if not pos:
				return '__main__()', 0, '1.0'

			if 'strings' in self.contents.tag_names(pos):
				#print('strings3', pos)
				continue

			break
			###################


		s, e = '%s linestart' % pos, '%s lineend' % pos

		if r := self.line_is_elided(pos): e = r[0]

		pos_line_contents = self.contents.get(s, e)


		ind_last_line = 0
		for char in pos_line_contents:
			if char in ['\t']: ind_last_line += 1
			else: break

		# Check if defline already
		if res := self.line_is_defline(pos_line_contents):
			idx = self.idx_linestart(pos)[0]
			return pos_line_contents.strip(), ind_last_line, idx

		### Stage 1 End ########


		patt = r'^[acd]'

		if absolutely_next:
			patt = r'^[[:blank:]]{0,}[acd]'
			pass
		elif ind_last_line == 1:
			pass
		else:
			if ind_last_line > 1:
				# Stage 2: Search backwards(up) from pos updating indentation level until:
				# defline with ind_last_line-1 blanks or less
				blank_range = '{0,%d}' % (ind_last_line - 1)

			# ind_last_line == 0:
			else:
				# Curline is not defline
				# --> can search with: '{1,}'
				blank_range = '{1,}'


			p1 = r'^[[:blank:]]%s' % blank_range
			# Not blank, not comment
			p2 = r'[^[:blank:]#]'
			patt = p1 + p2


		while pos:
			try:
				pos = self.contents.search(patt, pos, stopindex='1.0',
						regexp=True, backwards=True, count=self.search_count_var)

			except tkinter.TclError as e:
				print(e)
				break

			if not pos:
				return '__main__()', 0, '1.0'

			elif 'strings' in self.contents.tag_names(pos):
				#print('strings4', pos)
				continue

			################
			# -1: remove terminating char(not blank not #) from matched char count
			# Check patt if interested.
			ind_curline = self.search_count_var.get() - 1

			# Find previous line that:
			# Has one (or more) indentation level smaller indentation than ind_last_line
			# 	Then if it also is definition line --> success
			# 	update ind_last_line
			def_line_contents = self.contents.get( pos, '%s lineend' % pos )

			#####
			if res := self.line_is_defline(def_line_contents):
				idx = self.idx_linestart(pos)[0]

				# SUCCESS
				return def_line_contents.strip(), ind_curline, idx
			#####

			elif absolutely_next: pass

			# Update search pattern and indentation of matched pos line
			elif ind_curline > 1:
				patt = r'^[[:blank:]]{0,%d}[^[:blank:]#]' % (ind_curline-1)

			# ind_last_line == 1
			# No need to update indentation level of pos line anymore.
			else:
				patt = r'^[acd]'

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
			return self.contents.index(r[1])


		# Stage 1: Search forwards(down) from index for:
		# pos = Uncommented line with ind_def_line blanks or less
		blank_range = '{0,%d}' % ind_def_line
		p1 = r'^[[:blank:]]%s' % blank_range
		# Not blank, not comment
		p2 = r'[^[:blank:]#]'

		patt = p1 + p2

		# Skip possible defline at index
		pos = '%s +1 chars' % index


		while pos:
			try:
				pos = self.contents.search(patt, pos, stopindex='end', regexp=True)

			except tkinter.TclError as e:
				print(e)
				pos = 'end'
				break

			if not pos:
				pos = 'end'
				break

			if 'strings' in self.contents.tag_names(pos):
				#print('strings5', pos)
				# Dont want rematch curline
				pos = '%s +1 lines' % pos
				continue

			break
			### Stage 1 End ###

		# Stage 2: Search backwards(up) from pos up to index for:
		# Line with ind_def_line+1 blanks or more
		blank_range = '{%d,}' % (ind_def_line + 1)
		p1 = r'^[[:blank:]]%s' % blank_range
		# Not blank
		p2 = r'[^[:blank:]]'
		patt = p1 + p2


		#print(patt, pos)
		while pos:
			try:
				pos = self.contents.search(patt, pos, stopindex=index,
						regexp=True, backwards=True)

			except tkinter.TclError as e:
				print(e)
				pos = 'end'
				break

			if not pos:
				pos = 'end'
				break

			if 'strings' in self.contents.tag_names(pos):
				#print('strings4', pos)
				continue

			# ON SUCCESS
			break
			### Stage 2 End ###

		pos = self.contents.index('%s lineend' % pos)
		return pos


########## Utilities End
########## Gotoline etc Begin

	def stop_goto_def(self, event=None):
		self.bind("<Escape>", self.esc_override)
		self.contents.unbind( "<Double-Button-1>", funcid=self.bid )
		self.contents.config(state='normal')
		self.state = 'normal'

		# Set cursor pos
		curtab = self.tabs[self.tabindex]
		try:
			if self.save_pos:
				line = self.save_pos
				curtab.position = line
				self.save_pos = None
			else:
				line = curtab.position

			self.contents.focus_set()
			self.contents.mark_set('insert', line)
			self.wait_for(100)
			self.ensure_idx_visibility(line)

		except tkinter.TclError:
			curtab.position = self.contents.index(tkinter.INSERT)

		return 'break'


	def goto_def(self, event=None):
		''' Get word under cursor or use selection and
			go to function definition
		'''

		if (not self.is_pyfile()) or (self.state not in ['normal', 'search']):
			self.bell()
			return 'break'

		c = self.contents
		have_selection = len(c.tag_ranges('sel')) > 0


		if have_selection:
			word_at_cursor = c.selection_get()
		else:
			word_at_cursor = c.get('insert wordstart', 'insert wordend')

		word_at_cursor = word_at_cursor.strip()

		if word_at_cursor == '':
			return 'break'


		#print(word_at_cursor)
		# https://www.tcl.tk/man/tcl9.0/TclCmd/re_syntax.html#M31
		patt_indent = r'^#*[[:blank:]]*'
		patt_keywords = r'(?:async[[:blank:]]+)?def[[:blank:]]+'
		search_word = patt_indent + patt_keywords + word_at_cursor + r'\('

		try:
			pos = self.contents.search(search_word, '1.0', regexp=True)

		except tkinter.TclError:
			return 'break'

		if pos:
			#self.contents.mark_set('insert', pos)
			self.contents.focus_set()
			self.wait_for(100)
			self.ensure_idx_visibility(pos)

			if self.state == 'search': pass
			else:
				# Save cursor pos
				tab = self.tabs[self.tabindex]
				try: tab.position = self.contents.index(tkinter.INSERT)
				except tkinter.TclError: pass
				self.save_pos = None

				self.bind("<Escape>", self.stop_goto_def)
				self.bid = self.contents.bind("<Double-Button-1>",
					func=lambda event: self.update_curpos(event, **{'on_stop':self.stop_goto_def}),
						add=True )

				self.contents.config(state='disabled')
				self.state = 'goto_def'

			if have_selection:
				self.contents.tag_remove( 'sel', '1.0', tkinter.END )

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
					pos_mark = self.contents.index(mark_name)
					if self.contents.compare(pos_mark, '!=', 'insert' ):
						pos = pos_mark
						break

				mark_name = markfunc(mark_name)

			return pos

		# Start
		mark_func = self.contents.mark_next

		if back:
			mark_func = self.contents.mark_previous

		pos = get_mark('insert', mark_func)

		# At file_startend, try again from beginning of other end
		if not pos:
			start = '1.0'
			if back: start = tkinter.END
			pos = get_mark(start, mark_func)

		# No bookmarks in this tab
		if not pos:
			self.wait_for(100)
			self.bell()
			return 'break'


		try:
			self.contents.mark_set('insert', pos)
			self.wait_for(100)
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
			go to that line.

		'''

		try:
			# Get stuff after prompt
			tmp = self.entry.get()
			idx = self.entry.len_prompt
			tmp = tmp[idx:].strip()


			if tmp in ['-1', '']:
				line = tkinter.END

			elif '-' not in tmp:
				line = tmp + '.0'

			elif tmp[0] == '-' and '-' not in tmp[1:] and len(tmp) > 1:

				if int(tmp[1:]) < int(self.entry.endline):
					line = self.entry.endline + '.0 -%s lines' % tmp[1:]
				else:
					line = tkinter.END
			else:
				line = tkinter.INSERT

			self.tabs[self.tabindex].position = line


		except tkinter.TclError as e:
			print(e)

		self.stop_gotoline()
		return 'break'


	def stop_gotoline(self, event=None):
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
			self.contents.focus_set()
			self.contents.mark_set('insert', line)
			self.wait_for(100)
			self.ensure_idx_visibility(line)

			self.contents.tag_remove('sel', '1.0', tkinter.END)


		except tkinter.TclError:
			curtab.position = '1.0'

		return 'break'


	def gotoline(self, event=None):
		if self.state not in ['normal']:
			self.bell()
			return 'break'

		self.state = 'gotoline'

		try:
			pos = self.contents.index(tkinter.INSERT)
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
		max_idx = self.entry.len_prompt + len(self.entry.endline) + 1

		if int(i) < self.entry.len_prompt:
			self.entry.selection_clear()
			self.entry.icursor(self.entry.len_prompt)

			return S == ''

		elif len(P) > max_idx:
			return S == ''

		elif S.isdigit() or S == '-':
			return True

		else:
			return S == ''


########## Gotoline etc End
########## Save and Load Begin

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
			self.contents.bind( "<Mod1-Key-Return>", self.load)
		else:
			self.contents.bind( "<Alt-Return>", self.load)

		self.state = 'normal'


		for widget in [self.entry, self.btn_open, self.btn_save, self.contents]:
			widget.config(state='normal')

		return 'break'


	def loadfile(self, filepath):
		''' filepath is pathlib.Path
			If filepath is python-file, convert indentation to tabs.

			File is always opened to *current* tab
		'''

		filename = filepath
		openfiles = [tab.filepath for tab in self.tabs]
		curtab = self.tabs[self.tabindex]

		for widget in [self.entry, self.btn_open, self.btn_save, self.contents]:
			widget.config(state='normal')


		if filename in openfiles:
			print(f'file: {filename} is already open')
			self.bell()
			self.entry.delete(0, tkinter.END)

			if curtab.filepath != None:
				self.entry.insert(0, curtab.filepath)
				self.entry.xview_moveto(1.0)

			return


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
				self.remove_bookmarks(all_tabs=False)

				######
				self.line_can_update = False

				self.entry.delete(0, tkinter.END)
				if curtab.filepath != None:
					self.entry.insert(0, curtab.filepath)
					self.entry.xview_moveto(1.0)

				self.contents.delete('1.0', tkinter.END)
				self.contents.insert(tkinter.INSERT, curtab.contents)
				self.contents.mark_set('insert', '1.0')
				self.contents.see('1.0')

				self.line_can_update = True

				if self.can_do_syntax(curtab):
					self.update_lineinfo(curtab)
					self.insert_tokens(self.get_tokens(curtab), tab=curtab)
					self.line_can_update = True

				self.contents.edit_reset()
				self.contents.edit_modified(0)
				######

		except (EnvironmentError, UnicodeDecodeError) as e:
			print(e.__str__())
			print(f'\n Could not open file: {filename}')
			self.entry.delete(0, tkinter.END)

			if curtab.filepath != None:
				self.entry.insert(0, curtab.filepath)
				self.entry.xview_moveto(1.0)

		return


	def load(self, event=None):
		'''	Get just the filename,
			on success, pass it to loadfile()

			File is always opened to *current* tab
		'''

		if self.state != 'normal':
			self.bell()
			return 'break'

		elif self.tabs[self.tabindex].type == 'normal':
			if not self.save(activetab=True):
				self.bell()
				return 'break'


		if len(self.contents.tag_ranges('sel')) > 0:
			self.contents.tag_remove('sel', '1.0', 'end')


		# Called by: Open-button(event==None) or shortcut
		if (not event) or (event.widget != self.entry):

			self.state = 'filedialog'

			shortcut = "<Mod1-Key-Return>"
			if self.os_type != 'mac_os':
				shortcut = "<Alt-Return>"

			self.contents.bind( shortcut, self.do_nothing_without_bell)

			for widget in [self.entry, self.btn_open, self.btn_save, self.contents]:
				widget.config(state='disabled')

			self.tracevar_filename.set('empty')
			self.tracefunc_name = self.tracevar_filename.trace_add('write', self.trace_filename)

			p = pathlib.Path().cwd()

			if self.lastdir:
				p = p / self.lastdir

			filetop = tkinter.Toplevel()
			filetop.title('Select File')
			self.to_be_closed.append(filetop)


			fd = fdialog.FDialog(filetop, p, self.tracevar_filename, font=self.font, menufont=self.menufont, sb_widths=(self.scrollbar_width, self.elementborderwidth), os_type=self.os_type)

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


	def save_forced(self):
		''' Called from run() or quit_me()

			If python-file, convert indentation to tabs.
		'''
		# Dont do anything when widget is not alive
		if not self.__class__.alive: raise ValueError

		# Dont want contents to be replaced with errorlines or help.
		last_state = self.state

		while self.state != 'normal':
			self.contents.event_generate('<Escape>')

			# Is state actually changing, or is it stuck == there is a bug
			# --> cancel
			if self.state == last_state:
				print(r'\nState is not changing, currently: ', self.state)

				return False

			last_state = self.state



		res = True

		for tab in self.tabs:
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
				self.contents.focus_set()
				self.contents.mark_set('insert', line)
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


		fpath_in_entry = pathlib.Path().cwd() / tmp_entry
		##############

		try:
			pos = self.contents.index(tkinter.INSERT)
		except tkinter.TclError:
			pos = '1.0'


		oldtab = self.tabs[self.tabindex]
		oldtab.position = pos

		# Update oldtabs contents
		# [:-1]: text widget adds dummy newline at end of file when editing
		cur_contents = oldtab.contents = self.contents.get('1.0', tkinter.END)[:-1]
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

					if self.can_do_syntax(tab=oldtab):
						self.update_lineinfo(tab=oldtab)
						self.line_can_update = False
						self.insert_tokens(self.get_tokens(oldtab), tab=oldtab)
						self.line_can_update = True


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


				self.line_can_update = False

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
					self.line_can_update = True


				newtab.text_widget.edit_reset()
				newtab.text_widget.edit_modified(0)


			# Should not happen
			else:
				print('Error in save() while saving tab:')
				print(oldtab)
				return False


		# Not creating a new file
		else:
			# Skip disk-writing
			# Q: When this happens?
			# A: Pressing Save and fpath_in_entry == oldtab.filepath
			#    that is, file exist already on disk
			if not activetab:
				return True

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

	def print_bookmarks(self):

		self.wait_for(100)

		l = sorted([ (mark, self.contents.index(mark)) for mark in self.contents.mark_names() if 'bookmark' in mark], key=lambda x:float(x[1]) )

		for (mark, pos) in l:
			print(mark, pos)

		tab = self.tabs[self.tabindex]
		print(tab.bookmarks)


	def line_is_bookmarked(self, index):
		''' index:	tkinter.Text -index
		'''

		# Find first mark in line
		s = self.contents.index('%s display linestart' % index)
		mark_name = self.contents.mark_next(s)

		# Find first bookmark at or after s
		while mark_name:
			if 'bookmark' not in mark_name:
				mark_name = self.contents.mark_next(mark_name)
			else:
				break

		if mark_name:
			if 'bookmark' in mark_name:
				mark_line,_ = self.get_line_col_as_int(index=mark_name)
				pos_line,_ = self.get_line_col_as_int(index=s)

			if mark_line == pos_line:
				return mark_name

		return False


	def clear_bookmarks(self):
		''' Unsets bookmarks from current tab.

			Does NOT do: tab.bookmarks.clear()
		'''
		for mark in self.contents.mark_names():
			if 'bookmark' in mark:
				self.contents.mark_unset(mark)


	def save_bookmarks(self, tab):
		''' tab: Tab

			Info is in restore_bookmarks
		'''
		tab.bookmarks = list({ tab.text_widget.index(mark) for mark in tab.bookmarks })
		tab.bookmarks.sort()


	def restore_bookmarks(self, tab):
		''' tab: Tab

			When view changes, like in walk_tab(),
			before contents of oldtab gets deleted, its bookmarks
			are saved, but only their index position, not names, about like this:

			oldtab.bookmarks = [ self.contents.index(mark) for mark in oldtab.bookmarks ]

			And after tab has its contents again,
			bookmarks are restored here and tab.bookmarks holds again the names of bookmarks.
		'''

		for i, pos in enumerate(tab.bookmarks):
			tab.text_widget.mark_set('bookmark%d' % i, pos)

		tab.bookmarks.clear()

		for mark in tab.text_widget.mark_names():
			if 'bookmark' in mark:
				tab.bookmarks.append(mark)


	def remove_bookmarks(self, all_tabs=True):
		''' Removes bookmarks from current tab/all tabs
		'''

		tabs = [self.tabs[self.tabindex]]
		if all_tabs: tabs = self.tabs

		for tab in tabs:
			tab.bookmarks.clear()

		self.clear_bookmarks()


	def remove_single_bookmark(self):
		pos_cursor = self.contents.index(tkinter.INSERT)

		if mark_name := self.line_is_bookmarked(pos_cursor):

			self.contents.mark_unset(mark_name)
			tab = self.tabs[self.tabindex]
			tab.bookmarks.remove(mark_name)

			# Keeping right naming of bookmarks in tab.bookmarks is quite tricky
			# when removing and adding bookmarks in the same tab, without changing view.
			# Seems like the line: self.clear_bookmarks solves the issue.
			# Bookmarks where working right, but if doing self.print_bookmarks
			# after removing and adding bookmarks, it would look odd with ghost duplicates.
			self.save_bookmarks(tab)
			self.clear_bookmarks()
			self.restore_bookmarks(tab)

			return True

		else:
			return False


	def toggle_bookmark(self, event=None):
		''' Add/Remove bookmark at cursor position

			Bookmark is string, name of tk text mark like: 'bookmark11'
			It is appended to tab.bookmarks
		'''
		tests = (
				self.state not in [ 'normal', 'search', 'replace', 'goto_def' ],
				not self.contents.bbox('insert')
				)

		if any(tests):
			self.bell()
			return 'break'


		pos = tkinter.INSERT
		if self.state != 'normal':
			# 'focus'
			pos = self.search_focus[0]


		s = self.contents.index('%s display linestart' % pos)

		# If there is bookmark, remove it
		if self.remove_single_bookmark():
			self.bookmark_animate(s, remove=True)
			return 'break'


		curtab = self.tabs[self.tabindex]
		new_mark = 'bookmark' + str(len(curtab.bookmarks))
		self.contents.mark_set( new_mark, s )
		curtab.bookmarks.append(new_mark)

		self.bookmark_animate(s)
		return 'break'


	def bookmark_animate(self, idx_linestart, remove=False):
		''' Animate on Add/Remove bookmark

			Called from: toggle_bookmark()
		'''

		s = idx_linestart

		self.contents.edit_separator()

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
			width_char = self.font.measure('A')
			width_scr = self.contents.winfo_width()
			num_chars = width_scr // width_char

			if wanted_num_chars > num_chars:
				wanted_num_chars = want = num_chars



			flag_added_space = False
			flag_changed_contents_state = False


			# If line has not enough characters
			if (diff := want - col) > 0:

				# Check not over screen width 2
				if (self.contents.bbox(e0)[0] + diff * width_char) < (width_scr - width_char):

					# Add some space so we can tag more estate from line. It is later removed.
					flag_added_space = True

					# Searching, Replacing
					if self.contents.cget('state') == 'disabled':

						self.contents.config(state='normal')
						flag_changed_contents_state = True

					self.contents.insert(e0, diff * ' ')


				# Some deep indentation and small screen size combo
				# --> Line has enough characters, just update step
				else:
					wanted_num_chars = 0
					t = self.contents.get(s, e0)
					for char in t:
						wanted_num_chars += 1

					# Recalculate step
					step = time_wanted // wanted_num_chars
					want = wanted_num_chars



			e = self.idx_lineend()

			bg, fg = self.themes[self.curtheme]['sel'][:]
			self.contents.tag_config('animate', background=bg, foreground=fg)
			self.contents.tag_raise('animate')
			self.contents.tag_remove('animate', '1.0', tkinter.END)


			# Animate removing bookmark
			if remove:
				# 1: Tag wanted_num_chars from start. In effect this, but in loop
				# to enable use of after(), to get animating effect.
				# self.contents.tag_add('sel', s, '%s +%d chars' % (s, wanted_num_chars) )

				for i in range(wanted_num_chars):
					p0 = '%s +%d chars' % (s, wanted_num_chars - i-1 )
					p1 = '%s +%d chars' % (s, wanted_num_chars - i )

					self.after( (i+1)*step, lambda args=['animate', p0, p1]:
							self.contents.tag_add(*args) )

				# 2: Same story as when adding, just note some time has passed
				for i in range(wanted_num_chars):
					p0 = '%s +%d chars' % (s, wanted_num_chars - i-1 )
					p1 = '%s +%d chars' % (s, wanted_num_chars - i )

					self.after( ( time_wanted + (i+1)*step ), lambda args=['animate', p0, p1]:
							self.contents.tag_remove(*args) )


				if flag_added_space:
					self.after( (2*time_wanted + 30), lambda args=[e0, '%s display lineend' % e0]:
							self.contents.delete(*args) )

					if flag_changed_contents_state:
						self.after( (2*time_wanted + 40), lambda kwargs={'state':'disabled'}:
								self.contents.config(**kwargs) )



			# Animate adding bookmark
			else:
				# Info is in remove-section above
				for i in range(wanted_num_chars):
					p0 = '%s +%d chars' % (s, i)
					p1 = '%s +%d chars' % (s, i+1)

					self.after( (i+1)*step, lambda args=['animate', p0, p1]:
							self.contents.tag_add(*args) )


				self.after( (time_wanted + 300), lambda args=['animate', '1.0', tkinter.END]:
						self.contents.tag_remove(*args) )


				if flag_added_space:
					self.after( (time_wanted + 330), lambda args=[e0, '%s display lineend' % e0]:
							self.contents.delete(*args) )

					if flag_changed_contents_state:
						self.after( (time_wanted + 340), lambda kwargs={'state':'disabled'}:
								self.contents.config(**kwargs) )



		except tkinter.TclError as ee:
			print(ee)


		self.contents.edit_separator()

		######## bookmark_animate End #######


	def stop_help(self, event=None):
		self.state = 'normal'

		self.entry.config(state='normal')
		self.contents.config(state='normal')
		self.btn_open.config(state='normal')
		self.btn_save.config(state='normal')


		self.tab_close(self.tabs[self.tabindex])

		self.tabs.pop()
		self.tabindex = self.oldindex

		self.tab_open(self.tabs[self.tabindex])


		self.bind("<Escape>", self.esc_override)
		self.bind("<Button-%i>" % self.right_mousebutton_num,
			lambda event: self.raise_popup(event))


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
		self.contents.config(state='disabled')
		self.btn_open.config(state='disabled')
		self.btn_save.config(state='disabled')

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


	def can_expand_word(self):
		'''	Called from indent() and unindent()
		'''
		ins = tkinter.INSERT
		# There should not be selection, checked before call in caller.

		# Check previous char
		idx = self.contents.index(ins)
		col = int(idx.split(sep='.')[1])

		if col > 0:
			prev_char = self.contents.get( ('%s -1 char') % ins, '%s' % ins )

			if prev_char in self.expander.wordchars:
				return True

		return False


	def indent(self, event=None):
		if self.state in [ 'search', 'replace', 'replace_all', 'goto_def' ]:
			return 'break'

		if len(self.contents.tag_ranges('sel')) == 0:

			if self.can_expand_word():
				self.expander.expand_word(event=event)

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

				return 'break'

			# If at start of line: move line to match indent of previous line.
			elif indentation_level := self.tab_over_indent():
				self.contents.insert(tkinter.INSERT, indentation_level * '\t')
				self.line_can_update = True
				return 'break'

			else:
				self.line_can_update = True
				return

		try:
			self.line_can_update = False
			startline = int(self.contents.index(tkinter.SEL_FIRST).split(sep='.')[0])
			endline = int(self.contents.index(tkinter.SEL_LAST).split(sep='.')[0])
			i = self.contents.index(tkinter.INSERT)


			if len(self.contents.tag_ranges('sel')) != 0:

				# Is start of selection not viewable?
				if not self.contents.bbox(tkinter.SEL_FIRST):

					self.wait_for(150)
					self.ensure_idx_visibility(tkinter.SEL_FIRST, back=4)
					self.wait_for(100)


			for linenum in range(startline, endline+1):
				self.contents.mark_set(tkinter.INSERT, '%s.0' % linenum)
				self.contents.insert(tkinter.INSERT, '\t')


			if startline == endline:
				self.contents.mark_set(tkinter.INSERT, '%s +1c' %i)

			elif self.contents.compare(tkinter.SEL_FIRST, '<', tkinter.INSERT):
				self.contents.mark_set(tkinter.INSERT, tkinter.SEL_FIRST)

			self.ensure_idx_visibility('insert', back=4)
			self.contents.edit_separator()

		except tkinter.TclError:
			pass

		self.line_can_update = True

		return 'break'


	def unindent(self, event=None):
		if self.state in [ 'search', 'replace', 'replace_all', 'goto_def' ]:
			return 'break'


		if len(self.contents.tag_ranges('sel')) == 0:

			if self.can_expand_word():
				self.expander.expand_word(event=event)

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

				return 'break'

		try:
			self.line_can_update = False

			# Unindenting curline only:
			if len(self.contents.tag_ranges('sel')) == 0:
				startline = int(self.contents.index(tkinter.INSERT).split(sep='.')[0])
				endline = startline

			else:
				startline = int(self.contents.index(tkinter.SEL_FIRST).split(sep='.')[0])
				endline = int(self.contents.index(tkinter.SEL_LAST).split(sep='.')[0])

			i = self.contents.index(tkinter.INSERT)

			# Check there is enough space in every line:
			flag_continue = True

			for linenum in range(startline, endline+1):
				tmp = self.contents.get('%s.0' % linenum, '%s.0 lineend' % linenum)

				# Check that every *non empty* line has tab-char at beginning of line
				if len(tmp) != 0 and tmp[0] != '\t':
					flag_continue = False
					break

			if flag_continue:

				if len(self.contents.tag_ranges('sel')) != 0:

					# Is start of selection not viewable?
					if not self.contents.bbox(tkinter.SEL_FIRST):

						self.wait_for(150)
						self.ensure_idx_visibility('insert', back=4)
						self.wait_for(100)


				for linenum in range(startline, endline+1):
					tmp = self.contents.get('%s.0' % linenum, '%s.0 lineend' % linenum)

					if len(tmp) != 0:
						if len(self.contents.tag_ranges('sel')) != 0:
							self.contents.mark_set(tkinter.INSERT, '%s.0' % linenum)
							self.contents.delete(tkinter.INSERT, '%s+%dc' % (tkinter.INSERT, 1))

						else:
							self.contents.delete( '%s.0' % linenum, '%s.0 +1c' % linenum)


				# Is selection made from down to top or from right to left?
				if len(self.contents.tag_ranges('sel')) != 0:

					if startline == endline:
						self.contents.mark_set(tkinter.INSERT, '%s -1c' %i)

					elif self.contents.compare(tkinter.SEL_FIRST, '<', tkinter.INSERT):
						self.contents.mark_set(tkinter.INSERT, tkinter.SEL_FIRST)

					# Is start of selection not viewable?
					if not self.contents.bbox(tkinter.SEL_FIRST):
						self.ensure_idx_visibility('insert', back=4)

				self.contents.edit_separator()

		except tkinter.TclError:
			pass

		self.line_can_update = True

		return 'break'


	def comment(self, event=None):
		if self.state != 'normal':
			self.bell()
			return 'break'

		try:
			s = self.contents.index(tkinter.SEL_FIRST)
			e = self.contents.index(tkinter.SEL_LAST)

			startline,_ = self.get_line_col_as_int(index=s)
			startpos = self.contents.index( '%s -1l linestart' % s )

			endline,_ = self.get_line_col_as_int(index=e)
			endpos = self.contents.index( '%s +1l lineend' % e )

			self.line_can_update = False

			for linenum in range(startline, endline+1):
				self.contents.insert('%d.0' % linenum, '##')

			if self.can_do_syntax():
				self.update_lineinfo()
				self.update_tokens(start=startpos, end=endpos)
				self.line_can_update = True


		# No selection, comment curline
		except tkinter.TclError as e:
			startpos = self.contents.index( 'insert -1l linestart' )
			endpos = self.contents.index( 'insert +1l lineend' )
			self.line_can_update = False
			self.contents.insert('%s linestart' % tkinter.INSERT, '##')

			if self.can_do_syntax():
				self.update_lineinfo()
				self.update_tokens(start=startpos, end=endpos)
				self.line_can_update = True


		self.contents.edit_separator()
		return 'break'


	def uncomment(self, event=None):
		''' Should work even if there are uncommented lines between commented lines. '''
		if self.state != 'normal':
			self.bell()
			return 'break'

		idx_ins = self.contents.index(tkinter.INSERT)

		try:
			s = self.contents.index(tkinter.SEL_FIRST)
			e = self.contents.index(tkinter.SEL_LAST)

			startline,_ = self.get_line_col_as_int(index=s)
			endline,_ = self.get_line_col_as_int(index=e)
			startpos = self.contents.index('%s -1l linestart' % s)
			endpos = self.contents.index('%s +1l lineend' % e)
			changed = False

			self.line_can_update = False

			for linenum in range(startline, endline+1):
				tmp = self.contents.get('%d.0' % linenum,'%d.0 lineend' % linenum)

				if tmp.lstrip()[:2] == '##':
					self.contents.delete('%d.0' % linenum,
						'%d.0 +2c' % linenum)

					changed = True


			if changed:
				if self.can_do_syntax():
					self.update_lineinfo()
					self.update_tokens(start=startpos, end=endpos)
					self.line_can_update = False

				self.contents.edit_separator()


		# No selection, uncomment curline
		except tkinter.TclError as e:
			tmp = self.contents.get('%s linestart' % idx_ins,
				'%s lineend' % idx_ins)

			if tmp.lstrip()[:2] == '##':
				self.contents.delete('%s linestart' % idx_ins,
					'%s linestart +2c' % idx_ins)

				self.contents.edit_separator()

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
		tests = [self.contents.compare( '%s display linestart' % index, '<', index),
				not self.contents.compare('%s display lineend' % index, '>', index)
				]


		if all(tests): res = left

		return self.contents.index(res)


	def line_is_elided(self, index='insert'):

		# Cursor is at elided defline
		r = self.contents.tag_nextrange('elIdel', index)

		if len(r) > 0:
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

		ref = self.contents.index(index)
		idx = self.get_safe_index(index)


		# Show scope
		if r := self.line_is_elided(idx):
			self.contents.tag_remove('sel', '1.0', tkinter.END)
			self.wait_for(50)

			# Protect cursor from being pushed down
			self.contents.mark_set('insert', idx)

			self.contents.tag_remove('elIdel', r[0], r[1])

		else:
			patt = r'%s get {%s linestart} {%s lineend}' \
					% (self.tcl_name_of_contents, idx, idx)

			line = self.contents.tk.eval(patt)
			if not self.line_is_defline(line):
				return 'break'

			# Hide scope
			#
			# +1 lines: Enable matching defline at insert
			pos = '%s lineend +1 chars' % index

			(scope_line, ind_defline,
			idx_scope_start) = self.get_scope_start(index=pos)

			idx_scope_end = self.get_scope_end(ind_defline, idx_scope_start)


			s = '%s lineend' % idx_scope_start
			e = idx_scope_end

			self.contents.tag_remove('sel', '1.0', tkinter.END)
			self.wait_for(50)

			# Protect cursor from being elided
			self.contents.mark_set('insert', idx)

			self.contents.tag_add('elIdel', s, e)


		# If cursor was at defline lineend, it was moved one char left,
		# put it back to lineend
		if self.contents.compare(idx, '!=', ref):
			# 	Q: Why not '%s lineend' % idx ?
			#
			# 	A:	s = '%s lineend' % idx_scope_start
			#		self.contents.tag_add('elIdel', s, e)
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
			#	self.contents.tag_add('elIdel', s, e)
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


			self.contents.mark_set('insert', '%s display lineend' % idx)

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
		elif len(self.contents.tag_ranges('sel')) == 0:
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
		res = self.tk.call(tuple(search_args))

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



		# Get current index among search matches, this
		# concerns more when using_selection.
		# This is mainly for the possible future use,
		# showing info same way when doing real search.
		if using_selection:
			start = self.contents.index(tkinter.SEL_FIRST)

		else:
			start = self.contents.search(search_word, 'insert')


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


		# Now one could show info: "match idx/len(m)" etc.
		# This is start_index of search_word of next/previous match
		pos = m[idx]


		wordlen = len(search_word)
		word_end = "%s + %dc" % (pos, wordlen)

		self.wait_for(33)
		self.contents.tag_remove('sel', '1.0', tkinter.END)
		self.contents.mark_set(self.anchorname, pos)
		self.wait_for(12)
		self.contents.tag_add('sel', pos, word_end)
		self.contents.mark_set('insert', word_end)

		# Is it not viewable?
		if not self.contents.bbox(pos):
			self.wait_for(100)
			self.ensure_idx_visibility(pos)

		return 'break'


	def show_next(self, event=None):
		''' Note: side-effect, alters insert-mark
				self.contents.mark_set('insert')
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

		self.contents.tag_remove('focus', '1.0', tkinter.END)

		# match-mark marks start of the match
		start = mark_name


		# Make zero lenght matches visible
		if 'match_zero_lenght' in self.contents.tag_names(start):
			end = '%s +1c' % mark_name

		else:
			end = '%s +%dc' % ( mark_name, self.match_lenghts[self.search_index] )

		# self.search_focus is range of focus-tag.
		self.search_focus = (start, end)

		# idx: int
		# start: tkinter.Text -index
		self.handle_search_entry(idx, start)

		# Is it not viewable?
		if not self.contents.bbox(start):
			self.wait_for(100)

		self.ensure_idx_visibility(start)


		self.contents.mark_set('insert', start)


		if self.entry.flag_start:
			if self.state == 'search':
				self.wait_for(100)
				bg, fg = self.themes[self.curtheme]['match'][:]
				self.contents.tag_config('match', background=bg, foreground=fg)
			self.wait_for(200)
			self.entry.flag_start = False



		# Change color
		# self.search_focus is range of focus-tag.
		self.contents.tag_add('focus', self.search_focus[0], self.search_focus[1])



		self.entry.config(validate='key')

		if self.search_matches == 1:
			self.bind("<Control-n>", self.do_nothing)
			self.bind("<Control-p>", self.do_nothing)


		self.entry.xview_moveto(0)

		return 'break'


	def show_prev(self, event=None):
		''' Note: side-effect, alters insert-mark
				self.contents.mark_set('insert')
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

		self.contents.tag_remove('focus', '1.0', tkinter.END)

		# match-mark marks start of the match
		start = mark_name


		# Make zero lenght matches visible
		if 'match_zero_lenght' in self.contents.tag_names(start):
			end = '%s +1c' % mark_name

		else:
			end = '%s +%dc' % ( mark_name, self.match_lenghts[self.search_index] )

		# self.search_focus is range of focus-tag.
		self.search_focus = (start, end)


		# idx: int
		# start: tkinter.Text -index
		self.handle_search_entry(idx, start)

		# Is it not viewable?
		if not self.contents.bbox(start):
			self.wait_for(100)

		self.ensure_idx_visibility(start)
		self.contents.mark_set('insert', start)

		if self.entry.flag_start:
			if self.state == 'search':
				self.wait_for(100)
				bg, fg = self.themes[self.curtheme]['match'][:]
				self.contents.tag_config('match', background=bg, foreground=fg)
			self.wait_for(200)
			self.entry.flag_start = False


		# Change color
		# self.search_focus is range of focus-tag.
		self.contents.tag_add('focus', self.search_focus[0], self.search_focus[1])

		self.entry.config(validate='key')


		if self.search_matches == 1:
			self.bind("<Control-n>", self.do_nothing)
			self.bind("<Control-p>", self.do_nothing)


		self.entry.xview_moveto(0)

		return 'break'


	def reset_search_setting(self):

		defaults = [
				'search',
				'-all',
				'-count',
				self.match_lenghts_var
				]

		self.search_settings = defaults
		self.search_starts_at = '1.0'
		self.search_ends_at = False


	def print_search_setting(self):

		if not self.search_settings:
			self.reset_search_setting()

		print(
			self.search_settings[4:],
			'\n'
			'start:', self.search_starts_at,
			'\n'
			'end:', self.search_ends_at
			)


	def print_search_help(self):

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

		for line in helptxt.split('\n'):
			print(line)


	def edit_search_setting(self, search_setting):
		''' search_setting is string consisting of options below separated by spaces.

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

				edit_search_setting( '-regexp' )


			Example2, search backwards, give start-index if not sure what were old ones:

				edit_search_setting( '-backwards -start end' )


			Example3, use regexp, include elided text, search only from cursor to fileend:

				my_settings = "-regexp -elide -start insert -end end"

				edit_search_setting( my_settings )


			Example4, exact (default) search, backwards from cursor to 50 lines up:

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
			print_search_help()

			Print current search settings:
			print_search_setting()

			Reset search settings:
			reset_search_setting()

			https://www.tcl.tk/man/tcl9.0/TkCmd/text.html#M147
		'''

		if not self.search_settings:
			self.reset_search_setting()

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
		tmp = self.contents.get('1.0', '1.1')

		flag = False
		if not tmp:
			self.contents.insert('1.0', 'A')
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


		if flag: self.contents.delete('1.0', '1.1')

		#### edit_search_setting End ##############


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
				have_selection = len(self.contents.tag_ranges('sel')) > 0
				if have_selection:
					tmp = self.selection_get()
					if tmp == search_word:
						if '-backwards' not in self.search_settings:
							idx_sel_start = self.contents.index(tkinter.SEL_FIRST)
							return idx_sel_start
						else:
							idx_sel_end = self.contents.index(tkinter.SEL_LAST)
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

		res = self.tk.call(tuple(s))
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



		for mark in self.contents.mark_names():
			if 'match' in mark:
				self.contents.mark_unset(mark)

		match_ranges = list()
		match_zero_ranges = list()
		self.mark_indexes = list()

		# Tag matches, add mark to start of every match
		for i in range( len(start_indexes) ):

			mark_name = 'match%d' % i
			start_idx = start_indexes[i]
			self.contents.mark_set(mark_name, start_idx)
			self.mark_indexes.append(i)

			match_lenght = s[i]

			# Used in making zero lenght matches visible
			if match_lenght == 0 and 'elIdel' not in self.contents.tag_names(start_idx):
				end_idx = '%s +1c' % start_idx
				match_zero_ranges.append(mark_name)
				match_zero_ranges.append(end_idx)

			else:
				end_idx = '%s +%dc' % (mark_name, match_lenght)


			match_ranges.append(mark_name)
			match_ranges.append(end_idx)


		self.contents.tag_add('match', *match_ranges)
		if len(match_zero_ranges) > 0:
			self.contents.tag_add('match_zero_lenght', *match_zero_ranges)

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


		self.contents.tag_remove('match', '1.0', tkinter.END)
		self.contents.tag_remove('focus', '1.0', tkinter.END)
		self.contents.tag_config('match', background='', foreground='')

		self.search_matches = self.do_search(search_word)
		# 'match' is tagged in do_search()


		if self.search_matches > 0:

			self.old_word = search_word
			self.search_index = -1

			self.bind("<Button-%i>" % self.right_mousebutton_num, self.do_nothing)
			self.entry.config(validate='none')


			if self.state == 'search':

				self.bid_show_next = self.bind("<Control-n>", self.show_next )
				self.bid_show_prev = self.bind("<Control-p>", self.show_prev )
				self.entry.flag_start = True

				self.contents.focus_set()
				self.wait_for(100)

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


				bg, fg = self.themes[self.curtheme]['match'][:]
				self.contents.tag_config('match', background=bg, foreground=fg)


				self.entry.bind("<Return>", self.start_replace)
				self.entry.focus_set()
				self.entry.config(validate='key')

		else:
			self.bell()
			bg, fg = self.themes[self.curtheme]['match'][:]
			self.contents.tag_config('match', background=bg, foreground=fg)
			self.bind("<Control-n>", self.do_nothing)
			self.bind("<Control-p>", self.do_nothing)



		return 'break'


	def update_curpos(self, event=None, on_stop=None):
		''' on_stop: function to be executed on doubleclick
		'''

		self.save_pos = self.contents.index(tkinter.INSERT)

		on_stop()

		return 'break'


	def clear_search_tags(self, event=None):
		if self.state != 'normal':
			return 'break'

		self.contents.tag_remove('replaced', '1.0', tkinter.END)
		self.bind("<Escape>", self.esc_override)


	def stop_search(self, event=None):
		if self.state == 'waiting':
			return 'break'

		self.contents.config(state='normal')
		self.entry.config(state='normal')
		self.btn_open.config(state='normal')
		self.btn_save.config(state='normal')
		self.bind("<Button-%i>" % self.right_mousebutton_num,
			lambda event: self.raise_popup(event))

		#self.wait_for(200)
		self.contents.tag_remove('focus', '1.0', tkinter.END)
		self.contents.tag_remove('match', '1.0', tkinter.END)
		self.contents.tag_remove('match_zero_lenght', '1.0', tkinter.END)
		self.contents.tag_remove('sel', '1.0', tkinter.END)

		# Leave marks on replaced areas, Esc clears.
		if len(self.contents.tag_ranges('replaced')) > 0:
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
					self.save_pos = None
					# This will pass until focus_set
					pass

				line = self.save_pos
				curtab.position = line
				self.save_pos = None
			else:
				line = curtab.position

			self.contents.focus_set()
			self.contents.mark_set('insert', line)

		except tkinter.TclError:
			curtab.position = self.contents.index(tkinter.INSERT)


		self.new_word = ''
		self.search_matches = 0
		flag_all = False


		if self.state in ['replace_all']:
			flag_all = True
			if self.can_do_syntax():
				self.update_lineinfo()
				self.insert_tokens(self.get_tokens(curtab, update=True))

		if self.can_do_syntax(): self.line_can_update = True


		self.state = 'normal'


		if self.bid_show_next:
			self.unbind( "<Control-n>", funcid=self.bid_show_next )
			self.unbind( "<Control-p>", funcid=self.bid_show_prev )
			self.bid_show_next = None
			self.bid_show_prev = None

		self.contents.unbind( "<Control-n>", funcid=self.bid1 )
		self.contents.unbind( "<Control-p>", funcid=self.bid2 )
		self.contents.unbind( "<Double-Button-1>", funcid=self.bid3 )

		# Space is on hold for extra 200ms, released below
		self.contents.unbind( "<space>", funcid=self.bid4 )
		bid_tmp = self.contents.bind( "<space>", self.do_nothing_without_bell)


		self.contents.bind( "<Control-n>", self.search_next)
		self.contents.bind( "<Control-p>",
				lambda event: self.search_next(event, **{'back':True}) )

		self.contents.bind("<Return>", self.return_override)
		self.entry.bind("<Control-n>", self.do_nothing_without_bell)
		self.entry.bind("<Control-p>", self.do_nothing_without_bell)
		self.bind( "<Return>", self.do_nothing_without_bell)


		if not flag_all: self.ensure_idx_visibility(line)

		# Release space
		self.wait_for(200)
		self.contents.unbind( "<space>", funcid=bid_tmp )
		curtab.bid_space = self.contents.bind( "<space>", self.space_override)
		return 'break'


	def search(self, event=None):
		'''	Ctrl-f --> search --> start_search --> show_next / show_prev --> stop_search
		'''

		if self.state not in ['normal']:
			self.bell()
			return 'break'

		if not self.search_settings:
			self.reset_search_setting()

		# Save cursor pos
		try:
			self.tabs[self.tabindex].position = self.contents.index(tkinter.INSERT)

		except tkinter.TclError:
			pass


		self.state = 'search'
		self.btn_open.config(state='disabled')
		self.btn_save.config(state='disabled')
		self.entry.unbind("<Return>", funcid=self.entry.bid_ret)
		self.entry.bind("<Return>", self.start_search)
		self.bind("<Escape>", self.stop_search)

		self.bid1 = self.contents.bind("<Control-n>", func=self.skip_bindlevel )
		self.bid2 = self.contents.bind("<Control-p>", func=self.skip_bindlevel )
		self.entry.bind("<Control-n>", self.skip_bindlevel)
		self.entry.bind("<Control-p>", self.skip_bindlevel)
		self.bid_show_next = None
		self.bid_show_prev = None

		self.bid3 = self.contents.bind("<Double-Button-1>",
			func=lambda event: self.update_curpos(event, **{'on_stop':self.stop_search}),
				add=True )

		self.contents.unbind( "<space>", funcid=self.tabs[self.tabindex].bid_space )
		self.bid4 = self.contents.bind( "<space>", self.space_override )

		self.entry.delete(0, tkinter.END)


		tmp = False

		# Suggest selection as search_word if appropiate, else old_word.
		try:
			tmp = self.selection_get()

			# Allow one linebreak
			if not (80 > len(tmp) > 0 and len(tmp.splitlines()) < 3):
				tmp = False

				raise tkinter.TclError

		# No selection
		except tkinter.TclError:
			tmp = self.old_word


		if tmp:
			self.entry.insert(tkinter.END, tmp)
			self.entry.xview_moveto(1.0)
			self.entry.select_to(tkinter.END)
			self.entry.icursor(tkinter.END)


		patt = 'Search: '
		self.entry.insert(0, patt)
		self.entry.config(validate='key', validatecommand=self.validate_search)

		self.contents.config(state='disabled')
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
			self.reset_search_setting()

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
			self.tabs[self.tabindex].position = self.contents.index(tkinter.INSERT)
			if state == 'replace_all':
				self.save_pos = self.contents.index(tkinter.INSERT)

		except tkinter.TclError:
			pass

		self.state = state
		self.btn_open.config(state='disabled')
		self.btn_save.config(state='disabled')
		self.entry.unbind("<Return>", funcid=self.entry.bid_ret)
		self.entry.bind("<Return>", self.start_search)
		self.bind("<Escape>", self.stop_search)
		self.bid1 = self.contents.bind("<Control-n>", func=self.skip_bindlevel )
		self.bid2 = self.contents.bind("<Control-p>", func=self.skip_bindlevel )
		self.entry.bind("<Control-n>", self.skip_bindlevel)
		self.entry.bind("<Control-p>", self.skip_bindlevel)
		self.bid_show_next = None
		self.bid_show_prev = None


		self.bid3 = self.contents.bind("<Double-Button-1>",
			func=lambda event: self.update_curpos(event, **{'on_stop':self.stop_search}),
				add=True )

		self.contents.unbind( "<space>", funcid=self.tabs[self.tabindex].bid_space )
		self.bid4 = self.contents.bind("<space>", func=self.space_override )


		self.entry.delete(0, tkinter.END)


		tmp = False
		# Suggest selection as search_word if appropiate, else old_word.
		try:
			tmp = self.selection_get()

			if not (80 > len(tmp) > 0):
				tmp = False

				raise tkinter.TclError

		# No selection
		except tkinter.TclError:
			tmp = self.old_word


		if tmp:
			self.entry.insert(tkinter.END, tmp)
			self.entry.xview_moveto(1.0)
			self.entry.select_to(tkinter.END)
			self.entry.icursor(tkinter.END)


		patt = 'Replace this: '
		self.entry.insert(0, patt)
		self.entry.config(validate='key', validatecommand=self.validate_search)

		self.wait_for(400)
		self.contents.tag_remove('replaced', '1.0', tkinter.END)

		self.contents.config(state='disabled')
		self.entry.focus_set()
		return 'break'


	def replace_all(self, event=None):

		if not self.search_settings:
			self.reset_search_setting()

		if self.state != 'normal':
			self.bell()
			return 'break'

		elif '-overlap' in self.search_settings:
			self.wait_for(100)
			print('\nError: Can not replace_all while "-overlap" in search_settings')
			self.bell()
			return 'break'


		self.replace(event, state='replace_all')


	def do_single_replace(self, event=None):

		# Enable changing newword between replaces Begin
		#################
		# Get stuff after prompt
		tmp_orig = self.entry.get()
		idx = tmp_orig.index(':') + 2
		tmp = tmp_orig[idx:].strip()

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
		# Enable changing newword between replaces End
		#################



		# Apply normal 'Replace and proceed to next by pressing Return' -behaviour.
		# If last replace was done by pressing Return, there is currently no focus-tag.
		# Check this and get focus-tag with show_next() if this is the case, and break.
		# This means that the actual replacing happens only when have focus-tag.
		c = self.contents.tag_nextrange('focus', 1.0)

		if not len(c) > 0:
			self.show_next()
			return 'break'



		# Start of actual replacing
		self.contents.config(state='normal')

		wordlen_new = len(self.new_word)


		####
		mark_name = 'match%d' % self.search_index

		start = self.contents.index(mark_name)
		end_old = '%s +%dc' % ( start, self.match_lenghts[self.search_index] )
		end_new = "%s +%dc" % ( start, wordlen_new )


		# Regexp
		if ('-regexp' in self.search_settings):
			cont = r'[%s get {%s} {%s}]' \
					% (self.tcl_name_of_contents, start, end_old)
			search_re = self.old_word
			substit = r'{%s}' % self.new_word
			patt = r'regsub -line {%s} %s %s' % (search_re, cont, substit)
			new_word = self.contents.tk.eval(patt)
			len_new_word = len(new_word)
			end_new = "%s +%dc" % ( start, len_new_word )

		# Normal
		else: new_word = self.new_word


		self.contents.replace(start, end_old, new_word)

		if self.can_do_syntax():
			self.update_tokens(start='%s linestart' % start, end='%s lineend' % end_new)


		self.contents.tag_add('replaced', start, end_new)
		self.contents.tag_remove('focus', '1.0', tkinter.END)

		# Fix for use of non existing mark in self.save_pos
		self.search_focus = (start, end_new)
		# Mark gets here deleted

		self.contents.mark_unset(mark_name)
		self.mark_indexes.remove(self.search_index)
		####


		self.contents.config(state='disabled')

		self.search_matches -= 1

		if self.search_matches == 0:
			self.wait_for(100)
			self.stop_search()


	def do_replace_all(self, event=None):

		# Start of actual replacing
		self.contents.tag_config('match', background='', foreground='')
		self.contents.tag_remove('focus', '1.0', tkinter.END)
		self.contents.config(state='normal')
		wordlen_new = len(self.new_word)


		####
		i = self.mark_indexes[-1]
		last_mark = 'match%d' % i
		idx_last_mark = self.contents.index(last_mark)

		for index in self.mark_indexes[::-1]:

			mark_name = 'match%d' % index
			start = self.contents.index(mark_name)
			end_old = '%s +%dc' % ( start, self.match_lenghts[index] )
			end_new = "%s +%dc" % ( start, wordlen_new )


			# Regexp
			if ('-regexp' in self.search_settings):
				cont = r'[%s get {%s} {%s}]' \
						% (self.tcl_name_of_contents, start, end_old)
				search_re = self.old_word
				substit = r'{%s}' % self.new_word
				patt = r'regsub -line {%s} %s %s' % (search_re, cont, substit)
				new_word = self.contents.tk.eval(patt)
				len_new_word = len(new_word)
				end_new = "%s +%dc" % ( start, len_new_word )


			# Normal
			else: new_word = self.new_word


			self.contents.replace(start, end_old, new_word)


			self.contents.tag_add('replaced', start, end_new)
			self.contents.mark_unset(mark_name)
			self.mark_indexes.pop(-1)
		####


		# Is it not viewable?
		if not self.contents.bbox(idx_last_mark):
			self.wait_for(300)

		# Show last match that got replaced
		self.ensure_idx_visibility(idx_last_mark)
		self.wait_for(200)

		bg, fg = self.themes[self.curtheme]['replaced'][:]
		self.contents.tag_config('replaced', background=bg, foreground=fg)

		self.stop_search()
		###################


	def start_replace(self, event=None):

		# Get stuff after prompt
		tmp_orig = self.entry.get()
		idx = tmp_orig.index(':') + 2
		tmp = tmp_orig[idx:].strip()
		self.new_word = tmp

		# No check for empty newword to enable deletion.

		if self.old_word == self.new_word:
			self.bell()
			return 'break'


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
		self.line_can_update = False
		self.wait_for(100)

		self.show_next()

		self.bid_show_next = self.bind("<Control-n>", self.show_next )
		self.bid_show_prev = self.bind("<Control-p>", self.show_prev )

		self.entry.bind("<Return>", self.skip_bindlevel)
		self.contents.bind("<Return>", self.skip_bindlevel)
		self.contents.focus_set()

		if self.state == 'replace':
			self.bind( "<Return>", self.do_single_replace)

		elif self.state == 'replace_all':
			self.bind( "<Return>", self.do_replace_all)

		return 'break'


################ Replace End
########### Class Editor End

