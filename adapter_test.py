import serial
import serial.rs485

# python3 -m serial.tools.list_ports

ser=serial.rs485.RS485(port='/dev/ttyUSB0',
                       baudrate=9600,
                       bytesize = serial.EIGHTBITS,
                       parity = serial.PARITY_NONE,
                       stopbits = serial.STOPBITS_ONE,
                       timeout=0.05)

ser.flush()


## Get bytes from serial port and add to queue
while True:
    tmp = ser.read(100)
    if len(tmp) > 0:
        print(tmp)
    ser.flush()
