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
		self.curinsert = None
		self.curword = ''
		self.prefix = ''
		self.state = None
		self.editor = editor
		self.stub = ''
		self.stub_has_dot = False
		self.scope_separator = 28 * '~'
		self.no_words = False, False, None, False


	def cancel_completion(self, event=None):

		if not self.state or event.widget != self.text_widget: return False

		#col, ins_as_int = self.editor.get_line_col_as_int()
		curline = event.widget.get("insert linestart", "insert lineend")
		line = self.state[3]
		index = self.state[1]

		if line != curline: return False

		# There already should be stub
		elif index == -1: return False

		# Insertion cursor is allowed to be anywhere in line before cancel, so move it back
		self.text_widget.mark_set('insert', self.curinsert)

		# First remove old completion
		self.text_widget.delete("insert -%d chars" % len(self.curword), "insert")

		# Then add stub
		self.text_widget.insert("insert", self.stub)

		return True


	def expand_word(self, event=None, back=False):
		''' Replace the current word with the next expansion.
		'''

		def handle_words(word_list):

			if len(word_list) == 1:
				self.flag_unique = True


			words_to_be_returned = list()

			all_matches_are_in_cur_scope = False
			try:
				idx_sep = word_list.index(self.scope_separator)
			except ValueError:
				all_matches_are_in_cur_scope = True



			# Below, two cases, stub has dot or not.
			# If all matches are in cur_scope, for loop is normal
			# else, for loop is splitted in half at idx_sep, to possibly save some time
			if '.' in self.stub:

				# Lstrip to last dot for aligning completions with insertion-line, and to save some space
				idx_dot = self.stub_has_dot

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

				if all_matches_are_in_cur_scope:
					words_to_be_returned = word_list[:]
				else:
					for i in range(0, idx_sep):
						item = word_list[i]
						words_to_be_returned.append(item)

					words_to_be_returned.append(self.scope_separator)

					for i in range(idx_sep+1, len(word_list)):
						item = word_list[i]
						words_to_be_returned.append(item)


			return words_to_be_returned


		# Start
		curinsert = event.widget.index("insert")
		line_as_int, ins_as_int = self.editor.get_line_col_as_int()
		curline = event.widget.get("insert linestart", "insert lineend")
		update_completions = False

		# Tab changed. Not self.state: for example, no words at very first attempts
		if event.widget != self.text_widget or not self.state:
			self.text_widget = event.widget
			self.tcl_name_of_contents = str( self.text_widget.nametowidget(self.text_widget) )
			update_completions = True

		else:
			words, index, insert, line = self.state
			# Something else changed
			if insert != curinsert or line != curline:
				update_completions = True


		if update_completions:
			self.flag_unique = False
			self.getprefix(curline, ins_as_int)

			self.curword = self.stub
			# Note: self.prefix is used only in self.getwords
			# Explanation: because self.stub is (possibly) only tail of self.prefix, need additional variable (==self.prefix)
			# to make the actual searching in self.getwords
			# Q: But why self.stub gets stripped(in self.getprefix) when it has dots?
			# A: It simplifies greatly deletion of old completion at the end of this method
			word_list = self.getwords(curline, ins_as_int, self.prefix)

			# Not sure if this first check is necessary
			if not word_list: return self.no_words
			words = handle_words(word_list)
			if not words: return self.no_words

			index = -1



		# Handle index Begin ###
		def next_index(index, words):

			if back:
				index -= 1
				# Wrap from start to end
				if index == -2: index = len(words) -1

			else:
				index += 1
				# Wrap from end to start
				if index == len(words): index = -1

			return index


		index = next_index(index, words)
		newword = words[index]

		# Check for wrap around
		if index == -1:
			newword = self.stub

		# Skip over scope_separator
		if newword == self.scope_separator:
			index = next_index(index, words)
			newword = words[index]

			# Again, check for wrap around (should happen only if separator is first item and going back from item 1 to item 0(==separator))
			if index == -1:
				newword = self.stub


		# Handle index End ###
		pos = index


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

		#print(self.curword, newword)
		# First remove old completion
		self.text_widget.delete("insert -%d chars" % len(self.curword), "insert")

		# Then add newword/completion
		self.text_widget.insert("insert", newword)


		curinsert = self.curinsert = self.text_widget.index("insert")
		curline = self.text_widget.get("insert linestart", "insert lineend")
		self.curword = newword
		self.state = words, index, curinsert, curline


		if self.flag_unique: pos = 'unique'
		if update_completions:
			return self.stub, words, pos, newword
		else:
			return False, False, pos, newword


	def getwords(self, curline, ins_as_int, prefix):
		''' Return a list of words that match the prefix before the cursor.

			These methods of Editor are being used:
				get_scope_start()
				get_scope_end()
				can_do_syntax()

		'''

		all_words = False
		word = prefix
		#print(word)
		words = []

		if not word: return words

		escaped_word = word.replace('.', '\\.')



		# If in middle of string, add one space to fool regexp to treat word as two words split from insert.
		# Word is fixed back to one later at end.
		flag_instring = False
		try:
			if curline[ins_as_int-1] in self.wordchars and curline[ins_as_int] in self.wordchars+'([{':
				flag_instring = True
				self.text_widget.insert('insert', ' ')
				self.text_widget.mark_set('insert', 'insert -1c')
		# Nothing after cursor
		except IndexError: pass


		patt_end = ' get %s %s]'
		patt_start = r'regexp -all -line -inline {\m%s[[:alnum:]_.]+[(]?} [%s' \
				% (escaped_word, self.tcl_name_of_contents)


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
				p = patt_start + patt_end % (scope_start, '{insert lineend}')
				l1 = words_ins_def_up = self.text_widget.tk.eval(p).split()
				l1.reverse()

				# Down: insert - scope_end
				p = patt_start + patt_end % ('{insert lineend}', scope_end)
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
			p = patt_start + patt_end % ('1.0', '{insert lineend}')
			l1 = words_ins_filestart = self.text_widget.tk.eval(p).split()
			l1.reverse()

			p = patt_start + patt_end % ('{insert lineend}', 'end')
			l2 = words_ins_filestart = self.text_widget.tk.eval(p).split()

			all_words = l1 + l2
		#######################



		if flag_instring:
			self.text_widget.delete('insert', 'insert +1c')


		dictionary = {}

		for w in all_words:
			if dictionary.get(w):
				continue

			words.append(w)
			dictionary[w] = w


		# Remove non-sense separators
		if self.scope_separator in words:

			if len(words) == 1: return []

			elif 'self.' in words:
				# Self. and possibly one real match (and separator)
				if len(words) in (2,3):
					words.remove(self.scope_separator)

			# Separator and one match
			elif len(words) == 2:
				words.remove(self.scope_separator)

			elif words[-1] == self.scope_separator: words.pop()


		return words


	def getprefix(self, curline, ins_as_int):
		''' Return the word prefix before the cursor.
		'''

		tmp = curline[:ins_as_int]

		for i in reversed( range(len(tmp)) ):
			if tmp[i] not in self.wordchars:
				break

		# i == 0: word starts at indent0
		# + not: word does not start at indent0
		# tmp[0] in '\t	': line has indent1 of one tab (or one space)
		if not i == 0 or tmp[0] in '	 ':
			# +1: Strip the char that was not in self.wordchars
			tmp = tmp[i+1:]


		# self.prefix is used only in self.getwords
		self.prefix = self.stub = tmp

		self.stub_has_dot = False
		if '.' in self.stub:
			# Lstrip to last dot for aligning completions with insertion-line, and to save some space
			self.stub_has_dot = self.stub.rindex('.')
			self.stub = self.stub[self.stub_has_dot:]

			# Explanation: because self.stub is now only tail of self.prefix, need additional variable (==self.prefix)
			# to make the actual searching in self.getwords
			# Q: But why self.stub gets stripped when it has dots?
			# A: It simplifies greatly deletion of old completion at the end of self.expand_word


















