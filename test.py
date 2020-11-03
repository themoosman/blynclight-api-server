import time
from busylight.lights import Blynclight

light = Blynclight.first_light()

with light.batch_update():
    light.color = (255, 0, 0)
    light.speed = 1
    light.flash = 1
    light.on = True

time.sleep(10)
