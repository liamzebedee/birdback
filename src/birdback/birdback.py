# While writing this I was listening to Flight of the Conchord's song 'Hiphopopotamus vs. Rhymenoceros'
# When naming, I thought I'd take a cue from the Rhymenocerous, of whose back the birds lie.

import controller
import signal

if __name__ == '__main__':
	try:
		birdback = controller.Controller()
		signal.signal(signal.SIGTERM, birdback.quit)
		birdback.run()
	except KeyboardInterrupt:
		birdback.quit()
	except Exception as e:
		print(e)
		print("Critical error. Exiting.")
		birdback.quit(1)
