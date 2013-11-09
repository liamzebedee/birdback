# While writing this I was listening to Flight of the Conchord's song 'Hiphopopotamus vs. Rhymenoceros'
# When naming, I thought I'd take a cue from the Rhymenocerous, of whose back the birds lie.

import controller
import signal

if __name__ == '__main__':
	app = None
	try:
		app = controller.Controller()
		print("Controller instantiated")
		signal.signal(signal.SIGTERM, app.quit)
		app.run()
	except KeyboardInterrupt:
		app.quit()
	except Exception as e:
		print(e)
		print("Critical error. Exiting.")
		app.quit(1)
