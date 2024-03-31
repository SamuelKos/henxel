import keyword ok?

expand over dot ok?

expand indent_ no work to indent_cursor fixed ok?

canceled shortcut for run file:
removed binding ctrl_L-super_L-return to run file in return_override()	ok?

return_over if line empty rtsrip to cursor ok?

ctrl-q -> ctrl-Q del_tab prevent close tab without save by accident ok?

command-ae goto_lineends? ok?

#####
alt-right until: word,cursor,) then shift-right -> sel start moves one char right

in select_by_words():
self.contents.event_generate('<<PrevWord>>')
-->
self.contents.event_generate('<<SelectPrevWord>>')
ok? not ok, flashy at lineends--> using PrevWord with mark_set self.anchor:
self.contents.mark_names()
'insert', 'current', 'tk::anchor1'
self.contents.index('tk::anchor1')
'38.5'
self.contents.mark_set('tk::anchor1', '38.6')
#####


replace all
dont remove tags if do something after that binds escape but dont change view
like gotoline etc. this is ominaisuus, add to helpfile:
if absolutely want clear replaced tags
then switch back and forth tabs
if not another tab open new

####
entry search
ctrl-right no work ok?
in mac_cmd_overrides
####
removed binding fn-f ok?
handled in handle_config
####
self.entry.insert(0, self.tabs[self.tabindex].filepath)
self.entry.xview_moveto(1.0) ok?
####
selnextword gives anchor and
e.tk.eval('parray ::tcl::WordBreakRE' )
clearsel prevline because selection at end of file
####



update structure briefing?
update links after imports?



title label before open_btn

skip_bind?

ctrl-shift-ju select many lines?




chek sel line etc:
done:
	goto_linestartend
	goto_line
	yank line
	comment
	indent


search be able to select and copy?
arrow right esc here
remove buttonrelease-1


tab-comp in entry?


macos fullscreen title
self.wm_attri ok?
git branch to title
tab position to btn_git
gotoline search replace to entry



helpfile

pics to readme?

ctrl-c override?





entry.winfo_atom('bg')
81
e.entry.winfo_atom('fg')
82
e.entry.winfo_atomname(81)
'bg'
e.entry.winfo_atomname(82)
'fg'




guides?
on mouseover guideline: show startline of block

marks?
toggle mark




padx font measure
cont, ln_wid

padx = self.tab_width // self.ind_depth // 3
pady = padx
in init apply conf and update fonts


flash after view change?






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



cmd-w  to closetab?



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



after font change re-grid?




###################################
ctrl-r no work in python console
https://bugs.python.org/issue38995

Most likely what is happening is that the two Python instances you are using are linked to different versions of the external readline library.  From the version information, it's clear that you are using the Python 3.8.0 from the python.org macOS installer.  That Python uses the macOS-supplied BSD editline (AKA libedit) for readline functionality.  The Python 3.7.3 you have is not from python.org and based on the prompt it looks like it was linked with a version of GNU readline which probably does bind ^R to the reverse search function by default.  As described in the Python Library Reference page for readline (https://docs.python.org/3/library/readline.html), both GNU readline and BSD editline can be tailored via configuration files; GNU readline uses ~/.inputrc while BSD editline uses ~/.editrc.

On macOS, the available configuration commands for editline are described in the man page for editrc:

man 5 editrc

In particular, you should be able to enable editline's reverse search functionality by adding the following line to ~/.editrc:

bind ^R em-inc-search-prev

where ^R is two characters, not the single character CTRL-R.
###########################






if menufont is 14 buttons are mac buttons
if bigger they are basic buttons


mac_os:
When in fullscreen, other toplevels go to their own tab.
If fullscreen when fontchoose might press wrong close button.

fn-f now works

# fullscreen
# fn f
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








ctrl c override:
self.indent_selstart = 0
self.indent_nextline = 0
self.indent_diff = 0
self.flag_fix_indent = False
			
if selstart line not empty:
	
	if line in two nextlines below selstart not empty:

		self.indent_selstart = x
		self.indent_nextline = y
		self.indent_diff = y-x
		
		if self.indent_diff > 0:
			self.flag_fix_indent = True
			
			
when paste:

if self.flag_fix_indent:
	
	indent_cursor = x
	indent_diff_cursor = indent_cursor - self.indent_selstart
	
	paste firstline from clipboard
	
	for line in clipboard[1:]:
		
		if indent_diff_cursor > 0:
			line.indent += indent_diff_cursor
			
		elif indent_diff_cursor < 0:
			line.indent -= indent_diff_cursor
			
		paste line
			

toggle clipboard (10 newest items) dropdown in git_btn,
on click put to first?






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
