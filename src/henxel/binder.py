''' Do bindings in henxel.Editor.__init__()
'''


def do_binds(editor_widget):
	''' Do binds for henxel.Editor
	'''
	w = editor_widget
	# Bindigs Begin
	####################################################
	w.right_mousebutton_num = 3

	if w.os_type == 'mac_os':
		w.right_mousebutton_num = 2

		# Default cmd-q does not trigger quit_me
		# Override Cmd-Q:
		# https://www.tcl.tk/man/tcl8.6/TkCmd/tk_mac.html
		w.root.createcommand("tk::mac::Quit", w.quit_me)
		#w.root.createcommand("tk::mac::OnHide", w.test_hide)

	w.contents.bind( "<Button-%i>" % w.right_mousebutton_num, w.raise_popup)

	if w.os_type == 'linux':
		w.contents.bind( "<ISO_Left_Tab>", w.unindent)
	else:
		w.contents.bind( "<Shift-Tab>", w.unindent)


	############################################################
	# In macOS all Alt-shortcuts makes some special symbol.
	# Have to bind to this symbol-name to get Alt-shorcuts work.
	# For example binding to Alt-f:
	# w.contents.bind( "<function>", w.font_choose)

	# Except that tkinter does not give all symbol names, like
	# Alt-x or l
	# which makes these key-combinations quite unbindable.
	# It would be much easier if one could do bindings normally:
	# Alt-SomeKey
	# like in Linux and Windows.

	# Also binding to combinations which has Command-key (apple-key)
	# (or Meta-key as reported by events.py)
	# must use Mod1-Key as modifier name:
	# Mod1-Key-n == Command-Key-n

	# fn-key -bindings have to be done by checking the state of the event
	# in proxy-callback: mac_cmd_overrides

	# In short, In macOS one can not just bind like:
	# Command-n
	# fn-f
	# Alt-f

	# This is the reason why below is some extra
	# and strange looking binding-lines when using macOS.
	##############################################################
	if w.os_type != 'mac_os':

		w.bind( "<Alt-n>", w.new_tab)
		w.bind( "<Control-q>", w.quit_me)

		w.contents.bind( "<Control-b>", w.goto_bookmark)
		w.contents.bind( "<Control-B>",
			lambda event: w.goto_bookmark(event, **{'back':True}) )

		w.contents.bind( "<Control-l>", w.gotoline)
		w.contents.bind( "<Control-g>", w.goto_def)
		w.contents.bind( "<Alt-p>", w.toggle_bookmark)

		w.contents.bind( "<Alt-s>", w.color_choose)
		w.contents.bind( "<Alt-t>", w.toggle_color)

		w.bind( "<Alt-w>", w.walk_tabs)
		w.bind( "<Alt-q>", lambda event: w.walk_tabs(event, **{'back':True}) )

		w.contents.bind( "<Alt-Return>", lambda event: w.btn_open.invoke())
		w.contents.bind( "<Alt-l>", w.toggle_ln)
		w.contents.bind( "<Alt-x>", w.toggle_syntax)
		w.contents.bind( "<Alt-f>", w.font_choose)

		w.contents.bind( "<Control-c>", w.copy)
		w.contents.bind( "<Control-v>", w.paste)
		w.contents.bind( "<Control-x>",
			lambda event: w.copy(event, **{'flag_cut':True}) )

		w.contents.bind( "<Control-y>", w.yank_line)

		w.contents.bind( "<Control-Left>", w.move_by_words)
		w.contents.bind( "<Control-Right>", w.move_by_words)
		w.contents.bind( "<Control-Shift-Left>", w.select_by_words)
		w.contents.bind( "<Control-Shift-Right>", w.select_by_words)

		w.contents.bind( "<Control-Up>", w.move_many_lines)
		w.contents.bind( "<Control-Down>", w.move_many_lines)
		w.contents.bind( "<Control-Shift-Up>", w.move_many_lines)
		w.contents.bind( "<Control-Shift-Down>", w.move_many_lines)

		w.contents.bind( "<Control-8>", w.walk_scope)
		w.contents.bind( "<Control-Shift-(>",
			lambda event: w.walk_scope(event, **{'absolutely_next':True}) )
		w.contents.bind( "<Control-9>",
			lambda event: w.walk_scope(event, **{'down':True}) )
		w.contents.bind( "<Control-Shift-)>",
			lambda event: w.walk_scope(event, **{'down':True, 'absolutely_next':True}) )

		w.contents.bind( "<Alt-Shift-F>", w.select_scope)


		w.contents.bind("<Left>", w.check_sel)
		w.contents.bind("<Right>", w.check_sel)
		w.entry.bind("<Left>", w.check_sel)
		w.entry.bind("<Right>", w.check_sel)


	# w.os_type == 'mac_os':
	else:
		w.contents.bind( "<Left>", w.mac_cmd_overrides)
		w.contents.bind( "<Right>", w.mac_cmd_overrides)
		w.contents.bind( "<Up>", w.mac_cmd_overrides)
		w.contents.bind( "<Down>", w.mac_cmd_overrides)

		w.entry.bind( "<Right>", w.mac_cmd_overrides)
		w.entry.bind( "<Left>", w.mac_cmd_overrides)

		w.contents.bind( "<f>", w.mac_cmd_overrides)		# + fn full screen

		# Have to bind using Mod1 as modifier name if want bind to Command-key,
		# Last line is the only one working:
		#w.contents.bind( "<Meta-Key-k>", lambda event, arg=('AAA'): print(arg) )
		#w.contents.bind( "<Command-Key-k>", lambda event, arg=('AAA'): print(arg) )
		#w.contents.bind( "<Mod1-Key-k>", lambda event, arg=('AAA'): print(arg) )

		# 8,9 as '(' and ')' without Shift, nordic key-layout
		# 9,0 in us/uk ?
		w.contents.bind( "<Mod1-Key-8>", w.walk_scope)
		w.contents.bind( "<Mod1-Shift-(>",
			lambda event: w.walk_scope(event, **{'absolutely_next':True}) )
		w.contents.bind( "<Mod1-Key-9>",
			lambda event: w.walk_scope(event, **{'down':True}) )
		w.contents.bind( "<Mod1-Shift-)>",
			lambda event: w.walk_scope(event, **{'down':True, 'absolutely_next':True}) )

		w.contents.bind( "<Mod1-Shift-F>", w.select_scope)
		w.contents.bind( "<Mod1-Shift-E>", w.elide_scope)

		w.contents.bind( "<Mod1-Key-y>", w.yank_line)
		w.contents.bind( "<Mod1-Key-n>", w.new_tab)

		w.contents.bind( "<Mod1-Key-f>", w.search)
		w.contents.bind( "<Mod1-Key-r>", w.replace)
		w.contents.bind( "<Mod1-Key-R>", w.replace_all)

		w.contents.bind( "<Mod1-Key-c>", w.copy)
		w.contents.bind( "<Mod1-Key-v>", w.paste)
		w.contents.bind( "<Mod1-Key-x>",
			lambda event: w.copy(event, **{'flag_cut':True}) )

		w.contents.bind( "<Mod1-Key-b>", w.goto_bookmark)
		w.contents.bind( "<Mod1-Key-B>",
			lambda event: w.goto_bookmark(event, **{'back':True}) )

		w.contents.bind( "<Mod1-Key-p>", w.toggle_bookmark)
		w.contents.bind( "<Mod1-Key-g>", w.goto_def)
		w.contents.bind( "<Mod1-Key-l>", w.gotoline)
		w.contents.bind( "<Mod1-Key-a>", w.goto_linestart)
		w.contents.bind( "<Mod1-Key-e>", w.goto_lineend)

		w.entry.bind( "<Mod1-Key-a>", w.goto_linestart)
		w.entry.bind( "<Mod1-Key-e>", w.goto_lineend)

		w.contents.bind( "<Mod1-Key-z>", w.undo_override)
		w.contents.bind( "<Mod1-Key-Z>", w.redo_override)

		# Could not get keysym for Alt-l and x, so use ctrl
		w.contents.bind( "<Control-l>", w.toggle_ln)
		w.contents.bind( "<Control-x>", w.toggle_syntax)

		# have to bind to symbol name to get Alt-shorcuts work in macOS
		# This is: Alt-f
		w.contents.bind( "<function>", w.font_choose)		# Alt-f
		w.contents.bind( "<dagger>", w.toggle_color)		# Alt-t
		w.contents.bind( "<ssharp>", w.color_choose)		# Alt-s


	#######################################################


	# Arrange detection of CapsLock-state.
	w.capslock = 'init'
	w.motion_bind = w.bind('<Motion>', w.check_caps)
	if w.os_type != 'mac_os':
		w.bind('<Caps_Lock>', w.check_caps)
	else:
		w.bind('<KeyPress-Caps_Lock>', w.check_caps)
		w.bind('<KeyRelease-Caps_Lock>', w.check_caps)


	w.bind( "<Control-R>", w.replace_all)
	w.bind( "<Control-r>", w.replace)

	w.bind( "<Escape>", w.esc_override )
	w.bind( "<Return>", w.do_nothing_without_bell)
	w.bind( "<Control-minus>", w.decrease_scrollbar_width)
	w.bind( "<Control-plus>", w.increase_scrollbar_width)

	w.ln_widget.bind("<Control-n>", w.do_nothing_without_bell)
	w.ln_widget.bind("<Control-p>", w.do_nothing_without_bell)

	w.contents.bind( "<Control-a>", w.goto_linestart)
	w.contents.bind( "<Control-e>", w.goto_lineend)
	w.contents.bind( "<Control-A>", w.goto_linestart)
	w.contents.bind( "<Control-E>", w.goto_lineend)

	if w.os_type == 'windows':
		w.entry.bind( "<Control-E>",
			lambda event, arg=('<<SelectLineEnd>>'): w.entry.event_generate)
		w.entry.bind( "<Control-A>",
			lambda event, arg=('<<SelectLineStart>>'): w.entry.event_generate)

		w.entry.bind( "<Control-c>", w.copy_windows)
		w.entry.bind( "<Control-x>",
			lambda event: w.copy_windows(event, **{'flag_cut':True}) )


	w.contents.bind( "<Control-j>", w.center_view)
	w.contents.bind( "<Control-u>",
		lambda event: w.center_view(event, **{'up':True}) )

	w.contents.bind( "<Control-d>", w.del_tab)
	w.contents.bind( "<Control-Q>",
		lambda event: w.del_tab(event, **{'save':False}) )

	w.contents.bind( "<Shift-Return>", w.comment)
	w.contents.bind( "<Shift-BackSpace>", w.uncomment)
	w.contents.bind( "<Tab>", w.indent)

	w.contents.bind( "<Control-Tab>", w.insert_tab)

	w.contents.bind( "<Control-t>", w.tabify_lines)
	w.contents.bind( "<Control-z>", w.undo_override)
	w.contents.bind( "<Control-Z>", w.redo_override)
	w.contents.bind( "<Control-f>", w.search)

	w.contents.bind( "<Return>", w.return_override)
	w.contents.bind( "<BackSpace>", w.backspace_override)

	if w.os_type == 'mac_os':
		w.contents.bind( "<Mod1-Key-BackSpace>", w.del_to_dot)
	else:
		w.contents.bind( "<Alt-Key-BackSpace>", w.del_to_dot)

	# Used in searching
	w.bid_space = w.contents.bind( "<space>", w.space_override)

	w.contents.bind( "<Control-n>", w.search_next)
	w.contents.bind( "<Control-p>",
			lambda event: w.search_next(event, **{'back':True}) )


	# Unbind some default bindings
	# Paragraph-bindings: too easy to press by accident
	w.contents.unbind_class('Text', '<<NextPara>>')
	w.contents.unbind_class('Text', '<<PrevPara>>')
	w.contents.unbind_class('Text', '<<SelectNextPara>>')
	w.contents.unbind_class('Text', '<<SelectPrevPara>>')

	# LineStart and -End:
	# fix goto_linestart-end and
	# enable tab-walking in mac_os with cmd-left-right
	w.contents.unbind_class('Text', '<<LineStart>>')
	w.contents.unbind_class('Text', '<<LineEnd>>')
	w.contents.unbind_class('Text', '<<SelectLineEnd>>')
	w.contents.unbind_class('Text', '<<SelectLineStart>>')


















