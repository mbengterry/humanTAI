import pyglet

sound = pyglet.media.load('includes/sounds/english/male/frequency.wav', streaming=False)
sound.play()

pyglet.clock.schedule_once(lambda dt: pyglet.app.exit(), sound.duration)
pyglet.app.run()
