from dataclasses import dataclass, field
from typing import Any, List
import tkinter.font
import tkinter
import copy

defaults = dict()


# configparser? no?

##Q: what is here?
##A: Colors, Fonts, Class Tab, UI-stuff, Other-stuff,
##
##Q: what one wants to do with them?
##A: handle conf
##
##Q: what next?
##A: copy Color stuff to color dataclass








########## Old stuff Begin #################################################
############################################################################

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


def get_font(want_list):
	fontname = None

	fontfamilies = [f for f in tkinter.font.families()]

	for font in want_list:
		if font in fontfamilies:
			fontname = font
			break

	if not fontname: fontname = 'TkDefaulFont'

	return fontname


########## Configuration Related Begin #####################################
############################################################################

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


########## Configuration Related End ################################
########## From __init__() Begin
#####################################################################

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


## Fix for macos printing issue starting from about Python 3.13
# Can be set with: mac_print_fix_use
tests = (not self.in_mainloop, self.mac_print_fix, self.os_type == 'mac_os')
if all(tests):
	self.change_printer_to(FIIXED_PRINTER)
	print('using fixed printer')


# Get version control branch
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

#d['tests'] = ['', yellow] # NOTE: this (with any color) just doesn't work, and same with deflines
#n['tests'] = ['', yellow]
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
	#if self.os_type == 'mac_os': size0, size1 = 22, 16
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

########## From __init__() End ######################################
#####################################################################

########## Old stuff End ###################################################
############################################################################


















########## New stuff Begin #################################################
############################################################################



def check_for_deleted_old_key(data, setting_instance):
	list_of_old_keys = data.keys()

	for key in list_of_old_keys:
		try:
			_ = setting_instance[key]

		# Old conf-data has extra key --> is not loaded and not saved --> ok
		except KeyError:
			print('Old configuration had key(likely old) that is not used', key)


def load_conf(data, setting_instance):
	list_of_new_keys = setting_instance.keys()

	for key in list_of_new_keys:
		try:
			setting_instance.key = data[key]

		# Old conf-data has no new key --> ok
		except KeyError:
			print('Old configuration did not have key', key)




colors = c = dict()

# This is also color of comments
c['ln_color'] =	r'#c0c0c0'
c['red'] =		r'#c01c28'
c['cyan'] =		r'#2aa1b3'
c['magenta'] =	r'#a347ba'
c['green'] =	r'#26a269'
c['orange'] =	r'#e95b38'
c['yellow'] =	r'#d0d101'
c['gray'] =		r'#508490'
c['black'] =	r'#221247' # blue tint
c['white'] =	r'#d3d7cf'

c['strings_day'] =	r'#1b774c'
c['calls_day'] =	r'#1b3db5'


default_themes = dict()
default_themes['day']   = d = dict()
default_themes['night'] = n = dict()

# self.default_themes[self.curtheme][tagname] = [backgroundcolor, foregroundcolor]
d['normal_text'] = [c['white'], c['black']]
n['normal_text'] = [c['black'], c['white']]


d['keywords'] = ['',c['orange']]
n['keywords'] = ['',  'deep sky blue']
d['numbers'] = ['',	c['red']]
n['numbers'] = ['',	c['red']]
d['bools'] = ['',	c['magenta']]
n['bools'] = ['',	c['magenta']]
d['strings'] = ['',	c['strings_day']]
n['strings'] = ['',	c['green']]
d['comments'] = ['',c['black']]
n['comments'] = ['',c['ln_color']]
d['calls'] = ['',	c['calls_day']]
n['calls'] = ['',	c['cyan']]
d['breaks'] = ['',	c['orange']]
n['breaks'] = ['',	c['orange']]
d['selfs'] = ['',	c['gray']]
n['selfs'] = ['',	c['gray']]

d['match'] = ['lightyellow', 'black']
n['match'] = ['lightyellow', 'black']
d['focus'] = ['lightgreen',  'black']
n['focus'] = ['lightgreen',  'black']

d['replaced'] = [c['yellow'], 'black']
n['replaced'] = [c['yellow'], 'black']

d['mismatch'] = ['brown1', 'white']
n['mismatch'] = ['brown1', 'white']

d['sel'] = ['#c3c3c3', c['black']]
n['sel'] = ['#c3c3c3', c['black']]



class Fonts:
	root = None
	textfont = None
	menufont = None
	boldfont = None
	keyword_font = None
	linenum_font = None

	if not cls.textfont:
		cls.textfont = tkinter.font.Font(family='TkDefaulFont', size=12, name='textfont')
		cls.menufont = tkinter.font.Font(family='TkDefaulFont', size=10, name='menufont')
		cls.keyword_font = tkinter.font.Font(family='TkDefaulFont', size=12, name='keyword_font')
		cls.linenum_font = tkinter.font.Font(family='TkDefaulFont', size=12, name='linenum_font')

		cls.boldfont = cls.textfont.copy()







@dataclass
class Setting:

	###
	d['scrollbar_widths'] = self.scrollbar_width, self.elementborderwidth
	d['version_control_cmd'] = self.version_control_cmd
	d['marginals'] = self.margin, self.margin_fullscreen, self.gap, self.gap_fullscreen
	d['spacing_linenums'] = self.spacing_linenums
	d['start_fullscreen'] = self.start_fullscreen
	d['fdialog_sorting'] = self.dir_reverse, self.file_reverse
	d['popup_run_action'] = self.popup_run_action
	d['run_timeout'] = self.timeout
	d['run_module'] = self.module_run_name
	d['run_custom'] = self.custom_run_cmd
	d['check_syntax'] = self.check_syntax
	d['fix_mac_print'] = self.fix_mac_print
	d['want_ln'] = self.want_ln
	d['syntax'] = self.syntax
	d['ind_depth'] = self.ind_depth
	d['themes'] = self.themes
	###




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











########## New stuff End ###################################################
############################################################################



















