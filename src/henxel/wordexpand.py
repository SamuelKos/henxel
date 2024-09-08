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


		patt = r'regexp -all -line -inline {\m%s[[:alnum:]_.]+} [%s get 1.0 {insert wordstart}]' \
				% (word, self.tcl_name_of_contents)
				
		wbefore = self.textwid.tk.eval(patt).split()
		
		patt = r'regexp -all -line -inline {\m%s[[:alnum:]_.]+} [%s get {insert wordend} end]' \
				% (word, self.tcl_name_of_contents)
				
		wafter = self.textwid.tk.eval(patt).split()
		
		
		
		words = []
		dictionary = {}
		
		# Search backwards through words before
		wbefore.reverse()
		for w in wbefore:
			if dictionary.get(w):
				continue
				
			words.append(w)
			dictionary[w] = w

		# Search onwards through words after
		for w in wafter:
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
		
		
		for i in range(len(tmp)-1, -1, -1):
			if tmp[i] not in self.wordchars:
				break
		
		# Reached linestart --> Tabbing at __main__() (indent0)
		else: return tmp
		
		# +1: Strip the char that was not in self.wordchars
		return tmp[i+1:]


















