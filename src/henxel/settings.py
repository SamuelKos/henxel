from dataclasses import dataclass, field
from typing import Any, List
import tkinter.font

defaults = dict()


# This module is totally in unusable state and Work in progress
######################################################################
# From __init__.py

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


def fonts_exists(data):

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


def load_config(data):

	textfont, menufont, keyword_font, linenum_font = fonts_exists(data)
	return set_config(data, textfont, menufont, keyword_font, linenum_font)


def set_config(self, data, textfont, menufont, keyword_font, linenum_font):

	d = data

	# Set Font Begin ##############################
	flag_check_lineheights = False
	if not all((textfont, linenum_font)): flag_check_lineheights = True

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

	if flag_check_lineheights:
		self.flag_check_lineheights = True
		self.spacing_linenums = 0


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
	self.fix_mac_print = d['fix_mac_print']
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
		### One time conf End ###


	# Load tabs from conf
	else:
		self.tabs = [ Tab(self.create_textwidget(), **items) for items in d['tabs'] ]


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


	return True

	## set_config End #########

#################################################################






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






























