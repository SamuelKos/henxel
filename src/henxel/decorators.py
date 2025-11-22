import functools
import time

# Update printer, when necessary, Begin
# Get reference to printer set in henxel/__init__.py
import importflags

#ORIGINAL_PRINTER = print

# With this arrangement there is no need to do anything else,
# in this file, to actual code-lines which has print-calls.
# Printer is always the same than user selected in editor-session.

# Note: this slows printing, better would be if this could be iffed away
# when in mainloop, also in other modules
def fix_print(func):
	@functools.wraps(func)
	def wrapper_print(*args, **kwargs):
		printer = importflags.PRINTER['current']
		printer(*args, **kwargs)
	return wrapper_print


# Originally uses just these three lines below, but if need dynamic defining,
# there is use_fixed_printer() and reset_printer() below.
# However, printing seems to work just fine now without those.
global print
@fix_print
def print(*args, **kwargs): return


##def use_fixed_printer():
##	global print
##	@fix_print
##	def print(*args, **kwargs): return
##
##def reset_printer():
##	global print
##	print = ORIGINAL_PRINTER

# Update printer, when necessary, End



# Most of this is taken from realpython-page about decorations

def do_twice(func):
	@functools.wraps(func)
	def wrapper_do_twice(*args, **kwargs):
		func(*args, **kwargs)
		return func(*args, **kwargs)
	return wrapper_do_twice


def timer(func):
	''' Print the runtime of the decorated function
	'''
	@functools.wraps(func)
	def wrapper_timer(*args, **kwargs):
		start_time = time.perf_counter()
		value = func(*args, **kwargs)
		end_time = time.perf_counter()
		run_time = end_time - start_time
		print(f"Finished {func.__name__}() in {run_time:.4f} secs")
		return value
	return wrapper_timer


def debug(func):
	''' Print the function signature and return value.
		Also handles uncatched/raised errors.
	'''
	@functools.wraps(func)
	def wrapper_debug(*args, **kwargs):
		args_repr = [repr(a) for a in args]
		kwargs_repr = [f"{k}={repr(v)}" for k, v in kwargs.items()]
		signature = ", ".join(args_repr + kwargs_repr)

		print(f"Calling {func.__name__}({signature})")
		try:
			value = func(*args, **kwargs)
			print(f"{func.__name__}() returned {repr(value)}")
			return value

		except Exception as err:
			# See: __init__.py: Editor.debug_always_use_own_error_handler
			if not importflags.debug_use_own_error_handler:
				# Get original traceback when in mainloop
				if importflags.IN_MAINLOOP: raise err


			errors = list()
			errors.append(err)
			cur_err = err

			# Get whole error-chain
			while cur_err.__context__ is not None:
				cur_err = cur_err.__context__
				errors.append(cur_err)


			print('\nTraceback (most recent call last):')
			error = errors.pop()

			# Parse errors
			while error:

				tb = error.__traceback__
				while tb is not None:

					e = str(tb.tb_frame)

					# Get actual start
					idx = e.index(', ') + 2
					e = e[idx:]

					# file --> File
					e0 = e[0].capitalize()

					# -1: Remove trailing '>'
					e = e[1:-1]

					# Add '()' to indicate scope and
					# indent of one spaces
					e = ' ' + e0 + e + '()'

					# Put scope in own line
					e = e.replace(', code', '\n\tin')

					print(e)
					tb = tb.tb_next

				print( type(error).__name__ +': '+ error.__str__() )

				try:
					# Get next error from chain
					error = errors.pop()
					print('\nDuring handling of the above exception, another exception occurred:')

				except IndexError:
					error = None


	return wrapper_debug


### boilerplate
##def decorator(func):
##	@functools.wraps(func)
##	def wrapper_decorator(*args, **kwargs):
##		# Do something before
##		value = func(*args, **kwargs)
##		# Do something after
##		return value
##	return wrapper_decorator




