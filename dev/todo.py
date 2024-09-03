# ^/\|-_+:,.;'"*%?=!@&()[]{}~<>
###############################
cmd/Alt-p		save cursor position, so one can go back to it with cmd-b
cmd/Control-b	walk saved cursor positions
cmd/ctrl-g		goto_def, if selection use it
###############################################
bookmark Begin

when view changes, before close curtab:
	tab.bookmarks[:] = [ self.contents.index(mark) for mark in tab.bookmarks ]


when view changes, after open tab:
	restore_bookmarks()
	# Restore bookmarks
	for i, pos in enumerate(self.tabs[self.tabindex].bookmarks):
		self.contents.mark_set('bookmark%d' % i, pos)
		
	self.tabs[self.tabindex].bookmarks.clear()
	
	for mark in self.contents.mark_names():
		if 'bookmark' in mark:
			self.tabs[self.tabindex].bookmarks.append(mark)

view changes, after open tab, restore_bookmarks() is used in:
	walk_tab
	del_tab
	new_tab
	tag_link
	stop_show_errors
	loadfile
	stop_help
																			
	done ok?
	

animate add/remove bookmark		done ok?

toggle bookmark cmd/alt-p		done ok?
walk bookmarks cmd/Control-bB	done ok?

delete_all_bookmarks		no shortcut
print_bookmarks				no shortcut
	

tab.bookmarks = list()
add_bookmark --> tab.bookmarks.append(pos)
must be updated before view change etc
have to use real marks because of empty lines
currently marks persist in conf

bookmark End
############################################################
replace: space to exit?
fixed in start_replace() self.focus_set() --> self.contents.focus_set()
#####
select/move to linestartend when empty line no work, fixed, ok?
#####
add waiting to: goto_bookmark, goto_def, gotoline		done, ok? ####
#####
fixed yank_line no longer set insert mark ok?
#####
clear sel goto_def done ok?
#####
removed unused move_line and updown_override
#####
after paste:
selend is before real pasted text end	fixed ok?
#######################
macos when trying to open: /home

	PermissionError: [Errno 1] Operation not permitted: '/usr/bin/../../home'

fixed ok?
###########
check11 if other than py-files are tabified
	done they now are not tabified
	update help?
###########
fixed capslock macos linux windows ok?
########
cmd/ctrl-g --> goto_def, without selection? done ok?
cmd/ctrl-l --> gotoline
########
long selection: if index not visible,
show wanted side of selection at first keypress done ok?
########
async can be before def  done in get_scope ok?
async await orange?
##########
added get_scope_path
, add_bookmark, goto_bookmark
#############
add_bookmark: add tag, goto_bookmark to tag/position	done ok?
#############
unbind these:
	self.bind("<Control-n>", self.show_next)
	self.bind("<Control-p>", self.show_prev)	done ok?


show: Class.method instead of just: def method	done ok?
show scope when inspect
	tab.inspected set in insert_inspected()
	used only in handle_search_entry()
	could be used to:
		preserve syntax in inspected over things like walk_tab etc
						
	
search: no strip searchword						done, ok? ####
search, show scope in entry when show_next prev	done, ok? ####
show_next/prev: entry handling to function		done, ok? ####
#########
macos: esc should exit fullscreen, done with esc_override()	ok?
#########
save() now generates esc in while-loop and returns False if save fails	ok?
save is too big: splitted to save_forced/save
#########
removed no copy ln --> do_nothing_without_bell ok
#########
added state check11 in save() ok?
#########
tag_link/loadfile error handling bookmarks etc.
tag_link new_tab after f.read ok?
save, called from deltab: check11 done ok?
save, called from loadfile: check11 done ok?
#########
search open() in save, get wrong scope:
	fixed get_scope_path()
	-count varName self.search_count_var = tkinter.IntVar()
	done, ok?

	contents.search searches logical lines, not display lines, so no need
	to check for wrapped lines
######
check open() without encoding
tried, removed encoding='utf-8'
and added t for ensure textmode 'r' --> 'rt'	ok?, not ok
checked this in windows, todo.py does not open, codec charmap error, not ok
######
open file, get bell:
reason is in commit 4bf261d435e21
in save():
	if self.state != 'normal':
		self.bell()
		return 'break'
--> now:
	if self.state != 'normal' and not activetab:
	done ok?

also when load():
check when binding Return if in macOS,
done ok?
######################
esc_override(): Enable toggle fullscreen with Esc.
handle_config --> handle_window_resize
######################
removed tab_override()
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

######################
cmd-t, newtab
	back to cmd-n	done ok? not ok?########################################
####################
bookmark while searching, replacing		done ok?
#####################
search, replace:
search_word:
	suggest
	1: selection if short enough, update oldword if found
	2: old_word
	done ok?
#####################
Sticky top right corner, to get some space for console on left
Next line seems not to work in macos12 consistently.
#self.geometry('-0+0')
diff = self.winfo_screenwidth() - self.winfo_width()
if diff > 0:
	self.geometry('+%d+0' % diff )


test in linux windows
also check shift-tab unindent in windows


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
#####################
cmd-shift-left select indentation same as alt-left done ok?
cmd-shift-left/right, selects from, space only lines also
#####################
replace with replace(idx1 idx2 new_word)	done ok?
now undo works better
#####################
added waiting to undo redo search_next
#####################
search_next now searches with old_word if no selection
#####################
safe space when: search_next, search, replace
self.bid_space		done ok?
#####################
safe esc: if normal and selection, selection clear
for search_next
##############################
search, replace fixing Start

Have to use marks to get overlapping searches work.

Can not replace/replace_all while "-overlap" in search_settings
	
if -start == 'insert' and search_word == selection_get:
	start search from sel_start
	done in do_search ok?

show_prev show_next info
done ok?

search ACA:
ACABACABA
ACA

can search with -overlap, if want to replace, use -regexp:
boundary == A
want change contents B:
B(?=A)

(also matches BBA etc, so must check first with search)

search, replace fixing End
###################
search, replace, search_next
- Control-np in help, error, normal done ok?

reset_search_setting()
print_search_setting()
edit_search_setting(search_setting)

start_search() calls do_search(search_word)
	

if selection, use it, else oldword.

handle_search_entry not done #######################################

search_next in help error works
error: if want to search part of filepaths (select with mouse will open file)
	put cursor near taglink and
	move it to right place with alt-arrow etc and select with keyboard

###################
Below this: not done










#####################################################
search "self.match_lenghts" in edit_search_setting():
	no get funcname


tab on empty line, if at indent0, to same indent than prevline


enable cancel tab-completion
tab completion should first suggest from function scope


get(elided)
elided text is getted by default


inspect syntax
elif hasattr(self.tabs[self.tabindex], 'inspected')##
#####################################################








goto bookmark show position among all bookmarks etc.


cmd-ae in python shell in macos?
Control-d not Control-c to quit multiline command


todo path


find empty lines regexp
tokens:
	end_idx = '%s +%dc' % (start_idx, match_lenght)


replaced less yellow


chek move many lines() mac
after


update help
uncomment '##' must be at indent0 or it can not be removed --> help?


check use of token_can_update += 1


github:
fixed tag config -under --> -underline
2tkcon.tcl


show closing paren


show scope always
handle_search_entry not done in search_next
update scope path after:
	walk_tab etc
	in fname.py @Class.method()
	
unbind load() Return?
focusin focusout show full path?
#############

	


















#######################################
# Below this, not essential but wanted
#######################################

check syntax before quit?
python -c "import ast; ast.parse(open('src/henxel/__init__.py').read())"
	

search: regexp?
start of search/replace: insert window in start of entry:
	dropdown:
		1 use regexp
		2 start from filestart/cursor


macos:
if toggled terminal to fullscreen, after doing one dir(),
then switch to non fullscreen editor, editor is freezed.
pressing return in terminal and then switching back to editor
unfreezes editor.
If both are fullscreen, there is no freezing.
This is little similar to win11-behaviour when not using idle-shell


macos: sometimes closing in fullscreen no get focus back terminal


fdialog.py
	filter:
	sorted(pathlib.Path().glob("*AD*"))
	sorted(pathlib.Path().glob("normal filename"))
	two entries for setting filter at bottom,
	one for dirs, one for files: *.* as default
	

when creating for example new function newname(),
how to ensure newname has not already been reserved?


when paste multiline, if cursor is at idx_linestart of non empty line, and copied text
lastline is indentation only, indentation shape of following lines should be preserved when paste

when paste multiline, then undo that, then paste again same thing, then again undo:
	there can be something leftovers from paste?


check is it necessary to check event.state in select_by_words etc


fix arrow updown (put cursor to same col_nextline or
	lineend if nextline is shorter than col_curline)


bitmap check ensure width?


animate walk_tab, save etc?


save(): escape generate is necessary?
save is too big


todo: tagging system like in youversion


type(self).__name__


macos:
ctrl-d --> ctrl-q/cmd-w ?


fix macos topbar menus?


undo pause, check what is difference when in callback:
	only one edit_separator
	two edit_separators


check is it necessary to set insert mark before ensure_idx_visibility?


self.contents.bind( "<<TkWorldChanged>>", self.test_bind)
	then: self.menufont.configure(underline=1)
	works on macos


search/next also in errors, help


toggle indent with tabs --> space?


automate exit editor, check syntax, reopen python and editor


bind with eval from dict --> user editable binds


yank_line etc. not ideal usage of tag 'sel' --> custom tag


save file to disk when pressing save


tuple after_cancel: (from_who, after_object_id)


structure-viewer with taglinks


syntax highlight often slow, needs check
tokens to list --> after cancel
delete, cmd a, comment at linestart, no syntax
clarify update_tokens marked spot

	
check before copy, paste:
	is selection from editor?
	check indentation if not?


tab-comp in entry?


selection handling not perfect when:
	comment
	indent


guides ?
	on mouseover guideline: show startline of block


toggle clipboard (10 newest items) dropdown in git_btn
	on click put to first?


#################
fix search etc: after giving search word, quickly pressing return and esc
state is locked to search
		
		
FIXED with checking if state is waiting in stop_search

check other escapable callbacks?
#################


padx font measure
cont, ln_wid

padx = self.tab_width // self.ind_depth // 3
pady = padx
in init apply conf and update fonts

############################################
# Not essential End
############################################
# Below this, notes


unbind /give info about cmd shift A? man page
https://intellij-support.jetbrains.com/hc/en-us/articles/360005137400-Cmd-Shift-A-hotkey-opens-Terminal-with-apropos-search-instead-of-the-Find-Action-dialog

1. Open Apple menu | System Settings | Keyboard | Keyboard Shortcuts | Services
2. Under section: Text
3. Uncheck Search man Page Index in Terminal (or change the shortcut)


######################
list of tk::mac procs
https://www.tcl.tk/man/tcl9.0/TkCmd/tk_mac.html

::tk::mac::OpenApplication
If a proc of this name is defined, this proc fill fire when your application is initially opened. It is the default Apple Event handler for kAEOpenApplication, “oapp”.

::tk::mac::ReopenApplication
If a proc of this name is defined it is the default Apple Event handler for kAEReopenApplication, “rapp”, the Apple Event sent when your application is opened when it is already running (e.g. by clicking its icon in the Dock). Here is a sample that raises a minimized window when the Dock icon is clicked:

proc ::tk::mac::ReopenApplication {} {
	if {[wm state .] eq "withdrawn"} {
		wm state . normal
	} else {
		wm deiconify .
	}
	raise .
}
#######################
























entry.winfo_atom('bg')
81
e.entry.winfo_atom('fg')
82
e.entry.winfo_atomname(81)
'bg'
e.entry.winfo_atomname(82)
'fg'




Manual selection handling in Text-widget:
self.contents.mark_names()
'insert', 'current', 'tk::anchor1'
self.contents.index('tk::anchor1')
'38.5'
self.contents.mark_set('tk::anchor1', '38.6')
then set SEL_FIRST to same index if selection starts from top
else: SEL_LAST




win
plain a	==8
+ ctrl	==12
+ shift	==9
+ both	==13

win10 left
262144
win11 left
262152

linux and macos
plain a	==0
+ ctrl	==4
+ shift	==1
+ both	==5


mac_os extra keys:
fn Super	bind to key and check state == 64
Cmd Meta  	bind to key and check state == 8
Alt			bind to key and check state == 16
Mod1 == Cmd

# Binding to combinations which has Command-key (apple-key)
# (or Meta-key as reported by events.py)
# must use Mod1-Key as modifier name:
# Mod1-Key-n == Command-Key-n

cmd		-h 	hide
alt-cmd -h 	hide others
fn 		-h 	show desktop?

ctrl -up 	toggle show open apps
ctrl -down hide others temporarily, get them back with ctrl-up
ctrl -leftright  switch apps?


all alt shortcuts makes some special char
have to bind to symbol name to get alt-shorcuts work in macOS
self.contents.bind( "<function>", self.mac_cmd_overrides)



::tk::mac::OnHide
If defined, this is called when your application receives a kEventAppHidden event, e.g. via the hide menu item in the application or Dock menus.


::tk::mac::OnShow
If defined, this is called when your application receives a kEventAppShown event, e.g. via the show all menu item in the application menu, or by clicking the Dock icon of a hidden application.



# yet another way to find os_type
print tcl-array nicely
e.tk.eval('parray tcl_platform')

print using pattern
e.tk.eval('parray tcl_platform os')





self.bind("<<ThemeChanged>>", self.handle_configure)

# if macos: thread, tkinter.Tk(), button, string


system_colorname = self.entry.cget('fg')
colors_as_rgb_tuple = self.winfo_rgb(system_colorname)
for example, white color would get: (65535, 65535, 65535)


night colors mac_os:
btn_git
filedialog
entry
made quick fix





###################################
ctrl-r no work in python console
https://bugs.python.org/issue38995

Most likely what is happening is that the two Python instances you are using are linked to different versions of the external readline library.  From the version information, its clear that you are using the Python 3.8.0 from the python.org macOS installer.  That Python uses the macOS-supplied BSD editline (AKA libedit) for readline functionality.  The Python 3.7.3 you have is not from python.org and based on the prompt it looks like it was linked with a version of GNU readline which probably does bind ^R to the reverse search function by default.  As described in the Python Library Reference page for readline (https://docs.python.org/3/library/readline.html), both GNU readline and BSD editline can be tailored via configuration files; GNU readline uses ~/.inputrc while BSD editline uses ~/.editrc.

On macOS, the available configuration commands for editline are described in the man page for editrc:

man 5 editrc

In particular, you should be able to enable editlines reverse search functionality by adding the following line to ~/.editrc:

bind ^R em-inc-search-prev

where ^R is two characters, not the single character CTRL-R.
###########################




mac_os:
When in fullscreen, other toplevels go to their own tab.
If fullscreen when fontchoose might press wrong close button.

if menufont is 14 buttons are mac buttons
if bigger they are basic buttons


# self.tk.eval('wm attributes .!editor -fullscreen 1')

# get tcl name of widget
str(e.nametowidget(e.entry))
e.contents.winfo_name()
			
label .lbl

e.tk.eval('.!editor.!entry config -bg')

e.tk.eval('proc myproc {args} {puts AAA}')
e.tk.eval('set myvar A')
e.tk.eval('trace add variable myvar write myproc')



e.tk.eval('proc myproc {args} {puts AAA}')
e.tk.eval('trace add execution .!editor.!entry enter myproc')



e.tk.eval('set myvar B')





win11 ctrl-right no work
e.info_patchlevel()
_VersionInfoType(major=8, minor=6, micro=12, releaselevel='final', serial=0)

array values:
e.tk.eval('foreach key [array names ::tcl::WordBreakRE] {puts $::tcl::WordBreakRE($key)}' )
\s*(\S+)\s*$
\S\s|\s\S
\S*\s+\S
\s*\S+\s
^.*(\S\s|\s\S)

array keys:
e.tk.eval('foreach key [array names ::tcl::WordBreakRE] {puts $key}' )
previous
after
next
end
before


#################
To fix: replace array ::tcl::WordBreakRE contents with newer version, and
replace proc tk::TextNextWord with newer version which was looked in Debian 12 below.
Needs to generate ctrl-leftright before this eval works?:

e.contents.event_generate('<<NextWord>>')
e.tk.eval('set l3 [list previous {\W*(\w+)\W*$} after {\w\W|\W\w} next {\w*\W+\w} end {\W*\w+\W} before {^.*(\w\W|\W\w)}]; puts $l3 ')
e.tk.eval('array set ::tcl::WordBreakRE $l3 ')
e.tk.eval('proc tk::TextNextWord {w start} {TextNextPos $w $start tcl_endOfWord} ')

#################



# Debian 12, ctrl-right works
e.info_patchlevel()
_VersionInfoType(major=8, minor=6, micro=13, releaselevel='final', serial=0)

array values:
e.tk.eval('foreach index [array names ::tcl::WordBreakRE] {puts $::tcl::WordBreakRE($index)}')
\W*(\w+)\W*$
\w\W|\W\w
\w*\W+\w
\W*\w+\W
^.*(\w\W|\W\w)



# this is todo, and stub-editor for testing, might not work

# Run in python console
# >>> import todo
# >>> e=todo.Ed()


# Binding rewrite planning Begin

# print current bindings for a class
# e.contents.bind_class('Text')


# Unbinding default binding of Text-widget:
# e.contents.unbind_class('Text', '<Button-1>')

# So check what want to bind in self.contents, and unbind them from Text
# and it should then work: binding straight to self. Also can unbind all other unneeded bindings.


# remap keys?
# unbind always?

# self.is_binded_to_do_nothing = d = dict()
# d['copy'] = False

# self.is_binded_to_skip_bindlevel = d = dict()
# d['show next'] = True

# self.is_binded_to_normal = d = dict()
# d['show next'] = False


# self.bind_seqs = d = dict()
# seq = d['decrease scrollbar width'] = "<Control-minus>"
# bind_id = self.bind( seq, self.decrease_scrollbar_width)

# self.bind_ids = q = dict()
# q[seq] = bind_id


# when unbinding:
# seq = d['decrease scrollbar width']
# id = q[seq]
# self.contents.unbind(seq, funcid=id)
# q.pop(seq)

# Binding rewrite planning End

# /dev/idle/colorizer.py
# import builtins
# help(builtins)


# remove printings before build




# get line from python console:
# readline.get_line_buffer()

# insert line in console
#readline.insert_text('dir()')

# display it
#readline.redisplay()


#############
''' asd
	import tkinter
	import tkinter.font
	
'''

import tkinter
import tkinter.font






########################## Maybe interesting Begin:

# Handling of states and bindings is hard. One really should read a book about
# stateful programming or something similar if doing something more serious.


# Howto: cancel (not unbind) certain binding for time being:

# def cancelbind(self, event=None):
#	return 'break'

# self.keyid = self.mywidget.bind( "<Some-Key>", func=self.cancelbind)


# Howto: skip bindlevel for certain binding for time being:

# def skip_bindlevel(self, event=None):
#	return 'continue'

# self.keyid = self.mywidget.bind( "<Some-Key>", func=self.skip_bindlevel)


# Howto: lambda to nothing:
# self.contents.bind( "<Left>", lambda event: ...)
	

# Howto: unbind in tkinter:

# def mycallback1(self, event=None):
#	print(1, event.keysum, event.num)

# def mycallback2(self, event=None):
#	print(2, event.keysum, event.num)
	
# self.anykeyid = self.mywidget1.bind( "<Any-Key>", func=self.mycallback1)
# self.anybutid = self.mywidget1.bind( "<Any-Button>", func=self.mycallback2)

# self.contents.unbind("<Any-Key>", funcid=self.anykeyid)
# self.contents.unbind("<Any-Button>", funcid=self.anybutid)
		


############# About screen dimensions Begin

# This is correct:
# .winfo_screenheight()
# .winfo_screenwidth()

# check screen dpi:
#
# import tkinter
# import tkinter.font
# root = tkinter.Tk()
# t = tkinter.Text(root)
# t.pack()
# f = tkinter.font.Font(t, family='TkDefaulFont', size=12)
# dpi = f.metrics().get('linespace')*5

############### About screen dimensions End


# builtin stiples have too small and dense dots for hdpi:
# myTextwidget.tag_config('sel', bgstipple='gray12')

########################## Maybe interesting end


class Ed(tkinter.Toplevel):

	# use 10000 (10s) if need slow update interval for linenumbers
	UPDATE_PERIOD = 100 #ms

	updateId = None

	# This list is needed for classmethod updateAllLineNumbers() to work.
	# Self must be then added to this list in init with:
	# self.__class__.editors.append(self)
	editors = []
			
	def __init__(self):
		
		self.root = tkinter.Tk().withdraw()
		super().__init__(self.root)
		self.__class__.editors.append(self)
		
		self.lineNumbers = ''
		
		self.rowconfigure(1, weight=1)
		self.columnconfigure(1, weight=1)
		
		self.btn_test=tkinter.Button(self, text='Test')
		self.btn_test.grid(row=0, column = 0, sticky='w')
		
		self.entry = tkinter.Entry(self)
		self.entry.grid(row=0, column = 1, sticky='we')
		
		self.btn_open=tkinter.Button(self, text='Open')
		self.btn_save=tkinter.Button(self, text='Save')
		self.btn_open.grid(row=0, column = 2)
		self.btn_save.grid(row=0, column = 3, sticky='e')
		
		
		self.lb = tkinter.Text(self, width=5, padx=10)
		self.lb.grid(row=1, column = 0, sticky='nsw')
		
		self.contents = tkinter.Text(self, blockcursor=True, undo=True, maxundo=-1, autoseparators=True, tabstyle='wordprocessor')
		
		self.scrollbar = tkinter.Scrollbar(self, orient=tkinter.VERTICAL)
		
		
		self.contents.grid(row=1, column=1, columnspan=3, sticky='nswe')
		self.scrollbar.grid(row=1,column=3, sticky='nse')
		
		self.font = tkinter.font.Font(size=12)
		self.font.config(family='Noto Mono', size=12)
		
		self.lb.tag_config('justright', justify=tkinter.RIGHT)
	
		self.scrollbar_width = 30
		self.elementborderwidth = 4
		
		self.scrollbar.config(width=self.scrollbar_width)
		self.scrollbar.config(elementborderwidth=self.elementborderwidth)
		
		self.contents.config(font=self.font)
		self.entry.config(font=self.font)
		self.btn_open.config(font=self.font)
		self.btn_save.config(font=self.font)
		self.btn_test.config(font=self.font)
		self.lb.config(font=self.font, state='disabled')

		# Changing the settings to make the scrolling work
		
		self.scrollbar['command'] = self.contents.yview
		self.contents['yscrollcommand'] = self.scrollbar.set
		
		noOfLines = 500
		s = 'line ................................... %s'
		s = '\n'.join( s%i for i in range(1, noOfLines+1) )
			
		self.contents.insert(tkinter.END, s)
		
		# Needed in updateLineNumbers(), there is more info.
		# y_extra_offset is 3 but why, dont know:
		
		self.update_idletasks()
		_, self.y_extra_offset, _,  self.bbox_height = self.contents.bbox('1.0')
		
		
##		self.contents.bind('<<Modified>>', self.modified)
		
		self.contents.edit_reset()
		self.contents.edit_modified(0)
		self.eventnum = 0
		
		if self.__class__.updateId is None:
			self.updateAllLineNumbers()

		
	def modified(self, event=None):
		
		self.eventnum += 1
	
		print(f'Begin Event {self.eventnum}:\n')
	
		#l = [ item for item in dir(event) if '_' not in item ]
		
		print(event.__class__)
		print(event)
		print('asd', event.__repr__() )
		
		#for key in l:
		#	print(key, getattr(event, key))
		
		
		print(f'\nEnd Event {self.eventnum}:')
		print(10*'= ')
		
		self.contents.edit_modified(0)
		
		
	def getLineNumbers(self):

		x = 0
		line = '0'
		col= ''
		ln = ''

		# line-height is used as step, it depends on font:
		step = self.bbox_height

		nl = '\n'
		lineMask = '    %s\n'
		
		# @x,y is tkinter text-index:
		# The character that covers the (x,y) -coordinate within the text's window.
		indexMask = '@0,%d'

		for i in range(0, self.contents.winfo_height(), step):

			ll, cc = self.contents.index( indexMask % i).split('.')
			
			if line == ll:
				if col != cc:
					col = cc
					ln += nl
			else:
				line, col = ll, cc
				# -5: show up to four smallest number (0-9999)
				# then starts again from 0 (when actually 10000)
				ln += (lineMask % line)[-5:]
		
		return ln

		
	def updateLineNumbers(self):

		tt = self.lb
		ln = self.getLineNumbers()
		if self.lineNumbers != ln:
			self.lineNumbers = ln
			
			# 1 - 3 : adjust linenumber-lines with text-lines
			
			# 1: Actual line.col of x=0 y=0 in text-widget:
			# idx is index of currently visible first character
			idx = self.contents.index('@0,0')
			
			# 2: bbox returns this kind of tuple: (3, -9, 19, 38)
			# (bbox is cell that holds a character)
			# (x-offset, y-offset, width, height) in pixels
			# Want y-offset of first visible line, and reverse it.
			# Also update line-height (bbox_height) in case of font changes:
			
			_, y_offset, _, self.bbox_height = self.contents.bbox(idx)
			
			y_offset *= -1
			
			if y_offset != 0:
				y_offset += self.y_extra_offset
				
			tt.config(state='normal')
			tt.delete('1.0', tkinter.END)
			tt.insert('1.0', self.lineNumbers)
			tt.tag_add('justright', '1.0', tkinter.END)
			
			# 3: Then scroll lineswidget same amount to fix offset
			# compared to text-widget:
			tt.yview_scroll(y_offset, 'pixels')

			tt.config(state='disabled')


	@classmethod
	def updateAllLineNumbers(cls):

		if len(cls.editors) < 1:
			cls.updateId = None
			return
				
		for ed in cls.editors:
			ed.updateLineNumbers()

		cls.updateId = ed.contents.after(
			cls.UPDATE_PERIOD,
			cls.updateAllLineNumbers)
		
		# about double cpu compared to after(100ms), but is smoother
##		cls.updateId = ed.contents.after_idle(
##			cls.updateAllLineNumbers)
