import traceback
import builtins
import os


# Not used, but left as notes
##def get_normal_printer():
##
##	def print(*args, **kwargs):
##		builtins.print(*args, **kwargs)
##		return
##
##	return print


def get_fixed_printer():

	def print(*args, **kwargs):
		# Most of all below is about wrapping long lines
		width_prompt = 4
		width_screen = os.get_terminal_size()[0]
		width_screen_startline = width_screen - width_prompt

		# Join arguments to one string
		total = ''
		for arg in args:
			total += str(arg) + ' '

		total = total[:-1].replace('\t', 4*' ')
		total_as_list = total.splitlines()


		def handle_overlong(tmp, width=80):
			''' Arrange wordwrap on line tmp

				tmp string	to be wrapped

				width int	of terminal
			'''
			# Note, this is called when tmp is over width chars
			tmp = tmp[:width]
			idx = width

			try:
				idx = tmp.rindex(' ')
				tmp = tmp[:idx].rstrip()
				idx = len(tmp)

			# rindex, no spaces in string
			except ValueError: pass

			return tmp, idx



		if len(total_as_list) == 0:
			builtins.print('', end=chr(13)+chr(10), **kwargs)
			return


		#############
		# Real start
		print_lines = list()


		# Explanation of below: iter over lines in total_as_list
		# if len(line) > width_screen: split line to multiple lines
		firstline = total_as_list[0]

		# Handle prompt-line
		if len(firstline) > width_screen_startline:
			tmp, idx = handle_overlong(firstline, width_screen_startline)

			print_lines.append(tmp)
			firstline = firstline[idx:].lstrip()

			while len(firstline) > width_screen:
				tmp, idx = handle_overlong(firstline, width_screen)

				print_lines.append(tmp)
				firstline = firstline[idx:].lstrip()

			print_lines.append(firstline)
		else: print_lines.append(firstline)


		if len(total_as_list) > 1:
			for i in range(1, len(total_as_list)):
				nextline = total_as_list[i]

				# Handle rest lines
				while len(nextline) > width_screen:
					tmp, idx = handle_overlong(nextline, width_screen)

					print_lines.append(tmp)
					nextline = nextline[idx:].lstrip()

				print_lines.append(nextline)


		# Aand print
		for line in print_lines: builtins.print(line, end=chr(13)+chr(10), **kwargs)

		return


	return print
















