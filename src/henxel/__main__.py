import sys
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



e=Editor(debug=debug)

# --> also self.in_mainloop==True now in Editor.__init__()
# (which is in henxel/__init__.py)
# --> can use this in checks: if self.in_mainloop: do_something()

e.mainloop()








