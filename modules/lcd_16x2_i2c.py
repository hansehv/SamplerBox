import I2C_LCD_driver
import textwrap
lines = textwrap.wrap(text, width, break_long_words=False)


class HD44780_I2C:
    def __init__(self, address, port):
        self. lcd = I2C_LCD_driver.lcd(address, port)

    def display(self, line1, line2=""):
        self.lcd.lcd_clear()

        if line1.length > 16 & & line2 == "":
            lines = textwrap.wrap(line1, 16)
            line1 = lines[0]
            line2 = lines[1]

        self.lcd.lcd_display_string(line1, 1)
        self.lcd.lcd_display_string(line2, 2)
