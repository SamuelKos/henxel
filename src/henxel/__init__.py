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
# Theme Related
# Run file Related
# Overrides
# Save and Load
# Gotoline and Help
# Indent and Comment
# Search
# Replace
#
# Class Editor End

############ Stucture briefing End
############ TODO Begin

############ TODO End
############ Imports Begin

# from standard library
import tkinter.scrolledtext
import tkinter.filedialog
import tkinter.font
import tkinter
import pathlib
import json

import importlib.resources
import sys

# from current directory
from . import changefont

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

TAB_WIDTH = 4
TAB_WIDTH_CHAR = ' '
SLIDER_MINSIZE = 66

# This is list because order matters, best ones at the start etc..
GOODFONTS = [
			'Noto Mono',
			'Bitstream Vera Sans Mono',
			'Liberation Mono',
			'DejaVu Sans Mono',
			'Inconsolata',
			'Courier 10 Pitch'
			]
		
BADFONTS = frozenset([
					'Standard Symbols PS',
					'OpenSymbol',
					'Noto Color Emoji',
					'FontAwesome',
					'Dingbats',
					'Droid Sans Fallback',
					'D050000L'
					])
					
			
############ Constants End
			
class Editor(tkinter.Toplevel):


	def __init__(self):
		self.root = tkinter.Tk().withdraw()
		super().__init__(self.root, class_='Henxel', bd=4)
		self.protocol("WM_DELETE_WINDOW", self.quit_me)
		
		self.to_be_closed = list()
		self.quitting = False
		
		self.ln_string = ''
		self.oldconf = None
		
		if sys.prefix != sys.base_prefix:
			self.env = sys.prefix
		else:
			self.env = None
		
		self.tabs = list()
		self.tabindex = None
		self.branch = None
		
		# get current git-branch
		try:
			self.branch = subprocess.run('git branch --show-current'.split(),
					check=True, capture_output=True).stdout.decode().strip()
		except Exception as e:
			pass
		
		self.replace_overlap_index = None
		self.search_idx = ('1.0', '1.0')
		self.search_matches = 0
		self.search_pos = 0
		self.old_word = ''
		self.new_word = ''
		self.errlines = list()
		self.lastdir = None
		self.state = 'normal'
		
		self.font = tkinter.font.Font(family='TkDefaulFont', size=12)
		self.menufont = tkinter.font.Font(family='TkDefaulFont', size=10)
		
		# IMPORTANT if binding to 'root':
		# https://stackoverflow.com/questions/54185434/python-tkinter-override-default-ctrl-h-binding
		# https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/binding-levels.html
		# Still problems with this, so changed back to default bindtags.
		# If you can, avoid binding to root.
		
		self.bind( "<Escape>", self.do_nothing )
		self.bind( "<Control-minus>", self.decrease_scrollbar_width)
		self.bind( "<Control-plus>", self.increase_scrollbar_width)
		self.bind( "<Control-R>", self.replace_all)
		self.bind( "<Button-3>", self.raise_popup)
		self.bind( "<Control-g>", self.gotoline)
		self.bind( "<Control-r>", self.replace)
		self.bind( "<Control-p>", self.font_choose)
		self.bind( "<Control-s>", self.color_choose)
		self.bind( "<Alt-t>", self.toggle_color)
		self.bind( "<Alt-w>", self.walk_files)
		self.bind( "<Alt-q>", lambda event: self.walk_files(event, **{'back':True}) )
		
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
			
		
		# Layout Begin:
		####################################################
		self.rowconfigure(1, weight=1)
		self.columnconfigure(1, weight=1)
		
		self.btn_git=tkinter.Button(self)
		self.btn_git.grid(row=0, column = 0, sticky='nsew')
		
		if self.branch:
			self.btn_git.config(font=self.menufont, relief='flat', highlightthickness=0, padx=0, text=self.branch[:5], state='disabled')
		else:
			self.btn_git.config(font=self.menufont, relief='flat', highlightthickness=0, padx=0, bitmap='info', state='disabled')
		
		
		self.entry = tkinter.Entry(self, bd=4, highlightthickness=0, bg='#d9d9d9')
		self.entry.bind("<Return>", self.load)
		self.entry.grid(row=0, column = 1, sticky='nsew')
		
		self.btn_open=tkinter.Button(self, text='Open', bd=4, highlightthickness=0, command=self.load)
		self.btn_save=tkinter.Button(self, text='Save', bd=4, highlightthickness=0, command=self.save)
		self.btn_open.grid(row=0, column = 2, sticky='nsew')
		self.btn_save.grid(row=0, column = 3, columnspan=2, sticky='nsew')
		
		self.ln_widget = tkinter.Text(self, width=4, padx=10, highlightthickness=0, bd=4, pady=4)
		self.ln_widget.grid(row=1, column = 0, sticky='nsw')
		self.ln_widget.tag_config('justright', justify=tkinter.RIGHT)
		
		# disable copying linenumbers:
		self.ln_widget.bind('<Control-c>', self.no_copy_ln)
		
		
		self.contents = tkinter.Text(self, blockcursor=True, undo=True, maxundo=-1, autoseparators=True,
					tabstyle='wordprocessor', highlightthickness=0, bd=4, pady=4, padx=10)
		
		self.scrollbar = tkinter.Scrollbar(self, orient=tkinter.VERTICAL, highlightthickness=0,
					bd=0, command = self.contents.yview)

		self.contents.grid(row=1, column=1, columnspan=3, sticky='nswe')
		self.scrollbar.grid(row=1,column=4, sticky='nse')
		
		
		# Needed in update_linenums(), there is more info.
		self.update_idletasks()
		# if self.y_extra_offset > 0, it needs attention
		self.y_extra_offset = self.contents['highlightthickness'] + self.contents['bd'] + self.contents['pady']
		# Needed in update_linenums() and sbset_override()
		self.bbox_height = self.contents.bbox('@0,0')[3]
		self.text_widget_height = self.scrollbar.winfo_height()
		
		
		self.contents['yscrollcommand'] = lambda *args: self.sbset_override(*args)
		
		self.contents.tag_config('match', background='lightyellow', foreground='black')
		self.contents.tag_config('found', background='lightgreen')
		
		self.contents.bind( "<Control-f>", self.search)
		self.contents.bind( "<Control-n>", self.new_tab)
		self.contents.bind( "<Return>", self.return_override)
		self.contents.bind( "<Control-d>", self.del_tab)
		self.contents.bind( "<Shift-Return>", self.comment)
		self.contents.bind( "<Shift-BackSpace>", self.uncomment)
		self.contents.bind( "<Tab>", self.tab_override)
		self.contents.bind( "<ISO_Left_Tab>", self.unindent)
		self.contents.bind( "<Control-a>", self.select_all)
		self.contents.bind( "<Control-z>", self.undo_override)
		self.contents.bind( "<Control-Z>", self.redo_override)
		self.contents.bind( "<Control-v>", self.paste)
		self.contents.bind( "<Control-BackSpace>", self.search_next)
	
		self.contents.bind( "<<WidgetViewSync>>", self.viewsync)

		
		# Needed in leave() taglink in: Run file Related
		self.name_of_cursor_in_text_widget = self.contents['cursor']
		
		self.popup_whohasfocus = None
		self.popup = tkinter.Menu(self, tearoff=0, bd=0, activeborderwidth=0)
		self.popup.bind("<FocusOut>", self.popup_focusOut) # to remove popup when clicked outside
		self.popup.add_command(label="        copy", command=self.copy)
		self.popup.add_command(label="       paste", command=self.paste)
		self.popup.add_command(label="##   comment", command=self.comment)
		self.popup.add_command(label="   uncomment", command=self.uncomment)
		self.popup.add_command(label="      errors", command=self.show_errors)
		self.popup.add_command(label="         run", command=self.run)
		self.popup.add_command(label="        help", command=self.help)
		
		
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
			
			# Hide selection in linenumbers
			self.ln_widget.config( selectbackground=self.bgcolor, selectforeground=self.fgcolor, inactiveselectbackground=self.bgcolor )
			
			
		# if no conf:
		if self.tabindex == None:
		
			self.tabindex = -1
			self.new_tab()
			
			self.bgdaycolor = r'#D3D7CF'
			self.fgdaycolor = r'#000000'
			self.bgnightcolor = r'#000000'
			self.fgnightcolor = r'#D3D7CF'
			self.fgcolor = self.fgdaycolor
			self.bgcolor = self.bgdaycolor
			self.curcolor = 'day'
			
			# Set Font Begin ##################################################
			fontname = None
						
			fontfamilies = [f for f in tkinter.font.families() if f not in BADFONTS]
			
##			for font in GOODFONTS:
##				if font in fontfamilies:
##					fontname = font
##					break
					
			if not fontname:
				fontname = 'TkDefaulFont'

			# Initialize rest of configurables
			self.font.config(family=fontname, size=12)
			self.menufont.config(family=fontname, size=10)
		
			self.scrollbar_width = 30
			self.elementborderwidth = 4
			
			self.scrollbar.config(width=self.scrollbar_width)
			self.scrollbar.config(elementborderwidth=self.elementborderwidth)
			
			self.tab_width = self.font.measure(TAB_WIDTH * TAB_WIDTH_CHAR)
			self.contents.config(font=self.font, foreground=self.fgcolor,
				background=self.bgcolor, insertbackground=self.fgcolor,
				tabs=(self.tab_width, ))
				
			self.entry.config(font=self.menufont)
			self.btn_open.config(font=self.menufont)
			self.btn_save.config(font=self.menufont)
			self.popup.config(font=self.menufont)
			
			self.btn_git.config(font=self.menufont)
			
			self.ln_widget.config(font=self.font, foreground=self.fgcolor, background=self.bgcolor, selectbackground=self.bgcolor, selectforeground=self.fgcolor, inactiveselectbackground=self.bgcolor, state='disabled')

		
		self.update_title()
		
		############################# init End ######################
		

	def viewsync(self, event=None):
		'''	Triggered when event is <<WidgetViewSync>>
		
			This event itself is generated when inserting, deleting or on screen geometry change, but
			not when just scrolling (like yview). Almost all font-changes also generates this event,
			so that is good to know because I yet have not seen that TkWorldChange -event.
		'''
		
		# More info in update_linenums()
		self.bbox_height = self.contents.bbox('@0,0')[3]
		self.text_widget_height = self.scrollbar.winfo_height()
		
		self.update_linenums()


	def update_title(self, event=None):
		tail = len(self.tabs) - self.tabindex - 1
		self.title( f'Henxel {"0"*self.tabindex}@{"0"*(tail)}' )
		
		
	def do_nothing(self, event=None):
		self.bell()
		return 'break'
		
	
	def quit_me(self):
		# affects load():
		self.quitting = True
		
		self.save(forced=True)
		self.save_config()
		self.clipboard_clear()
		
		
		# affects color and fontchoose:
		for widget in self.to_be_closed:
			widget.destroy()
		
		self.quit()
		self.destroy()
		
		
############## Linenumbers Begin

	def no_copy_ln(self, event=None):
		# This is curiosity, return 'break' does the thing
		self.ln_widget.selection_clear()
		
		return 'break'
		
		
	def get_linenums(self):

		x = 0
		line = '0'
		col= ''
		ln = ''

		# line-height is used as step, it depends on font:
		step = self.bbox_height

		nl = '\n'
		lineMask = '    %s\n'
		
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
				
		# remove unwanted newline:
		return ln[:-1]

	
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
			return
	
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
			
		newtab = Tab(active=True, filepath=None, contents='', oldcontents='', position='1.0', type='newtab')
		
		self.tabindex += 1
		self.tabs.insert(self.tabindex, newtab)
		
		self.contents.focus_set()
		self.contents.see('1.0')
		self.contents.mark_set('insert', '1.0')
		
		self.contents.edit_reset()
		self.contents.edit_modified(0)
		
		self.update_title()
		return 'break'
		
		
	def del_tab(self, event=None):

		if ((len(self.tabs) == 1) and self.tabs[self.tabindex].type == 'newtab') or (self.state != 'normal'):
			self.bell()
			return 'break'

		if self.tabs[self.tabindex].type == 'normal':
			self.save(deltab=True)
			
		self.tabs.pop(self.tabindex)
		self.contents.delete('1.0', tkinter.END)
		self.entry.delete(0, tkinter.END)
			
		if (len(self.tabs) == 0):
			newtab = Tab(active=True, filepath=None, contents='', oldcontents='', position='1.0', type='newtab')
			self.tabs.append(newtab)
	
		if self.tabindex > 0:
			self.tabindex -= 1
	
		self.tabs[self.tabindex].active = True

		self.contents.insert(tkinter.INSERT, self.tabs[self.tabindex].contents)
		if self.tabs[self.tabindex].filepath:
			self.entry.insert(0, self.tabs[self.tabindex].filepath)

		try:
			line = self.tabs[self.tabindex].position
			self.contents.focus_set()
			self.contents.mark_set('insert', line)
			# ensure we see something before and after
			self.contents.see('%s - 2 lines' % line)
			self.update_idletasks()
			self.contents.see('%s + 2 lines' % line)
			
		except tkinter.TclError:
			self.tabs[self.tabindex].position = '1.0'
			self.contents.focus_set()
			self.contents.see('1.0')
			self.contents.mark_set('insert', '1.0')
			
		self.contents.edit_reset()
		self.contents.edit_modified(0)
		
		self.update_title()
		
		return 'break'

		
	def walk_files(self, event=None, back=False):
	
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

		self.contents.delete('1.0', tkinter.END)
		self.contents.insert(tkinter.INSERT, self.tabs[self.tabindex].contents)
		self.entry.delete(0, tkinter.END)
		
		if self.tabs[self.tabindex].filepath:
			self.entry.insert(0, self.tabs[self.tabindex].filepath)
		
		try:
			line = self.tabs[self.tabindex].position
			self.contents.focus_set()
			self.contents.mark_set('insert', line)
			# ensure we see something before and after
			self.contents.see('%s - 2 lines' % line)
			self.update_idletasks()
			self.contents.see('%s + 2 lines' % line)
			
		except tkinter.TclError:
			self.tabs[self.tabindex].position = '1.0'
			self.contents.focus_set()
			self.contents.see('1.0')
			self.contents.mark_set('insert', '1.0')
			
		
		self.contents.edit_reset()
		self.contents.edit_modified(0)
		
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
		self.apply_config()
		
	
	def fonts_exists(self, dictionary):
		
		res = True
		fontfamilies = [f for f in tkinter.font.families() if f not in BADFONTS]
		
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
		
		dictionary['fgcolor'] = self.contents.cget('foreground')
		dictionary['bgcolor'] = self.contents.cget('background')
		dictionary['fgdaycolor'] = self.fgdaycolor
		dictionary['bgdaycolor'] = self.bgdaycolor
		dictionary['fgnightcolor'] = self.fgnightcolor
		dictionary['bgnightcolor'] = self.bgnightcolor
		dictionary['curcolor'] = self.curcolor
		dictionary['lastdir'] = self.lastdir.__str__()
		
		dictionary['font'] = self.font.config()
		dictionary['menufont'] = self.menufont.config()
		dictionary['scrollbar_width'] = self.scrollbar_width
		dictionary['elementborderwidth'] = self.elementborderwidth
		
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
		self.fgnightcolor = dictionary['fgnightcolor']
		self.bgnightcolor = dictionary['bgnightcolor']
		self.fgdaycolor = dictionary['fgdaycolor']
		self.bgdaycolor = dictionary['bgdaycolor']
		self.fgcolor = dictionary['fgcolor']
		self.bgcolor = dictionary['bgcolor']
		self.curcolor = dictionary['curcolor']
		
		# Set Font Begin ##################################################
		if not fonts_exists:
			fontname = None
			
			fontfamilies = [f for f in tkinter.font.families() if f not in BADFONTS]
			
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
						tab.contents = f.read()
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
		
		
		if self.tabindex == None:
			if len(self.tabs) == 0:
				self.tabindex = -1
				self.new_tab()
			# recently active normal tab is gone:
			else:
				self.tabindex = 0
				self.tabs[self.tabindex].active = True
		

	def apply_config(self):
	
		self.tab_width = self.font.measure(TAB_WIDTH * TAB_WIDTH_CHAR)
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
		
		try:
			line = self.tabs[self.tabindex].position
			self.contents.focus_set()
			# ensure we see something before and after
			self.contents.see('%s - 2 lines' % line)
			self.update_idletasks()
			self.contents.see('%s + 2 lines' % line)
			self.contents.mark_set('insert', line)
		except tkinter.TclError:
			self.tabs[self.tabindex].position = '1.0'
			self.contents.focus_set()
			self.contents.see('1.0')
			self.contents.mark_set('insert', '1.0')
		
########## Configuration Related End
########## Theme Related Begin

	def increase_scrollbar_width(self, event=None):
		'''	Change width of scrollbar of self.contents and of
			tkinter.filedialog.FileDialog which is used in self.load().
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
		'''	Change width of scrollbar of self.contents and of
			tkinter.filedialog.FileDialog which is used in self.load().
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
		if self.curcolor == 'day':
			self.fgcolor = self.fgnightcolor
			self.bgcolor = self.bgnightcolor
		else:
			self.fgcolor = self.fgdaycolor
			self.bgcolor = self.bgdaycolor
			
		if self.curcolor == 'day':
			self.curcolor = 'night'
		else:
			self.curcolor = 'day'
			
		self.contents.config(foreground=self.fgcolor, background=self.bgcolor,
			insertbackground=self.fgcolor)
			
		self.ln_widget.config(foreground=self.fgcolor, background=self.bgcolor, selectbackground=self.bgcolor, selectforeground=self.fgcolor, inactiveselectbackground=self.bgcolor )
		
		return 'break'
		
			
	def font_choose(self, event=None):
		if self.state != 'normal':
			self.bell()
			return "break"
			
		choose = changefont.FontChooser([self.font, self.menufont])
		self.to_be_closed.append(choose)
		
		return 'break'
		
			
	def color_choose(self, event=None):
		if self.state != 'normal':
			self.bell()
			return "break"
			
		# I am not sure why this works but it is possibly related
		# to fact that there can only be one root window,
		# or actually one Tcl-interpreter in single python-program or -console.
		colortop = tkinter.Toplevel()
		colortop.title('Choose Color')
		colortop.btnfg = tkinter.Button(colortop, text='Text color', font=('TkDefaultFont', 16),
				command = lambda args=['fg']: self.chcolor(args) )
				
		colortop.btnfg.pack(padx=10, pady=10)
		
		colortop.btnbg = tkinter.Button(colortop, text='Ref. color', font=('TkDefaultFont', 16),
				command = lambda args=['bg']: self.chcolor(args) )
				
		colortop.btnbg.pack(padx=10, pady=10)
		
		colortop.lb = tkinter.Listbox(colortop, font=('TkDefaultFont', 12), selectmode=tkinter.SINGLE)
		colortop.lb.pack(pady=10)
		colortop.choiseslist = ['day', 'night']
		
		for item in colortop.choiseslist:
			colortop.lb.insert('end', item)
		
		idx = colortop.choiseslist.index(self.curcolor)
		colortop.lb.select_set(idx)
		colortop.lb.see(idx)
		colortop.lb.bind('<ButtonRelease-1>', lambda event, args=[colortop]: self.choose_daynight(args, event))
		
		self.to_be_closed.append(colortop)
		
		
		
	def choose_daynight(self, args, event=None):
		parent = args[0]
		oldcolor = self.curcolor
		self.curcolor = parent.lb.get(parent.lb.curselection())
		
		if self.curcolor != oldcolor:
		
			if self.curcolor == 'day':
			
				self.fgcolor = self.fgdaycolor
				self.bgcolor = self.bgdaycolor
			
			else:
				self.fgcolor = self.fgnightcolor
				self.bgcolor = self.bgnightcolor
			
			self.contents.config(foreground=self.fgcolor, background=self.bgcolor,
			insertbackground=self.fgcolor)
			
			self.ln_widget.config(foreground=self.fgcolor, background=self.bgcolor, selectbackground=self.bgcolor, selectforeground=self.fgcolor, inactiveselectbackground=self.bgcolor )
			
			
	def chcolor(self, args, event=None):
	

		if args[0] == 'bg':
			
			res = self.tk.call('tk_chooseColor')
			tmpcolorbg = str(res)
			
			if tmpcolorbg in [None, '']:
				return 'break'
			
			if self.curcolor == 'day':
				self.bgdaycolor = tmpcolorbg
				self.bgcolor = self.bgdaycolor
			else:
				self.bgnightcolor = tmpcolorbg
				self.bgcolor = self.bgnightcolor
		else:
				
			res = self.tk.call('tk_chooseColor')
			tmpcolorfg = str(res)
			
			if tmpcolorfg in [None, '']:
				return 'break'
			
			if self.curcolor == 'day':
				self.fgdaycolor = tmpcolorfg
				self.fgcolor = self.fgdaycolor
			else:
				self.fgnightcolor = tmpcolorfg
				self.fgcolor = self.fgnightcolor
		
		try:
			self.contents.config(foreground=self.fgcolor, background=self.bgcolor,
				insertbackground=self.fgcolor)
				
			self.ln_widget.config(foreground=self.fgcolor, background=self.bgcolor, selectbackground=self.bgcolor, selectforeground=self.fgcolor, inactiveselectbackground=self.bgcolor )
		
		except tkinter.TclError as e:
			# because if closed editor, this survives
			pass
			
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
		
		if filepath == self.tabs[self.tabindex].filepath:
			pass
			
		elif filepath in openfiles:
			for i,tab in enumerate(self.tabs):
				if tab.filepath == filepath:
					self.tabs[self.tabindex].active = False
					self.tabindex = i
					self.tabs[self.tabindex].active = True
					break
		else:
			try:
				with open(filepath, 'r', encoding='utf-8') as f:
					self.new_tab(error=True)
					fcontents = f.read()
					self.tabs[self.tabindex].contents = fcontents
					self.tabs[self.tabindex].filepath = filepath
					self.tabs[self.tabindex].oldcontents = self.tabs[self.tabindex].contents
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
		self.contents.edit_reset()
		self.contents.edit_modified(0)
		self.contents.focus_set()
		
		line = errline + '.0'
		# ensure we see something before and after
		self.contents.see('%s - 2 lines' % line)
		self.update_idletasks()
		self.contents.see('%s + 2 lines' % line)
		self.contents.mark_set('insert', line)
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
			return
			
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
				
				# parse filepath and linenums from errors
				if 'File ' in line and 'line ' in line:
					data = line.split(',')[:2]
					linenum = data[1][6:]
					filepath = data[0][8:-1]
					filepath = pathlib.Path(filepath)
					
					if filepath in openfiles:
						self.contents.tag_config(tagname, foreground='brown1')
					
					self.errlines.append((filepath, linenum))
					self.contents.insert(tkinter.INSERT, tmp +"\n", tagname)
				else:
					self.contents.insert(tkinter.INSERT, tmp +"\n")
				

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
			
			i = 0
			for line in self.err:
				tmp = line
				
				# parse filepath and linenums from errors
				if 'File ' in line and 'line ' in line:
					data = line.split(',')[:2]
					linenum = data[1][6:]
					filepath = data[0][8:-1]
					self.errlines.append((filepath, linenum))
					self.contents.insert(tkinter.INSERT, tmp +"\n", 'hyper-%d' % i)
					i += 1
				else:
					self.contents.insert(tkinter.INSERT, tmp +"\n")

									
	def stop_show_errors(self, event=None):
		self.state = 'normal'
		self.bind("<Escape>", self.do_nothing)
		self.bind("<Button-3>", lambda event: self.raise_popup(event))
		
		self.contents.delete('1.0', tkinter.END)
		self.contents.insert(tkinter.INSERT, self.tabs[self.tabindex].contents)
		self.entry.delete(0, tkinter.END)
		
		if self.tabs[self.tabindex].type == 'normal':
			self.entry.insert(0, self.tabs[self.tabindex].filepath)
			
		self.contents.edit_reset()
		self.contents.edit_modified(0)
		self.contents.focus_set()

		# ensure we see something before and after
		pos = self.tabs[self.tabindex].position
		self.contents.see('%s - 2 lines' % pos)
		self.update_idletasks()
		self.contents.see('%s + 2 lines' % pos)
		self.contents.mark_set('insert', pos)
		
########## Run file Related End
########## Overrides Begin

	def raise_popup(self, event=None):
		self.popup_whohasfocus = event.widget
		self.popup.post(event.x_root, event.y_root)
		self.popup.focus_set() # Needed to remove popup when clicked outside.
		
		
	def popup_focusOut(self, event=None):
		self.popup.unpost()
	

	def copy(self):
		''' When copy is selected from popup-menu
		'''
		self.clipboard_clear()
		self.clipboard_append(self.selection_get())
		
		
	def paste(self, event=None):
		'''	Keeping original behaviour, in which indentation is preserved
			but first line usually is in wrong place after paste
			because of selection has not started at the beginning of the line.
			So we put cursor at the beginning of insertion after pasting it
			so we can start indenting it. This problem can be avoided by
			starting copying of a block at the empty line before first line of
			the block.
		'''
		try:
			tmp = self.clipboard_get()
			wordlen = len(tmp)
			tmp = tmp.splitlines(True)
		except tkinter.TclError:
			# is empty
			return 'break'
		
		if len(tmp) > 1:
			pos = self.contents.index(tkinter.INSERT)
			self.contents.event_generate('<<Paste>>')
			
			lastpos = "%s + %dc" % (pos, wordlen)
			self.contents.tag_remove('sel', '1.0', tkinter.END)
			self.contents.tag_add('sel', pos, lastpos)
			
			self.contents.mark_set('insert', pos)
		
			self.contents.see('%s - 2 lines' % pos)
			self.update_idletasks()
			self.contents.see('%s + 2 lines' % pos)
			
			return 'break'
			
		else:
			if event == None:
				self.popup_whohasfocus.event_generate('<<Paste>>')
				return 'break'
			else:
				return


	def undo_override(self, event=None):
		if self.state != 'normal':
			self.bell()
			return "break"
		 
		try:
			self.contents.edit_undo()
			
		except tkinter.TclError:
			self.bell()
			
		return 'break'
		
		
	def redo_override(self, event=None):
		if self.state != 'normal':
			self.bell()
			return "break"
			
		try:
			self.contents.edit_redo()
		except tkinter.TclError:
			self.bell()
			
		return 'break'
		
		
	def select_all(self, event):
		self.contents.tag_remove('sel', '1.0', tkinter.END)
		self.contents.tag_add('sel', 1.0, tkinter.END)
		return "break"
	
	
	def tab_override(self, event):
		'''	Used to bind Tab-key with indent()
		'''
		
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
			# No selection, continue to next bindtag
			return


	def return_override(self, event):
	
		# Cursor indexes when pressed return:
		line, row = map(int, self.contents.index(tkinter.INSERT).split('.'))
		# is same as:
		# line = int(self.contents.index(tkinter.INSERT).split('.')[0])
		# row = int(self.contents.index(tkinter.INSERT).split('.')[1])
		
		# First an easy case:
		if row == 0:
			self.contents.insert(tkinter.INSERT, '\n')
			self.contents.see(f'{line+1}.0')
			self.contents.edit_separator()
			return "break"
				
		tmp = self.contents.get('%s.0' % str(line),'%s.0 lineend' % str(line))
		
		# Then one special case: check if cursor is inside indentation,
		# and line is not empty.
		
		if tmp[:row].isspace() and not tmp[row:].isspace():
			self.contents.insert(tkinter.INSERT, '\n')
			self.contents.insert('%s.0' % str(line+1), tmp[:row])
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
		''' Fix for: not being able to config slider min-size
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
########## Save and Load Begin

	def tabify(self, line):
		
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
			if count == TAB_WIDTH:
				indent_string = indent_string.replace(TAB_WIDTH * ' ', '\t', True)
				count = 0
		
		tabified_line = ''.join([indent_string, line])
		return tabified_line
	
	
	def load(self, event=None):

		if self.state != 'normal':
			self.bell()
			return
		
		##################### Get filename begin
		
		# Pressed Open-button
		if event == None:
			self.d = tkinter.filedialog.FileDialog(self, title='Select File')
			
			self.d.dirs.configure(font=self.font, width=30, selectmode='single')
			self.d.files.configure(font=self.font, width=30, selectmode='single')
			self.d.cancel_button.configure(font=self.menufont)
			self.d.filter.configure(font=self.menufont)
			self.d.filter_button.configure(font=self.menufont)
			self.d.ok_button.configure(font=self.menufont)
			self.d.selection.configure(font=self.menufont)

			self.d.dirsbar.configure(width=self.scrollbar_width)
			self.d.filesbar.configure(width=self.scrollbar_width)
			self.d.filesbar.configure(elementborderwidth=self.elementborderwidth)
			self.d.dirsbar.configure(elementborderwidth=self.elementborderwidth)
			
			
			# tmp is now absolute path
			if self.lastdir:
				tmp = self.d.go(self.lastdir.__str__())
			else:
				tmp = self.d.go('.')
				
			# Otherwise this (blocking, for reason) callback
			# would try to continue after deletion of the filedialog:
			if self.quitting:
				return

			# avoid bell when dialog is closed without selection
			if tmp == None:
				self.entry.delete(0, tkinter.END)
				if self.tabs[self.tabindex].filepath != None:
					self.entry.insert(0, self.tabs[self.tabindex].filepath)
				return
			
			else:
				# update self.lastdir
				 dirp = pathlib.Path().cwd() / tmp
				 self.lastdir = pathlib.Path(*dirp.parts[:-1])
			
			
		# Entered filename to be opened in entry:
		else:
			tmp = self.entry.get().strip()

		if not isinstance(tmp, str) or tmp.isspace():
			self.bell()
			return
		
		filename = pathlib.Path().cwd() / tmp
		
		###################################### Get filename end
		
		
		openfiles = [tab.filepath for tab in self.tabs]
		
		if filename in openfiles:
			print(f'file: {filename} is already open')
			self.bell()
			self.entry.delete(0, tkinter.END)
			
			if self.tabs[self.tabindex].filepath != None:
				self.entry.insert(0, self.tabs[self.tabindex].filepath)
			return
		
		if self.tabs[self.tabindex].type == 'normal':
			# keyword argument deltab should be renamed
			self.save(deltab=True)
		
		# Using same tab:
		try:
			with open(filename, 'r', encoding='utf-8') as f:
				fcontents = f.read()
				self.tabs[self.tabindex].contents = fcontents
				self.tabs[self.tabindex].oldcontents = self.tabs[self.tabindex].contents
				self.contents.delete('1.0', tkinter.END)
				self.entry.delete(0, tkinter.END)
				self.tabs[self.tabindex].filepath = filename
				self.tabs[self.tabindex].type = 'normal'
				self.tabs[self.tabindex].position = '1.0'
				
				self.contents.insert(tkinter.INSERT, self.tabs[self.tabindex].contents)
				self.contents.focus_set()
				self.contents.see('1.0')
				self.contents.mark_set('insert', '1.0')
				self.entry.insert(0, filename)
				self.contents.edit_reset()
				self.contents.edit_modified(0)
		except (EnvironmentError, UnicodeDecodeError) as e:
			print(e.__str__())
			print(f'\n Could not open file: {filename}')
			self.entry.delete(0, tkinter.END)
			
			if self.tabs[self.tabindex].filepath != None:
				self.entry.insert(0, self.tabs[self.tabindex].filepath)
			

	def save(self, deltab=False, forced=False):
		''' forced when run() or quit_me()
			deltab==True from load() and del_tab()
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
				
			tmp = self.contents.get('1.0', tkinter.END).splitlines(True)
	
			# Check indent (tabify):
			tmp[:] = [self.tabify(line) for line in tmp]
			tmp = ''.join(tmp)[:-1]
			
			self.tabs[self.tabindex].position = pos
			self.tabs[self.tabindex].contents = tmp
			
			# then save tabs to disk
			for tab in self.tabs:
				if tab.type == 'normal':
				
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
					
		tmp = self.contents.get('1.0', tkinter.END).splitlines(True)
		
		# Check indent (tabify):
		tmp[:] = [self.tabify(line) for line in tmp]
		tmp = ''.join(tmp)[:-1]
		
		self.tabs[self.tabindex].position = pos
		self.tabs[self.tabindex].contents = tmp

		openfiles = [tab.filepath for tab in self.tabs]
		
		# creating new file
		if fpath_in_entry != self.tabs[self.tabindex].filepath and not deltab:
		
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
				self.contents.edit_reset()
				self.contents.edit_modified(0)
				
				try:
					line = self.tabs[self.tabindex].position
					self.contents.focus_set()
					# ensure we see something before and after
					self.contents.see('%s - 2 lines' % line)
					self.update_idletasks()
					self.contents.see('%s + 2 lines' % line)
					self.contents.mark_set('insert', line)
				except tkinter.TclError:
					self.tabs[self.tabindex].position = '1.0'
				
		else:
			# skip unnecessary disk-writing silently
			if not deltab:
				return

			# if closing tab or loading file:
			
			if self.tabs[self.tabindex].contents == self.tabs[self.tabindex].oldcontents:
				return
				
			try:
				with open(self.tabs[self.tabindex].filepath, 'w', encoding='utf-8') as f:
					f.write(tmp)
					
			except EnvironmentError as e:
				print(e.__str__())
				print(f'\n Could not save file: {self.tabs[self.tabindex].filepath}')
				return
	
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
			# ensure we see something before and after
			self.contents.see('%s - 2 lines' % line)
			self.update_idletasks()
			self.contents.see('%s + 2 lines' % line)
			self.contents.mark_set('insert', line)
			
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
		
		try:
			line = self.tabs[self.tabindex].position
			self.contents.focus_set()
			# ensure we see something before and after
			self.contents.see('%s - 2 lines' % line)
			self.update_idletasks()
			self.contents.see('%s + 2 lines' % line)
			self.contents.mark_set('insert', line)
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
		
		self.contents.delete('1.0', tkinter.END)
		self.contents.insert(tkinter.INSERT, self.tabs[self.tabindex].contents)
		self.contents.edit_reset()
		self.contents.edit_modified(0)
		
		if self.tabs[self.tabindex].filepath:
			self.entry.insert(0, self.tabs[self.tabindex].filepath)
		try:
			line = self.tabs[self.tabindex].position
			self.contents.focus_set()
			# ensure we see something before and after
			self.contents.see('%s - 2 lines' % line)
			self.update_idletasks()
			self.contents.see('%s + 2 lines' % line)
			self.contents.mark_set('insert', line)
		except tkinter.TclError:
			self.tabs[self.tabindex].position = '1.0'
		
		self.bind("<Escape>", self.do_nothing)
		self.bind("<Button-3>", lambda event: self.raise_popup(event))
		
		
	def help(self, event=None):
		self.state = 'help'
		
		try:
			pos = self.contents.index(tkinter.INSERT)
		except tkinter.TclError:
			pos = '1.0'
		
		self.tabs[self.tabindex].position = pos
		tmp = self.contents.get('1.0', tkinter.END)
		# [:-1]: remove unwanted extra newline
		self.tabs[self.tabindex].contents = tmp[:-1]
			
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

	def indent(self, event=None):
		if self.state != 'normal':
			self.bell()
			
		try:
			startline = int(self.contents.index(tkinter.SEL_FIRST).split(sep='.')[0])
			endline = int(self.contents.index(tkinter.SEL_LAST).split(sep='.')[0])
			for linenum in range(startline, endline+1):
				self.contents.mark_set(tkinter.INSERT, '%s.0' % linenum)
				self.contents.insert(tkinter.INSERT, '\t')
			
			self.contents.mark_set(tkinter.INSERT, tkinter.SEL_FIRST)
			self.contents.edit_separator()
			
		except tkinter.TclError:
			pass
			

	def unindent(self, event=None):
		if self.state != 'normal':
			self.bell()
			return "break"
			
		try:
			startline = int(self.contents.index(tkinter.SEL_FIRST).split(sep='.')[0])
			endline = int(self.contents.index(tkinter.SEL_LAST).split(sep='.')[0])
			# Check there is enough space in every line:
			flag_continue = True
			
			for linenum in range(startline, endline+1):
				tmp = self.contents.get('%s.0' % linenum, '%s.0 lineend' % linenum)
				
				if len(tmp) != 0 and tmp[0] != '\t':
					flag_continue = False
					break
				
			if flag_continue:
				for linenum in range(startline, endline+1):
					tmp = self.contents.get('%s.0' % linenum, '%s.0 lineend' % linenum)
				
					if len(tmp) != 0:
						self.contents.mark_set(tkinter.INSERT, '%s.0' % linenum)
						self.contents.delete(tkinter.INSERT, '%s+%dc' % (tkinter.INSERT, 1))
						
				self.contents.mark_set(tkinter.INSERT, tkinter.SEL_FIRST)
				self.contents.edit_separator()
		
		except tkinter.TclError as e:
			pass
			
		return "break"

	
	def comment(self, event=None):
		if self.state != 'normal':
			self.bell()
			return "break"
			
		try:
			startline = int(self.contents.index(tkinter.SEL_FIRST).split(sep='.')[0])
			endline = int(self.contents.index(tkinter.SEL_LAST).split(sep='.')[0])
			
			for linenum in range(startline, endline+1):
				self.contents.mark_set(tkinter.INSERT, '%s.0' % linenum)
				self.contents.insert(tkinter.INSERT, '##')
			
			self.contents.edit_separator()
			return "break"
		
		except tkinter.TclError as e:
			print(e)
			return "break"
	

	def uncomment(self, event=None):
		'''should work even if there are uncommented lines between commented lines'''
		if self.state != 'normal':
			self.bell()
			return "break"
			
		try:
			startline = int(self.contents.index(tkinter.SEL_FIRST).split(sep='.')[0])
			endline = int(self.contents.index(tkinter.SEL_LAST).split(sep='.')[0])
			changed = False
			
			for linenum in range(startline, endline+1):
				self.contents.mark_set(tkinter.INSERT, '%s.0' % linenum)
				tmp = self.contents.get('%s.0' % linenum,'%s.0 lineend' % linenum)
				
				if tmp.lstrip()[:2] == '##':
					tmp = tmp.replace('##', '', 1)
					self.contents.delete('%s.0' % linenum,'%s.0 lineend' % linenum)
					self.contents.insert(tkinter.INSERT, tmp)
					changed = True
					
			if changed: self.contents.edit_separator()
			
		except tkinter.TclError as e:
			print(e)
		return "break"
		
########## Indent and Comment End
################ Search Begin

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
		pos = self.contents.search(self.old_word, tkinter.INSERT, tkinter.END)
		
		# Try again from the beginning this time:
		if not pos:
			pos = self.contents.search(self.old_word, '1.0', tkinter.END)
			
			# no oldword in file:
			if not pos:
				self.bell()
				return "break"
		
		lastpos = "%s + %dc" % (pos, wordlen)
		self.contents.tag_remove('sel', '1.0', tkinter.END)
		self.contents.tag_add('sel', pos, lastpos)
		self.contents.mark_set('insert', lastpos)
		
		self.contents.see('%s - 2 lines' % pos)
		self.update_idletasks()
		self.contents.see('%s + 2 lines' % pos)
		
		return "break"


	def show_next(self, event=None):
		if self.state not in [ 'search', 'replace', 'replace_all' ]:
			return
			
		self.contents.config(state='normal')
		
		# check if at last match or beyond:
		i = len(self.contents.tag_ranges('match')) - 2
		last = self.contents.tag_ranges('match')[i]
	
		if self.contents.compare(self.search_idx[0], '>=', last):
			self.search_idx = ('1.0', '1.0')
			self.search_pos = 0
				
		self.contents.tag_remove('found', '1.0', tkinter.END)
		self.search_idx = self.contents.tag_nextrange('match', self.search_idx[1])
		# change color
		self.contents.tag_add('found', self.search_idx[0], self.search_idx[1])
		
		# ensure we see something before and after
		self.contents.see('%s - 2 lines' % self.search_idx[0])
		self.update_idletasks()
		self.contents.see('%s + 2 lines' % self.search_idx[0])

		self.search_pos += 1
		
		# compare found to match
		num_matches = int(len(self.contents.tag_ranges('match'))/2)
		ref = self.contents.tag_ranges('found')[0]
		
		for c in range(num_matches):
			tmp = self.contents.tag_ranges('match')[c*2]
			if self.contents.compare(ref, '==', tmp): break
		
		self.title('Search: %s/%s' % (str(c+1), str(self.search_matches)))
		
		if self.search_matches == 1:
			self.bind("<Alt-n>", self.do_nothing)
			self.bind("<Alt-p>", self.do_nothing)
		
		self.contents.config(state='disabled')


	def show_prev(self, event=None):
		
		if self.state not in [ 'search', 'replace', 'replace_all' ]:
			return
		
		self.contents.config(state='normal')
		first = self.contents.tag_ranges('match')[0]
	
		if self.contents.compare(self.search_idx[0], '<=', first):
			self.search_idx = (tkinter.END, tkinter.END)
			self.search_pos = self.search_matches + 1

			
		self.contents.tag_remove('found', '1.0', tkinter.END)
		
		self.search_idx = self.contents.tag_prevrange('match', self.search_idx[0])
		
		# change color
		self.contents.tag_add('found', self.search_idx[0], self.search_idx[1])
		
		# ensure we see something before and after
		self.contents.see('%s - 2 lines' % self.search_idx[0])
		self.update_idletasks()
		self.contents.see('%s + 2 lines' % self.search_idx[0])
		
		self.search_pos -= 1
		
		# compare found to match
		num_matches = int(len(self.contents.tag_ranges('match'))/2)
		ref = self.contents.tag_ranges('found')[0]
		
		for c in range(num_matches):
			tmp = self.contents.tag_ranges('match')[c*2]
			if self.contents.compare(ref, '==', tmp): break
			
		self.title('Search: %s/%s' % (str(c+1), str(self.search_matches)))
		
		if self.search_matches == 1:
			self.bind("<Alt-n>", self.do_nothing)
			self.bind("<Alt-p>", self.do_nothing)
		
		self.contents.config(state='disabled')
			
		
	def start_search(self, event=None):
		self.old_word = self.entry.get()
		self.contents.tag_remove('match', '1.0', tkinter.END)
		self.contents.tag_remove('found', '1.0', tkinter.END)
		self.search_idx = ('1.0', '1.0')
		self.search_matches = 0
		self.search_pos = 0
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
					self.show_next()
				pos = "%s + %dc" % (pos, wordlen+1)
				
		if self.search_matches > 0:
			self.contents.config(state='disabled')
			self.bind("<Button-3>", self.do_nothing)
			
			if self.state == 'search':
				self.title('Found: %s matches' % str(self.search_matches))
				self.bind("<Alt-n>", self.show_next)
				self.bind("<Alt-p>", self.show_prev)
			else:
				self.bind("<Alt-n>", self.do_nothing)
				self.bind("<Alt-p>", self.do_nothing)

				self.title('Replace %s matches with:' % str(self.search_matches))
				self.entry.bind("<Return>", self.start_replace)
				self.entry.focus_set()
		else:
			self.bell()
				
				
	def stop_search(self, event=None):
		self.contents.config(state='normal')
		self.entry.config(state='normal')
		self.btn_open.config(state='normal')
		self.btn_save.config(state='normal')
		self.bind("<Button-3>", lambda event: self.raise_popup(event))
		self.contents.tag_remove('match', '1.0', tkinter.END)
		self.contents.tag_remove('found', '1.0', tkinter.END)
		self.bind("<Escape>", self.do_nothing)
		self.entry.bind("<Return>", self.load)
		self.entry.delete(0, tkinter.END)
	
		if self.tabs[self.tabindex].filepath:
			self.entry.insert(0, self.tabs[self.tabindex].filepath)
	
		self.new_word = ''
		self.search_matches = 0
		self.replace_overlap_index = None
		self.update_title()
		self.state = 'normal'
		self.contents.focus_set()


	def search(self, event=None):
		if self.state != 'normal':
			self.bell()
			return "break"
			
		self.state = 'search'
		self.btn_open.config(state='disabled')
		self.btn_save.config(state='disabled')
		self.entry.bind("<Return>", self.start_search)
		self.bind("<Escape>", self.stop_search)
		self.title('Search:')
		self.entry.delete(0, tkinter.END)
		
		# autofill from clipboard
		try:
			tmp = self.contents.clipboard_get()
			if 80 > len(tmp) > 0:
				self.entry.insert(tkinter.END, tmp)
				self.entry.select_to(tkinter.END)
				self.entry.icursor(tkinter.END)
				
		# empty clipboard
		except tkinter.TclError:
			pass
			
		self.entry.focus_set()
		return "break"
			

################ Search End
################ Replace Begin

	def replace(self, event=None, state='replace'):
		if self.state != 'normal':
			self.bell()
			return "break"
			
		self.state = state
		self.btn_open.config(state='disabled')
		self.btn_save.config(state='disabled')
		self.entry.bind("<Return>", self.start_search)
		self.bind("<Escape>", self.stop_search)
		self.title('Replace this:')
		self.entry.delete(0, tkinter.END)
		
		# autofill from clipboard
		try:
			tmp = self.contents.clipboard_get()
			if 80 > len(tmp) > 0:
				self.entry.insert(tkinter.END, tmp)
				self.entry.select_to(tkinter.END)
				self.entry.icursor(tkinter.END)
	
		except tkinter.TclError:
			pass
				
		self.entry.focus_set()
		return "break"


	def replace_all(self, event=None):
		if self.state != 'normal':
			self.bell()
			return "break"
			
		self.replace(event, state='replace_all')
		
		
	def do_single_replace(self, event=None):
		self.contents.config(state='normal')
		self.entry.config(state='disabled')
		self.search_matches = 0
		wordlen = len(self.old_word)
		wordlen2 = len(self.new_word)
		pos = '1.0'
		self.contents.tag_remove('match', '1.0', tkinter.END)
		
		# Next while-loop tags matches again, this is the main reason why
		# there is a problem if new_word contains old_word:it will be rematched.
		# This is why when there is a match, we move
		# replace_overlap_index characters back and check if there already is
		# new_word. If so, it means there have already happened a replacement
		# and therefore search pos must be recalculated over this manifestation
		# of new_word.
		 
		while True:
			pos = self.contents.search(self.old_word, pos, tkinter.END)
			if not pos: break
			
			if self.replace_overlap_index != None:
				# find the startpos (pos2) and lastpos of new_word:
				tmp = int(pos.split('.')[1]) - self.replace_overlap_index
				pos2 = pos.split('.')[0] +'.'+ str(tmp)
				lastpos = "%s + %dc" % (pos2, wordlen2)
				
				if self.contents.get(pos2, lastpos) == self.new_word:
					# skip this match
					pos = "%s + %dc" % (pos2, wordlen2+1)
				else:
					lastpos = "%s + %dc" % (pos, wordlen)
					self.contents.tag_add('match', pos, lastpos)
					pos = "%s + %dc" % (pos, wordlen+1)
					self.search_matches += 1
			else:
				lastpos = "%s + %dc" % (pos, wordlen)
				self.contents.tag_add('match', pos, lastpos)
				pos = "%s + %dc" % (pos, wordlen+1)
				self.search_matches += 1

		self.contents.tag_remove('found', self.search_idx[0], self.search_idx[1])
		self.contents.tag_remove('match', self.search_idx[0], self.search_idx[1])
		self.contents.delete(self.search_idx[0], self.search_idx[1])
		self.contents.insert(self.search_idx[0], self.new_word)
		self.contents.config(state='disabled')
		
		self.search_matches -= 1
		
		if self.search_matches == 0:
			self.stop_search()

	
	def do_replace_all(self, event=None):
		count = self.search_matches
		
		for i in range(count):
			self.do_single_replace()
			if i < (count - 1): self.show_next()
				
		
	def start_replace(self, event=None):
		self.new_word = self.entry.get()
		
		if self.old_word == self.new_word:
			return
		else:
		
			self.replace_overlap_index = None
			self.bind("<Alt-n>", self.show_next)
			self.bind("<Alt-p>", self.show_prev)
			
			# Check if new_word contains old_word, if so:
			# record its overlap-index, which we need in do_single_replace()
			# (explanation for why this is needed is given there)
			if self.old_word in self.new_word:
				self.replace_overlap_index = self.new_word.index(self.old_word)
				
			if self.state == 'replace':
				self.entry.bind("<Return>", self.do_single_replace)
				self.title('Replacing %s matches of %s with: %s' % (str(self.search_matches), self.old_word, self.new_word) )
			elif self.state == 'replace_all':
				self.entry.bind("<Return>", self.do_replace_all)
				self.title('Replacing ALL %s matches of %s with: %s' % (str(self.search_matches), self.old_word, self.new_word) )


################ Replace End
########### Class Editor End

