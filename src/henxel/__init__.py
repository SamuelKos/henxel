############ Stucture briefing Begin

# Stucture briefing
# TODO
# Imports
# Class Tab

####################
# Class Editor Begin
#
# Constants
# init etc.
# Linenumbers
# Tab Related
# Configuration Related
# Syntax highlight
# Theme Related
# Run file Related
# Overrides
# Utilities
# Save and Load
# Gotoline and Help
# Indent and Comment
# Search
# Replace
#
# Class Editor End

############ Stucture briefing End
############ TODO Begin

#

############ TODO End
############ Imports Begin

# from standard library
import tkinter.font
import tkinter
import pathlib
import json
import copy

# used in init
import importlib.resources
import importlib.metadata
import sys

# used in syntax highlight
import tokenize
import io

# from current directory
from . import wordexpand
from . import changefont
from . import fdialog

# for executing edited file in the same env than this editor, which is nice:
# It means you have your installed dependencies available. By self.run()
import subprocess

############ Imports End
############ Class Tab Begin
					
class Tab:
	'''	Represents a tab-page of an Editor-instance
	'''
	
	def __init__(self, **entries):
		self.active = True
		self.filepath = None
		self.contents = ''
		self.oldcontents = ''
		self.position = '1.0'
		self.type = 'newtab'
		
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
# https://www.tcl.tk/man/tcl8.6/TkCmd/event.htm
# https://docs.python.org/3/library/tkinter.html
#
###############################################################################

############ Constants Begin
CONFPATH = 'editor.cnf'
ICONPATH = 'editor.png'
HELPPATH = 'help.txt'
VERSION = importlib.metadata.version(__name__)


TAB_WIDTH = 4
TAB_WIDTH_CHAR = ' '

SLIDER_MINSIZE = 66


GOODFONTS = [
			'Noto Mono',
			'Bitstream Vera Sans Mono',
			'Liberation Mono',
			'DejaVu Sans Mono',
			'Inconsolata',
			'Courier 10 Pitch'
			]
			
############ Constants End
			
class Editor(tkinter.Toplevel):

	alive = False
	
	
	def __new__(cls):
	
		if not cls.alive:
			return super(Editor, cls).__new__(cls)
			
		else:
			print('Instance of ', cls, ' already running!\n')
			
			# By raising error the object creation is totally aborted.
			raise ValueError()
			
			

	def __init__(self):
	
		self.root = tkinter.Tk().withdraw()
		super().__init__(self.root, class_='Henxel', bd=4)
		self.protocol("WM_DELETE_WINDOW", self.quit_me)
		
		# other widgets
		self.to_be_closed = list()
		
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
		
		
		self.font = tkinter.font.Font(family='TkDefaulFont', size=12, name='textfont')
		self.menufont = tkinter.font.Font(family='TkDefaulFont', size=10, name='menufont')
		
		# get current git-branch
		try:
			self.branch = subprocess.run('git branch --show-current'.split(),
					check=True, capture_output=True).stdout.decode().strip()
		except Exception as e:
			pass
		
		self.search_idx = ('1.0', '1.0')
		self.search_matches = 0
		self.old_word = ''
		self.new_word = ''
		
		self.errlines = list()
		
		# When clicked with mouse button 1 while searhing
		# to set cursor position to that position clicked.
		self.save_pos = None
		
		# used in load()
		self.tracevar_filename = tkinter.StringVar()
		self.tracefunc_name = None
		self.lastdir = None

		self.check_pars = False
		self.par_err = False
		
		self.waitvar = tkinter.IntVar()
		self.state = 'normal'
		
		
		# IMPORTANT:
		# 1: Event is triggered in the widget that has focus but it has no binding for that event.
		# 2: Widget is subclassed from such widget-class that has default bindging for this event.
		# 3: The desired binding is in the nearest parent-widget.
		
		# https://stackoverflow.com/questions/54185434/python-tkinter-override-default-ctrl-h-binding
		# https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/binding-levels.html
		
		# Example, print bindtag-order of two widgets in python-console,
		# first widget is Text-widget and then Editor-widget
		# >>> e=henxel.Editor()
		# >>> e.contents.bindtags()
		# ('.!editor.!text2', 'Text', '.!editor', 'all')
		
		# >>> e.bindtags()
		# ('.!editor', 'Henxel', 'all')
		
		# Bindings are executed from left to right.
		
		# Example: in class Editor there is:
		# self.bind( "<Return>", self.do_nothing)
		
		# Then if focus is in Editor.contents (pressing newline in editor),
		# first to catch the event (after OS) is: '.!editor.!text2'
		# That is the Text-class-instance, if there is a binding for that event,
		
		# And there is:
		# self.contents.bind( "<Return>", self.return_override)
		
		# It is executed and if there is no 'break' returned, this Return-event will continue
		# to the next bindtag: 'Text' which has all the default bindings for a Text-class.
		# After that the event would be going to the parent widget, Editor-widget etc.
		
		
		# What is this for? Say we have a widget: Text-widget and binding to its parent Editor-widget like:
		# 	self.bind( "<Return>", self.return_override_editor)
		# And there would not be binding like:
		# 	self.contents.bind( "<Return>", self.return_override_text)
		# But then if Text-widget has focus and pressed Return: 'Text' class-bindings are executed before
		# Editor-widget and this might not be what we wanted:
		# ('.!editor.!text2', 'Text', '.!editor', 'all')
		
		# But that event can be unbinded, Example: Print current bindings for a class:
		# >>> e.contents.bind_class('Text')
		
		# Unbinding default binding of Text-widget:
		# e.contents.unbind_class('Text', '<Return>')
		# And then it works.
		
		
		self.bind( "<Escape>", self.do_nothing )
		self.bind( "<Return>", self.do_nothing)
		self.bind( "<Control-minus>", self.decrease_scrollbar_width)
		self.bind( "<Control-plus>", self.increase_scrollbar_width)
		self.bind( "<Control-R>", self.replace_all)
		self.bind( "<Button-3>", self.raise_popup)
		self.bind( "<Control-g>", self.gotoline)
		self.bind( "<Control-r>", self.replace)
		self.bind( "<Alt-s>", self.color_choose)
		self.bind( "<Alt-t>", self.toggle_color)
		self.bind( "<Alt-n>", self.new_tab)
		self.bind( "<Alt-w>", self.walk_tabs)
		
		
		self.bind( "<Alt-q>", lambda event: self.walk_tabs(event, **{'back':True}) )
		
		pkg_contents = importlib.resources.files(__name__)
		
		self.helptxt = 'Could not load help-file. Press ESC to return.'
		no_icon = True
		
		for item in pkg_contents.iterdir():
			if item.name == HELPPATH:
				try:
					self.helptxt = item.read_text()
				except Exception as e:
					print(e.__str__())
			
			elif item.name == ICONPATH:
				try:
					self.pic = tkinter.Image("photo", file=item)
					self.tk.call('wm','iconphoto', self._w, self.pic)
					no_icon = False
				except tkinter.TclError as e:
					print(e)
					
		if no_icon: print('Could not load icon-file.')
			
		
		# Initiate widgets
		####################################
		self.btn_git=tkinter.Button(self, takefocus=0)
		
		if self.branch:
			branch = self.branch[:5]
			self.btn_git.config(font=self.menufont, relief='flat', highlightthickness=0,
						padx=0, text=branch, state='disabled')
			
			if 'main' in self.branch or 'master' in self.branch:
				self.btn_git.config(disabledforeground='brown1')
				
		else:
			self.btn_git.config(font=self.menufont, relief='flat', highlightthickness=0,
						padx=0, bitmap='info', state='disabled')
		
		
		self.entry = tkinter.Entry(self, bd=4, highlightthickness=0, bg='#d9d9d9')
		self.entry.bind("<Return>", self.load)
		
		self.btn_open=tkinter.Button(self, takefocus=0, text='Open', bd=4, highlightthickness=0, command=self.load)
		self.btn_save=tkinter.Button(self, takefocus=0, text='Save', bd=4, highlightthickness=0, command=self.save)
		
		# Get conf:
		string_representation = None
		data = None
		
		# Try to apply saved configurations:
		if self.env:
			p = pathlib.Path(self.env) / CONFPATH
		
		if self.env and p.exists():
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
			
		
		self.ln_widget = tkinter.Text(self, width=4, padx=10, highlightthickness=0, bd=4, pady=4)
		self.ln_widget.tag_config('justright', justify=tkinter.RIGHT)
		
		# disable copying linenumbers:
		self.ln_widget.bind('<Control-c>', self.no_copy_ln)
		
		self.contents = tkinter.Text(self, blockcursor=True, undo=True, maxundo=-1, autoseparators=True,
					tabstyle='wordprocessor', highlightthickness=0, bd=4, pady=4, padx=10)
		
		self.scrollbar = tkinter.Scrollbar(self, orient=tkinter.VERTICAL, highlightthickness=0,
					bd=0, command = self.contents.yview)

		self.expander = wordexpand.ExpandWord(self.contents)
		self.contents.bind( "<Alt-e>", self.expander.expand_word_event)
		
		# Widgets are initiated, now more configuration
		################################################
		# Needed in update_linenums(), there is more info.
		self.update_idletasks()
		# if self.y_extra_offset > 0, it needs attention
		self.y_extra_offset = self.contents['highlightthickness'] + self.contents['bd'] + self.contents['pady']
		# Needed in update_linenums() and sbset_override()
		self.bbox_height = self.contents.bbox('@0,0')[3]
		self.text_widget_height = self.scrollbar.winfo_height()
				
		self.contents['yscrollcommand'] = lambda *args: self.sbset_override(*args)
		
		self.contents.bind( "<Alt-Return>", lambda event: self.btn_open.invoke())
		
		self.contents.bind( "<Alt-l>", self.toggle_ln)
		self.contents.bind( "<Control-f>", self.search)
		
		self.contents.bind( "<Control-a>", self.goto_linestart)
		self.contents.bind( "<Control-i>", self.move_right)
		self.contents.bind( "<Control-j>", self.center_view)
		
		self.contents.bind( "<Alt-f>", self.font_choose)
		self.contents.bind( "<Alt-x>", self.toggle_syntax)
		self.contents.bind( "<Return>", self.return_override)
		
		self.contents.bind( "<Control-d>", self.del_tab)
		self.contents.bind( "<Control-q>", lambda event: self.del_tab(event, **{'save':False}) )
		
		
		self.contents.bind( "<Shift-Return>", self.comment)
		self.contents.bind( "<Shift-BackSpace>", self.uncomment)
		self.contents.bind( "<Tab>", self.tab_override)
		self.contents.bind( "<ISO_Left_Tab>", self.unindent)
		self.contents.bind( "<Control-t>", self.tabify_lines)
		self.contents.bind( "<Control-z>", self.undo_override)
		self.contents.bind( "<Control-Z>", self.redo_override)
		self.contents.bind( "<Control-v>", self.paste)
		
		self.contents.bind( "<Control-BackSpace>", self.search_next)
		self.contents.bind( "<BackSpace>", self.backspace_override)
		self.contents.bind("<Left>", lambda event: self.move_line(event, **{'direction':'left'} ))
		self.contents.bind("<Right>", lambda event: self.move_line(event, **{'direction':'right'} ))
		
		# Unbind some default bindings
		self.contents.unbind_class('Text', '<<NextPara>>')
		self.contents.unbind_class('Text', '<<PrevPara>>')
		self.contents.unbind_class('Text', '<<SelectNextPara>>')
		self.contents.unbind_class('Text', '<<SelectPrevPara>>')
		
	
		# Needed in leave() taglink in: Run file Related
		self.name_of_cursor_in_text_widget = self.contents['cursor']
		
		self.popup = tkinter.Menu(self.contents, tearoff=0, bd=0, activeborderwidth=0)
		self.popup.bind("<FocusOut>", self.popup_focusOut) # to remove popup when clicked outside
		self.popup.add_command(label="         run", command=self.run)
		self.popup.add_command(label="        copy", command=self.copy)
		self.popup.add_command(label="       paste", command=self.paste)
		self.popup.add_command(label="##   comment", command=self.comment)
		self.popup.add_command(label="   uncomment", command=self.uncomment)
		self.popup.add_command(label="  select all", command=self.select_all)
		self.popup.add_command(label="     inspect", command=self.insert_inspected)
		self.popup.add_command(label="      errors", command=self.show_errors)
		self.popup.add_command(label="        help", command=self.help)
		
		
		if data:
			self.apply_config()
			
			# Hide selection in linenumbers
			self.ln_widget.config( selectbackground=self.bgcolor, selectforeground=self.fgcolor, inactiveselectbackground=self.bgcolor )
			
		
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
		self.default_themes['day'] = d = dict()
		self.default_themes['night'] = n = dict()
		
		# self.default_themes[self.curtheme][tagname] = [backgroundcolor, foregroundcolor]
		d['normal_text'] = [white, black]
		n['normal_text'] = [black, white]
		
		# if background is same as sel background, change
		
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
		
		
		# if no conf:
		if self.tabindex == None:
		
			self.tabindex = -1
			self.new_tab()
			
			self.curtheme = 'night'
			self.themes = copy.deepcopy(self.default_themes)
			
			for tagname in self.themes[self.curtheme]:
				bg, fg = self.themes[self.curtheme][tagname][:]
				self.contents.tag_config(tagname, background=bg, foreground=fg)
			
			
			self.bgcolor, self.fgcolor = self.themes[self.curtheme]['normal_text'][:]
			
			
			# Set Font Begin ##################################################
			fontname = None
						
			fontfamilies = [f for f in tkinter.font.families()]
			
			for font in GOODFONTS:
				if font in fontfamilies:
					fontname = font
					break
					
			if not fontname:
				fontname = 'TkDefaulFont'

			# Initialize rest of configurables
			self.font.config(family=fontname, size=12)
			self.menufont.config(family=fontname, size=10)
		
			self.scrollbar_width = 30
			self.elementborderwidth = 4
			
			self.scrollbar.config(width=self.scrollbar_width)
			self.scrollbar.config(elementborderwidth=self.elementborderwidth)
			
			self.ind_depth = TAB_WIDTH
			self.tab_width = self.font.measure(self.ind_depth * self.tab_char)
			self.contents.config(font=self.font, foreground=self.fgcolor,
				background=self.bgcolor, insertbackground=self.fgcolor,
				tabs=(self.tab_width, ))
				
			self.entry.config(font=self.menufont)
			self.btn_open.config(font=self.menufont)
			self.btn_save.config(font=self.menufont)
			self.popup.config(font=self.menufont)
			
			self.btn_git.config(font=self.menufont)
			
			self.ln_widget.config(font=self.font, foreground=self.fgcolor, background=self.bgcolor, selectbackground=self.bgcolor, selectforeground=self.fgcolor, inactiveselectbackground=self.bgcolor, state='disabled')

		
		self.helptxt = f'{self.helptxt}\n\nHenxel v. {self.version}'
		
		# Widgets are configured
		###############################
		#
		# Syntax-highlight Begin #################
		
		self.keywords = [
						'self',
						'False',
						'True',
						'None',
						'break',
						'for',
						'not',
						'class',
						'from',
						'or',
						'continue',
						'global',
						'pass',
						'def',
						'if',
						'raise',
						'and',
						'del',
						'import',
						'return',
						'as',
						'elif',
						'in',
						'try',
						'assert',
						'else',
						'is',
						'while',
						'async',
						'except',
						'lambda',
						'with',
						'await',
						'finally',
						'nonlocal',
						'yield',
						'open'
						]
						
		self.bools = [ 'False', 'True', 'None' ]
		self.breaks = [
						'break',
						'return',
						'continue',
						'pass',
						'raise',
						'assert',
						'yield'
						]
						
		self.tests = [
					'not',
					'or',
					'and',
					'in',
					'as'
					]
		
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
		
		
		self.boldfont = self.font.copy()
		self.boldfont.config(weight='bold')
		
		self.contents.tag_config('keywords', font=self.boldfont)
		self.contents.tag_config('numbers', font=self.boldfont)
		self.contents.tag_config('comments', font=self.boldfont)
		self.contents.tag_config('breaks', font=self.boldfont)
		self.contents.tag_config('calls', font=self.boldfont)

		# search tags have highest priority
		self.contents.tag_raise('match')
		self.contents.tag_raise('replaced')
		self.contents.tag_raise('focus')
		
		
		self.oldline = ''
		self.token_err = False
		self.token_can_update = False
		self.oldlinenum = self.contents.index(tkinter.INSERT).split('.')[0]
		
		self.do_syntax(everything=True)
			
		self.contents.bind( "<<WidgetViewSync>>", self.viewsync)
		
		####  Syntax-highlight End  ######################################
		
		# Layout Begin
		################################
		self.rowconfigure(1, weight=1)
		self.columnconfigure(1, weight=1)
		
		# It seems that widget is shown on screen when doing grid_configure
		self.btn_git.grid_configure(row=0, column = 0, sticky='nsew')
		self.entry.grid_configure(row=0, column = 1, sticky='nsew')
		self.btn_open.grid_configure(row=0, column = 2, sticky='nsew')
		self.btn_save.grid_configure(row=0, column = 3, columnspan=2, sticky='nsew')
		
		self.ln_widget.grid_configure(row=1, column = 0, sticky='nsw')
			
		# If want linenumbers:
		if self.want_ln:
			self.contents.grid_configure(row=1, column=1, columnspan=3, sticky='nswe')
		
		else:
			self.contents.grid_configure(row=1, column=0, columnspan=4, sticky='nswe')
			self.ln_widget.grid_remove()
			
		self.scrollbar.grid_configure(row=1,column=4, sticky='nse')
		
		
		# set cursor pos:
		line = self.tabs[self.tabindex].position
		self.contents.focus_set()
		
		try:
			self.contents.mark_set('insert', line)
			self.ensure_idx_visibility(line)
			
		except tkinter.TclError:
			self.contents.mark_set('insert', '1.0')
			self.tabs[self.tabindex].position = '1.0'
			self.contents.see('1.0')
		
		
		self.avoid_viewsync_mess()
		self.update_idletasks()
		self.viewsync()
		self.__class__.alive = True
		self.update_title()
		
		############################# init End ##########################
		
		
	def update_title(self, event=None):
		tail = len(self.tabs) - self.tabindex - 1
		self.title( f'Henxel {"0"*self.tabindex}@{"0"*(tail)}' )
		
	
	def wait_for(self, ms):
		self.waitvar.set(False)
		self.after(ms, self.waiter)
		self.wait_variable(self.waitvar)
		
	
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
		
	
	def ensure_idx_visibility(self, index, back=None):
		b=2
		if back:
			b=back
			
		self.contents.mark_set('insert', index)
		s = self.contents.bbox('%s - %ilines' % (index,b))
		e = self.contents.bbox('%s + 4lines' % index)
		
		tests = [
				not s,
				not e,
				( s and s[1] < 0 )
				]
				
		if any(tests):
			self.contents.see('%s - %ilines' % (index,b))
			self.update_idletasks()
			self.contents.see('%s + 4lines' % index)
		
		
	def quit_me(self):
	
		self.save(forced=True)
		self.save_config()
		
		# affects color, fontchoose, load:
		for widget in self.to_be_closed:
			widget.destroy()
		
		self.quit()
		self.destroy()
		
		if self.tracefunc_name:
			self.tracevar_filename.trace_remove('write', self.tracefunc_name)
		
		del self.font
		del self.menufont
		del self.boldfont
		
		# this is maybe not necessary
		del self.entry
		del self.btn_open
		del self.btn_save
		del self.btn_git
		del self.contents
		del self.ln_widget
		del self.scrollbar
		del self.popup
				
		self.__class__.alive = False
		
	
	def avoid_viewsync_mess(self, event=None):
		# Avoid viewsync messing when cursor
		# position is in line with multiline string marker:
		
		if self.tabs[self.tabindex].filepath:
			if self.can_do_syntax():
				pos = self.tabs[self.tabindex].position
				lineend = '%s lineend' % pos
				linestart = '%s linestart' % pos
				tmp = self.contents.get( linestart, lineend )
				self.oldline = tmp
				self.oldlinenum = pos.split('.')[0]
				self.token_can_update = True


	def viewsync(self, event=None):
		'''	Triggered when event is <<WidgetViewSync>>
			Used to update linenumbers and syntax highlight.
		
			This event itself is generated *after* when inserting, deleting or on screen geometry change, but
			not when just scrolling (like yview). Almost all font-changes also generates this event.
		'''
		
		# More info in update_linenums()
		self.bbox_height = self.contents.bbox('@0,0')[3]
		self.text_widget_height = self.scrollbar.winfo_height()
		
		self.update_linenums()
		
		if self.tabs[self.tabindex].filepath:
			if self.can_do_syntax():
				if self.token_can_update:
				
					#  tag alter triggers this event if font changes, like from normal to bold.
					# --> need to check if line is changed to prevent self-trigger
					line_idx = self.contents.index( tkinter.INSERT )
					linenum = line_idx.split('.')[0]
					#prev_char = self.contents.get( '%s - 1c' % tkinter.INSERT )
					
					
					lineend = '%s lineend' % line_idx
					linestart = '%s linestart' % line_idx
					
					tmp = self.contents.get( linestart, lineend )
					
					if self.oldline != tmp or self.oldlinenum != linenum:
					
						#print('sync')
						self.oldline = tmp
						self.oldlinenum = linenum
						self.update_tokens(start=linestart, end=lineend, line=tmp)
				

############## Linenumbers Begin

	def no_copy_ln(self, event=None):
		return 'break'
		
	
	def toggle_ln(self, event=None):
		
		# if dont want linenumbers:
		if self.want_ln:
			# remove remembers grid-options
			self.ln_widget.grid_remove()
			self.contents.grid_configure(column=0, columnspan=4)
			self.want_ln = False
		else:
			self.contents.grid_configure(column=1, columnspan=3)
			self.ln_widget.grid()
			
			self.want_ln = True
		
		return 'break'
		
	
	def get_linenums(self):

		x = 0
		line = '0'
		col= ''
		ln = ''

		# line-height is used as step, it depends on font:
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
				# is the line wrapping:
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
			
			y_offset = self.contents.bbox('@0,0')[1]
			
			y_offset *= -1
			
			#if self.y_extra_offset > 0, we need this:
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

	def new_tab(self, event=None, error=False):

		# event == None when clicked hyper-link in tag_link()
		if self.state != 'normal' and event != None:
			self.bell()
			return 'break'
	
		if len(self.tabs) > 0  and not error:
			try:
				pos = self.contents.index(tkinter.INSERT)
				
			except tkinter.TclError:
				pos = '1.0'
				
			self.tabs[self.tabindex].position = pos
			
			tmp = self.contents.get('1.0', tkinter.END)
			# [:-1]: remove unwanted extra newline
			self.tabs[self.tabindex].contents = tmp[:-1]
			
			
		self.contents.delete('1.0', tkinter.END)
		self.entry.delete(0, tkinter.END)
		
		if len(self.tabs) > 0:
			self.tabs[self.tabindex].active = False
			
		newtab = Tab()
		
		self.tabindex += 1
		self.tabs.insert(self.tabindex, newtab)
		
		self.contents.focus_set()
		self.contents.see('1.0')
		self.contents.mark_set('insert', '1.0')
		
		self.contents.edit_reset()
		self.contents.edit_modified(0)
		
		self.update_title()
		return 'break'
		
		
	def del_tab(self, event=None, save=True):

		if self.state != 'normal':
			self.bell()
			return 'break'
			
		if ((len(self.tabs) == 1) and self.tabs[self.tabindex].type == 'newtab'):
			self.contents.delete('1.0', tkinter.END)
			self.bell()
			return 'break'

		if self.tabs[self.tabindex].type == 'normal' and save:
			self.save(activetab=True)
			
		self.tabs.pop(self.tabindex)
			
		if (len(self.tabs) == 0):
			newtab = Tab()
			self.tabs.append(newtab)
	
		if self.tabindex > 0:
			self.tabindex -= 1
	
		self.tabs[self.tabindex].active = True
		self.entry.delete(0, tkinter.END)
		
		if self.tabs[self.tabindex].filepath:
			self.entry.insert(0, self.tabs[self.tabindex].filepath)
		
		
		self.contents.delete('1.0', tkinter.END)
		self.contents.insert(tkinter.INSERT, self.tabs[self.tabindex].contents)
		
		
		self.do_syntax(everything=True)
		
		# set cursor pos
		line = self.tabs[self.tabindex].position
		self.contents.focus_set()
		
		try:
			self.contents.mark_set('insert', line)
			self.ensure_idx_visibility(line)
			
		except tkinter.TclError:
			self.contents.mark_set('insert', '1.0')
			self.tabs[self.tabindex].position = '1.0'
			self.contents.see('1.0')
		
			
		self.contents.edit_reset()
		self.contents.edit_modified(0)
		
		self.avoid_viewsync_mess()
		self.update_title()
		
		return 'break'

		
	def walk_tabs(self, event=None, back=False):
	
		if self.state != 'normal' or len(self.tabs) < 2:
			self.bell()
			return "break"
		
		self.tabs[self.tabindex].active = False
		
		try:
			pos = self.contents.index(tkinter.INSERT)
		except tkinter.TclError:
			pos = '1.0'
		
		self.tabs[self.tabindex].position = pos
			
		tmp = self.contents.get('1.0', tkinter.END)
		# [:-1]: remove unwanted extra newline
		self.tabs[self.tabindex].contents = tmp[:-1]
			
		idx = self.tabindex
		
		if back:
			if idx == 0:
				idx = len(self.tabs)
			idx -= 1
			
		else:
			if idx == len(self.tabs) - 1:
				idx = -1
			idx += 1
		
		self.tabindex = idx
		self.tabs[self.tabindex].active = True
		self.entry.delete(0, tkinter.END)


		if self.tabs[self.tabindex].filepath:
			self.entry.insert(0, self.tabs[self.tabindex].filepath)
			
		
		self.token_can_update = False
		self.contents.delete('1.0', tkinter.END)
		self.contents.insert(tkinter.INSERT, self.tabs[self.tabindex].contents)
	
		if self.tabs[self.tabindex].filepath:
			if self.can_do_syntax():
				self.update_tokens(start='1.0', end=tkinter.END, everything=True)

		# set cursor pos
		line = self.tabs[self.tabindex].position
		self.contents.focus_set()
		
		try:
			self.contents.mark_set('insert', line)
			self.ensure_idx_visibility(line)
			
		except tkinter.TclError:
			self.contents.mark_set('insert', '1.0')
			self.tabs[self.tabindex].position = '1.0'
			self.contents.see('1.0')

		
		self.contents.edit_reset()
		self.contents.edit_modified(0)
		
		self.avoid_viewsync_mess()
		self.update_title()
		
		return 'break'

########## Tab Related End
########## Configuration Related Begin

	def save_config(self, event=None):
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
		
		have_fonts = self.fonts_exists(data)
		self.set_config(data, have_fonts)
		
	
	def fonts_exists(self, dictionary):
		
		res = True
		fontfamilies = [f for f in tkinter.font.families()]
		
		font = dictionary['font']['family']
		
		if font not in fontfamilies:
			print(f'Font {font.upper()} does not exist.')
			res = False
		
		font = dictionary['menufont']['family']
		
		if dictionary['menufont']['family'] not in fontfamilies:
			print(f'Font {font.upper()} does not exist.')
			res = False
			
		return res
		
		
	def get_config(self):
		dictionary = dict()
		dictionary['curtheme'] = self.curtheme
		dictionary['lastdir'] = self.lastdir.__str__()
		dictionary['font'] = self.font.config()
		dictionary['menufont'] = self.menufont.config()
		dictionary['scrollbar_width'] = self.scrollbar_width
		dictionary['elementborderwidth'] = self.elementborderwidth
		dictionary['want_ln'] = self.want_ln
		dictionary['syntax'] = self.syntax
		dictionary['ind_depth'] = self.ind_depth
		dictionary['themes'] = self.themes
		
		for tab in self.tabs:
			tab.contents = ''
			tab.oldcontents = ''
			
			# Convert tab.filepath to string for serialization
			if tab.filepath:
				tab.filepath = tab.filepath.__str__()
		
		tmplist = [ tab.__dict__ for tab in self.tabs ]
		dictionary['tabs'] = tmplist
		
		return dictionary
		
		
	def set_config(self, dictionary, fonts_exists=True):
		
		# Set Font Begin ##############################
		if not fonts_exists:
			fontname = None
			
			fontfamilies = [f for f in tkinter.font.families()]
			
			for font in GOODFONTS:
				if font in fontfamilies:
					fontname = font
					break
			
			if not fontname:
				fontname = 'TkDefaulFont'
				
			dictionary['font']['family']=fontname
			dictionary['menufont']['family']=fontname
			
		self.font.config(**dictionary['font'])
		self.menufont.config(**dictionary['menufont'])
		self.scrollbar_width 	= dictionary['scrollbar_width']
		self.elementborderwidth	= dictionary['elementborderwidth']
		self.want_ln = dictionary['want_ln']
		self.syntax = dictionary['syntax']
		self.ind_depth = dictionary['ind_depth']
		self.themes = dictionary['themes']
		self.curtheme = dictionary['curtheme']
		
		self.bgcolor, self.fgcolor = self.themes[self.curtheme]['normal_text'][:]
			
		self.lastdir = dictionary['lastdir']
		
		if self.lastdir != None:
			self.lastdir = pathlib.Path(dictionary['lastdir'])
			if not self.lastdir.exists():
				self.lastdir = None
		
		self.tabs = [ Tab(**item) for item in dictionary['tabs'] ]
		
		# Have to step backwards here to avoid for-loop breaking
		# while removing items from the container.
		
		for i in range(len(self.tabs)-1, -1, -1):
			tab = self.tabs[i]
			
			if tab.type == 'normal':
				try:
					with open(tab.filepath, 'r', encoding='utf-8') as f:
						tmp = f.read()
						tab.contents = tmp
						tab.oldcontents = tab.contents
						
					tab.filepath = pathlib.Path(tab.filepath)
					
					
				except (EnvironmentError, UnicodeDecodeError) as e:
					print(e.__str__())
					self.tabs.pop(i)
			else:
				tab.filepath = None
				tab.position = '1.0'
				
		for i,tab in enumerate(self.tabs):
			if tab.active == True:
				self.tabindex = i
				break
		

	def apply_config(self):
		
		if self.tabindex == None:
			if len(self.tabs) == 0:
				self.tabindex = -1
				self.new_tab()
			# recently active normal tab is gone:
			else:
				self.tabindex = 0
				self.tabs[self.tabindex].active = True
		
	
		self.tab_width = self.font.measure(self.ind_depth * TAB_WIDTH_CHAR)
		

		for tagname in self.themes[self.curtheme]:
			bg, fg = self.themes[self.curtheme][tagname][:]
			self.contents.tag_config(tagname, background=bg, foreground=fg)
		
		
		self.contents.config(font=self.font, foreground=self.fgcolor,
			background=self.bgcolor, insertbackground=self.fgcolor,
			tabs=(self.tab_width, ))
			
		self.scrollbar.config(width=self.scrollbar_width)
		self.scrollbar.config(elementborderwidth=self.elementborderwidth)
		
		self.ln_widget.config(font=self.font, foreground=self.fgcolor, background=self.bgcolor)
			
		self.entry.config(font=self.menufont)
		self.btn_open.config(font=self.menufont)
		self.btn_save.config(font=self.menufont)
		self.btn_git.config(font=self.menufont)
		self.popup.config(font=self.menufont)
		
		if self.tabs[self.tabindex].type == 'normal':
			self.contents.insert(tkinter.INSERT, self.tabs[self.tabindex].contents)
			self.entry.insert(0, self.tabs[self.tabindex].filepath)
			
		self.contents.edit_reset()
		self.contents.edit_modified(0)
		
########## Configuration Related End
########## Syntax highlight Begin
	
	def toggle_syntax(self, event=None):
		
		if self.syntax:
			self.syntax = False
			self.token_can_update = False
			
			for tag in self.tagnames:
				self.contents.tag_remove( tag, '1.0', tkinter.END )
				
			return 'break'
	
		else:
			self.syntax = True
			self.do_syntax(everything=True)
			
			return 'break'
			
	
	def can_do_syntax(self):
	
		return '.py' in self.tabs[self.tabindex].filepath.suffix and self.syntax
		
		
	def do_syntax(self, everything=False):
	
		if self.tabs[self.tabindex].filepath:
			if self.can_do_syntax():
			
				self.token_err = True
				content_is_uptodate = everything
				self.update_tokens(start='1.0', end=tkinter.END, everything=content_is_uptodate)
				self.token_can_update = True
				
			else:
				self.token_err = False
				self.token_can_update = False
			
		else:
			self.token_err = False
			self.token_can_update = False
			
	
	def update_tokens(self, start=None, end=None, line=None, everything=False):
	
		start_idx = start
		end_idx = end
		linecontents = None
		
		if not everything:
			if line:
				linecontents = line
				test1 = [
					self.token_err,
					( '"""' in linecontents and '#' in linecontents ),
					( "'''" in linecontents and '#' in linecontents )
					]
			else:
				test1 = [self.token_err]
				
				
			if any(test1):
				start_idx = '1.0'
				end_idx = tkinter.END
				linecontents = None
				#print('err')
		
			# check if inside multiline string
			elif 'strings' in self.contents.tag_names(tkinter.INSERT) and \
					not ( start_idx == '1.0' and end_idx == tkinter.END ):
				
				try:
					s, e = self.contents.tag_prevrange('strings', tkinter.INSERT)
					l0, l1 = map( lambda x: int( x.split('.')[0] ), [s, e] )
				
					if l0 != l1:
						start_idx, end_idx = (s, e)
						linecontents = None
		
				except ValueError:
					pass
			
			
			if not linecontents:
				tmp = self.contents.get( start_idx, end_idx )
				
			else:
				tmp = linecontents
				
		else:
			tmp = self.tabs[self.tabindex].contents
			
		
		
		prev_char = self.contents.get( '%s - 1c' % tkinter.INSERT, tkinter.INSERT )
		if prev_char in [ '(', ')', '[', ']' , '{', '}' ]:
			self.par_err = True
		
		linenum = int(start_idx.split('.')[0])
		flag_err = False
		#print(self.token_err)
		
		
		try:
			par_err = None
			
			with io.BytesIO( tmp.encode('utf-8') ) as fo:
			
				tokens = tokenize.tokenize( fo.readline )
			
				# Remove old tags:
				for tag in self.tagnames:
					self.contents.tag_remove( tag, start_idx, end_idx )
					
				# Retag:
				idx_start = None
				for token in tokens:
					#print(token)
					
					# token.line contains line as string which contains token.
					
					if token.type == tokenize.NAME or \
						( token.type in [ tokenize.NUMBER, tokenize.STRING, tokenize.COMMENT] ) or \
						( token.exact_type == tokenize.LPAR ):
						
						# initiate indexes with correct linenum
						s0, s1 = map(str, [ token.start[0] + linenum - 1, token.start[1] ] )
						e0, e1 = map(str, [ token.end[0] + linenum - 1, token.end[1] ] )
						idx_start = s0 + '.' + s1
						idx_end = e0 + '.' + e1
						
							
						if token.type == tokenize.NAME:
							
							#lastoken = token
							last_idx_start = idx_start
							last_idx_end = idx_end
							
							if token.string in self.keywords:
							
								if token.string == 'self':
									self.contents.tag_add('selfs', idx_start, idx_end)
								
								elif token.string in self.bools:
									self.contents.tag_add('bools', idx_start, idx_end)
									
##								elif token.string in self.tests:
##									self.contents.tag_add('tests', idx_start, idx_end)
								
								elif token.string in self.breaks:
									self.contents.tag_add('breaks', idx_start, idx_end)
								
								else:
									self.contents.tag_add('keywords', idx_start, idx_end)
								
						
						# calls
						elif token.exact_type == tokenize.LPAR:
							# Need to know if last char before ( was not empty.
							# Previously used test was:
							#if self.contents.get( '%s - 1c' % idx_start, idx_start ).strip():
							
							# token.line contains line as string which contains token.
							prev_char_idx = token.start[1]-1
							if prev_char_idx > -1 and token.line[prev_char_idx].isalnum():
								self.contents.tag_add('calls', last_idx_start, last_idx_end)
								
						elif token.type == tokenize.STRING:
							self.contents.tag_add('strings', idx_start, idx_end)
							
						elif token.type == tokenize.COMMENT:
							self.contents.tag_add('comments', idx_start, idx_end)
						
						# token.type == tokenize.NUMBER
						else:
							self.contents.tag_add('numbers', idx_start, idx_end)
					
		
		except IndentationError as e:
##			for attr in ['args', 'filename', 'lineno', 'msg', 'offset', 'text']:
##				item = getattr( e, attr)
##				print( attr,': ', item )

			# This Error needs info about whole block, one line is not enough, so quite rare.
			#print( e.args[0], '\nIndentation errline: ', self.contents.index(tkinter.INSERT) )
			flag_err = True
			self.token_err = True

		
		except tokenize.TokenError as ee:
			
			if 'EOF in multi-line statement' in ee.args[0]:
				self.check_pars = idx_start
				
			elif 'multi-line string' in ee.args[0]:
				flag_err = True
				self.token_err = True
			
			
		# from backspace_override:
		if self.check_pars:
			startl = self.check_pars
			par_err = self.checkpars(startl)
			
		elif self.par_err:
			startl = False
			par_err = self.checkpars(startl)

		self.check_pars = False
		self.par_err = par_err

		if not par_err:
			# not always checking whole file for par mismatches, so clear
			self.contents.tag_remove('mismatch', '1.0', tkinter.END)
			


		if not flag_err and ( start_idx == '1.0' and end_idx == tkinter.END ):
			#print('ok')
			self.token_err = False
			
			
	def checkpars(self, idx_start):
		# possible par mismatch may be caused from another line,
		# so find current block: find first empty line before and after curline
		# then count pars in it.
		
		if not idx_start:
			# line had nothing but brace in it and it were deleted
			idx_start = self.contents.index(tkinter.INSERT)
			
		curline = int( idx_start.split('.')[0] )
		startline, endline, lines = self.find_empty_lines(curline)
		err_indexes = self.count_pars(startline, lines)
		
		err = False
		
		if err_indexes:
			err = True
			err_line = startline + err_indexes[0]
			err_col = err_indexes[1]
			err_idx = '%i.%i' % (err_line, err_col)
			
			self.contents.tag_remove('mismatch', '1.0', tkinter.END)
			self.contents.tag_add('mismatch', err_idx, '%s +1c' % err_idx)
		
		#print(err)
		return err
	
	
	def count_pars(self, startline, lines):
		
		pars = list()
		bras = list()
		curls = list()
		
		opening  = [ '(', '[', '{' ]
		closing  = [ ')', ']', '}' ]
		
		tags = None
		
		# populate lists and return at first extra closer:
		for i in range(len(lines)):
			
			for j in range(len(lines[i])):
				c = lines[i][j]
				patt = '%i.%i' % (startline+i, j)
				tags = self.contents.tag_names(patt)

				# skip if string or comment:
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
		# Return last extra opener:
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

		
	def find_empty_lines(self, lnstart):
		'''	Finds first empty lines before and after current line
			
			returns
				linenumber of start and end of the block
				and list of lines.

			called from update_tokens
		'''

		lines = list()

		# first empty line before curline:
		endln = 1
		ln = lnstart

		if ln > endln:
			ln -= 1
			t = self.contents.get('%i.0' % ln, '%i.end' % ln)
			
			while t != '' and not t.isspace():
				lines.append(t)
				ln -= 1
				
				if ln < endln:
					break
				
				t = self.contents.get('%i.0' % ln, '%i.end' % ln)
			
			ln += 1

		else:
			pass
			# curline is firstline


		# ln is now first empty linenum above curline or firstline
		startline = ln


		# add curline to list
		ln = lnstart
		lines.reverse()
		t = self.contents.get('%i.0' % ln, '%i.end' % ln)
		lines.append(t)


		# first empty line after curline:
		endln = int( self.contents.index(tkinter.END).split('.')[0] )
		ln += 1
		
		if ln < endln:
			
			t = self.contents.get('%i.0' % ln, '%i.end' % ln)

			while  t != '' and not t.isspace():
				lines.append(t)
				ln += 1

				if ln > endln:
					break

				t = self.contents.get('%i.0' % ln, '%i.end' % ln)
				
			ln -= 1
			
		else:
			# curline is lastline
			pass

		# ln is now first empty linenum after curline or lastline
		endline = ln

		return startline, endline, lines
							

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


	def increase_scrollbar_width(self, event=None):
		'''	Change width of scrollbar and self.contents
			Shortcut: Ctrl-plus
		'''
		if self.scrollbar_width >= 100:
			self.bell()
			return 'break'
			
		self.scrollbar_width += 7
		self.elementborderwidth += 1
		self.scrollbar.config(width=self.scrollbar_width)
		self.scrollbar.config(elementborderwidth=self.elementborderwidth)
			
		return 'break'
		
		
	def decrease_scrollbar_width(self, event=None):
		'''	Change width of scrollbar and self.contents
			Shortcut: Ctrl-minus
		'''
		if self.scrollbar_width <= 0:
			self.bell()
			return 'break'
			
		self.scrollbar_width -= 7
		self.elementborderwidth -= 1
		self.scrollbar.config(width=self.scrollbar_width)
		self.scrollbar.config(elementborderwidth=self.elementborderwidth)
			
		return 'break'
		

	def toggle_color(self, event=None):
		
		if self.curtheme == 'day':
			self.curtheme = 'night'
		else:
			self.curtheme = 'day'
		
		self.update_normal_text()
		
		return 'break'


	def update_normal_text(self):
	
		self.bgcolor, self.fgcolor = self.themes[self.curtheme]['normal_text'][:]
			
	
		for tagname in self.themes[self.curtheme]:
			bg, fg = self.themes[self.curtheme][tagname][:]
			self.contents.tag_config(tagname, background=bg, foreground=fg)
	
		
		self.contents.config(foreground=self.fgcolor, background=self.bgcolor,
			insertbackground=self.fgcolor)
			
		self.ln_widget.config(foreground=self.fgcolor, background=self.bgcolor, selectbackground=self.bgcolor, selectforeground=self.fgcolor, inactiveselectbackground=self.bgcolor )
	
	
	def update_fonts(self):
		self.boldfont = self.font.copy()
		self.boldfont.config(weight='bold')
		
		self.contents.tag_config('keywords', font=self.boldfont)
		self.contents.tag_config('numbers', font=self.boldfont)
		self.contents.tag_config('comments', font=self.boldfont)
		self.contents.tag_config('breaks', font=self.boldfont)
		self.contents.tag_config('calls', font=self.boldfont)
		
		self.tab_width = self.font.measure(self.ind_depth * self.tab_char)
		self.contents.config(tabs=(self.tab_width, ))

					
	def font_choose(self, event=None):
		if self.state != 'normal':
			self.bell()
			return "break"
		
		fonttop = tkinter.Toplevel()
		fonttop.title('Choose Font')
		
		fonttop.protocol("WM_DELETE_WINDOW", lambda: ( fonttop.destroy(),
				self.contents.bind( "<Alt-f>", self.font_choose)) )
			
		changefont.FontChooser( fonttop, [self.font, self.menufont], tracefunc=self.update_fonts )
		self.contents.bind( "<Alt-f>", self.do_nothing)
		self.to_be_closed.append(fonttop)
	
		return 'break'
		
		
	def enter2(self, args, event=None):
		''' When mousecursor enters hyperlink tagname in colorchooser.
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
		
		
		t = wid.textwid
	
		if tagname in syntags:
			r = t.tag_nextrange(tagname, 1.0)
			
			t.delete(r[0], r[1])
			t.insert(r[0], '%s\n' % tagname, tagname)
		
		
		t.config(cursor="hand2")
		t.tag_config(tagname, underline=1, font=self.boldfont)
		
		
	def leave2(self, args, event=None):
		''' When mousecursor leaves hyperlink tagname in colorchooser.
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
		
		
		t = wid.textwid
	
		if tagname in syntags:
			r = t.tag_nextrange(tagname, 1.0)
			
			t.delete(r[0], r[1])
			t.insert(r[0], '%s\n' % tagname, tagname)
		
		
		t.config(cursor=self.name_of_cursor_in_text_widget)
		t.tag_config(tagname, underline=0, font=self.menufont)
		
		
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
				return 'break'
			
			
			try:
				if wid.frontback_mode == 'foreground':
					self.themes[self.curtheme][tagname][1] = tmpcolor
					self.contents.tag_config(tagname, foreground=tmpcolor)
				else:
					self.themes[self.curtheme][tagname][0] = tmpcolor
					self.contents.tag_config(tagname, background=tmpcolor)
			
			
				if tagname == 'normal_text':
					self.update_normal_text()
				
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
			
			if tagname == 'Save_TMP':
				wid.tmp_theme = copy.deepcopy(self.themes)
				wid.flag_tmp = True
				self.flash_tag(wid, tagname)
				
			elif tagname == 'TMP' and flag_tmp:
				self.themes = copy.deepcopy(wid.tmp_theme)
				self.flash_tag(wid, tagname)
				
			elif tagname == 'Start':
				self.themes = copy.deepcopy(wid.start_theme)
				self.flash_tag(wid, tagname)
				
			elif tagname == 'Defaults':
				self.themes = copy.deepcopy(self.default_themes)
				self.flash_tag(wid, tagname)
				
				
			if (tagname in ['Defaults', 'Start']) or (tagname == 'TMP' and wid.flag_tmp):
			
				for tag in self.themes[self.curtheme]:
					bg, fg = self.themes[self.curtheme][tag][:]
					self.contents.tag_config(tag, background=bg, foreground=fg)
	
				self.update_normal_text()
				
				
	def flash_tag(self, wid, tagname):
		''' Flash save_tag when clicked in colorchooser.
		'''
		t = wid.textwid
		
		wid.after(100, lambda args=[tagname],
				kwargs={'background':'green'}: t.tag_config(*args, **kwargs) )
					
		wid.after(600, lambda args=[tagname],
				kwargs={'background':t.cget('background')}: t.tag_config(*args, **kwargs) )
					
	
	def color_choose(self, event=None):
		if self.state != 'normal':
			self.bell()
			return "break"
			
		colortop = tkinter.Toplevel()
		c = colortop
		c.title('Choose Color')
		c.start_theme = copy.deepcopy(self.themes)
		c.tmp_theme = copy.deepcopy(self.themes)
		c.flag_tmp = False
		
		c.protocol("WM_DELETE_WINDOW", lambda: ( c.destroy(),
				self.bind( "<Alt-s>", self.color_choose),
				self.bind( "<Alt-t>", self.toggle_color)) )
				
		self.bind( "<Alt-s>", self.do_nothing)
		self.bind( "<Alt-t>", self.do_nothing)
		
		#c.textfont = tkinter.font.Font(family='TkDefaulFont', size=10)
		c.titlefont = tkinter.font.Font(family='TkDefaulFont', size=12)
		
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
		t.insert(i, 'normal_text\n', 'normal_text')
		
		
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
		
		# passing tagname-string as argument to function self.taglink()
		# which in turn is a value of tagname-key in dictionary taglinks:
		self.taglinks[tagname](tagname)
		

	def tag_link(self, tagname, event=None):
		''' Used in error-page, executed when hyperlink tagname is clicked.
		'''
		
		i = int(tagname.split("-")[1])
		filepath, errline = self.errlines[i]
		
		filepath = pathlib.Path(filepath)
		openfiles = [tab.filepath for tab in self.tabs]
		
		# clicked activetab, do nothing
		if filepath == self.tabs[self.tabindex].filepath:
			pass
			
		# clicked file that is open, switch activetab
		elif filepath in openfiles:
			for i,tab in enumerate(self.tabs):
				if tab.filepath == filepath:
					self.tabs[self.tabindex].active = False
					self.tabindex = i
					self.tabs[self.tabindex].active = True
					break
					
		# else: open file in newtab
		else:
			try:
				with open(filepath, 'r', encoding='utf-8') as f:
					self.new_tab(error=True)
					tmp = f.read()
					self.tabs[self.tabindex].oldcontents = tmp
					
					if '.py' in filepath.suffix:
						indentation_is_alien, indent_depth = self.check_indent_depth(tmp)
						
						if indentation_is_alien:
							# Assuming user wants self.ind_depth, change it without notice:
							tmp = self.tabs[self.tabindex].oldcontents.splitlines(True)
							tmp[:] = [self.tabify(line, width=indent_depth) for line in tmp]
							tmp = ''.join(tmp)
							self.tabs[self.tabindex].contents = tmp
							
						else:
							self.tabs[self.tabindex].contents = self.tabs[self.tabindex].oldcontents
					else:
						self.tabs[self.tabindex].contents = self.tabs[self.tabindex].oldcontents
				
					
					self.tabs[self.tabindex].filepath = filepath
					self.tabs[self.tabindex].type = 'normal'
			except (EnvironmentError, UnicodeDecodeError) as e:
				print(e.__str__())
				print(f'\n Could not open file: {filepath}')
				self.bell()
				return

		
		self.entry.delete(0, tkinter.END)
		self.entry.insert(0, self.tabs[self.tabindex].filepath)
		
		
		self.contents.delete('1.0', tkinter.END)
		self.contents.insert(tkinter.INSERT, self.tabs[self.tabindex].contents)
		
		
		if self.syntax:
		
			lineend = '%s lineend' % tkinter.INSERT
			linestart = '%s linestart' % tkinter.INSERT
			
			tmp = self.contents.get( linestart, lineend )
			self.oldline = tmp
			
			self.token_err = True
			self.update_tokens(start='1.0', end=tkinter.END)
			self.token_can_update = True
		
		
		# set cursor pos
		line = errline + '.0'
		self.contents.focus_set()
		self.contents.mark_set('insert', line)
		self.ensure_idx_visibility(line)
					
		
		self.contents.edit_reset()
		self.contents.edit_modified(0)
		
		self.bind("<Button-3>", lambda event: self.raise_popup(event))
		self.state = 'normal'
		self.update_title()
		

	def run(self):
		'''	Run file currently being edited. This can not catch errlines of
			those exceptions that are catched. Like:
			
			try:
				code we know sometimes failing with SomeError
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
		if (self.state != 'normal') or (self.tabs[self.tabindex].type == 'newtab'):
			self.bell()
			return 'break'
			
		self.save(forced=True)
		
		# https://docs.python.org/3/library/subprocess.html

		res = subprocess.run(['python', self.tabs[self.tabindex].filepath], stderr=subprocess.PIPE).stderr
		
		err = res.decode()
		
		if len(err) != 0:
			self.bind("<Escape>", self.stop_show_errors)
			self.bind("<Button-3>", self.do_nothing)
			self.state = 'error'
			
			self.taglinks = dict()
			self.errlines = list()
			openfiles = [tab.filepath for tab in self.tabs]
			
			self.contents.delete('1.0', tkinter.END)
			
			for tag in self.contents.tag_names():
				if 'hyper' in tag:
					self.contents.tag_delete(tag)
				
			self.err = err.splitlines()
			
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
					
					# Make look bit nicer:
					if self.syntax:
						# -1 lines because we have added linebreak already.
						start = self.contents.index('insert -1 lines linestart')
						end = self.contents.index('insert -1 lines lineend')
						
						self.update_tokens(start=start, end=end, line=line)
			
					
		return 'break'
				

	def show_errors(self):
		''' Show traceback from last run with added hyperlinks.
		'''
		
		if len(self.errlines) != 0:
			self.bind("<Escape>", self.stop_show_errors)
			self.bind("<Button-3>", self.do_nothing)
			self.state = 'error'
			
			tmp = self.contents.get('1.0', tkinter.END)
			# [:-1]: remove unwanted extra newline
			self.tabs[self.tabindex].contents = tmp[:-1]
			
			try:
				pos = self.contents.index(tkinter.INSERT)
			except tkinter.TclError:
				pos = '1.0'
				
			self.tabs[self.tabindex].position = pos
			self.contents.delete('1.0', tkinter.END)
			openfiles = [tab.filepath for tab in self.tabs]
			
			for tag in self.contents.tag_names():
				if 'hyper' in tag:
					self.contents.tag_config(tag, foreground=self.fgcolor)
			
			i = 0
			for line in self.err:
				tmp = line
				tagname = 'hyper-%d' % i
				
				# Parse filepath and linenums from errors
				if 'File ' in line and 'line ' in line:
					self.contents.insert(tkinter.INSERT, '\n')
					data = line.split(',')[:2]
					linenum = data[1][6:]
					path = data[0][8:-1]
					pathlen = len(path) + 2
					filepath = pathlib.Path(path)
					
					self.contents.insert(tkinter.INSERT, tmp)
					s0 = tmp.index(path) - 1
					s = self.contents.index('insert linestart +%sc' % s0 )
					e = self.contents.index('%s +%sc' % (s, pathlen) )
					
					self.contents.tag_add(tagname, s, e)
					
					if filepath in openfiles:
						self.contents.tag_config(tagname, foreground='brown1')
						self.contents.tag_raise(tagname)
						
						
					self.contents.insert(tkinter.INSERT, '\n')
					
					i += 1
					
				else:
					self.contents.insert(tkinter.INSERT, tmp +"\n")
					
					# Make look bit nicer:
					if self.syntax:
						# -1 lines because we have added linebreak already.
						start = self.contents.index('insert -1 lines linestart')
						end = self.contents.index('insert -1 lines lineend')
						
						self.update_tokens(start=start, end=end, line=line)
			
					
									
	def stop_show_errors(self, event=None):
		self.state = 'normal'
		self.bind("<Escape>", self.do_nothing)
		self.bind("<Button-3>", lambda event: self.raise_popup(event))
		
		self.entry.delete(0, tkinter.END)
		
		if self.tabs[self.tabindex].type == 'normal':
			self.entry.insert(0, self.tabs[self.tabindex].filepath)
			
		
		self.contents.delete('1.0', tkinter.END)
		self.contents.insert(tkinter.INSERT, self.tabs[self.tabindex].contents)
		
		
		self.do_syntax(everything=True)
		
		
		# set cursor pos
		line = self.tabs[self.tabindex].position
		self.contents.focus_set()
		self.contents.mark_set('insert', line)
		self.ensure_idx_visibility(line)
			
			
		self.contents.edit_reset()
		self.contents.edit_modified(0)
		
		
########## Run file Related End
########## Overrides Begin

	def move_right(self, event=None):
		''' move cursor right with
			ctrl-i
		'''
		
		if self.state not in  [ 'normal', 'error' ]:
			self.bell()
			return "break"
		
		pos = self.contents.index( '%s + 1c' % tkinter.INSERT)
		self.contents.see(pos)
		self.contents.mark_set('insert', pos)
		
		return "break"
		
	
	def center_view(self, event=None):
		''' Raise insertion-line
		'''
		if self.state != 'normal':
			self.bell()
			return "break"
			
			
		self.contents.yview_scroll(12, 'units')
		return "break"
		
		
	def goto_linestart(self, event=None):
		if self.state != 'normal':
			self.bell()
			return "break"
		
		self.ensure_idx_visibility('insert')
		
		# In case of wrapped lines
		y_cursor = self.contents.bbox(tkinter.INSERT)[1]
		p = self.contents.index( '@0,%s' % y_cursor )
		p2 = self.contents.index( '%s linestart' % p )
		
		# is wrapped?
		c1 = int(p.split('.')[1])
		l2 = int(p2.split('.')[0])
		
		# yes, put cursor start of line not the whole line:
		if c1 != 0:
			pos = p
			
		# no, so put cursor after indentation:
		else:
			tmp = self.contents.get( '%s linestart' % p2, '%s lineend' % p2 )
			if len(tmp) > 0:
				if not tmp.isspace():
					tmp2 = tmp.lstrip()
					indent = tmp.index(tmp2)
					pos = self.contents.index( '%i.%i' % (l2, indent) )
		
		
		self.contents.see(pos)
		self.contents.mark_set('insert', pos)
		
		return "break"
	
	
	def raise_popup(self, event=None):
		if self.state != 'normal':
			self.bell()
			return "break"
		
		self.popup.post(event.x_root, event.y_root)
		self.popup.focus_set() # Needed to remove popup when clicked outside.
		
		
	def popup_focusOut(self, event=None):
		self.popup.unpost()
	

	def copy(self):
		''' When copy is selected from popup-menu
		'''
		try:
			self.clipboard_clear()
			self.clipboard_append(self.selection_get())
		except tkinter.TclError:
			# is empty
			return 'break'
		

	def move_line(self, event=None, direction=None):
		''' Adjust cursor line indentation, with arrow left and right,
			when pasting more than one line etc.
		'''

		# Enable continue adjusting selection area
		if self.state != 'normal' or event.state != 0:
			return 'continue'


		if len(self.contents.tag_ranges('sel')) > 0:
			insert_at_selstart = False

			s = self.contents.index(tkinter.SEL_FIRST)
			e = self.contents.index(tkinter.SEL_LAST)
			i = self.contents.index(tkinter.INSERT)
			# contents of line with cursor:
			t = self.contents.get('%s linestart' % i, '%s lineend' % i)

			if i == s:
				insert_at_selstart = True

			# else: insert at selend

			line_s = s.split('.')[0]
			line_e = e.split('.')[0]

			# One line only:
			if line_s == line_e: 	return 'continue'

			# cursor line is empty:
			if len(t.strip()) == 0: return 'continue'


			self.contents.tag_remove('sel', '1.0', tkinter.END)
			self.contents.tag_add('sel', '%s linestart' % i, '%s lineend' % i)


			if direction == 'left':

				# Cursor at the start of the line, or there is no indentation left:
				if i.split('.')[1] == 0 or not t[0].isspace():
					self.contents.tag_remove('sel', '1.0', tkinter.END)
					self.contents.tag_add('sel', s, e)
					return 'break'

				self.unindent()
				self.contents.tag_remove('sel', '1.0', tkinter.END)

				if insert_at_selstart:
					self.contents.tag_add('sel',  '%s -1c' % s, e)
				else:
					self.contents.tag_add('sel', s, '%s -1c' % e)

			# right
			else:
				self.indent()
				self.contents.tag_remove('sel', '1.0', tkinter.END)

				if insert_at_selstart:
					self.contents.tag_add('sel',  '%s +1c' % s, e)
				else:
					self.contents.tag_add('sel', s, '%s +1c' % e)
					

			return 'break'

		return 'continue'
	

	def paste(self, event=None):
		'''	First line usually is in wrong place after paste
			because of selection has not started at the beginning of the line.
			So we put cursor at the beginning of insertion after pasting it
			so we can start indenting it.
		'''
		
		try:
			tmp = self.clipboard_get()
			tmp = tmp.splitlines(True)
		
		except tkinter.TclError:
			# is empty
			return 'break'
	
		line = self.contents.index(tkinter.INSERT)
		self.contents.event_generate('<<Paste>>')
		
								
		if len(tmp) > 1:
			self.contents.tag_remove('sel', '1.0', tkinter.END)
			
			s = self.contents.index( '%s linestart' % line)
			e = self.contents.index( 'insert lineend')
			t = self.contents.get( s, e )
			
			if self.tabs[self.tabindex].filepath:
				if self.can_do_syntax():
					self.update_tokens( start=s, end=e, line=t )
					
			
			self.contents.tag_add('sel', line, tkinter.INSERT)
			self.contents.mark_set('insert', line)
				
			self.wait_for(100)
			self.ensure_idx_visibility(line)
			
			
		elif len(tmp) == 1 and tmp[-1][-1] == '\n':
			s = self.contents.index( '%s linestart' % line)
			e = self.contents.index( '%s lineend' % line)
			t = self.contents.get( s, e )
			
			if self.tabs[self.tabindex].filepath:
				if self.can_do_syntax():
					self.update_tokens( start=s, end=e, line=t )
				
		
		return 'break'
	

	def undo_override(self, event=None):
		if self.state != 'normal':
			self.bell()
			return "break"
		 
		try:
			self.contents.edit_undo()
			
			
			self.do_syntax()
			
			
		except tkinter.TclError:
			self.bell()
			
		return 'break'
		
		
	def redo_override(self, event=None):
		if self.state != 'normal':
			self.bell()
			return "break"
			
		try:
			self.contents.edit_redo()
			
			
			self.do_syntax()
			
			
		except tkinter.TclError:
			self.bell()
			
		return 'break'
		
		
	def select_all(self, event=None):
		self.contents.tag_remove('sel', '1.0', tkinter.END)
		self.contents.tag_add('sel', 1.0, tkinter.END)
		return "break"
	
	
	def tab_override(self, event):
		'''	Used to bind Tab-key with indent()
		'''
		
		if self.state in [ 'search', 'replace', 'replace_all' ]:
			return 'break'
				
		# dont know if this is needed
		if hasattr(event, 'state') and event.state != 0:
			return
		
		# Fix for tab-key not working sometimes.
		# This happens because os-clipboard content is (automatically)
		# added to selection content of a Text widget, and since there is no
		# actual selection (clipboard-text is outside from Text-widget),
		# tab_override() gets quite broken.
		if len(self.contents.tag_ranges('sel')) == 0:
			return
		
		try:
			tmp = self.contents.selection_get()
			self.indent(event)
			return 'break'
			
		except tkinter.TclError:
			# No selection
			return

	
	def backspace_override(self, event):
		""" for syntax highlight
		"""
		
		if self.state != 'normal' or event.state != 0:
			return
		
		pars = [ '(', ')', '[', ']' , '{', '}' ]
		
		try:
			
			# Is there a selection?
			if len(self.contents.tag_ranges('sel')) > 0:
				tmp = self.contents.selection_get()
				l = [ x for x in tmp if x in pars ]
				if len(l) > 0:
					self.par_err = True
				
			self.contents.delete( tkinter.SEL_FIRST, tkinter.SEL_LAST )
			
			self.do_syntax()
			
			return 'break'
			
				
		except tkinter.TclError:
			# Deleting one letter
			
			
			# Rest is multiline string check
			chars = self.contents.get( '%s - 3c' % tkinter.INSERT, '%s + 2c' % tkinter.INSERT )
			
			triples = ["'''", '"""']
			doubles = ["''", '""']
			singles = ["'", '"']
			
			prev_3chars = chars[:3]
			prev_2chars = chars[1:3]
			next_2chars = chars[-2:]
			
			prev_char = chars[2:3]
			next_char = chars[-2:-1]
		
			quote_tests = [
						(prev_char == '#'),
						(prev_3chars in triples),
						( (prev_2chars in doubles) and (next_char in singles) ),
						( (prev_char in singles) and (next_2chars in doubles) )
						]
						
			if any(quote_tests):
				#print('#')
				self.token_err = True
				
				
			# To trigger parcheck if only one of these was in line and it was deleted:
			if prev_char in pars:
				self.par_err = True
				
				
		#print('deleting')
				
		return

	
	def return_override(self, event):
		if self.state != 'normal':
			self.bell()
			return "break"
		
		# ctrl_L-super_L-return
		if event.state == 68:
			self.run()
			return "break"
		
	
		# Cursor indexes when pressed return:
		line, col = map(int, self.contents.index(tkinter.INSERT).split('.'))
		
		
		# First an easy case:
		if col == 0:
			self.contents.insert(tkinter.INSERT, '\n')
			self.contents.see(f'{line+1}.0')
			self.contents.edit_separator()
			return "break"
			
		
		tmp = self.contents.get('%s.0' % str(line),'%s.0 lineend' % str(line))
		
		# Then one special case: check if cursor is inside indentation,
		# and line is not empty.
		if tmp[:col].isspace() and not tmp[col:].isspace():
			self.contents.insert(tkinter.INSERT, '\n')
			self.contents.insert('%s.0' % str(line+1), tmp[:col])
			self.contents.see(f'{line+1}.0')
			self.contents.edit_separator()
			return "break"
			
		else:
			for i in range(len(tmp)):
				if tmp[i] != '\t':
					break
	
			self.contents.insert(tkinter.INSERT, '\n') # Manual newline because return is overrided.
			self.contents.insert(tkinter.INSERT, i*'\t')
			self.contents.see(f'{line+1}.0')
			self.contents.edit_separator()
			return "break"
			
			
	def sbset_override(self, *args):
		'''	Fix for: not being able to config slider min-size
		'''
		self.scrollbar.set(*args)
		
		h = self.text_widget_height

		# Relative position (tuple on two floats) of
		# slider-top (a[0]) and -bottom (a[1]) in scale 0-1, a[0] is smaller:
		a = self.scrollbar.get()

		# current slider size:
		# (a[1]-a[0])*h

		# want to set slider size to at least p (SLIDER_MINSIZE) pixels,
		# by adding relative amount(0-1) of d to slider, that is: d/2 to both ends:
		# ( a[1]+d/2 - (a[0]-d/2) )*h = p
		# a[1] - a[0] + d = p/h
		# d = p/h - a[1] + a[0]


		d = SLIDER_MINSIZE/h - a[1] + a[0]

		if h*(a[1] - a[0]) < SLIDER_MINSIZE:
			self.scrollbar.set(a[0], a[1]+d)
		
		self.update_linenums()
		

########## Overrides End
########## Utilities Begin

	def insert_inspected(self):
		''' Tries to inspect selection. On success: opens new tab and pastes lines there.
			New tab can be safely closed with ctrl-d later, or saved with new filename.
		'''
		try:
			target = self.contents.selection_get()
		except tkinter.TclError:
			self.bell()
			return 'break'
		
		target=target.strip()
		
		if not len(target) > 0:
			self.bell()
			return 'break'
		
		
		import inspect
		is_module = False
		
		try:
			mod = importlib.import_module(target)
			is_module = True
			filepath = inspect.getsourcefile(mod)
			
			if not filepath:
				# for example: readline
				self.bell()
				print('Could not inspect:', target, '\nimport and use help()')
				return 'break'
			
			try:
				with open(filepath, 'r', encoding='utf-8') as f:
					fcontents = f.read()
					self.new_tab()
					
					# just in case:
					if '.py' in filepath:
						indentation_is_alien, indent_depth = self.check_indent_depth(fcontents)
						
						if indentation_is_alien:
							# Assuming user wants self.ind_depth, change it without notice:
							tmp = fcontents.splitlines(True)
							tmp[:] = [self.tabify(line, width=indent_depth) for line in tmp]
							tmp = ''.join(tmp)
							self.tabs[self.tabindex].contents = tmp
							
						else:
							self.tabs[self.tabindex].contents = fcontents
					else:
						self.tabs[self.tabindex].contents = fcontents
				
					
					self.tabs[self.tabindex].position = '1.0'
					self.contents.focus_set()
					self.contents.see('1.0')
					self.contents.mark_set('insert', '1.0')
					self.contents.insert(tkinter.INSERT, self.tabs[self.tabindex].contents)
					
					if self.syntax:
						self.token_err = True
						self.update_tokens(start='1.0', end=tkinter.END)
						self.token_can_update = True
						
					else:
						self.token_can_update = False
						
						
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
				
				self.new_tab()
				
				# just in case:
				indentation_is_alien, indent_depth = self.check_indent_depth(t)
				
				if indentation_is_alien:
					# Assuming user wants self.ind_depth, change it without notice:
					tmp = t.splitlines(True)
					tmp[:] = [self.tabify(line, width=indent_depth) for line in tmp]
					tmp = ''.join(tmp)
					self.tabs[self.tabindex].contents = tmp
					
				else:
					self.tabs[self.tabindex].contents = t
				
				
				self.tabs[self.tabindex].position = '1.0'
				self.contents.focus_set()
				self.contents.see('1.0')
				self.contents.mark_set('insert', '1.0')
				self.contents.insert(tkinter.INSERT, self.tabs[self.tabindex].contents)
				
				if self.syntax:
					self.token_err = True
					self.update_tokens(start='1.0', end=tkinter.END)
					self.token_can_update = True
					
				else:
					self.token_can_update = False
				
											
				self.contents.edit_reset()
				self.contents.edit_modified(0)
				
				return 'break'
			
			# from .rindex()
			except ValueError:
				self.bell()
				return 'break'
				
			except Exception as e:
				self.bell()
				print(e.__str__())
				return 'break'
		
		return 'break'
	
	
	def tabify_lines(self, event=None):
	
		try:
			startline = self.contents.index(tkinter.SEL_FIRST).split(sep='.')[0]
			endline = self.contents.index(tkinter.SEL_LAST).split(sep='.')[0]
			
			start = '%s.0' % startline
			end = '%s.0 lineend' % endline
			tmp = self.contents.get(start, end)
			
			indentation_is_alien, indent_depth = self.check_indent_depth(tmp)
			
			tmp = tmp.splitlines()
			
			if indentation_is_alien:
				# Assuming user wants self.ind_depth, change it without notice:
				tmp[:] = [self.tabify(line, width=indent_depth) for line in tmp]
							
			else:
				tmp[:] = [self.tabify(line) for line in tmp]
			
						
			tmp = ''.join(tmp)
			
			self.contents.delete(start, end)
			self.contents.insert(start, tmp)
			
			
			self.update_tokens(start=start, end=end)
						
															
			self.contents.edit_separator()
			return "break"
		
		except tkinter.TclError as e:
			#print(e)
			return "break"
	
	
	def tabify(self, line, width=None):
		
		if width:
			ind_width = width
		else:
			ind_width = self.ind_depth
			
		indent_stop_index = 0
		
		for char in line:
			if char in [' ', '\t']: indent_stop_index += 1
			else: break
			
		if indent_stop_index == 0:
			# remove trailing space
			if not line.isspace():
				line = line.rstrip() + '\n'
				
			return line
		
		
		indent_string = line[:indent_stop_index]
		line = line[indent_stop_index:]
		
		# remove trailing space
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
	
	

########## Utilities End
########## Save and Load Begin

	
	def trace_filename(self, *args):
		
		# canceled
		if self.tracevar_filename.get() == '':
			self.entry.delete(0, tkinter.END)
			
			if self.tabs[self.tabindex].filepath != None:
				self.entry.insert(0, self.tabs[self.tabindex].filepath)
				
		else:
			# update self.lastdir
			filename = pathlib.Path().cwd() / self.tracevar_filename.get()
			self.lastdir = pathlib.Path(*filename.parts[:-1])
		
			self.loadfile(filename)
		
		
		self.tracevar_filename.trace_remove('write', self.tracefunc_name)
		self.tracefunc_name = None
		self.contents.bind( "<Alt-Return>", lambda event: self.btn_open.invoke())
		
		self.state = 'normal'
		
	
		for widget in [self.entry, self.btn_open, self.btn_save, self.contents]:
			widget.config(state='normal')
		
		return 'break'
		
			
	def loadfile(self, filepath):
		''' filepath is tkinter.pathlib.Path
		'''

		filename = filepath
		openfiles = [tab.filepath for tab in self.tabs]
		
		for widget in [self.entry, self.btn_open, self.btn_save, self.contents]:
			widget.config(state='normal')
		
		
		if filename in openfiles:
			print(f'file: {filename} is already open')
			self.bell()
			self.entry.delete(0, tkinter.END)
			
			if self.tabs[self.tabindex].filepath != None:
				self.entry.insert(0, self.tabs[self.tabindex].filepath)
			
			return
		
		if self.tabs[self.tabindex].type == 'normal':
			self.save(activetab=True)
		
		# Using same tab:
		try:
			with open(filename, 'r', encoding='utf-8') as f:
				tmp = f.read()
				self.tabs[self.tabindex].oldcontents = tmp
				
				if '.py' in filename.suffix:
					indentation_is_alien, indent_depth = self.check_indent_depth(tmp)
					
					if indentation_is_alien:
						# Assuming user wants self.ind_depth, change it without notice:
						tmp = self.tabs[self.tabindex].oldcontents.splitlines(True)
						tmp[:] = [self.tabify(line, width=indent_depth) for line in tmp]
						tmp = ''.join(tmp)
						self.tabs[self.tabindex].contents = tmp
						
					else:
						self.tabs[self.tabindex].contents = self.tabs[self.tabindex].oldcontents
				else:
					self.tabs[self.tabindex].contents = self.tabs[self.tabindex].oldcontents
				
			
				
				self.entry.delete(0, tkinter.END)
				self.tabs[self.tabindex].filepath = filename
				self.tabs[self.tabindex].type = 'normal'
				self.tabs[self.tabindex].position = '1.0'
				self.entry.insert(0, filename)
				
				
				self.contents.delete('1.0', tkinter.END)
				self.contents.insert(tkinter.INSERT, self.tabs[self.tabindex].contents)
				
				
				self.do_syntax(everything=True)
				
				
				self.contents.focus_set()
				self.contents.see('1.0')
				self.contents.mark_set('insert', '1.0')
				
				self.contents.edit_reset()
				self.contents.edit_modified(0)
				self.avoid_viewsync_mess()
				
		except (EnvironmentError, UnicodeDecodeError) as e:
			print(e.__str__())
			print(f'\n Could not open file: {filename}')
			self.entry.delete(0, tkinter.END)
			
			if self.tabs[self.tabindex].filepath != None:
				self.entry.insert(0, self.tabs[self.tabindex].filepath)
				
		return
		
	
	def load(self, event=None):
		'''	Get just the filename,
			on success, pass it to loadfile()
		'''
		
		if self.state != 'normal':
			self.bell()
			return 'break'
		
		
		# Pressed Open-button
		if event == None:
		
			self.state = 'filedialog'
			self.contents.bind( "<Alt-Return>", self.do_nothing)
			
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
			
			fd = fdialog.FDialog(filetop, p, self.tracevar_filename, self.font, self.menufont)
			
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

					
	def save(self, activetab=False, forced=False):
		''' forced when run() or quit_me()
			activetab=True from load() and del_tab()
		'''
		
		if forced:
			
			# Dont want contents to be replaced with errorlines or help.
			if self.state != 'normal':
				self.contents.event_generate('<Escape>')
			
			# update active tab first
			try:
				pos = self.contents.index(tkinter.INSERT)
			except tkinter.TclError:
				pos = '1.0'
				
			tmp = self.contents.get('1.0', tkinter.END)
	
			self.tabs[self.tabindex].position = pos
			self.tabs[self.tabindex].contents = tmp
			
			
			# Then save tabs to disk
			for tab in self.tabs:
				if tab.type == 'normal':
					
					# Check indent (tabify) and rstrip:
					tmp = tab.contents.splitlines(True)
					tmp[:] = [self.tabify(line) for line in tmp]
					tmp = ''.join(tmp)
					
					if tab.active == True:
						tmp = tmp[:-1]
					
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
				else:
					tab.position = '1.0'
					
			return

		# if not forced (Pressed Save-button):

		tmp = self.entry.get().strip()
		
		if not isinstance(tmp, str) or tmp.isspace():
			print('Give a valid filename')
			self.bell()
			return
		
		fpath_in_entry = pathlib.Path().cwd() / tmp
		
		try:
			pos = self.contents.index(tkinter.INSERT)
		except tkinter.TclError:
			pos = '1.0'
					
		tmp = self.contents.get('1.0', tkinter.END)
		
		self.tabs[self.tabindex].position = pos
		self.tabs[self.tabindex].contents = tmp

		openfiles = [tab.filepath for tab in self.tabs]
		
		
		# creating new file
		if fpath_in_entry != self.tabs[self.tabindex].filepath and not activetab:
		
			if fpath_in_entry in openfiles:
				self.bell()
				print(f'\nFile: {fpath_in_entry} already opened')
				self.entry.delete(0, tkinter.END)
			
				if self.tabs[self.tabindex].filepath != None:
					self.entry.insert(0, self.tabs[self.tabindex].filepath)
				return
				
			if fpath_in_entry.exists():
				self.bell()
				print(f'\nCan not overwrite file: {fpath_in_entry}')
				self.entry.delete(0, tkinter.END)
			
				if self.tabs[self.tabindex].filepath != None:
					self.entry.insert(0, self.tabs[self.tabindex].filepath)
				return
			
			if self.tabs[self.tabindex].type == 'newtab':
			
				# avoiding disk-writes, just checking filepath:
				try:
					with open(fpath_in_entry, 'w', encoding='utf-8') as f:
						self.tabs[self.tabindex].filepath = fpath_in_entry
						self.tabs[self.tabindex].type = 'normal'
				except EnvironmentError as e:
					print(e.__str__())
					print('\n Could not save file: {fpath_in_entry}')
					return
				
				if self.tabs[self.tabindex].filepath != None:
					self.entry.delete(0, tkinter.END)
					self.entry.insert(0, self.tabs[self.tabindex].filepath)
					
					
					self.do_syntax()
			
				
				# set cursor pos
				try:
					line = self.tabs[self.tabindex].position
					self.contents.focus_set()
					self.contents.mark_set('insert', line)
					self.ensure_idx_visibility(line)
					
				except tkinter.TclError:
					self.tabs[self.tabindex].position = '1.0'
				
				self.contents.edit_reset()
				self.contents.edit_modified(0)
				
					
				
			# want to create new file with same contents:
			else:
				try:
					with open(fpath_in_entry, 'w', encoding='utf-8') as f:
						pass
				except EnvironmentError as e:
					print(e.__str__())
					print(f'\n Could not save file: {fpath_in_entry}')
					self.entry.delete(0, tkinter.END)
			
					if self.tabs[self.tabindex].filepath != None:
						self.entry.insert(0, self.tabs[self.tabindex].filepath)
					return
					
				self.new_tab()
				self.tabs[self.tabindex].filepath = fpath_in_entry
				self.tabs[self.tabindex].contents = tmp
				self.tabs[self.tabindex].position = pos
				self.tabs[self.tabindex].type = 'normal'
				
				self.entry.delete(0, tkinter.END)
				self.entry.insert(0, self.tabs[self.tabindex].filepath)
				
			
				self.contents.insert(tkinter.INSERT, self.tabs[self.tabindex].contents)
		
				
				self.do_syntax(everything=True)
				
				
				# set cursor pos
				try:
					line = self.tabs[self.tabindex].position
					self.contents.focus_set()
					self.contents.mark_set('insert', line)
					self.ensure_idx_visibility(line)
					
				except tkinter.TclError:
					self.tabs[self.tabindex].position = '1.0'
				
				
				self.contents.edit_reset()
				self.contents.edit_modified(0)
				
				
		else:
			# skip unnecessary disk-writing silently
			if not activetab:
				return

			# if closing tab or loading file:
		
			# Check indent (tabify) and rstrip:
			tmp = self.tabs[self.tabindex].contents.splitlines(True)
			tmp[:] = [self.tabify(line) for line in tmp]
			tmp = ''.join(tmp)[:-1]
			
			if self.tabs[self.tabindex].contents == self.tabs[self.tabindex].oldcontents:
				return
				
			try:
				with open(self.tabs[self.tabindex].filepath, 'w', encoding='utf-8') as f:
					f.write(tmp)
					
			except EnvironmentError as e:
				print(e.__str__())
				print(f'\n Could not save file: {self.tabs[self.tabindex].filepath}')
				return
				
		############# Save End #######################################
	
########## Save and Load End
########## Gotoline and Help Begin

	def do_gotoline(self, event=None):
		try:
			tmp = self.entry.get().strip()
	
			if tmp in ['-1', '']:
				line = tkinter.END
			else:
				line = tmp + '.0'
			
			self.contents.focus_set()
			self.contents.mark_set('insert', line)
			self.ensure_idx_visibility(line)
			
			
			try:
				pos = self.contents.index(tkinter.INSERT)
			except tkinter.TclError:
				pos = '1.0'
		
			self.tabs[self.tabindex].position = pos
			self.stop_gotoline()
		
		except tkinter.TclError as e:
			print(e)
			self.stop_gotoline()
	
	
	def stop_gotoline(self, event=None):
		self.bind("<Escape>", self.do_nothing)
		self.entry.bind("<Return>", self.load)
		self.entry.delete(0, tkinter.END)
		if self.tabs[self.tabindex].filepath:
			self.entry.insert(0, self.tabs[self.tabindex].filepath)
		self.update_title()
		
		# set cursor pos
		try:
			line = self.tabs[self.tabindex].position
			self.contents.focus_set()
			self.contents.mark_set('insert', line)
			self.ensure_idx_visibility(line)
			
		except tkinter.TclError:
			self.tabs[self.tabindex].position = '1.0'
		
	
	def gotoline(self, event=None):
		if self.state != 'normal':
			self.bell()
			return "break"
			
		try:
			pos = self.contents.index(tkinter.INSERT)
		except tkinter.TclError:
			pos = '1.0'
		
		self.tabs[self.tabindex].position = pos
		
		# Remove extra line
		endline = int(self.contents.index(tkinter.END).split('.')[0]) - 1
		
		self.entry.bind("<Return>", self.do_gotoline)
		self.bind("<Escape>", self.stop_gotoline)
		self.title('Go to line, 1-%s:' % endline)
		self.entry.delete(0, tkinter.END)
		self.entry.focus_set()
		return "break"
	
	
	def stop_help(self, event=None):
		self.state = 'normal'
		
		self.entry.config(state='normal')
		self.contents.config(state='normal')
		self.btn_open.config(state='normal')
		self.btn_save.config(state='normal')
		
		if self.tabs[self.tabindex].filepath:
			self.entry.insert(0, self.tabs[self.tabindex].filepath)
		
		self.token_can_update = True
		self.contents.delete('1.0', tkinter.END)
		self.contents.insert(tkinter.INSERT, self.tabs[self.tabindex].contents)
		
		
		self.do_syntax(everything=True)
		
		
		# set cursor pos
		try:
			line = self.tabs[self.tabindex].position
			self.contents.focus_set()
			self.contents.mark_set('insert', line)
			self.ensure_idx_visibility(line)
			
		except tkinter.TclError:
			self.tabs[self.tabindex].position = '1.0'
		
			
		self.contents.edit_reset()
		self.contents.edit_modified(0)
		self.avoid_viewsync_mess()
		
		self.bind("<Escape>", self.do_nothing)
		self.bind("<Button-3>", lambda event: self.raise_popup(event))
		
		
	def help(self, event=None):
		if self.state != 'normal':
			self.bell()
			return "break"
			
		self.state = 'help'
		
		try:
			pos = self.contents.index(tkinter.INSERT)
		except tkinter.TclError:
			pos = '1.0'
		
		self.tabs[self.tabindex].position = pos
		tmp = self.contents.get('1.0', tkinter.END)
		# [:-1]: remove unwanted extra newline
		self.tabs[self.tabindex].contents = tmp[:-1]
		
		self.token_can_update = False
		
		self.entry.delete(0, tkinter.END)
		self.contents.delete('1.0', tkinter.END)
		self.contents.insert(tkinter.INSERT, self.helptxt)
		
		self.entry.config(state='disabled')
		self.contents.config(state='disabled')
		self.btn_open.config(state='disabled')
		self.btn_save.config(state='disabled')
		
		self.bind("<Button-3>", self.do_nothing)
		self.bind("<Escape>", self.stop_help)
			
########## Gotoline and Help End
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
								( indent <= 0 ),
								( not flag_space and indent > 1 )
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
	
	
	def indent(self, event=None):
		if self.state != 'normal':
			self.bell()
			
		try:
			startline = int(self.contents.index(tkinter.SEL_FIRST).split(sep='.')[0])
			endline = int(self.contents.index(tkinter.SEL_LAST).split(sep='.')[0])
			i = self.contents.index(tkinter.INSERT)
			
			start_idx = self.contents.index(tkinter.SEL_FIRST)
			end_idx = self.contents.index(tkinter.SEL_LAST)
					
			self.contents.tag_remove('sel', '1.0', tkinter.END)
			self.contents.tag_add('sel', start_idx, end_idx)
			
		
			if len(self.contents.tag_ranges('sel')) != 0:
					
				# is start of selection viewable?
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
			

	def unindent(self, event=None):
		if self.state != 'normal':
			self.bell()
			return "break"
			
		try:
			# unindenting curline only:
			if len(self.contents.tag_ranges('sel')) == 0:
				startline = int( self.contents.index(tkinter.INSERT).split(sep='.')[0] )
				endline = startline
	
			else:
				startline = int(self.contents.index(tkinter.SEL_FIRST).split(sep='.')[0])
				endline = int(self.contents.index(tkinter.SEL_LAST).split(sep='.')[0])
			
			i = self.contents.index(tkinter.INSERT)
			
			# Check there is enough space in every line:
			flag_continue = True
			
			for linenum in range(startline, endline+1):
				tmp = self.contents.get('%s.0' % linenum, '%s.0 lineend' % linenum)
				
				if len(tmp) != 0 and tmp[0] != '\t':
					flag_continue = False
					break
				
			if flag_continue:
				
				if len(self.contents.tag_ranges('sel')) != 0:
					
					# is start of selection viewable?
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
				
		
				# is selection made from down to top or from right to left?
				if len(self.contents.tag_ranges('sel')) != 0:
				
					if startline == endline:
						self.contents.mark_set(tkinter.INSERT, '%s -1c' %i)
					
					elif self.contents.compare(tkinter.SEL_FIRST, '<', tkinter.INSERT):
						self.contents.mark_set(tkinter.INSERT, tkinter.SEL_FIRST)
						
					# is start of selection viewable?
					if not self.contents.bbox(tkinter.SEL_FIRST):
						self.ensure_idx_visibility('insert', back=4)
					
				self.contents.edit_separator()
		
		except tkinter.TclError as e:
			pass
			
		return "break"
	
	
	def comment(self, event=None):
		if self.state != 'normal':
			self.bell()
			return "break"
			
		try:
			s = self.contents.index(tkinter.SEL_FIRST)
			e = self.contents.index(tkinter.SEL_LAST)
		
			startline = int( s.split('.')[0] )
			startpos = self.contents.index( '%s linestart' % s )
			
			endline = int( e.split('.')[0] )
			endpos = self.contents.index( '%s lineend' % e )
			
			
			for linenum in range(startline, endline+1):
				self.contents.mark_set(tkinter.INSERT, '%s.0' % linenum)
				self.contents.insert(tkinter.INSERT, '##')
				
						
			self.update_tokens(start=startpos, end=endpos)
			
				
			self.contents.edit_separator()
			return "break"
		
		except tkinter.TclError as e:
			print(e)
			return "break"
	

	def uncomment(self, event=None):
		''' Should work even if there are uncommented lines between commented lines. '''
		if self.state != 'normal':
			self.bell()
			return "break"
			
		try:
			s = self.contents.index(tkinter.SEL_FIRST)
			e = self.contents.index(tkinter.SEL_LAST)
		
			startline = int(s.split('.')[0])
			endline = int(e.split('.')[0])
			startpos = self.contents.index('%s linestart' % s)
			endpos = self.contents.index('%s lineend' % e)
				
			changed = False
			
			for linenum in range(startline, endline+1):
				self.contents.mark_set(tkinter.INSERT, '%s.0' % linenum)
				tmp = self.contents.get('%s.0' % linenum,'%s.0 lineend' % linenum)
				
				if tmp.lstrip()[:2] == '##':
					tmp = tmp.replace('##', '', 1)
					self.contents.delete('%s.0' % linenum,'%s.0 lineend' % linenum)
					self.contents.insert(tkinter.INSERT, tmp)
					changed = True
					
					
			if changed:
			
				self.update_tokens(start=startpos, end=endpos)
				
				self.contents.edit_separator()
			
		except tkinter.TclError as e:
			print(e)
		return "break"
		
########## Indent and Comment End
################ Search Begin
	
	def check_next_event(self, event=None):
		
		if event.keysym == 'Left':
			line = self.lastcursorpos
			self.contents.tag_remove('sel', '1.0', tkinter.END)
			self.contents.mark_set('insert', line)
			self.ensure_idx_visibility(line)
			
			
			self.contents.unbind("<Any-Key>", funcid=self.anykeyid)
			self.contents.unbind("<Any-Button>", funcid=self.anybutid)
		
			return 'break'
		else:
			self.contents.unbind("<Any-Key>", funcid=self.anykeyid)
			self.contents.unbind("<Any-Button>", funcid=self.anybutid)
			return
			
		
	def search_next(self, event=None):
		'''	Do last search from cursor position, show and select next match.
			
			This is for cases when you can not do replace ALL.
			You need to choose when to insert AND insertion is not always
			the same. But replace is too limited (can not insert, like in search).
			So you do normal search and quit quickly. Then copy your insertion
			'pattern' in clipboard, what you add to certain matches and then
			maybe change something else, or you need sometimes delete match and
			insert your clipboard 'pattern' etc...
			
			In short:
			1: Do normal search
			2: copy what you need to have in clipboard
			3: ctrl-backspace until in right place
			4: now easy to delete or add clipboard contents etc..
			5: repeat 3-4
			
			shortcut: ctrl-backspace
		'''
		
		if self.state != 'normal' or self.old_word == '':
			self.bell()
			return "break"
		
		wordlen = len(self.old_word)
		self.lastcursorpos = self.contents.index(tkinter.INSERT)
		pos = self.contents.search(self.old_word, 'insert +1c', tkinter.END)
		
		# Try again from the beginning this time:
		if not pos:
			pos = self.contents.search(self.old_word, '1.0', tkinter.END)
			
			# no oldword in file:
			if not pos:
				self.bell()
				#print('no')
				return "break"
		
		# go back to last place with arrow left
		self.anykeyid = self.contents.bind( "<Any-Key>", self.check_next_event)
		self.anybutid = self.contents.bind( "<Any-Button>", self.check_next_event)
		
		lastpos = "%s + %dc" % (pos, wordlen)
		self.contents.tag_remove('sel', '1.0', tkinter.END)
		self.contents.tag_add('sel', pos, lastpos)
		self.contents.mark_set('insert', lastpos)
		line = pos
		self.ensure_idx_visibility(line)
		
					
		return "break"


	def show_next(self, event=None):
		if self.state not in [ 'search', 'replace', 'replace_all' ]:
			return
			
		match_ranges = self.contents.tag_ranges('match')
		
		# check if at last match or beyond:
		i = len(match_ranges) - 2
		last = match_ranges[i]
	
		if self.contents.compare(self.search_idx[0], '>=', last):
			self.search_idx = ('1.0', '1.0')
				
		if self.search_idx != ('1.0', '1.0'):
			self.contents.tag_remove('focus', self.search_idx[0], self.search_idx[1])
		else:
			self.contents.tag_remove('focus', '1.0', tkinter.END)
		
		
		self.search_idx = self.contents.tag_nextrange('match', self.search_idx[1])
		line = self.search_idx[0]
		
		# is it viewable?
		if not self.contents.bbox(line):
			self.wait_for(100)
		
		self.ensure_idx_visibility(line)
		
		
		# change color
		self.contents.tag_add('focus', self.search_idx[0], self.search_idx[1])
		
		# compare found to match
		ref = self.contents.tag_ranges('focus')[0]
		
		for idx in range(self.search_matches):
			tmp = match_ranges[idx*2]
			if self.contents.compare(ref, '==', tmp): break
		
		
		if self.state == 'replace':
			self.title( f'Replace: {idx+1}/{self.search_matches}' )
		else:
			self.title( f'Search: {idx+1}/{self.search_matches}' )
		
		
		if self.search_matches == 1:
			self.bind("<Control-n>", self.do_nothing)
			self.bind("<Control-p>", self.do_nothing)
		
		return 'break'
		

	def show_prev(self, event=None):
		
		if self.state not in [ 'search', 'replace', 'replace_all' ]:
			return
		
		match_ranges = self.contents.tag_ranges('match')
		
		first = match_ranges[0]
	
		if self.contents.compare(self.search_idx[0], '<=', first):
			self.search_idx = (tkinter.END, tkinter.END)
		
		if self.search_idx != (tkinter.END, tkinter.END):
			self.contents.tag_remove('focus', self.search_idx[0], self.search_idx[1])
		else:
			self.contents.tag_remove('focus', '1.0', tkinter.END)
		
		self.search_idx = self.contents.tag_prevrange('match', self.search_idx[0])
		
		line = self.search_idx[0]
		# is it viewable?
		if not self.contents.bbox(line):
			self.wait_for(100)
		
		self.ensure_idx_visibility(line)
		
		# change color
		self.contents.tag_add('focus', self.search_idx[0], self.search_idx[1])
		
		# compare found to match
		ref = self.contents.tag_ranges('focus')[0]
		
		for idx in range(self.search_matches):
			tmp = match_ranges[idx*2]
			if self.contents.compare(ref, '==', tmp): break
			
		
		if self.state == 'replace':
			self.title( f'Replace: {idx+1}/{self.search_matches}' )
		else:
			self.title( f'Search: {idx+1}/{self.search_matches}' )
		
		
		if self.search_matches == 1:
			self.bind("<Control-n>", self.do_nothing)
			self.bind("<Control-p>", self.do_nothing)
			
		return 'break'
		
		
	def start_search(self, event=None):
		self.old_word = self.entry.get()
		self.contents.tag_remove('match', '1.0', tkinter.END)
		self.contents.tag_remove('focus', '1.0', tkinter.END)
		self.search_idx = ('1.0', '1.0')
		self.search_matches = 0
		
		if len(self.old_word) != 0:
			pos = '1.0'
			wordlen = len(self.old_word)
			flag_start = True
			
			while True:
				pos = self.contents.search(self.old_word, pos, tkinter.END)
				if not pos: break
				self.search_matches += 1
				lastpos = "%s + %dc" % (pos, wordlen)
				self.contents.tag_add('match', pos, lastpos)
				if flag_start:
					flag_start = False
					self.contents.focus_set()
					self.wait_for(100)
					self.show_next()
				pos = "%s + %dc" % (pos, wordlen+1)
				
		if self.search_matches > 0:
			self.bind("<Button-3>", self.do_nothing)
			
			if self.state == 'search':
				self.title('Found: %s matches' % str(self.search_matches))
				self.bind("<Control-n>", self.show_next)
				self.bind("<Control-p>", self.show_prev)
			
			else:
				self.title('Replace %s matches with:' % str(self.search_matches))
				self.entry.bind("<Return>", self.start_replace)
				self.entry.focus_set()
		else:
			self.bell()
				
		return 'break'
		
		
	def update_curpos(self, event=None):
		self.save_pos = self.contents.index(tkinter.INSERT)
		
		# This is needed to enable replacing with Return.
		# Because of binding to self in start_replace().
		# And when pressing contents with mouse, self.contents gets focus,
		# so put it back to self.
		self.focus_set()
		
		return "break"
			
			
	def clear_search_tags(self, event=None):
		if self.state != 'normal':
			return "break"
			
		self.contents.tag_remove('replaced', '1.0', tkinter.END)
		self.bind("<Escape>", self.do_nothing)
		
	
	def stop_search(self, event=None):
		self.contents.config(state='normal')
		self.entry.config(state='normal')
		self.btn_open.config(state='normal')
		self.btn_save.config(state='normal')
		self.replace_overlap_index = None
		self.bind("<Button-3>", lambda event: self.raise_popup(event))
		
		#self.wait_for(200)
		self.contents.tag_remove('focus', '1.0', tkinter.END)
		self.contents.tag_remove('match', '1.0', tkinter.END)
			
		# Leave marks on replaced areas, Esc clears.
		if len(self.contents.tag_ranges('replaced')) > 0:
			self.bind("<Escape>", self.clear_search_tags)
		else:
			self.bind("<Escape>", self.do_nothing)
			
		
		self.entry.bind("<Return>", self.load)
		self.entry.delete(0, tkinter.END)
	
		if self.tabs[self.tabindex].filepath:
			self.entry.insert(0, self.tabs[self.tabindex].filepath)
	
		self.new_word = ''
		self.search_matches = 0
		self.update_title()
		flag_all = False
		if self.state == 'replace_all': flag_all = True
		
		if self.state in [ 'replace_all', 'replace' ]:
			
				self.state = 'normal'
				
				self.do_syntax()
				
				
		self.state = 'normal'
		self.bind( "<Return>", self.do_nothing)
		self.contents.unbind( "<Control-n>", funcid=self.bid1 )
		self.contents.unbind( "<Control-p>", funcid=self.bid2 )
		self.contents.unbind( "<ButtonRelease-1>", funcid=self.bid3 )
		
		#self.wait_for(200)
		
		# set cursor pos
		try:
			if self.save_pos:
				line = self.save_pos
				self.tabs[self.tabindex].position = line
				self.save_pos = None
			else:
				line = self.tabs[self.tabindex].position
			
			self.contents.focus_set()
			self.contents.mark_set('insert', line)
	
			if not flag_all:
				self.ensure_idx_visibility(line)
			
		except tkinter.TclError:
			self.tabs[self.tabindex].position = self.contents.index(tkinter.INSERT)
			
	
	def search(self, event=None):
		if self.state != 'normal':
			self.bell()
			return "break"
		
		# save cursor pos
		try:
			self.tabs[self.tabindex].position = self.contents.index(tkinter.INSERT)
		
		except tkinter.TclError:
			pass
			
		self.state = 'search'
		self.btn_open.config(state='disabled')
		self.btn_save.config(state='disabled')
		self.entry.bind("<Return>", self.start_search)
		self.bind("<Escape>", self.stop_search)
		
		self.bid1 = self.contents.bind("<Control-n>", func=self.skip_bindlevel )
		self.bid2 = self.contents.bind("<Control-p>", func=self.skip_bindlevel )
		self.bid3 = self.contents.bind("<ButtonRelease-1>", func=self.update_curpos, add=True )
		
		self.title('Search:')
		self.entry.delete(0, tkinter.END)
		
		# autofill from clipboard
		try:
			tmp = self.clipboard_get()
			if 80 > len(tmp) > 0:
				self.entry.insert(tkinter.END, tmp)
				self.entry.select_to(tkinter.END)
				self.entry.icursor(tkinter.END)
				
		# empty clipboard
		except tkinter.TclError:
			pass
			
		self.contents.config(state='disabled')
		self.entry.focus_set()
		return "break"
			

################ Search End
################ Replace Begin

	def replace(self, event=None, state='replace'):
		if self.state != 'normal':
			self.bell()
			return "break"
		
		# save cursor pos
		try:
			self.tabs[self.tabindex].position = self.contents.index(tkinter.INSERT)
		
		except tkinter.TclError:
			pass
		
		self.state = state
		self.btn_open.config(state='disabled')
		self.btn_save.config(state='disabled')
		self.entry.bind("<Return>", self.start_search)
		self.bind("<Escape>", self.stop_search)
		self.bid1 = self.contents.bind("<Control-n>", func=self.skip_bindlevel )
		self.bid2 = self.contents.bind("<Control-p>", func=self.skip_bindlevel )
		self.bid3 = self.contents.bind("<ButtonRelease-1>", func=self.update_curpos, add=True )
		
		self.title('Replace this:')
		self.entry.delete(0, tkinter.END)
		
		# autofill from clipboard
		try:
			tmp = self.clipboard_get()
			if 80 > len(tmp) > 0:
				self.entry.insert(tkinter.END, tmp)
				self.entry.select_to(tkinter.END)
				self.entry.icursor(tkinter.END)
	
		except tkinter.TclError:
			pass
			
		
		self.contents.config(state='disabled')
		self.entry.focus_set()
		return "break"


	def replace_all(self, event=None):
		if self.state != 'normal':
			self.bell()
			return "break"
			
		self.replace(event, state='replace_all')
		
		
	def do_single_replace(self, event=None):
	
		
		# Apply normal 'Replace and proceed to next by pressing Return' -behaviour
		c = self.contents.tag_nextrange('focus', 1.0)
		
		if not len(c) > 0:
			self.show_next()
			return 'break'
			
		
		# Start of actual replacing
		self.contents.config(state='normal')
		self.search_matches = 0
		
		if self.replace_overlap_index != None:
			
			if self.replace_overlap_index == 0:
				range_func = self.contents.tag_nextrange
			
			else:
				range_func = self.contents.tag_prevrange
		else:
			range_func = self.contents.tag_prevrange
			
		wordlen = len(self.old_word)
		wordlen2 = len(self.new_word)
		pos = '1.0'
		self.contents.tag_remove('match', '1.0', tkinter.END)
		
		while True:
			pos = self.contents.search(self.old_word, pos, tkinter.END)
			if not pos: break
			
			if 'replaced' in self.contents.tag_names(pos):
				x = range_func('replaced', pos)
				if len(x) == 0:
					x = range_func('replaced', pos)
				# replaced already, skip
				pos = "%s + %dc" % ( x[1], wordlen2+1 )
				
			else:
				lastpos = "%s + %dc" % (pos, wordlen)
				self.contents.tag_add('match', pos, lastpos)
				pos = "%s + %dc" % (pos, wordlen+1)
				self.search_matches += 1
			
			
		self.contents.tag_remove('focus', self.search_idx[0], self.search_idx[1])
		self.contents.tag_remove('match', self.search_idx[0], self.search_idx[1])
		self.contents.delete(self.search_idx[0], self.search_idx[1])
		self.contents.insert(self.search_idx[0], self.new_word)
		
		# tag replacement to avoid rematching same place
		p = "%s + %dc" % (self.search_idx[0], wordlen2)
		self.contents.tag_add('replaced', self.search_idx[0], p)
		
		
		self.contents.config(state='disabled')
		
		self.search_matches -= 1
		
		if self.search_matches == 0:
			self.wait_for(100)
			self.stop_search()

	
	def do_replace_all(self, event=None):
		
		self.contents.config(state='normal')
		wordlen = len(self.old_word)
		wordlen2 = len(self.new_word)
		pos = '1.0'
		
		while True:
			pos = self.contents.search(self.old_word, pos, tkinter.END)
			if not pos: break
			
			lastpos = "%s + %dc" % ( pos, wordlen )
			lastpos2 = "%s + %dc" % ( pos, wordlen2 )
			
			self.contents.delete( pos, lastpos )
			self.contents.insert( pos, self.new_word )
			self.contents.tag_add( 'replaced', pos, lastpos2 )
				
			pos = "%s + %dc" % (pos, wordlen+1)
			
		# show lastpos but dont put cursor on it
		line = lastpos
		self.wait_for(100)
		self.ensure_idx_visibility(line)


		self.stop_search()
		
		
	def start_replace(self, event=None):
		self.new_word = self.entry.get()
		
		if self.old_word == self.new_word:
			return
		else:
			self.bind("<Control-n>", self.show_next)
			self.bind("<Control-p>", self.show_prev)
			
			# prevent focus messing
			self.entry.bind("<Return>", self.do_nothing)
			self.entry.config(state='disabled')
			self.focus_set()
			
			self.contents.tag_remove('replaced', '1.0', tkinter.END)
	
			
			if self.state == 'replace':
			
				self.replace_overlap_index = None
				
				if self.old_word in self.new_word:
					self.replace_overlap_index = self.new_word.index(self.old_word)
				
				self.title( f'Replace: 1/{self.search_matches}' )
				self.bind( "<Return>", self.do_single_replace)
				
			elif self.state == 'replace_all':
				self.bind( "<Return>", self.do_replace_all)
				self.title('Replacing ALL %s matches of %s with: %s' % (str(self.search_matches), self.old_word, self.new_word) )


################ Replace End
########### Class Editor End

