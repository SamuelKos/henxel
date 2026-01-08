import tkinter.font
import tkinter

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



class FontChooser:

	def __init__(self, master, fontlist, big=False, sb_widths=None, on_fontchange=None):
		'''	master		tkinter.Toplevel
			fontlist	list of tkinter.font.Font instances
			big			If true start with bigger font.
			sb_widths	Tuple containing scrollbar_width and elementborderwidth

			on_fontchange	function, used in change_font()
							and checkbutton_command(). It is executed after
							change on any item in fontlist. It should return True or False depending on
							how good the results were. If return False, old values are restored for that font
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

		# Set font of dropdown button
		self.optionmenu.config(font=('TkDefaultFont',10))

		# Set font of dropdown items
		self.menu = self.topframe.nametowidget(self.optionmenu.menuname)
		self.menu.config(font=('TkDefaultFont',10))

		# Optionmenu contains font-instances to be configured
		self.optionmenu.pack(side=tkinter.LEFT)

		# This button toggles font-size of fontchooser widgets between big and small size
		# It can be used if size is too small or too big
		self.button = tkinter.Button(self.topframe, text='SMALL', command=self.button_command)
		self.button.pack()
		self.scrollbar = tkinter.Scrollbar(self.topframe)


		# Listbox contains font-choises to select from
		self.lb = tkinter.Listbox(self.topframe, font=('TkDefaultFont', 10),
								selectmode='single', width=40,
								yscrollcommand=self.scrollbar.set)
		self.lb.pack(pady=10, side='left')
		self.scrollbar.pack(side='left', fill='y')

		self.scrollbar.config(width=self.scrollbar_width,
							elementborderwidth=self.elementborderwidth, command=self.lb.yview)


		# Spinbox sets font size
		self.sb = tkinter.Spinbox(self.topframe, font=('TkDefaultFont', 10), from_=self.min,
								to=self.max, increment=1, width=3, command=lambda kwargs={'widget':'spinbox'}: self.change_font(**kwargs))
		self.sb.pack(pady=10, anchor='w')


		# Make checkboxes for other font configurations
		self.bold = tkinter.StringVar()
		self.cb1 = tkinter.Checkbutton(self.topframe, font=('TkDefaultFont', 10),
									offvalue='normal', onvalue='bold', text='Bold',
									variable=self.bold)
		self.cb1.pack(pady=10, anchor='w')
		self.cb1.config(command=lambda args=[self.bold, 'weight']: self.checkbutton_command(args) )

		#######

		self.ital = tkinter.StringVar()
		self.cb2 = tkinter.Checkbutton(self.topframe, font=('TkDefaultFont', 10),
									offvalue='roman', onvalue='italic', text='Italic',
									variable=self.ital)
		self.cb2.pack(pady=10, anchor='w')
		self.cb2.config(command=lambda args=[self.ital, 'slant']: self.checkbutton_command(args) )

		# End of checkboxes #####


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
		self.cb2.deselect()
		self.cb5.deselect()

		if self.font['weight'] == 'bold': self.cb1.select()

		self.lb.bind('<ButtonRelease-1>', self.change_font)


		# Increase font-size
		if big:
			self.button_command()


		self.fontnames = list()
		self.fontnames_mono = list()

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
					self.cb2,
					self.cb5
					]

		text, size = 'BIG', 20
		if self.button['text'] == 'BIG': text, size = 'SMALL', 10

		self.button['text'] = text

		for widget in widgetlist: widget.config(font=('TkDefaultFont', size))


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
			# Next line sets "index of listbox insertion cursor",
			# cursor theme is for example: dotbox
			self.top.after(100, lambda args=[fontindex]: self.lb.activate(args))
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

		old_value = self.font[key]
		self.font[key] = var.get()
		new_value = var.get()

		if self.on_fontchange:
			# Enable canceling unwanted changes
			try:
				if not self.on_fontchange(fontname=self.font.name):

					# cb reset
					cb = self.cb1
					if var == self.ital:
						cb = self.cb2
					cb.deselect()

					#self.wait_for(300)

					if old_value == cb['onvalue']:
						self.cb.select()

			except Exception as e:
				print(e)


	def optionmenu_command(self, event=None):
		'''	When font(instance) is selected from optionmenu.
		'''
		self.font = tkinter.font.nametofont(self.var.get())
		self.update_fontlistbox()


		self.sb.delete(0, 'end')
		fontsize = self.font['size']
		self.sb.insert(0, fontsize)

		self.cb1.deselect()
		self.cb2.deselect()

		if self.font['weight'] == 'bold': self.cb1.select()
		if self.font['slant'] == 'italic': self.cb2.select()


	def get_max_size_of(self):
		''' compared to textfont
		'''
		textfont = False
		for font in self.fonts:
			if font.name == 'textfont':
				textfont = font


		sizetextfont = textfont.cget('size')
		size = self.font.cget('size')

		linespace_textfont = textfont.metrics()['linespace']
		linespace_otherfont = self.font.metrics()['linespace']
		diff = linespace_textfont - linespace_otherfont

		# textfont is currently bigger
		if diff > 0:
			while diff > 0:
				size += 1
				self.font.config(size=size)
				linespace_otherfont = self.font.metrics()['linespace']
				diff = linespace_textfont - linespace_otherfont

			# It could be one off
			while diff < 0:
				size -= 1
				self.font.config(size=size)
				linespace_otherfont = self.font.metrics()['linespace']
				diff = linespace_textfont - linespace_otherfont

		# textfont is currently smaller
		elif diff < 0:
			while diff < 0:
				size -= 1
				self.font.config(size=size)
				linespace_otherfont = self.font.metrics()['linespace']
				diff = linespace_textfont - linespace_otherfont

		return size


	def change_font(self, event=None, widget=None):
		'''	Change values of current font-instance.
		'''

		l = None
		l = self.lb.curselection()

		old_family = self.font['family']
		old_size = self.font['size']
		flag_only_size = False


		if widget == 'spinbox':
			flag_only_size = True
			self.font.config(
				size=self.sb.get()
				)

		# Changing fontfamily
		else:
			f = self.lb.get(l)

			self.font.config(family=f)

			# Set initially to maxsize
			if self.font.name in ['linenum_font', 'keyword_font']:
				maxsize = self.get_max_size_of()
				self.font.config(size=maxsize)
				self.sb.delete(0, 'end')
				self.sb.insert(0, maxsize)
			else:
				self.font.config( size=self.sb.get() )



		if self.on_fontchange:

			# Enable canceling unwanted changes
			if not self.on_fontchange(fontname=self.font.name):

				if flag_only_size:
					self.font.config(size=old_size)
					self.wait_for(200)

					# sb reset
					self.sb.delete(0, 'end')
					self.sb.insert(0, old_size)

				else:
					self.font.config(
						family=old_family,
						size=old_size
						)
					self.wait_for(200)

					# sb reset
					self.sb.delete(0, 'end')
					self.sb.insert(0, old_size)

					# lb reset
					self.update_fontlistbox()
##					self.top.selection_clear()
##
##					# Show current fontname in listbox
##					fontname = self.font.actual("family")
##					fontindex = self.fontnames.index(fontname)
##					self.top.after(100, lambda args=[fontindex]: self.lb.select_set(args))
##					self.top.after(300, lambda args=[fontindex]: self.lb.see(args))

					### change_font End ########


	def wait_for(self, ms):
		self.waitvar.set(False)
		self.top.after(ms, self.waiter)
		self.top.wait_variable(self.waitvar)


	def waiter(self):
		self.waitvar.set(True)


	def get_fonts(self):

		font = tkinter.font.Font(family='TkDefaultFont', size=12)

		def font_is_vertical(f):
			return f[0] == '@'


		fontnames = [f for f in tkinter.font.families() if not font_is_vertical(f)]

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
















