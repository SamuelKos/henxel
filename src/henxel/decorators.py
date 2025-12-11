import traceback
import functools
import time


# Update printer, when necessary, Begin
# Get reference to printer set in henxel/__init__.py
import importflags

# With this arrangement there is no need to do anything else,
# in this file, to actual code-lines which has print-calls.
# Printer is always the same than user selected in editor-session.

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
			# Apply possible printer fix to traceback
			tb = traceback.format_exception(err)
			for line in tb: print(line)


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



















