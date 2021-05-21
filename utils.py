def addParity(mess):
    tmp = mess
    if mess != 0x00:            # not null char
        parity = calcParity(mess)
        tmp.append(parity)

    return tmp

def checkMessage(mess):
    par = calcParity(mess)
    print(mess)
    print(par)

    if par != mess[-1]:
        return False
    else:
        return True

def calcParity(mess):
    tmp = 0xAA
    bSum = int(sum(mess) + tmp)
    h = hex(bSum)
    l = len(h[2:])
    padded = h[2:].zfill(l % 2 + l)

    tmp = 0
    for start in list(range(0, len(padded) - 1, 2)):
        tmp += int(padded[start:start + 2], 16)

    return tmp % 256


def splitBytesById(bytes_in):
    # from ADT 2.7 galaxy 16+
    ids = ["10", "20", "30", "40", "4d", "01", "11", "21", "23"]

    first_pos = 9999
    second_pos = 9999
    first_second = 9999
    offset = 0

    # if the message is too short, it must just be partial, so return and wait for next loop
    if len(bytes_in) < 7:
        return ("","", bytes_in)

    # loop through the string increasing the offset to handle ids inside message body for different reasons
    while offset <= len(bytes_in):
        for x in ids:
            pos = bytes_in.find(x, offset)
            
            if pos > -1:
                if pos < first_pos:
                    if first_pos != 9999:
                        second_pos = first_pos
                    first_pos = pos
                else:
                    second_pos = min(second_pos, pos)

            # the second position is the earliest valid one we find        
            first_second = min(first_second, second_pos)
    
        command = ""
        skipped = ""
        remainder = ""

        if second_pos != 9999:
            command = bytes_in[first_pos:second_pos]
            remainder = bytes_in[second_pos:]
        else:
            command = bytes_in[first_pos:]

        if first_pos > 0:
            skipped = bytes_in[0:first_pos]

        parity = hex(calcParity(bytes.fromhex(command[0:-3])))
        cmd_parity = '0x{}'.format(command[-3:].strip())

        command = command[0:-3]

        # print(offset, ':', first_pos, '-', second_pos)

        if '{}'.format(parity,'02x') == cmd_parity:
            # print('ok')
            return (command.strip(), skipped.strip(), remainder.strip())
        else:
            offset = second_pos + 3 # start the search for the second position after this value, string is in 3 char blocks
            second_pos = 9999       # reset the second position, so we restart search

    print('part line')
    return ("", "",  bytes_in)


def format_for_return(bytes_list):
    return " ".join(bytes_list)

def checkParity(bytes_list):
    calc_parity = hex(calcParity(bytes.fromhex(format_for_return(bytes_list[0:-1]))))
    mess_parity = '0x{}'.format(bytes_list[-1])

    if '{}'.format(calc_parity,'02x') == mess_parity:
        return True
    else:
        return False

def splitBytesById2(bytes_in):
    # from ADT 2.7 galaxy 16+
    ids = ["10", "20", "30", "4d", "01", "11", "21", "23"]

    bytes_list = bytes_in.split(' ')

    MAX_COMMAND_LENGTH = 50

    # first_pos = 9999
    # second_pos = 9999
    # first_second = 9999
    # offset = 0

    # if the message is too short, it must just be partial, so return and wait for next loop
    if len(bytes_list) < 3:
        return ("","", format_for_return(bytes_list))


    n = len(bytes_list)
    for offset in range(n):           # loop through the string increasing the offset to handle ids inside message body for different reasons
        first_pos = 9999
        second_pos = 9999

        for i in range(offset,n):
            if bytes_list[i] in ids:
                if first_pos == 9999:
                    first_pos = i
                else:
                    second_pos = min(second_pos, i)
            
                # if we have found a second position as well...
                if second_pos < 9999:
                    command = bytes_list[first_pos:second_pos]

                    if checkParity(command) and len(command)<MAX_COMMAND_LENGTH:
                        # print('ok')
                        return (format_for_return(command), format_for_return(bytes_list[second_pos:]), "")
                    else:
                        second_pos = 9999       # reset the second position, so we restart search
            
            # if we are at the end of the command, and have a valid first position, test to see if the command is valid
            if first_pos < 9999 and i == n-1:
                command = bytes_list[first_pos:]

                if checkParity(command):
                    # print('ok')
                    return (format_for_return(command), "", "")
                # else:
                #     # if we haven't found anything, then just return everything we got as potential partial sub-command
                #     return ("", bytes_in, "")

        # move start position 1 further down...

    # if we get here we haven't found anything in the string for every start position 
    # so just return the string as a new stub
    # print('nothing found')
    return ("", bytes_in, "")
    
