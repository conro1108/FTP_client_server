# server creates welcoming socket to which the client connects
# on RETR, create a connection at client's welcoming socket

import sys
from socket import *

valid_commands = ['USER', 'PASS', 'TYPE', 'SYST', 'NOOP', 'QUIT', 'PORT', 'RETR']


# returns true if all characters in token are valid ascii characters, false otherwise
def validate_ascii(token):
    for char in token:
        if ord(char) > 127:
            return False
    return True


# returns true if every character in token are newline characters, false otherwise
def is_newline(token):
    for char in token:
        if char not in '\r\n':
            return False
    return True


# returns false and sys.stdout.writes correct error message if cmd_string is malformed, otherwise
# returns a tuple with the command type and parameters
def validate_command(cmd_string):
    params = cmd_string.split(" ", 1)
    command_test = params[0].upper().strip()

    if command_test not in valid_commands:
        if len(command_test) == 3 or len(command_test) == 4:
            sys.stdout.write('502 Command not implemented.\r\n')
            return False
        sys.stdout.write('500 Syntax error, command unrecognized.\r\n')
        return False

    if '\r\n' not in cmd_string:
        sys.stdout.write('501 Syntax error in parameter.\r\n')
        return False

    elif command_test in [valid_commands[i] for i in range(0, 2)]:  # USER, PASS
        if len(params) == 1:  # user\r\n is an invalid command
            sys.stdout.write('500 Syntax error, command unrecognized.\r\n')
            return False
        else:
            arg = params[1].lstrip()  # remove leading whitespaces after command
            if is_newline(arg):
                sys.stdout.write('501 Syntax error in parameter.\r\n')
                return False
            else:
                arg = arg.strip('\r\n')

            if not validate_ascii(arg):
                sys.stdout.write('501 Syntax error in parameter.\r\n')
                return False

            return [command_test, arg]

    elif command_test == valid_commands[2]:  # TYPE command
        if len(params) == 1:  # missing type
            sys.stdout.write('500 Syntax error, command unrecognized.\r\n')
            return False
        else:
            arg = params[1].lstrip()
            if arg[0] not in ['A', 'I']:
                sys.stdout.write('501 Syntax error in parameter.\r\n')
                return False
            elif len(arg.strip('\r\n')) != 1:
                sys.stdout.write('501 Syntax error in parameter.\r\n')
                return False
            return [command_test, arg.strip('\r\n')]

    elif command_test in [valid_commands[i] for i in range(3, 6)]:  # SYST, NOOP, QUIT
        if len(params) != 1:  # extra params
            sys.stdout.write('501 Syntax error in parameter.\r\n')
            return False
        else:
            return [command_test]

    elif command_test == valid_commands[6]:  # PORT command
        numbers = params[1].strip().split(',')  # split parameters into comma separated numbers

        if len(numbers) != 6:
            sys.stdout.write('501 Syntax error in parameter.\r\n')
            return False
        for num in numbers:
            if not num.isdigit():
                sys.stdout.write('501 Syntax error in parameter.\r\n')
                return False
            elif int(num) not in range(0, 256):
                sys.stdout.write('501 Syntax error in parameter.\r\n')
                return False

        port_num = int(numbers[4]) * 256 + int(numbers[5])
        numbers = [numbers[i] for i in range(0, 4)]  # remove port numbers
        return [command_test, '.'.join(numbers), port_num]

    elif command_test == valid_commands[7]:  # RETR command
        if len(params) == 1:
            sys.stdout.write('500 Syntax error, command unrecognized.\r\n')
            return False
        else:
            arg = params[1].lstrip()  # remove leading whitespaces after command
            if is_newline(arg):
                sys.stdout.write('501 Syntax error in parameter.\r\n')
                return False
            else:
                arg = arg.strip('\r\n')

            if not validate_ascii(arg):
                sys.stdout.write('501 Syntax error in parameter.\r\n')
                return False

            return_val = [command_test, arg.lstrip('\\/')]

            return return_val


# return whether or not username and password have been supplied
def logged_in():
    return username is not None and password is not None


username = None
password = None
client_port = None
client_ip = None
welcome_port = int(sys.argv[1])

server_socket = socket(AF_INET, SOCK_STREAM)
server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
server_socket.bind(('', welcome_port))
server_socket.listen(1)
while True:
    FTP_control, client_addr = server_socket.accept()
    FTP_control.settimeout(30)
    sys.stdout.write('220 COMP 431 FTP server ready.\r\n')
    FTP_control.send('220 COMP 431 FTP server ready.\r\n'.encode())

    while True:
        FTP_cmd = FTP_control.recv(2048).decode()

        if len(FTP_cmd) == 0:
            continue

        sys.stdout.write(FTP_cmd)

        FTP_cmd_parsed = validate_command(FTP_cmd)

        if not FTP_cmd_parsed:
            continue

        command = FTP_cmd_parsed[0]

        if command == valid_commands[0]:  # USER
            sys.stdout.write('331 Guest access OK, send password.\r\n')
            FTP_control.send('331 Guest access OK, send password.\r\n'.encode())
            username = FTP_cmd_parsed[1]
            password = None
            continue

        elif command == valid_commands[1]:  # PASS
            if username is None or password is not None:
                sys.stdout.write('503 Bad sequence of commands.\r\n')
                FTP_control.send('503 Bad sequence of commands.\r\n'.encode())
                continue
            elif password is None:
                sys.stdout.write('230 Guest login OK.\r\n')
                FTP_control.send('230 Guest login OK.\r\n'.encode())
                password = FTP_cmd_parsed[1]

        elif command == valid_commands[2]:  # TYPE
            if not logged_in():
                sys.stdout.write('530 Not logged in.\r\n')
                FTP_control.send('530 Not logged in.\r\n'.encode())
                continue
            else:
                type_code = FTP_cmd_parsed[1]
                if type_code == 'I':
                    sys.stdout.write('200 Type set to I.\r\n')
                    FTP_control.send('200 Type set to I.\r\n'.encode())
                    continue
                elif type_code == 'A':
                    sys.stdout.write('200 Type set to A.\r\n')
                    FTP_control.send('200 Type set to A.\r\n'.encode())

        elif command == valid_commands[3]:  # SYST
            if not logged_in():
                sys.stdout.write('530 Not logged in.\r\n')
                FTP_control.send('530 Not logged in.\r\n'.encode())
                continue
            else:
                sys.stdout.write('215 UNIX Type: L8.\r\n')
                FTP_control.send('215 UNIX Type: L8.\r\n'.encode())
                continue

        elif command == valid_commands[4]:  # NOOP
            if not logged_in():
                sys.stdout.write('530 Not logged in.\r\n')
                FTP_control.send('530 Not logged in.\r\n'.encode())
                continue
            else:
                sys.stdout.write('200 Command OK.\r\n')
                FTP_control.send('200 Command OK.\r\n'.encode())
                continue

        elif command == valid_commands[5]:  # QUIT
            sys.stdout.write('221 Goodbye.\r\n')
            FTP_control.send('221 Goodbye.\r\n'.encode())

            FTP_control.close()
            username = None
            password = None
            client_port = None
            break

        elif command == valid_commands[6]:  # PORT
            if not logged_in():
                sys.stdout.write('530 Not logged in.\r\n')
                FTP_control.send('530 Not logged in.\r\n'.encode())
                continue
            else:
                client_port = FTP_cmd_parsed[2]
                client_ip = FTP_cmd_parsed[1]
                port = str(FTP_cmd_parsed[1]) + ',' + str(FTP_cmd_parsed[2])
                sys.stdout.write('200 Port command successful (' + port + ').\r\n')
                FTP_control.send(('200 Port command successful (' + port + ').\r\n').encode())
                continue

        elif command == valid_commands[7]:  # RETR
            if not logged_in():
                sys.stdout.write('530 Not logged in.\r\n')
                FTP_control.send('530 Not logged in.\r\n'.encode())
                continue
            if client_port is None:
                sys.stdout.write('503 Bad sequence of commands.\r\n')
                FTP_control.send('503 Bad sequence of commands.\r\n'.encode())
                continue
            else:
                file_data = None
                try:
                    with open(FTP_cmd_parsed[1], 'rb') as target_file:
                        file_data = target_file.read()
                except IOError:
                    sys.stdout.write('550 File not found or access denied.\r\n')
                    FTP_control.send('550 File not found or access denied.\r\n'.encode())
                    continue
                else:
                    sys.stdout.write('150 File status okay.\r\n')
                    FTP_control.send('150 File status okay.\r\n'.encode())

                    try:
                        data_socket = socket(AF_INET, SOCK_STREAM)
                        data_socket.settimeout(3)
                        data_socket.connect((client_ip, client_port))
                    except:
                        sys.stdout.write('425 Can not open data connection\r\n')
                        FTP_control.send('425 Can not open data connection\r\n'.encode())
                        continue

                    data_socket.sendall(file_data)
                    sys.stdout.write('250 Requested file action completed.\r\n')
                    FTP_control.send('250 Requested file action completed.\r\n'.encode())
                    data_socket.close()
                    client_port = None
                    client_ip = None
                    continue
