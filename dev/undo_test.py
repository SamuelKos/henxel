import tkinter as tk

# paste 6 letters
# enter 3 letters
# paste 6 letters

# delete 3 letters in middle
# undo
# redo
# undo 
# redo

class MyText(tk.Text):

	def __init__(self, master=None, **kw):
		tk.Text.__init__(self, master, undo=False, **kw)
		
		self._undo_stack = []
		self._redo_stack = []
		self.flag_separators = True
		self.max_action_count = 10
		
		# do not touch this
		self._undo_separator = tuple(( (0,0),(0,0) ))
		
		# create proxy
		self._orig = self._w + "_orig"
		self.tk.call("rename", self._w, self._orig)
		self.tk.createcommand(self._w, self._proxy)


	def _proxy(self, *args):
		if args[0] in ["insert", "delete"]:
			
			index = self.index(args[1])
			
			if args[0] == "insert":
				undo_args = ("delete", index, "{}+{}c".format(index, len(args[2])))
				
				# Is not 'insert' only in return_override() and do_single_replace()
				# This also clears possible (unwanted) tags away from undo-stack: args[3]
				if args[1] == 'insert':
					print('insert')
					a0 = args[0]
					a1 = self.index(args[1])
					a2 = args[2]
					args = (a0,a1,a2)
					
			else:
				# deleted selection
				# fix insert when has selection:
				if 'sel.first' in args:
					a0 = args[0]
					a1 = self.index(args[1])
					a2 = self.index(args[2])
					args = (a0,a1,a2)
					
				# pressed backspace
				# fix 'insert-1c' as index:
				elif 'insert-1c' in args:
					a0 = args[0]
					a1 = self.index(args[1])
					args = (a0,a1)
				
	
				undo_args = ("insert", index, self.get(*args[1:]))
			
			self._redo_stack.clear()
			self._undo_stack.append((undo_args, args))
			
			
		result = self.tk.call((self._orig,) + args)
		return result



	def undo(self):
		if not self._undo_stack:
			return
		
		undo_args, redo_args = self._undo_stack.pop()
		self._redo_stack.append((undo_args, redo_args))
		
		print('pressed undo ', undo_args, redo_args)
			
		self.tk.call((self._orig,) + undo_args)
		
		# update cursor pos
		if undo_args[0] == 'insert':
			pos = f"{undo_args[1]}+{len(undo_args[2])}c"
		else:
			pos = undo_args[1]
			
		self.mark_set( 'insert', pos )
		

	def redo(self):
		if not self._redo_stack:
			return
		
		undo_args, redo_args = self._redo_stack.pop()
		self._undo_stack.append((undo_args, redo_args))
		
		print('pressed redo', undo_args, redo_args)
		
		self.tk.call((self._orig,) + redo_args)
		
		# update cursor pos
		if redo_args[0] == 'insert':
			pos = f"{redo_args[1]}+{len(redo_args[2])}c"
		else:
			pos = redo_args[1]
			
		self.mark_set( 'insert', pos )





root = tk.Tk()

text = MyText(root, width=65, height=20, font="consolas 14")
text.pack()

undo_button = tk.Button(root, text="Undo", command=text.undo)
undo_button.pack()

redo_button = tk.Button(root, text="Redo", command=text.redo)
redo_button.pack()

text.focus_set()


root.mainloop()

