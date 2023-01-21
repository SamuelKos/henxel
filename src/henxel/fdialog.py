import tkinter.font
import tkinter
import pathlib


class FDialog:
	''' Get filepath, cwd is given as pathlib object, result is saved
		in tkinter.StringVar object, which is set to empty string: ''
		on cancel
		
		Bindings:
		window close, Esc		cancel and quit
		double-click, Return	chdir or select file and quit
		
		Tab		switch focus between dirs and files
	'''


	def __init__(self, master, path, stringvar, font=None):
		'''	master		tkinter.Toplevel
			path		pathlib.Path
			stringvar	tkinter.StringVar
			font		tkinter.font.Font
		'''
		
		self.top = master
		self.path = path
		self.var = stringvar
		self.font = font
		
		if not self.font:
			self.font = tkinter.font.Font(family='TkDefaulFont', size=12)
		
		self.top.config(bd=4)
		
		self.dirlist = list()
		self.dotdirlist = list()
		self.filelist = list()
		self.dotfilelist = list()
		
		self.filesbar = tkinter.Scrollbar(self.top, takefocus=0)
		self.filesbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
		
		# yet another unconfigurable:activestyle
		# choosed underline because dotbox was almost invisible.
		self.files = tkinter.Listbox(self.top, exportselection=0, activestyle='underline', setgrid=1)
		self.files.pack(side=tkinter.RIGHT, expand=1, fill=tkinter.BOTH)
		
		self.files['yscrollcommand'] = self.filesbar.set
		self.filesbar.config(command=self.files.yview)
		
		self.dirsbar = tkinter.Scrollbar(self.top, takefocus=0)
		self.dirsbar.pack(side=tkinter.LEFT, fill=tkinter.Y)
		self.dirs = tkinter.Listbox(self.top, exportselection=0, activestyle='underline', setgrid=1)
		self.dirs.pack(side=tkinter.LEFT, expand=1, fill=tkinter.BOTH)
		
		self.dirs['yscrollcommand'] = self.dirsbar.set
		self.dirsbar.config(command=self.dirs.yview)

		self.dirs.configure(font=self.font, width=30, selectmode='single', bd=4,
					highlightthickness=0, bg='#d9d9d9')
		self.files.configure(font=self.font, width=30, selectmode='single', bd=4,
					highlightthickness=0, bg='#d9d9d9')
		
		self.dirsbar.configure(width=30)
		self.filesbar.configure(width=30)
		self.filesbar.configure(elementborderwidth=4)
		self.dirsbar.configure(elementborderwidth=4)
		
		self.dirs.bind('<Double-ButtonRelease-1>', self.chdir)
		self.dirs.bind('<Return>', self.chdir)
		self.files.bind('<Return>', self.selectfile)
		self.files.bind('<Double-ButtonRelease-1>', self.selectfile)
		
		self.top.wait_visibility() # window needs to be visible for the grab
		self.top.grab_set()
		
		self.top.bind('<Escape>', self.quit_me)
		self.top.protocol("WM_DELETE_WINDOW", self.quit_me)
		
		
		self.update_view()
		#################### init end ################
		

	def quit_me(self, event=None):
		self.var.set('')
		self.top.destroy()
		
	
	def chdir(self, event=None):
		try:
			# pressed Return:
			if event.num != 1:
				self.dirs.selection_clear(0, tkinter.END)
				self.dirs.selection_set( self.dirs.index('active') )
				d = self.dirs.get('active')
			
			# button-1:
			else:
				self.dirs.activate( self.dirs.curselection() )
				d = self.dirs.get('active')
			
			if d == '..':
				self.path = self.path / '..'
			else:
				self.path = self.path / d
	
			self.update_view()
				
		except tkinter.TclError as e:
			print(e)


	def selectfile(self, event=None):
		try:
			if event.num != 1:
				self.files.selection_clear(0, tkinter.END)
				self.files.selection_set(self.files.index('active'))
				f = self.files.get('active')
			
			else:
				f = self.files.get( self.files.curselection() )
			
			filename = self.path.resolve() / f
			
			self.var.set(filename.__str__())
			self.top.destroy()
			
		except tkinter.TclError as e:
			print(e)
		
			
	def update_view(self):
		
		self.dirs.selection_clear(0, tkinter.END)
		
		self.dirs.delete(0, tkinter.END)
		self.files.delete(0, tkinter.END)
		
		self.dirlist.clear()
		self.dotdirlist.clear()
		self.filelist.clear()
		self.dotfilelist.clear()
		
		
		for item in self.path.iterdir():
			
			if item.is_file():
				name = item.stem + item.suffix
			
				if name[0] == '.':
					self.dotfilelist.append(name)
				else:
					self.filelist.append(name)
					
			elif item.is_dir():
			
				if item.name[0] == '.':
					self.dotdirlist.append(item.name + '/')
				else:
					self.dirlist.append(item.name + '/')
				
		
		# __pycache__/ etc last:
		self.dirlist.sort(reverse=True)
		self.dotdirlist.sort()
		
		self.filelist.sort()
		self.dotfilelist.sort()
		
		
		for f in self.filelist:
			self.files.insert(tkinter.END, f)
			
		for d in self.dirlist:
			self.dirs.insert(tkinter.END, d)
			
		for f in self.dotfilelist:
			self.files.insert(tkinter.END, f)
			self.files.itemconfig(tkinter.END, fg='gray')
		
		for d in self.dotdirlist:
			self.dirs.insert(tkinter.END, d)
			self.dirs.itemconfig(tkinter.END, fg='gray')
		
		
		if self.path.resolve().name not in [ '', self.path.absolute().root ]:
			self.dirs.insert(0, '..')
		
		self.dirs.select_set(0)
		self.dirs.activate(0)
		self.dirs.focus_set()
		
