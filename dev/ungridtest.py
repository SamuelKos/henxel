
# Run: python3 name_of_this_file.py

# Demonstrates switching between two text-widgets
# Control-l 	(as lemon) to switch

# Switch is no more blinky, because background color of toplevel widget
# is set to same color of text-widget. Scrollbar still flashes but
# this should be fine.


import tkinter
import tkinter.font



class Ed(tkinter.Toplevel):


	def __init__(self):
		self.root = tkinter.Tk()
		self.root.withdraw()
		super().__init__(self.root)
		self.protocol("WM_DELETE_WINDOW", self.quit_me)

		self.rowconfigure(1, weight=1)
		self.columnconfigure(1, weight=1)

		self.btn_test=tkinter.Button(self, text='Test')
		self.btn_test.grid(row=0, column = 0, sticky='we')

		self.entry = tkinter.Entry(self)
		self.entry.grid(row=0, column = 1, sticky='nswe')

		self.btn_open=tkinter.Button(self, text='Open')
		self.btn_save=tkinter.Button(self, text='Save')
		self.btn_open.grid(row=0, column = 2)
		self.btn_save.grid(row=0, column = 3, sticky='e')

		self.lb = tkinter.Text(self, width=5, padx=10)
		self.lb.grid(row=1, column = 0, sticky='nsw')

		self.t1 = tkinter.Text(self, blockcursor=True, undo=True, maxundo=-1, autoseparators=True, tabstyle='wordprocessor')

		self.t2 = tkinter.Text(self, blockcursor=True, undo=True, maxundo=-1, autoseparators=True, tabstyle='wordprocessor')
		self.contents = self.t1

		self.t1.bind('<Control-l>', self.f1)
		self.t2.bind('<Control-l>', self.f2)

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

		self.fgcolor = r'#D3D7CF'
		self.bgcolor = r'#000000'
		self.config(bg=self.bgcolor)

		self.t1.config(font=self.font, foreground=self.fgcolor,
				background=self.bgcolor, insertbackground=self.fgcolor)

		self.t2.config(font=self.font, foreground=self.fgcolor,
				background=self.bgcolor, insertbackground=self.fgcolor)

		self.t1.config(font=self.font)
		self.t2.config(font=self.font)

		self.entry.config(font=self.font)
		self.btn_open.config(font=self.font)
		self.btn_save.config(font=self.font)
		self.btn_test.config(font=self.font)
		self.lb.config(font=self.font, state='disabled')

		# Make scrolling work
		self.scrollbar['command'] = self.contents.yview
		self.t1['yscrollcommand'] = self.scrollbar.set
		self.t2['yscrollcommand'] = self.scrollbar.set

		noOfLines = 500
		s = 'line ................................... %s'
		s = '\n'.join( s%i for i in range(1, noOfLines+1) )

		self.contents.insert(tkinter.END, s)


	def quit_me(self, event=None):
		self.quit()
		self.destroy()


	def f1(self, event=None):

		self.scrollbar.config(command='')

		self.contents.grid_forget()
		self.contents = self.t2

		self.scrollbar.config(command=self.contents.yview)
		self.scrollbar.set(*self.contents.yview())

		self.contents.grid(row=1, column=1, columnspan=3, sticky='nswe')
		self.scrollbar.grid(row=1,column=3, sticky='nse')

		self.contents.focus_set()
		print('jou1')

		return 'break'


	def f2(self, event=None):

		self.scrollbar.config(command='')

		self.contents.grid_forget()
		self.contents = self.t1

		self.scrollbar.config(command=self.contents.yview)
		self.scrollbar.set(*self.contents.yview())

		self.contents.grid(row=1, column=1, columnspan=3, sticky='nswe')
		self.scrollbar.grid(row=1,column=3, sticky='nse')

		self.contents.focus_set()
		print('jou2')

		return 'break'



t=Ed()
t.mainloop()
