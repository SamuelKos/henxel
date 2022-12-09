# this is todo, and stub-editor for testing

# Run in python console:
# >>> import todo
# >>> e=todo.Ed()

import tkinter
import tkinter.font


# add 'extra line' to ln getLineNumbers() 	ok ####################

# added borders 							ok ################


# undo only char at time, need edit-separators
# testi.py	




# I tested this: grid_forget() + grid()   is just too blinky to be really usable

##	Goal: 
##	Tab-spesific undo-mechanism, that survives as long as tab page is open,
## 	and maybe show in title if tab (with contents on disk) is modified.
##	like:
##	self.tabs[self.tabindex].modified = 
##	self.tabs[self.tabindex].textwidget.edit_modified()
##	
##	How:
##	Now have single tkinter.Text -widget with single undo-stack that is used
##	in all situations and tabs. Want all tabs have its own text-widget and
##	undo stack:
##	self.tabs[self.tabindex].textwidget = tkinter.Text(**options)
##	Help and error-views must also have their own text-widgets.
##	
##	How view is changed:
##	Now self.contents is emptied and filled again when view changes.
##	This is unnecessary when each view has its own text-widget.
##	When view is called to change: old views (a tab page most likely) 
##	textwidget must be first unpacked with (tab-page was open in this example):
##	self.tabs[self.tabindex].textwidget.grid_forget()
##	and then do necessary updates to whatever objects is needed like: 
##	self.tabindex += 1
##	and	then pack the new views text-widget with
##	(open another tab-page in this example):
##	self.tabs[self.tabindex].textwidget.grid(**options)
##	
##	This is big change and will take some time to do.
	



########################## Maybe interesting:

## w.wait_variable(v)
## Waits until the value of variable v is set, even if the value does not change. This method enters a
## local wait loop, so it does not block the rest of the application.

## w.wait_visibility(w)
## Wait until widget w (typically a Toplevel) is visible.
##

# check screen dpi:
# font is tkinter.font.Font-instance
# dpi = self.font.metrics().get('linespace')*5

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
		
		# about double cpu compared to after(100ms), but is smoother:
##		cls.updateId = ed.contents.after_idle(
##			cls.updateAllLineNumbers)
			
			