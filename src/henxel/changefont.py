import tkinter.font
import tkinter


class FontChooser:

	def __init__(self, master, fontlist, big=False, sb_widths=None, on_fontchange=None):
		'''	master		tkinter.Toplevel
			fontlist	list of tkinter.font.Font instances
			big			If true start with bigger font.
			sb_widths	Tuple containing scrollbar_width and elementborderwidth

			on_fontchange	function, used in change_font()
							and checkbutton_command(). It is executed after
							change on any item in fontlist.
						This is practically same as if there would be virtual
						event <<FontChanged>> and on_fontchange binded to it.
		'''

		self.top = master
		self.fonts = fontlist
		self.scrollbar_width, self.elementborderwidth = sb_widths


		if on_fontchange:
			self.on_fontchange = on_fontchange
		else:
			self.on_fontchange = None

		self.max = 42
		self.min = 8

		self.topframe = tkinter.Frame(self.top)
		self.bottomframe = tkinter.Frame(self.top)
		self.topframe.pack()
		self.bottomframe.pack()


		self.option_menu_list = list()

		for font in self.fonts:
			self.option_menu_list.append(font.name)

		self.waitvar = tkinter.IntVar()
		self.var = tkinter.StringVar()
		self.var.set(self.option_menu_list[0])
		self.font = tkinter.font.nametofont(self.var.get())

		self.optionmenu = tkinter.OptionMenu(self.topframe, self.var, *self.option_menu_list,
											command=self.optionmenu_command)

		# Set font of dropdown button:
		self.optionmenu.config(font=('TkDefaultFont',10))

		# Set font of dropdown items:
		self.menu = self.topframe.nametowidget(self.optionmenu.menuname)
		self.menu.config(font=('TkDefaultFont',10))

		# Optionmenu contains font-instances to be configured:
		self.optionmenu.pack(side=tkinter.LEFT)


		self.button = tkinter.Button(self.topframe, text='BIG', command=self.button_command)
		self.button.pack()
		self.scrollbar = tkinter.Scrollbar(self.topframe)

		# Listbox contains font-choises to select from:
		self.lb = tkinter.Listbox(self.topframe, font=('TkDefaultFont', 10),
								selectmode=tkinter.SINGLE, width=40,
								yscrollcommand=self.scrollbar.set)
		self.lb.pack(pady=10, side='left')
		self.scrollbar.pack(side='left', fill='y')

		self.scrollbar.config(width=self.scrollbar_width,
							elementborderwidth=self.elementborderwidth, command=self.lb.yview)


		# With spinbox we set font size:
		self.sb = tkinter.Spinbox(self.topframe, font=('TkDefaultFont', 10), from_=self.min,
								to=self.max, increment=2, width=3, command=self.change_font)
		self.sb.pack(pady=10, anchor='w')

		# Make checkboxes for other font configurations
		self.bold = tkinter.StringVar()
		self.cb1 = tkinter.Checkbutton(self.topframe, font=('TkDefaultFont', 10),
									offvalue='normal', onvalue='bold', text='Bold',
									variable=self.bold)
		self.cb1.pack(pady=10, anchor='w')
		self.cb1.config(command=lambda args=[self.bold, 'weight']:
						self.checkbutton_command(args))



		self.filter_mono = tkinter.IntVar()
		self.cb5 = tkinter.Checkbutton(self.topframe, font=('TkDefaultFont', 10), offvalue=0,
									onvalue=1, text='Mono', variable=self.filter_mono)
		self.cb5.pack(pady=10, anchor='w')
		self.cb5.config(command=self.update_fontlistbox)


		# Get current fontsize and show it in spinbox
		self.sb.delete(0, 'end')
		fontsize = self.font['size']
		self.sb.insert(0, fontsize)


		# Check rest font configurations:
		self.cb1.deselect()
		self.cb5.deselect()

		if self.font['weight'] == 'bold': self.cb1.select()

		self.lb.bind('<ButtonRelease-1>', self.change_font)


		# Increase font-size
		if big: self.button_command()


		self.fontnames = list()
		self.fontnames_mono = list()
		self.fontnames_const_line = list()
		self.fontnames_const_line_mono = list()

		self.top.after(200, self.get_fonts)


	def button_command(self, event=None):
		'''	In case there is not font-scaling in use by OS and
			using hdpi-screen.
		'''
		widgetlist = [
					self.optionmenu,
					self.menu,
					self.lb,
					self.sb,
					self.cb1,
					self.cb5
					]

		if self.button['text'] == 'BIG':
			for widget in widgetlist:
				widget.config(font=('TkDefaultFont', 20))

		if self.button['text'] == 'SMALL':
			for widget in widgetlist:
				widget.config(font=('TkDefaultFont', 10))

		if self.button['text'] == 'BIG':
			self.button['text'] = 'SMALL'
		else:
			self.button['text'] = 'BIG'



	def update_fontlistbox(self, event=None):
		'''	Show all fonts or mono-spaced,
			depending on cb5 setting.
		'''

		filter_mono = self.filter_mono.get()
		fonts = None


		if filter_mono:
			fonts = self.fontnames_mono
		else:
			fonts = self.fontnames


		self.top.selection_clear()
		self.lb.delete(0, 'end')


		for name in fonts:
			self.lb.insert('end', name)


		# Show current fontname in listbox if found
		try:
			fontname = self.font.actual("family")
			fontindex = fonts.index(fontname)
			self.top.after(100, lambda args=[fontindex]: self.lb.select_set(args))
			self.top.after(300, lambda args=[fontindex]: self.lb.see(args))

		except ValueError:
			# not in list
			pass


	def checkbutton_command(self, args, event=None):
		'''	args[0] is tkinter.StringVar instance
			args[1] is string
		'''
		var = args[0]
		key = args[1]


		self.font[key] = var.get()

		if self.on_fontchange:
			self.on_fontchange()


	def optionmenu_command(self, event=None):
		'''	When font(instance) is selected from optionmenu.
		'''
		self.font = tkinter.font.nametofont(self.var.get())
		self.update_fontlistbox()


		self.sb.delete(0, 'end')
		fontsize = self.font['size']
		self.sb.insert(0, fontsize)

		self.cb1.deselect()

		if self.font['weight'] == 'bold': self.cb1.select()


	def change_font(self, event=None):
		'''	Change values of current font-instance.
		'''

		l = None
		l = self.lb.curselection()


		if l in [(), None, ""]:
			self.font.config(
				size=self.sb.get()
				)

		else:
			f = self.lb.get(l)

			self.font.config(
				family=f,
				size=self.sb.get()
				)


		if self.on_fontchange:
			self.on_fontchange()


	def wait_for(self, ms):
		self.waitvar.set(False)
		self.top.after(ms, self.waiter)
		self.top.wait_variable(self.waitvar)


	def waiter(self):
		self.waitvar.set(True)


	def get_fonts(self):

		font = tkinter.font.Font(family='TkDefaultFont', size=12)

		# Test: filter out vertical fonts.
		def test_font(f):
			return f[0] == '@'


		fontnames = [f for f in tkinter.font.families() if not test_font(f)]

		# Remove duplicates then sort
		s = set(fontnames)
		fontnames = [f for f in s]
		fontnames.sort()


		for name in fontnames:
			font.config(family=name)
			font_is_fixed = font.metrics()['fixed']
			self.fontnames.append(name)
			self.lb.insert('end', name)
			self.lb.see('end')
			self.wait_for(4)

			if font_is_fixed: self.fontnames_mono.append(name)


		# Show current fontname in listbox
		try:
			fontname = self.font.actual("family")
			fontindex = self.fontnames.index(fontname)
			self.top.after(100, lambda args=[fontindex]: self.lb.select_set(args))
			self.top.after(300, lambda args=[fontindex]: self.lb.see(args))

		except ValueError:
			# not in list
			pass
