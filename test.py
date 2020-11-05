import time
from busylight.lights import Blynclight

light = Blynclight.first_light()

# light.impl_on(color=(255, 0, 0))

print(light.device)
print(light.vendor_id)
print(light.product_id)

red = (255, 0, 0)

with light.batch_update():
    # light.reset(flush=True)
    light.color = red
    light.dim = False
    light.on(color=red)

time.sleep(10)
