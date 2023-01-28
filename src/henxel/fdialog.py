import tkinter.font
import tkinter
import pathlib


class FDialog:
	''' Get filepath, cwd is given as pathlib object, result is saved
		in tkinter.StringVar object, which is set to: ''
		on cancel
		
		Bindings:
		window close, Esc		cancel and quit
		double-click, Return	chdir or select file and quit
		
		Tab		switch focus between dirs and files
		
		
		Note that there is no function to be called like this:
		fd = FDialog(*args, **kwargs)
		filepath = fd.non_existing_function_that_returns_filepath_as_string()
		
		Instead you must arrange a variable observer for stringvar with
			stringvar.trace_add('write', my_tracefunc)
		
		or you can just wait for it to change with
			tkinter.wait_variable(stringvar)
		
	'''


	def __init__(self, master, path, stringvar, font=None, menufont=None):
		'''	master		tkinter.Toplevel
			path		pathlib.Path
			stringvar	tkinter.StringVar
			fonts		tkinter.font.Font
		'''
		
		self.top = master
		self.path = path
		self.var = stringvar
		self.font = font
		self.menufont = menufont
		
		if not self.font:
			self.font = tkinter.font.Font(family='TkDefaulFont', size=12)
	
		if not self.menufont:
			self.menufont = tkinter.font.Font(family='TkDefaulFont', size=10)
		
		self.top.config(bd=4)
		self.direction = 'up'
		
		self.dirlist = list()
		self.dotdirlist = list()
		self.filelist = list()
		self.dotfilelist = list()


		self.entry = tkinter.Entry(self.top, takefocus=0, bd=4, font=self.menufont,
					highlightthickness=0, bg='#d9d9d9',
					disabledbackground='#d9d9d9', disabledforeground='black')
				
		self.filesbar = tkinter.Scrollbar(self.top, takefocus=0)
		
		# choosed activestyle:underline because dotbox was almost invisible.
		self.files = tkinter.Listbox(self.top, exportselection=0, activestyle='underline', setgrid=1)
		self.files['yscrollcommand'] = self.filesbar.set
		self.filesbar.config(command=self.files.yview)
		
		self.dirsbar = tkinter.Scrollbar(self.top, takefocus=0)
		self.dirs = tkinter.Listbox(self.top, exportselection=0, activestyle='underline', setgrid=1)
		self.dirs['yscrollcommand'] = self.dirsbar.set
		self.dirsbar.config(command=self.dirs.yview)

		self.dirs.configure(font=self.font, width=30, selectmode='single', bd=4,
					highlightthickness=0, bg='#d9d9d9')
		self.files.configure(font=self.font, width=30, selectmode='single', bd=4,
					highlightthickness=0, bg='#d9d9d9')
		
		self.dirsbar.configure(width=30, elementborderwidth=4)
		self.filesbar.configure(width=30, elementborderwidth=4)
		
		self.dirs.bind('<Double-ButtonRelease-1>', self.chdir)
		self.dirs.bind('<Return>', self.chdir)
		self.dirs.bind('<Tab>', self.nogoto_emptylist)
		
		self.dirs.bind('<Up>', self.carousel)
		self.dirs.bind('<Down>', self.carousel)
		self.files.bind('<Up>', self.carousel)
		self.files.bind('<Down>', self.carousel)
		
		self.files.bind('<Return>', self.selectfile)
		self.files.bind('<Double-ButtonRelease-1>', self.selectfile)
		
		self.top.bind('<Escape>', self.quit_me)
		self.top.protocol("WM_DELETE_WINDOW", self.quit_me)
		
		self.top.rowconfigure(1, weight=1)
		self.top.columnconfigure(1, weight=1)
		
		self.entry.grid_configure(row=0, column = 0, columnspan=4, sticky='sew')
		self.dirsbar.grid_configure(row=1, column = 0, sticky='nsw')
		self.dirs.grid_configure(row=1, column = 1, sticky='nsew')
		self.files.grid_configure(row=1, column = 2, sticky='nsew')
		self.filesbar.grid_configure(row=1, column = 3, sticky='nse')
		
		self.update_view()
		
		#################### init end ################
		
	
	def carousel(self, event=None):
		
		if event.widget.size() > 1:
		
			idx = event.widget.index('active')
			idx_last_file = event.widget.size() - 1
			
			if event.keysym == 'Up' and idx == 0:
				event.widget.activate(idx_last_file)
				event.widget.see(idx_last_file)
				
				return 'break'
			
			elif event.keysym == 'Down' and idx == idx_last_file:
				event.widget.activate(0)
				event.widget.see(0)
				
				return 'break'
				
	
	def nogoto_emptylist(self, event=None):
		'''	prevent tabbing into empty file-box.
			Tab to same line from dirs to files if possible.
		'''
		
		if self.files.size() == 0:
			return 'break'
		
		else:
			self.files.focus_set()
			
			idx = self.dirs.index('active')
			idx_last_file = self.files.size() - 1
			
			if idx >= idx_last_file:
				self.files.activate(idx_last_file)
				self.files.see(idx_last_file)
				
			else:
				self.files.activate(idx)
				self.files.see(idx)
				
			return 'break'
			
				
	def quit_me(self, event=None):
	
		self.top.destroy()
		self.var.set('')
				
	
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
				self.direction = 'up'
			else:
				self.path = self.path / d
				self.direction = 'down'
	
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
			
			self.top.destroy()
			self.var.set(filename.__str__())
			
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
		
		
		if self.path.resolve().__str__() != self.path.absolute().root:
			self.dirs.insert(0, '..')
		
		self.entry.config(state='normal')
		self.entry.delete(0, tkinter.END)
		self.entry.insert(0, self.path.resolve())
		self.entry.config(state='disabled')
		
		# speed up climbing
		if self.direction == 'up':
			self.dirs.select_set(0)
			self.dirs.activate(0)
		
		# speed up diving
		elif self.dirs.size() > 1:
			self.dirs.select_set(1)
			self.dirs.activate(1)
		
		# no dirs
		else:
			self.dirs.select_set(0)
			self.dirs.activate(0)
			
		
		self.dirs.focus_set()
		
