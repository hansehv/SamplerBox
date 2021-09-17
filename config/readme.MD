This directory contains the configurable items.

On the distributed image, it links to /boot/samplerbox.
This makes it visible as \samplerbox on the SD first partition
 when the SD is inserted in a PC.

You can
 - adapt the samplerbox to your hardware setup
 - change the box's behaviour
 - add or change the chords & scales

The /boot/config.txt actually controls the OS hardware setup,
 so if a device needs a specific driver, editing
 the samplerbox/configuration.txt is not enough:
"USE_PIMORONI_LCD = True" just tells samplerbox to use
  the LCD of this already properly installed/defined card.
