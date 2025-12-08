''' Pass info to henxel-module that must be available at import time.

https://stackoverflow.com/questions/3720740/pass-variable-on-import/39360070#39360070


Example usage:
1: Build flags that need to be build:
   o=MyObject()
   data=get_mydata()

2: Put flags to dict:

   d=dict(LAUNCH=True, VISIBLE=False, MYSTRING='hello', MYOBJECT=o, MYDATA=data)

3: Import placeholder module, that is this module, so that henxel-module
   ges refence to flags:

   import importflags

4: Insert flags to importflags:

   importflags.FLAGS=d

5: import henxel

Now, henxel-module has access everything in dict d at import-time!
It means one can modify the structure of a class or a function
depending on flags.

Example use in module henxel with MyClass and my_func:
	import somemodule
	import importflags
	FLAGS = importflags.FLAGS

	do something with or without flags at import time


	class MyClass:
		object = None
		if FLAGS: object = FLAGS['MYOBJECT']

		do something with or without flags etc at import time

		def __init__(self):
			self.object = self.__class__.object
			if self.object: do something with object at runtime

			do something else with or without flags at runtime


	def my_func(arg1=None, arg2=None):

		if FLAGS:
			data = FLAGS['MYDATA']
			string = FLAGS['MYSTRING']
			visible = FLAGS['VISIBLE']
			launch = FLAGS['LAUNCH']
			do something with data and string and flags

		do something else with or without flags etc


Currently this is used in debugging, test-launching Editor
and for passing data to other modules
'''

FLAGS = False
PRINTER = {'default':1, 'fixed':2, 'current':3}
IN_MAINLOOP = False

































