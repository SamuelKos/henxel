import tkinter.font
import tkinter
import pathlib

# Update printer, when necessary, Begin
import functools
# Get reference to printer set in henxel
import importflags

def fix_print(func):
	@functools.wraps(func)
	def wrapper_print(*args, **kwargs):
		printer = importflags.PRINTER['current']
		printer(*args, **kwargs)
	return wrapper_print

global print
@fix_print
def print(*args, **kwargs): return
# Update printer, when necessary, End



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
			some_tkinter_widget.wait_variable(stringvar)

	'''


	def __init__(self, master, path, stringvar, font=None, menufont=None, os_type='linux'):
		'''	master		tkinter.LabelFrame
			path		pathlib.Path
			stringvar	tkinter.StringVar
			fonts		tkinter.font.Font
			os_type		'linux', 'mac_os', 'windows'
		'''

		self.top = master
		self.path = path
		self.var = stringvar
		self.font = font
		self.menufont = menufont

		self.scrollbar_width, self.elementborderwidth = 9,1

		# Sorting orders, see: __init__.py: Editor.set_filedialog_sorting_order
		self.dir_reverse = True
		self.file_reverse = False


		s0, s1 = 12, 10
		if os_type == 'mac_os': s0, s1 = 16, 14

		if not self.font:
			self.font = tkinter.font.Font(family='TkDefaulFont', size=s0)

		if not self.menufont:
			self.menufont = tkinter.font.Font(family='TkDefaulFont', size=s1)

		self.top.config(bd=4)
		self.direction = 'up'

		self.dirlist = list()
		self.dotdirlist = list()
		self.filelist = list()
		self.dotfilelist = list()


		self.entry = tkinter.Entry(self.top, takefocus=0, bd=4, font=self.menufont,
								highlightthickness=0)

		self.filesbar = tkinter.Scrollbar(self.top, takefocus=0)

		# Choosed activestyle:underline because dotbox was almost invisible
		self.files = tkinter.Listbox(self.top, exportselection=0, activestyle='underline')
		self.files['yscrollcommand'] = self.filesbar.set
		self.filesbar.config(command=self.files.yview)

		self.dirsbar = tkinter.Scrollbar(self.top, takefocus=0)

		# Note: if using: setgrid=1, it would mess up with setting height(num lines) in Editor.load
		self.dirs = tkinter.Listbox(self.top, exportselection=0, activestyle='underline')
		self.dirs['yscrollcommand'] = self.dirsbar.set
		self.dirsbar.config(command=self.dirs.yview)

		self.dirs.configure(font=self.font, width=30, selectmode='single',
							highlightthickness=0)

		self.files.configure(font=self.font, width=30, selectmode='single',
							highlightthickness=0)

		if os_type != 'mac_os':
			self.dirs.config(bg='#d9d9d9', bd=4)
			self.files.config(bg='#d9d9d9', bd=4)
			self.entry.config(bg='#d9d9d9', disabledbackground='#d9d9d9',
							disabledforeground='black')


		self.dirs.bind('<Double-ButtonRelease-1>', self.chdir)
		self.dirs.bind('<Return>', self.chdir)
		self.dirs.bind('<Tab>', self.nogoto_emptylist)

		self.dirs.bind('<Up>', self.carousel)
		self.dirs.bind('<Down>', self.carousel)
		self.files.bind('<Up>', self.carousel)
		self.files.bind('<Down>', self.carousel)

		self.files.bind('<Return>', self.selectfile)
		self.files.bind('<Double-ButtonRelease-1>', self.selectfile)

		#self.entry.bind('<Return>', self.selectfile)######################

		self.top.rowconfigure(1, weight=1)
		self.top.columnconfigure(1, weight=1)

		self.entry.grid_configure(row=0, column = 0, columnspan=4, sticky='sew')
		self.dirsbar.grid_configure(row=1, column = 0, sticky='nsw')
		self.dirs.grid_configure(row=1, column = 1, sticky='nsew')
		self.files.grid_configure(row=1, column = 2, sticky='nsew')
		self.filesbar.grid_configure(row=1, column = 3, sticky='nse')

		#################### init end ################


	def carousel(self, event=None):
		if event.widget.size() > 1:

			idx = event.widget.index('active')
			idx_last_file = event.widget.size() - 1

			idx_start = event.widget.index('@0,0')
			idx_end = event.widget.index('@0,65535')
			num_items_onscreen = idx_end - idx_start + 1


			if event.keysym == 'Up':

				if idx == 0:
					event.widget.activate(idx_last_file)
					event.widget.see(idx_last_file)
					return 'break'

				# if all items are not visible
				elif num_items_onscreen -1 < idx_last_file:

					# if at first fifth: scroll up one line
					one_fifth = num_items_onscreen * 2 // 10
					if one_fifth > 10: one_fifth = 10
					elif one_fifth < 3: one_fifth = 3

					idx_new = idx_start + one_fifth

					if idx < idx_new:
						# scroll up one line
						event.widget.see(idx_start - 1)


			elif event.keysym == 'Down':

				if idx == idx_last_file:
					event.widget.activate(0)
					event.widget.see(0)
					return 'break'

				# if all items are not visible
				elif num_items_onscreen -1 < idx_last_file:

					# if at last fifth: scroll down one line
					one_fifth = num_items_onscreen * 2 // 10
					if one_fifth > 10: one_fifth = 4
					elif one_fifth < 3: one_fifth = 3

					idx_new = idx_end - one_fifth

					if idx > idx_new:
						# scroll down one line
						event.widget.see(idx_end + 1)


	def nogoto_emptylist(self, event=None):
		'''	Prevent tabbing into empty file-box.
		'''

		if self.files.size() == 0: pass
		else:
			self.files.focus_set()
			self.files.activate(0)
			self.files.see(0)
		return 'break'


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

		try:
			for item in self.path.iterdir():

				if item.is_file():
					name = item.stem + item.suffix

					if name[0] == '.':
						self.dotfilelist.append(name)
					else:
						self.filelist.append(name)

				elif item.is_dir():

					if item.name[0] in '._':
						self.dotdirlist.append(item.name + '/')
					else:
						self.dirlist.append(item.name + '/')


		# For example, if no access to some folder
		except EnvironmentError as e:
			err = e.__str__()

			# Change relative pathname in traceback to absolute
			if '..' in e.filename:
				abs_fpath = self.path.resolve().__str__()
				err = err.replace(e.filename, abs_fpath)

			print(err)


		self.dirlist.sort(reverse=self.dir_reverse)
		self.dotdirlist.sort()

		self.filelist.sort(reverse=self.file_reverse)
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

