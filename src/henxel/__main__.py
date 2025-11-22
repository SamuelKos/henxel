import sys
from .__init__ import Editor


Editor.in_mainloop = True


debug = False

try:
	first_arg = sys.argv[1]
	if first_arg == '--debug':
		debug = True
		print('starting debug mode')
##	else:
##		print('opening file:', first_arg)

except IndexError:
	pass

##if len(sys.argv) > 1:
##	second_arg = sys.argv[2]
##	print('opening file:', second_arg)



e=Editor(debug=debug)

# --> also self.in_mainloop==True now in Editor.__init__()
# (which is in henxel/__init__.py)
# --> can use this in checks: if self.in_mainloop: do_something()
#print(e.in_mainloop)

e.mainloop()
