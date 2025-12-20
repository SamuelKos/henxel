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

##	Explanation of error mentioned in __init__.py in get_scope_path
##	search this here:
##	editor.

# Related line in get_scope_path:
# pos = self.text_widget.tag_prevrange('strings', pos)[0] + ' linestart'



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



class ExpandWord:
	wordchars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.'
	# string.ascii_letters + string.digits + "_" + "."


	def __init__(self, editor):
		# text_widget is tkinter.Text -widget
		self.text_widget = None
		self.flag_unique = False
		self.state = None
		self.editor = editor
		self.stub = ''
		self.stub_has_dot = False
		self.flag_scope_separator = False
		self.scope_separator = 28 * '~'
		self.no_words = False, False, None, False


	def expand_word(self, event=None, back=False):
		''' Replace the current word with the next expansion.
		'''

		curinsert = event.widget.index("insert")
		curline = event.widget.get("insert linestart", "insert lineend")


		def filter_words(word_list):

			self.stub = word_list.pop()
			if len(word_list) == 1:
				self.flag_unique = True


			words_to_be_returned = list()

			all_matches_are_in_cur_scope = False
			try:
				idx_sep = word_list.index(self.scope_separator)
			except ValueError:
				all_matches_are_in_cur_scope = True


			self.stub_has_dot = False
			if '.' in self.stub:
				self.stub_has_dot = idx_dot = self.stub.rindex('.')

				if all_matches_are_in_cur_scope:
					for i in range(0, len(word_list)):
						words_to_be_returned.append(word_list[i][idx_dot:])
				else:
					for i in range(0, idx_sep):
						words_to_be_returned.append(word_list[i][idx_dot:])

					words_to_be_returned.append(self.scope_separator)

					for i in range(idx_sep+1, len(word_list)):
						words_to_be_returned.append(word_list[i][idx_dot:])


			else:
				patt = self.stub + '.'

				if all_matches_are_in_cur_scope:
					for item in word_list:
						if not item.startswith(patt):
							words_to_be_returned.append(item)
				else:
					for i in range(0, idx_sep):
						item = word_list[i]
						if not item.startswith(patt):
							words_to_be_returned.append(item)

					words_to_be_returned.append(self.scope_separator)

					for i in range(idx_sep+1, len(word_list)):
						item = word_list[i]
						if not item.startswith(patt):
							words_to_be_returned.append(item)


			return words_to_be_returned



		update_completions = False


		# Tab changed
		if event.widget != self.text_widget:
			self.text_widget = event.widget
			self.tcl_name_of_contents = str( self.text_widget.nametowidget(self.text_widget) )

			update_completions = True
			self.flag_unique = False
			word_list = self.getwords()

			# Not sure if this first check is necessary
			if not word_list: return self.no_words
			words = filter_words(word_list)
			if not words: return self.no_words

			index = -1


		else:
			words, index, insert, line = self.state
			# Something else changed
			if insert != curinsert or line != curline:

				update_completions = True
				self.flag_unique = False
				word_list = self.getwords()

				# Not sure if this first check is necessary
				if not word_list: return self.no_words
				words = filter_words(word_list)
				if not words: return self.no_words

				index = -1



		word = self.getprevword()



		if back:
			index -= 1
			# Wrap to end
			if index == -2: index = len(words) -1

		else:
			index += 1
			# Wrap to start
			if index == len(words): index = -1

		newword = words[index]
		if index == -1 and not update_completions:
			newword = self.stub


		pos = index

		if newword == self.scope_separator:
			self.flag_scope_separator = True
		else:
			self.flag_scope_separator = False

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

##		.someword1
##		.someword2
##		.someword3
##		# Note: this wont expand to those above
##		.some


		if not self.flag_scope_separator:

			# First remove old completion
			if self.stub_has_dot:
				dots = self.stub_has_dot

				# 'rstrip' to first dot (-1c) when starting completion
				if index == 0 and update_completions:
					tail = len(self.stub) - dots
					self.text_widget.delete("insert -%d chars" % tail, "insert")

				# wrapped back to stub
				elif newword == self.stub:
					self.text_widget.delete("insert -%d chars" % len(word), "insert")

				# must 'add' head of stub because of not so wise self.getprevword()
				else:
					self.text_widget.delete("insert -%d chars +%d chars" % (len(word), dots), "insert")

			else:
				self.text_widget.delete("insert -%d chars" % len(word), "insert")

			# Then add newword/completion
			self.text_widget.insert("insert", newword)


		curinsert = self.text_widget.index("insert")
		curline = self.text_widget.get("insert linestart", "insert lineend")
		self.state = words, index, curinsert, curline


		if self.flag_unique: pos = 'unique'
		if update_completions:
			return self.stub, words, pos, newword
		else:
			return False, False, pos, False


	def getwords(self):
		''' Return a list of words that match the prefix before the cursor.

			These methods of Editor are being used:
				get_scope_start()
				get_scope_end()
				can_do_syntax()

		'''

		all_words = False
		word = self.getprevword()
		#print(word)
		words = []

		if not word: return words


		word_with_escaped_dots = word.replace('.', '\\.')

		patt_end = ' get %s %s]'
		patt_start = r'regexp -all -line -inline {\m%s[[:alnum:]_.]+} [%s' \
				% (word_with_escaped_dots, self.tcl_name_of_contents)


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
				all_words.append(self.scope_separator)
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


		# Remove trailing separator
		if self.scope_separator in words:
			if len(words) == 1 or words.index(self.scope_separator) == len(words) -1:
				words.remove(self.scope_separator)

		# Add stub
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




