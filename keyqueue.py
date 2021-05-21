import queue

class Queue:
    def __init__(self):
        self.queue = queue.Queue()
        self.next_key = ''
        self.last_crc = -1

    def get(self):
        if self.next_key == '':
            self.next_key = self.queue.get()

        return self.next_key

    def put(self, val):
        self.queue.put(val)

    def ack(self, crc):
        if crc != self.last_crc:
            self.next_key = ''      # clear the last key so we get a new one
            self.last_crc = crc
            return True
        else:
            return False

    def empty(self):
        return (self.next_key=='' and self.queue.empty())

    def print_stack(self):
        tmp = [elem for elem in list(self.queue.queue)]
        if self.next_key != '':
            tmp = [self.next_key] + tmp
        print(tmp)

