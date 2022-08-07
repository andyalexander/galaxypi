import serial
import serial.rs485
from multiprocessing import Queue, Process

import keyqueue
import keypad
import utils

import uvicorn
from fastapi import FastAPI
# from fastapi.logger import logger
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

app = FastAPI()

ser=serial.rs485.RS485(port='/dev/ttyUSB0',
                       baudrate=9600,
                       bytesize = serial.EIGHTBITS,
                       parity = serial.PARITY_NONE,
                       stopbits = serial.STOPBITS_ONE,
                       timeout=0.05)

ser.flush()


def serial_reader(serial_port, queue):
    ## Get bytes from serial port and add to queue
    while True:
        tmp = serial_port.read(100)
        if len(tmp) > 0:
            queue.put(tmp)
        ser.flush()


def raw_processor(queue_in, queue_out):
    tmp = ""
    stub = ""
    bytes_in = ""
    last_line = ""

    while True:
        if not queue_in.empty():
            tmp = queue_in.get()

            bytes_in = " ".join(format(x,'02x') for x in tmp)
            
            bytes_in = stub + ' ' + bytes_in.strip()
        else:
            bytes_in = stub

        # bytes_in = bytes_in.strip()

        skipped = ""
        if len(bytes_in) > 0:
            ret, stub, skipped = utils.splitBytesById2(bytes_in)
            # print(bytes_in, ' : ', ret,'-', stub)

            if len(ret)>0:
                queue_out.put(ret)

        # if len(skipped) > 0:
            # print("MISSING COMMAND: ", skipped, ' : ', bytes_in, ' : ', last_line)

        if len(stub) > 2000:
            print("stub too long")
            print(stub)
            stub = ""

        # if len(bytes_in)>0:
            # last_line = bytes_in



def command_processor(queue, my_keypad, my_ser):
    ## Process the queue
    k_id = hex(my_keypad.DEVICE_ID).replace('0x','')
    filter = [k_id,'11',10]
    exclude = [
        '11 fe ba',          # ack to panel
        '21 00 08 d3', 
        '10 06 c0',          # no clue!
        '10 0d 01 c8',       # backlight
        '10 07 81 43',       # prev message ack,    
        '10 0c 00 00 00 c6', # beeps off
        '10 19 01 d4',       # activity poll
        '10 00 08 c2',       # initial device poll
        '11 ff 08 00 64 28'  # initial device response 
        ]

    # TODO: i have no clue what the 10 06 c0 does

    # exclude = []

    while True:
        if not queue.empty():
            item = queue.get()

            if item[0:2] in filter and item not in exclude:
                print('message:', item)

            if item[0:2] == k_id:
                tmp = item[3:5]

                # if tmp != '06':
                    # print('item:', item)

                resp = my_keypad.handle_message(item)
                if k_id != '12':
                    # ser.write(resp)

                    if ser.out_waiting > 0:
                        print('Waiting to write {}'.format(ser.out_waiting))

                    # ignore the ack
                    ignore = [
                        bytearray(b'\x11\xfe\xbau\xea\xd5\xab'),
                        bytearray(b'\x11\xfe\xbau\xea\xd5\xabW\xae]\xbau\xea'),
                        bytearray(b'\x11\xfe\xba'),
                        bytearray(b'\x11\xfe\xbau'),
                        bytearray(b'\x11\xfe\xbau\xea'),
                        bytearray(b'\x11\xff\x08\x00d(')
                    ]
                    if resp not in ignore:
                        print('Wrote: {}'.format(resp))

            # elif item[0:2] in filter and item not in exclude:
            # elif item not in exclude:
            #     print('non-keypad', item)

@app.get("/")
def root():
    my_keypad.send_keys('1234')

if __name__=='__main__':  
    my_keypad = keypad.Keypad(0x10)

    pqueue_raw = Queue() # writer() writes to pqueue from _this_ process
    pqueue_command = Queue()
    
    serial_reader_p = Process(target=serial_reader, args=(ser, pqueue_raw,))
    serial_reader_p.daemon = True
    serial_reader_p.start() 

    raw_processor_p = Process(target=raw_processor, args=(pqueue_raw, pqueue_command))     
    raw_processor_p.daemon = True
    raw_processor_p.start()  

    command_processor_p = Process(target=command_processor, args = (pqueue_command, my_keypad, ser))
    command_processor_p.daemon = True
    command_processor_p.start()

    uvicorn.run(app=app)

#     while True:
#         pass

    