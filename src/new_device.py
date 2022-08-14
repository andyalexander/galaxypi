import serial
import serial.rs485
from multiprocessing import Queue, Process

import keyqueue
import keypad
import utils

ser=serial.rs485.RS485(port='/dev/ttyUSB0',
                       baudrate=9600,
                       bytesize = serial.EIGHTBITS,
                       parity = serial.PARITY_NONE,
                       stopbits = serial.STOPBITS_ONE,
                       timeout=0.1)

ser.flush()

