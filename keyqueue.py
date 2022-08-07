# import queue
import multiprocessing as queue

class Queue:
    def __init__(self, id):
        self.queue = queue.Queue()
        self.next_key = ''
        self.last_crc = 0
        self.id = id

    def get(self):
        if self.next_key == '':
            self.next_key = self.queue.get()

        return self.next_key

    def put(self, val):
        # print("added key:", val)
        self.queue.put(val)

    def ack(self, crc):
        if crc != self.last_crc:
            self.next_key = ''      # clear the last key so we get a new one
            self.last_crc = crc
            return True
        else:
            return False

    def empty(self):
        is_empty = self.queue.empty()
        return (self.next_key=='' and is_empty)

    def print_stack(self):
        tmp = [elem for elem in list(self.queue.queue)]
        if self.next_key != '':
            tmp = [self.next_key] + tmp
        print('stack:', tmp)

