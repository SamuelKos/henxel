'''Complete current word before cursor with words in editor.

This file is taken from Python:idlelib -github-page:
https://github.com/python/cpython/tree/3.11/Lib/idlelib/

Each call to expand_word() replaces the word with a
different word with same prefix. Search starts from cursor and
moves towards filestart. It then starts again from cursor and
moves towards fileend. It then returns to original word and
cycle starts again.

Changing current text line or leaving cursor in a different
place before requesting next selection causes ExpandWord to reset
its state.

These methods of Editor are being used in getwords():
	get_scope_start()
	get_scope_end()
	can_do_syntax()

'''


class ExpandWord:
	wordchars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.'
	# string.ascii_letters + string.digits + "_" + "."


	def __init__(self, editor):
		# text_widget is tkinter.Text -widget
		self.text_widget = None
		self.state = None
		self.editor = editor


	def expand_word(self, event=None):
		''' Replace the current word with the next expansion.
		'''

		curinsert = event.widget.index("insert")
		curline = event.widget.get("insert linestart", "insert lineend")


		# Tab changed
		if event.widget != self.text_widget:
			self.text_widget = event.widget
			self.tcl_name_of_contents = str( self.text_widget.nametowidget(self.text_widget) )
			words = self.getwords()
			index = 0


		else:

			words, index, insert, line = self.state

			if insert != curinsert or line != curline:
				words = self.getwords()
				#print(words)
				index = 0


		if not words:
			self.text_widget.bell()
			return "break"



		word = self.getprevword()
		newword = words[index]
		index += 1

		# Gone through all words once
		if index == len(words):
			index = 0
			self.text_widget.bell()


		#######################
		# Test-area
		# Test completion inside this area, at empty line.
		# Insert 's', then press Tab etc.
		# Remove line after test.
		########################
		# s = lkajsd
		# se = aklsjd
		# ranges('sel', asd)
		# asd(self, asd)

		# self.text_widget.delete(as,ads)
		# self.text_widget.insert(as,ads)
		###########################


		#print(word, len(word), newword)
		self.text_widget.delete("insert - %d chars" % len(word), "insert")
		self.text_widget.insert("insert", newword)


		curinsert = self.text_widget.index("insert")
		curline = self.text_widget.get("insert linestart", "insert lineend")
		self.state = words, index, curinsert, curline

		return "break"


	def getwords(self):
		''' Return a list of words that match the prefix before the cursor.

			These methods of Editor are being used:
				get_scope_start()
				get_scope_end()
				can_do_syntax()

		'''

		all_words = False
		word = self.getprevword()
		words = []

		if not word: return words


		patt_end = ' get %s %s]'
		patt_start = r'regexp -all -line -inline {\m%s[[:alnum:]_.]+} [%s' \
				% (word, self.tcl_name_of_contents)


		if self.editor.can_do_syntax():

			# Get atrributes of 'self' faster. For example, if want: self.attribute1,
			# one writes single s-letter and hits Tab, and gets 'self.'
			# Then add 'a' --> prevword is now 'self.a'. Now continue Tabbing:
			# --> self.attribute1 is now likely to appear soon.
			if word in ['s', 'se', 'sel']:
				words.append('self.')

			# Next, get words to list all_words
			# First, try to append from current scope, function or class.
			# Second, append from rest of file (or whole file is First fails)
			####################################################################

			# On fail, scope_start == '1.0'
			scope_line, ind_defline, scope_start = self.editor.get_scope_start()
			scope_end = False
			if scope_line != '__main__()':
				scope_end = self.editor.get_scope_end(ind_defline, scope_start)

			#print(scope_line, ind_defline, scope_start, scope_end)
			l1 = False
			l2 = False
			l3 = False
			l4 = False

			if scope_end:
				# Up: insert - scope_start == scope_start - insert reversed
				p = patt_start + patt_end % (scope_start, '{insert wordstart}')
				l1 = words_ins_def_up = self.text_widget.tk.eval(p).split()
				l1.reverse()

				# Down: insert - scope_end
				p = patt_start + patt_end % ('{insert wordend}', scope_end)
				l2 = words_ins_def_down = self.text_widget.tk.eval(p).split()

				if scope_start != '1.0':
					# Up: scope_start - filestart == filestart - scope_start reversed
					p = patt_start + patt_end % ('1.0', scope_start)
					l3 = words_def_up_filestart = self.text_widget.tk.eval(p).split()
					l3.reverse()

				if scope_end != 'end':
					# Down: scope_end - fileend
					p = patt_start + patt_end % (scope_end, 'end')
					l4 = words_def_down_fileend = self.text_widget.tk.eval(p).split()


				all_words = l1 + l2
				if l3: all_words += l3
				if l4: all_words += l4


		# For example: Tabbing at __main__() or in non py-file
		if not all_words:
			p = patt_start + patt_end % ('1.0', '{insert wordstart}')
			l1 = words_ins_filestart = self.text_widget.tk.eval(p).split()
			l1.reverse()

			p = patt_start + patt_end % ('{insert wordstart}', 'end')
			l2 = words_ins_filestart = self.text_widget.tk.eval(p).split()

			all_words = l1 + l2
		#######################


		dictionary = {}

		for w in all_words:
			if dictionary.get(w):
				continue

			words.append(w)
			dictionary[w] = w

		words.append(word)

		return words


	def getprevword(self):
		''' Return the word prefix before the cursor.
		'''
		patt = r'%s get {insert linestart} insert' \
				% self.tcl_name_of_contents

		tmp = self.text_widget.tk.eval(patt)


		for i in reversed( range(len(tmp)) ):
			if tmp[i] not in self.wordchars:
				break

		# Reached linestart --> Tabbing at __main__() (indent0)
		else: return tmp

		# +1: Strip the char that was not in self.wordchars
		return tmp[i+1:]




