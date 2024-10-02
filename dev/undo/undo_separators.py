# Run: python3 name_of_this_file.py

# First check undo_no_separators.py
# Then return

import tkinter



##	Pseudo-code related to undo-stack handling in _proxy() in undo_separator_test.py
##
##	0: Empty or not empty undo and redo stacks
##
##	1: User made action  == insert or delete
##
##	2: need_separators() makes a decision: if action is such,
##		that needs to be separated in undo-stack:
##
##
##	These kind of series of actions (like from indent() ) needs to be separated as a whole,
##	no separators in between. So need a flag to know when not to put separators.
##
##	But there can, and will be situations where this kind of functions makes calls to other
##	such functions which set this flag by themselves. This is why need to know who made the
##	initial flag-setting. This is solved by making flag a tuple. But that alone is not
##	enough. There must be can_add_separator() -function:
##
##	Initial setting in __init__:
##		flag_separators = (True, None)
##
##
##	def can_add_separator( from_who ):
##
##		if flag_separators[0] == True:
##			flag_separators = (False, from_who)
##
##		else:
##			if flag_separators[1] == from_who:
##				flag_separators = (True, None)
##
##
##	Example:
##	User makes action, such that sets this flag, like replace_all():
##		can_add_separator('replace_all') --> flag_separators = (False, 'replace_all')
##
##	replace_all calls do_single_replace which also calls can_add_separator:
##		can_add_separator('replace') --> flag_separators stays the same, because caller is not original.
##
##
##	###### Pseudo-code End



class UndoText(tkinter.Text):

	def __init__(self, master=None, **kw):
		tkinter.Text.__init__(self, master, undo=False, **kw)

		# These need to change when view changes:
		self._undo_stack = []
		self._redo_stack = []
		self.action_count = 0
		self.is_modified = False

		self.flag_separators = (True, None)
		self.max_action_count = 8

		# Do _not_ touch this
		self._undo_separator = tuple(( (0,0),(0,0) ))

		# Create proxy
		self._orig = self._w + "_orig"
		self.tk.call("rename", self._w, self._orig)
		self.tk.createcommand(self._w, self._proxy)


	def can_add_separator(self, from_who):
		'''	from_who is string, naming the caller
		'''

		if self.flag_separators[0] == True:
			self.flag_separators = (False, from_who)

		else:
			if self.flag_separators[1] == from_who:
				self.flag_separators = (True, None)


	def action_is_important(self, *args):
		''' Should one put separator before this one letter insert- or delete-action
		'''

		# There already is separator
		if self._undo_stack[-1][0][0] == 0:
			return False

		line, col = map( int, self.index(args[1]).split('.') )
		lastline, lastcol = map( int, self._undo_stack[-1][1][1].split('.') )

		# Action is on different line than previous one letter action
		if line != lastline:
			return True

		# Action is in the same line than previous action
		else:
			# But it is not the same type
			if self._undo_stack[-1][1][0] != args[0]:
				return True

			# Same type but not near last action
			elif col not in [ lastcol-1, lastcol, lastcol+1 ]:
				return True

			# Action is near last action and it is the same type
			else:
				return False


	def action_is_long(self, *args):

		if args[0] == "insert":
			if len(args[2]) > 1:
				return True
			else:
				return False

		# Delete
		else:
			if 'sel.first' in args:
				return True
			else:
				return False


	def put_separator(self, start=None, end=None):

		if self.flag_separators[0] == True:

			if start and self._undo_stack[-1][0][0] != 0:
				self._undo_stack.append(self._undo_separator)

			if end:
				self._undo_stack.append(self._undo_separator)


	def need_separators(self, *args):
		''' Does action need separators
		'''
		need_separator_in_start = False
		need_separator_in_end = False


		if len(self._undo_stack) == 0:
			self.action_count = 0

			if self.action_is_long(*args):
				need_separator_in_end = True

			else:
				self.action_count += 1


		# Action lenght > 1:
		elif self.action_is_long(*args):

			need_separator_in_start = True
			need_separator_in_end = True
			self.action_count = 0


		elif self.action_is_important(*args):
			# Action is one letter lenght but needs to be separated from previous action
			need_separator_in_start = True
			self.action_count = 0


		else:
			# Want to collect more actions
			self.action_count += 1

			if self.action_count > self.max_action_count:
				need_separator_in_end = True
				self.action_count = 0


		return need_separator_in_start, need_separator_in_end


	def _proxy(self, *args):

		if args[0] in ["insert", "delete"]:

			############################### Build undo-action begin

			need_separator_in_start, need_separator_in_end = self.need_separators(*args)
			index = self.index(args[1])

			if args[0] == "insert":
				undo_args = ("delete", index, "{}+{}c".format(index, len(args[2])))

				# Is not 'insert' only in return_override() and do_single_replace()
				# This also clears possible (unwanted) tags away from undo-stack: args[3]
				if args[1] == 'insert':
					a0 = args[0]
					a1 = self.index(args[1])
					a2 = args[2]
					args = (a0,a1,a2)

			else:
				# Deleted selection
				# Fix insert when has selection:
				if 'sel.first' in args:
					a0 = args[0]
					a1 = self.index(args[1])
					a2 = self.index(args[2])
					args = (a0,a1,a2)

				# Pressed backspace
				# Fix 'insert-1c' as index:
				elif 'insert-1c' in args:
					a0 = args[0]
					a1 = self.index(args[1])
					args = (a0,a1)


				undo_args = ("insert", index, self.get(*args[1:]))

			############################### Build undo-action end
			############################### Put action to undo_stack begin

			self._redo_stack.clear()
			self.is_modified = True

			self.put_separator(start = need_separator_in_start)
			self._undo_stack.append((undo_args, args))
			self.put_separator(end = need_separator_in_end)

			############################### Put action to undo_stack end


		# Back to normal action handling
		result = self.tk.call((self._orig,) + args)
		return result


	def undo_clear(self):

		self._undo_stack.clear()
		self._redo_stack.clear()
		self.action_count = 0
		self.is_modified = False


	def undo(self, event=None):
		# Info:
		# self._undo_stack[-1][0] == undo_args

		undo_args = (0,0)

		while undo_args[0] == 0:
			if len(self._undo_stack) == 0:
				self.is_modified = False
				return

			undo_args, redo_args = self._undo_stack.pop()

		self._redo_stack.append(self._undo_separator)

		action_list = list()

		while undo_args[0] != 0:
			self._redo_stack.append((undo_args, redo_args))
			action_list.append(undo_args)

			if len(self._undo_stack) == 0:
				self.is_modified = False
				break

			undo_args, redo_args = self._undo_stack.pop()


		# Check if undo-stack is efectively empty, Begin

		if self.is_modified:
			empty = True
			for undo, redo in self._undo_stack:
				if undo[0] != 0:
					empty = False
					break

			if empty:
				self._undo_stack.clear()
				self.is_modified = False
		# Check if undo-stack is efectively empty, End


		self._undo_stack.append(self._undo_separator)

		for action in action_list:
			self.tk.call((self._orig,) + action)

		# Update cursor pos
		if action[0] == 'insert':
			pos = f"{action[1]}+{len(action[2])}c"
		else:
			pos = action[1]

		self.mark_set( 'insert', pos )

		self.action_count = 0
		###### undo End ###################################


	def redo(self, event=None):
		# Info:
		# self._redo_stack[-1][1] == redo_args

		redo_args = (0,0)

		while redo_args[0] == 0:
			if len(self._redo_stack) == 0:
				return

			undo_args, redo_args = self._redo_stack.pop()

		self._undo_stack.append(self._undo_separator)

		action_list = list()

		while redo_args[0] != 0:
			self._undo_stack.append((undo_args, redo_args))
			action_list.append(redo_args)

			if len(self._redo_stack) == 0:
				break

			undo_args, redo_args = self._redo_stack.pop()


		self._redo_stack.append(self._undo_separator)

		for action in action_list:
			self.tk.call((self._orig,) + action)

		self.is_modified = True

		# Update cursor pos
		if action[0] == 'insert':
			pos = f"{action[1]}+{len(action[2])}c"
		else:
			pos = action[1]

		self.mark_set( 'insert', pos )

		self.action_count = 0
		###### redo End ###################################



root = tkinter.Tk()

text = UndoText(root, width=65, height=20, font="consolas 14")
text.pack()

undo_button = tkinter.Button(root, text="Undo", command=text.undo)
undo_button.pack()

redo_button = tkinter.Button(root, text="Redo", command=text.redo)
redo_button.pack()

text.insert(tkinter.END, 10*'1' +'A'+ 10*'1' +'\n')
text.insert(tkinter.END, 10*'2' +'B'+ 10*'2' +'\n')
text.insert(tkinter.END, 10*'3' +'C'+ 10*'3' +'\n')

text.undo_clear()
text.focus_set()


root.mainloop()

