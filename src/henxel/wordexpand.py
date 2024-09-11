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
'''


class ExpandWord:
	wordchars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.'
	# string.ascii_letters + string.digits + "_" + "."


	def __init__(self, textwid):
		''' textwid is tkinter.Text -widget'''

		self.textwid = textwid
		self.bell = self.textwid.bell
		self.state = None


	def expand_word(self):
		''' Replace the current word with the next expansion.
		'''

		curinsert = self.textwid.index("insert")
		curline = self.textwid.get("insert linestart", "insert lineend")

		# if used the very first time:
		if not self.state:
			self.tcl_name_of_contents = str( self.textwid.nametowidget(self.textwid) )
			words = self.getwords()
			index = 0


		else:

			words, index, insert, line = self.state

			if insert != curinsert or line != curline:
				words = self.getwords()
				#print(words)
				index = 0


		if not words:
			self.bell()
			return "break"



		word = self.getprevword()
		newword = words[index]
		index += 1

		# Gone through all words once
		if index == len(words):
			index = 0
			self.bell()

		#print(word, len(word), newword)
		self.textwid.delete("insert - %d chars" % len(word), "insert")
		self.textwid.insert("insert", newword)


		curinsert = self.textwid.index("insert")
		curline = self.textwid.get("insert linestart", "insert lineend")
		self.state = words, index, curinsert, curline

		return "break"


	def getwords(self):
		''' Return a list of words that match the prefix before the cursor.
		'''

		word = self.getprevword()
		if not word:
			return []


		# Next, get words to list all_words
		# First, try to append from current scope, function or class.
		# Second, append from rest of file (or whole file is First fails)
		####################################################################
		patt_start = r'regexp -all -line -inline {\m%s[[:alnum:]_.]+} [%s' \
				% (word, self.tcl_name_of_contents)

		patt_end = ' get %s %s]'

		editor = self.textwid.master

		# On fail, scope_start == '1.0'
		scope_path, ind_curline, scope_start = editor.get_scope_path('insert', flag_only_one=True)

		#print(scope_path, ind_curline, scope_start)
		all_words = False

		if scope_start != '1.0':
			scope_end = editor.get_scope_end(ind_curline)
			#print(scope_end)
			# Up: insert - scope_start == scope_start - insert reversed
			p = patt_start + patt_end % (scope_start, '{insert wordstart}')
			l1 = words_ins_def_up = self.textwid.tk.eval(p).split()
			l1.reverse()

			# Down: insert - scope_end
			p = patt_start + patt_end % ('{insert wordend}', scope_end)
			l2 = words_ins_def_down = self.textwid.tk.eval(p).split()

			# Up: scope_start - filestart == filestart - scope_start reversed
			p = patt_start + patt_end % ('1.0', scope_start)
			l3 = words_def_up_filestart = self.textwid.tk.eval(p).split()
			l3.reverse()

			if scope_end != 'end':
				# Down: scope_end - fileend
				p = patt_start + patt_end % (scope_end, 'end')
				l4 = words_def_down_fileend = self.textwid.tk.eval(p).split()

				all_words = l1 + l2 + l3 + l4

			# Insertion cursor is in last function
			else:
				all_words = l1 + l2 + l3


		# Tabbing at __main__()
		if not all_words:
			p = patt_start + patt_end % ('1.0', '{insert wordstart}')
			l1 = words_ins_filestart = self.textwid.tk.eval(p).split()
			l1.reverse()

			p = patt_start + patt_end % ('{insert wordstart}', 'end')
			l2 = words_ins_filestart = self.textwid.tk.eval(p).split()

			all_words = l1 + l2
		#######################


		words = []
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

		tmp = self.textwid.tk.eval(patt)


		for i in reversed( range(len(tmp)) ):
			if tmp[i] not in self.wordchars:
				break

		# Reached linestart --> Tabbing at __main__() (indent0)
		else: return tmp

		# +1: Strip the char that was not in self.wordchars
		return tmp[i+1:]


















