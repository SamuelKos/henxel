import functools
import importflags

def fix_print(func):
	"""Decorator to use the current printer from importflags"""
	@functools.wraps(func)
	def wrapper_print(*args, **kwargs):
		printer = importflags.PRINTER['current']
		printer(*args, **kwargs)
	return wrapper_print

# Apply decorator at module level
@fix_print
def print(*args, **kwargs):
	return
