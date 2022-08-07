import keyqueue
from utils import checkMessage, addParity, calcParity

class Keypad:
    _keydict = {'0':0x00,'1':0x01,'2':0x02,'3':0x03,'4':0x04,'5':0x05,'6':0x06,'7':0x07,'8':0x08,'9':0x09,'A':0x0B,'B':0x0A,'ent':0x0C,'esc':0x0D,'*':0x0E,'#':0x0F}
    _screensize = (2,16)
    _suppress = {'beep':1, 'backlight':1, 'poll':0, 'initial_poll':1, 'update':0}

    def __init__(self, device_id):
        self.PANEL_ID = 0x11
        self.DEVICE_ID = device_id
        self.KEY_QUEUE = keyqueue.Queue('keypad0')
        self.BACKLIGHT = False
        self.RESP_ALL_OK = bytearray([self.PANEL_ID, 0xFE])
        self.init_display()
        self.SCREEN_FLASH = False

        self.SCREEN_SIZE = Keypad._screensize

        self.log('Starting keypad: {}'.format(hex(device_id)))
        self.CRC = 0

    def init_display(self):
        self.SCREEN = [['' for y in range(self._screensize[1])] for x in range(self._screensize[0])]
        self.CURSOR_ROW = 0
        self.CURSOR_COL = 0

    def log(self, message, finish_line=True):
        end_char =" :: "
        if finish_line:
            end_char = '\n'
        print(message, end=end_char)

    def handle_message(self, b_message_in):
        bMessage = bytes.fromhex(b_message_in)
        resp = bytearray([0x00])

        if bMessage[0] == self.DEVICE_ID:
            resp = self.RESP_ALL_OK.copy()
            
            # ignore the poll
            # if bMessage[1] != 0x06:
                # self.log("message for keypad: {}".format(hex(self.DEVICE_ID)), False)

            if bMessage[1] == 0x00:                 # initial poll
                resp = self.handle_initial_poll()
            elif bMessage[1] == 0x19:               # activity poll
                resp = self.handle_activity_poll()
            elif bMessage[1] == 0x0D:               # backlight
                resp = self.backlight_set(bMessage[2]==0x01)
            elif bMessage[1] == 0x0B:               # button acknowledgement
                self.CRC = bMessage[2]
                resp = self.ack_button()
            elif bMessage[1] == 0x0C:               # beep
                resp = self.beep_set(bMessage[2])
            elif bMessage[1] == 0x07:               # screen update
                # handle flags
                flag = bMessage[2]
                resp = self.RESP_ALL_OK.copy()

                if flag & 0x10 != 0:                # we have a button to ack
                    self.CRC = flag & 0x02          # toggle the CRC

                    # print('upd: button ack')
                    resp = self.ack_button()

                if flag & 0x80 != 0:                # new update command                   
                    self.screen_update(bMessage[3:-1])
                # else:
                    # print('update, duplicate')

            elif bMessage[1] == 0x06:              # check if all ok...
                # self.log("Status check")
                resp = self.RESP_ALL_OK.copy()
            else:
                self.log('UNKNOWN COMMAND: {}'.format(b_message_in))

            resp = addParity(resp)

        # if bMessage[1] != 0x06:
            # self.log('')
        
        return resp


    def handle_initial_poll(self):
        if not self._suppress['initial_poll']:
            self.log('Poll message')
        resp = bytearray([self.PANEL_ID, 0xFF, 0x08, 0x00, 0x64])
        return resp

    def handle_activity_poll(self):
        ## pass back the next key or 'ok'
        resp = bytearray([0x00])
        if self.KEY_QUEUE.empty():
            resp = self.RESP_ALL_OK.copy()
        else:
            k = self._keydict[self.KEY_QUEUE.get()]
            self.log('sending key:{0}'.format(k))
            resp = bytearray([self.PANEL_ID, 0xF4])
            resp.append(k)

        # if not self._suppress['poll']:
            # self.log('Activity poll, returning:', resp.hex())

        return resp

    def send_enter(self):
        self.key_add_to_queue('ent')

    def send_esc(self):
        self.key_add_to_queue('esc')

    def send_keys(self,keystrokes):
        for k in keystrokes:
            self.key_add_to_queue(k)

    def key_add_to_queue(self, key):
        if key in self._keydict:
            self.KEY_QUEUE.put(key)

    def backlight_set(self, isOn):
        self.BACKLIGHT = isOn
        if not self._suppress['backlight']:
            self.log("Backlight - {}".format(isOn))
        resp = self.RESP_ALL_OK
        return resp

    def beep_set(self, state):
        if state == 0x01:
            if not self._suppress['beep']:
                self.log("Beep - On")
        elif state == 0x03:
            self.log("Beep - Beeping")
        elif state == 0x00:
            if not self._suppress['beep']:
                self.log("Beep - Off")
        else:
            self.log("Beep - UNKNOWN")

        resp = self.RESP_ALL_OK
        return resp

    def ack_button(self):
        # TODO: handle the wierd alternating CRC ack piece
        # https://richard.burtons.org/2019/03/09/honeywell-galaxy-keypad-cp038-rs485-protocol/
        self.KEY_QUEUE.ack(self.CRC)
        resp = self.handle_activity_poll()
        return resp

    def cursor_left(self):
        self.CURSOR_COL -= 1
        if self.CURSOR_COL < 0:
            if self.CURSOR_ROW == 1:
                self.CURSOR_ROW = 0
                self.CURSOR_COL = 0
            else:
                self.CURSOR_COL = 0

    def cursor_right(self):
        self.CURSOR_COL += 1
        if self.CURSOR_COL > self.SCREEN_SIZE[1]-1:
            if self.CURSOR_ROW == 0:
                self.CURSOR_ROW = 1
                self.CURSOR_COL = 0
            else:
                self.CURSOR_COL = self.SCREEN_SIZE[1]-1


    def screen_update(self, mess):
        for x in range(len(mess)):
            cmd = mess[x]
            if cmd == 0x01:
                self.CURSOR_ROW = 0
                self.CURSOR_COL = 0
            elif cmd == 0x02:
                self.CURSOR_ROW = 1
                self.CURSOR_COL = 0
            elif cmd == 0x03:
                x+=1
                cmd_next = mess[x]
                self.CURSOR_COL = cmd_next % 0x40
                if cmd_next >= 0x40:
                    self.CURSOR_ROW = 1
                else:
                    self.CURSOR_ROW = 0
            elif cmd == 0x04:
                pass
            elif cmd == 0x05:
                pass
            elif cmd == 0x14:
                self.cursor_left()
                self.SCREEN[self.CURSOR_ROW][self.CURSOR_COL] = ''
            elif cmd == 0x15:
                self.cursor_left()
            elif cmd == 0x16:
                self.cursor_right()
            elif cmd == 0x17:
                self.init_display()
            elif cmd == 0x18:
                self.SCREEN_FLASH = True
            elif cmd == 0x19:
                self.SCREEN_FLASH = False
            elif cmd >= 0x20:
                char = chr(cmd)
                if cmd == 219:          # empty block
                    char = '-'
                if cmd == 255:          # filled block
                    char = '|'

                self.SCREEN[self.CURSOR_ROW][self.CURSOR_COL] = char
                self.cursor_right()

        self.log('Update screen')
        self.display_screen()

        # resp = self.RESP_ALL_OK
        # resp = self.ack_button()            # if we get an update, can also respond to button
        #return resp


    def display_screen(self):
        self.log(self.SCREEN)

