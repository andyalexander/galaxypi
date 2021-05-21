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
    exclude = ['11 fe ba', '21 00 08 d3']
    # exclude = []

    while True:
        if not queue.empty():
            item = queue.get()

            # if item[0:2] in filter:
                # print(item)

            if item[0:2] == k_id:
                tmp = item[3:5]
                if tmp != '06':
                    print(item)
                resp = my_keypad.handle_message(item)
                if k_id != '10':
                    # ser.write(resp)

                    if ser.out_waiting > 0:
                        print('Waiting to write {}'.format(ser.out_waiting))

                    print('Wrote: {}'.format(resp))

            # elif item[0:2] in filter and item not in exclude:
            elif item not in exclude:
                print(item)




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

    command_processor_p = Process(target=command_processor, args = (pqueue_command,my_keypad, ser))
    command_processor_p.daemon = True
    command_processor_p.start()

    while True:
        pass

    