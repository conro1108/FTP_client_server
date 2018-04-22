# Author: CONNOR ROWE, CS login: cdrowe

# client takes command line arg of port number for welcoming socket
# on CONNECT, attempt to create socket connection to server/port specified in cmd "FTP control"
# FTP control is closed and a new connection is attempted on subsequent CONNECT

import sys
from socket import *

valid_commands = ['CONNECT', 'GET', 'QUIT']


# returns true if every character in token are newline characters, false otherwise
def is_newline(token):
    for char in token:
        if char not in '\r\n':
            return False
    return True


# returns true if all characters in token are valid ascii characters, false otherwise
def validate_ascii(token):
    for char in token:
        if ord(char) > 127 or ord(char) < 0:
            return False
    return True


# returns true if all character in tokens are letters or digits, false otherwise
def validate_letdig(token):
    for char in token:
        char_code = ord(char)
        if not(char_code in range(48, 58) or char_code in range(65, 91) or char_code in range(97, 123)):
            return False
    return True


# returns true if all chars in token are letters, false otherwise
def validate_let(token):
    for char in token:
        if not(ord(char) in range(65, 91) or ord(char) in range(97, 123)):
            return False
    return True


def validate_domain(token):
    domain_arr = token.split('.')
    for element in domain_arr:
        if not validate_let(element[0]):
            return False
        elif not len(element) > 1:
            return False
        elif not validate_letdig(element):
            return False
    return True


# return true if token remains the same when casted to int then back to string (ie no leading zeroes)
# and is in the proper range
def validate_port(token):
    token_int = int(token)
    token_int_str = str(token_int)
    if token_int_str != token or token_int not in range(0, 65536):
        return False
    return True


# returns false and sys.stdout.writes correct error message if cmd_string is malformed, otherwise
# returns a tuple with the command type and parameters
def validate_command(cmd_string):
    params = cmd_string.split(' ', 1)
    cmd_test = params[0].upper().strip()

    if cmd_test not in valid_commands:
        print('ERROR -- request')
        return False

    if cmd_test == valid_commands[0]:  # CONNECT
        if len(params) == 1:
            print('ERROR -- request')
            return False

        if is_newline(params[1]):
            print('ERROR -- server-host')
            return False

        server_info = params[1].lstrip(' ').split(' ', 1)

        server_info[0] = server_info[0].lstrip(' ')
        if not validate_domain(server_info[0]):
            print('ERROR -- server-host')
            return False

        if len(server_info) < 2:
            print('ERROR -- server-port')
            return False

        server_info[1] = server_info[1].lstrip(' ').rstrip('\r\n')
        if not validate_port(server_info[1]):
            print('ERROR -- server-port')
            return False
        else:
            return [cmd_test, server_info[0], server_info[1]]

    elif cmd_test == valid_commands[1]:  # GET
        if len(params) == 1:
            print('ERROR -- request')
            return False

        if is_newline(params[1]):
            print('ERROR -- pathname')
            return False

        path = params[1].lstrip(' ').rstrip('\r\n')
        if not validate_ascii(path):
            print('ERROR -- pathname')
            return False
        else:
            return [cmd_test, path]

    elif cmd_test == valid_commands[2]:  # QUIT
        if len(params) > 1:  # space after quit or extra junk in request
            print('ERROR -- request')
            return False
        else:
            return [cmd_test]


# processes FTP responses from server
def process_reply(reply_string):
    reply_arr = reply_string.strip('\r\n').split(' ', 1)

    reply_code = reply_arr[0]

    # reply-code is invalid for non numeric string, numeric string with leading zeroes, or numeric string out of range
    if not reply_code.isnumeric() or str(int(reply_code)) != reply_code or int(reply_code) not in range(100, 600):
        print('ERROR -- reply-code')
        return False

    # missing or malformed reply-text
    if len(reply_arr) < 2 or not validate_ascii(reply_arr[1]):
        print('ERROR -- reply-text')
        return False

    if '\r\n' not in reply_string:
        print('ERROR -- <CRLF>')
        return False

    print('FTP reply {0} accepted. Text is: {1}'.format(reply_arr[0], reply_arr[1].strip()))

    if reply_arr[0][0] in ['4', '5']:
        return -1


# inputs = sys.stdin.readlines()

connected = False
file_count = 1

welcome_port = int(sys.argv[1])

for cmd in sys.stdin:
    sys.stdout.write(cmd)
    cmd_parsed = validate_command(cmd)

    if not cmd_parsed:
        continue

    command = cmd_parsed[0]

    if command == valid_commands[0]:  # CONNECT
        server_name = cmd_parsed[1]
        server_port = int(cmd_parsed[2])
        print('CONNECT accepted for FTP server at host {0} and port {1}'.format(server_name, server_port))

        if connected:
            FTP_control.close()
            connected = False

        try:
            FTP_control = socket(AF_INET, SOCK_STREAM)
            FTP_control.settimeout(3)
            FTP_control.connect((server_name, server_port))
        except:
            print('CONNECT failed')
            continue

        connected = True

        FTP_reply = FTP_control.recv(2048).decode()
        if process_reply(FTP_reply) == -1:
            continue

        sys.stdout.write('USER anonymous\r\n')
        FTP_control.send('USER anonymous\r\n'.encode())
        FTP_reply = FTP_control.recv(2048).decode()
        if process_reply(FTP_reply) == -1:
            continue

        sys.stdout.write('PASS guest@\r\n')
        FTP_control.send('PASS guest@\r\n'.encode())
        FTP_reply = FTP_control.recv(2048).decode()
        if process_reply(FTP_reply) == -1:
            continue

        sys.stdout.write('SYST\r\n')
        FTP_control.send('SYST\r\n'.encode())
        FTP_reply = FTP_control.recv(2048).decode()
        if process_reply(FTP_reply) == -1:
            continue

        sys.stdout.write('TYPE I\r\n')
        FTP_control.send('TYPE I\r\n'.encode())
        FTP_reply = FTP_control.recv(2048).decode()
        if process_reply(FTP_reply) == -1:
            continue

    elif command == valid_commands[1]:  # GET
        if not connected:
            print('ERROR -- expecting CONNECT')
            continue
        print('GET accepted for {0}'.format(cmd_parsed[1]))

        host_ip = gethostbyname(gethostname())
        host_address = ','.join(host_ip.split('.'))
        port_number = ','.join([str(welcome_port // 256), str(welcome_port % 256)])
        host_port = ','.join([host_address, port_number])

        #try:
        #    welcome_socket = socket(AF_INET, SOCK_STREAM)
        #    welcome_socket.bind(('', welcome_port))
        #    welcome_socket.listen(1)
        #except:
        #    print('GET failed, FTP-data port not allocated')
        #    continue

        welcome_socket = socket(AF_INET, SOCK_STREAM)
        welcome_socket.bind(('', welcome_port))
        welcome_socket.listen(1)

        sys.stdout.write('PORT {0}\r\n'.format(host_port))
        FTP_control.send('PORT {0}\r\n'.format(host_port).encode())
        if process_reply(FTP_control.recv(2048).decode()) == -1:
            continue

        sys.stdout.write('RETR {0}\r\n'.format(cmd_parsed[1]))
        FTP_control.send('RETR {0}\r\n'.format(cmd_parsed[1]).encode())

        if process_reply(FTP_control.recv(2048).decode()) == -1:
            continue
        try:
            if process_reply(FTP_control.recv(2048).decode()) == -1:
                continue
        except:
            pass

        data_socket, server_addr = welcome_socket.accept()
        data_socket.settimeout(2)

        # open file in write mode to clear out any existing ones
        clear = open('retr_files/file{0}'.format(file_count), 'wb')
        clear.close()
        while True:
            chunk = data_socket.recv(2048)
            with open('retr_files/file{0}'.format(file_count), 'ab') as retr_file:
                retr_file.write(chunk)
            try:
                chunk = data_socket.recv(2048)
            except:
                break
            if len(chunk) == 0:
                break

        welcome_port += 1
        file_count += 1

    elif command == valid_commands[2]:  # QUIT
        if not connected:
            print('ERROR -- expecting CONNECT')
            continue
        print('QUIT accepted, terminating FTP client')
        sys.stdout.write('QUIT\r\n')
        FTP_control.send('QUIT\r\n'.encode())
        FTP_reply = FTP_control.recv(2048).decode()
        if process_reply(FTP_reply) == -1:
            continue
        FTP_control.close()
        break
