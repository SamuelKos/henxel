import sys
import traceback
from .__init__ import Editor


Editor.in_mainloop = True


debug = False

try:
	args = sys.argv[1:]
	first_arg = args[0]
	# Note: debug-session in Windows should be started using script
	# found under /dev
	if first_arg == '--debug': debug = True
	# Use one time conf(original conf remains untouched) to enable 'adhoc behaviour' editor
	# like normal editor: python -m henxel filepath1 filepath2
	else: Editor.files_to_be_opened = args

except IndexError: pass


# In theory, could do something with errors raising from Editor.__new__()
# In practise, This can be also init_err when not debugging, and also __new__ is not very big
try:
	e=Editor(debug=debug)
except Exception as new_err:

	if debug:
		traceback.print_exception(new_err)
		# This is used to break debug-restart-loop
		sys.exit(0)
	else:
		raise new_err



# --> also self.in_mainloop==True now in Editor.__init__()
# (which is in henxel/__init__.py)
# --> can use this in checks: if self.in_mainloop: do_something()

e.mainloop()























