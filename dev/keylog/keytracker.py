# https://stackoverflow.com/questions/27215326/tkinter-keypress-and-keyrelease-events


class KeyTracker():
	key = ''
	last_press_time = 0
	last_release_time = 0

	def track(self, key):
		self.key = key

	def is_pressed(self):
		return time.time() - self.last_press_time < .1

	def report_key_press(self, event):
		if event.keysym == self.key:
			if not self.is_pressed():
				on_key_press(event)
			self.last_press_time = time.time()

	def report_key_release(self, event):
		if event.keysym == self.key:
			timer = threading.Timer(.1, self.report_key_release_callback, args=[event])
			timer.start()

	def report_key_release_callback(self, event):
		if not self.is_pressed():
			on_key_release(event)
		self.last_release_time = time.time()


key_tracker = KeyTracker()
window.bind_all('<KeyPress>', key_tracker.report_key_press)
window.bind_all('<KeyRelease>', key_tracker.report_key_release)
key_tracker.track('space')
