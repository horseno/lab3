import sys
sys.path.append("./")
import setting

import xmlrpclib 
import SimpleXMLRPCServer
import socket
import select
import time
import random

class Sensor:
    ''' Represents any senors'''
    def __init__(self,name,serveradd,localadd,devNum):
        '''initialize a sensor, create a client to connect to server'''
        self._isLeader = 0 #whether it is leader
        self._timeoffset = 0 #synchronized time offset
        self._electID = random.random()  #id for election
        self.name = name
        self.ctype = 'sensor'
        self.localadd = localadd
        self.c0 = xmlrpclib.ServerProxy("http://"+serveradd[0]+":"+str(serveradd[1]),verbose=0)#rpc server
        self.state = '0'
        self.vector = [0] * devNum #vector clock
        
    def leader_elect(self):
        time.sleep(1+random.random()) #wait for server setting up
        address = ('<broadcast>', setting.eleport)
        clt_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        clt_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        clt_socket.sendto(self.name, address) #broadcast its address to register for election
        #receive next node's address in the ring
        nextadd, addr = clt_socket.recvfrom(2048)
        tmp = nextadd[1:-1].split(",")
        nextadd = (tmp[0][1:-1],int(tmp[1]))
        #receive election message
        recv_data, preaddr = clt_socket.recvfrom(2048)
        #add its election id
        recv_data = recv_data+"#"+str(self._electID)
        clt_socket.sendto(recv_data, nextadd)
        #receive election result
        id_data, addr = clt_socket.recvfrom(2048)
        if id_data == "1":
           self._isLeader = 1
        if self._isLeader == 1:
            print self.name,"is Leader"
        return 1
        
    def time_syn(self):
        #as master
        if self._isLeader == 1:
            connect_list = []
            syn_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            syn_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            syn_socket.bind(("127.0.0.1", setting.synport))#port for listening slaves' connection
            syn_socket.listen(8)
            #getting slaves' address
            while len(connect_list) < setting.devNum-1:
                sockfd, addr = syn_socket.accept()
                connect_list.append(sockfd)
            #send master's current time
            for sk in connect_list:
                sk.send(str(time.time()))
            offsets = []
            ready = []
            #get offsets   
            while len(offsets)< setting.devNum-1:#setting.devNum-1
                read_sockets,write_sockets,error_sockets = select.select(connect_list,[],[])
                for sk in read_sockets:
                    if sk not in ready:
                        of = sk.recv(1024)
                        offsets.append(float(of))
                        ready.append(sk)  
            #average offsets 
            moffset = sum(offsets)/(len(offsets)+1.0)
            #send average offset
            for sk in connect_list:
                sk.send(str(moffset))
            self._timeoffset = moffset
            syn_socket.close()   
        #as slave 
        else:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            time.sleep(1+random.random())#wait for time master to start listening
            s.connect(("127.0.0.1",setting.synport))#connect to master
            mt = s.recv(1024)#get master's time
            offset = time.time()-float(mt)#calculate offset
            #send offset
            s.send(str(offset))
            #get average offset
            moffset = s.recv(1024)
            #set its own offset
            self._timeoffset = float(moffset) - offset
            s.close()
        print self.name,"time offset",self._timeoffset
    
    def register_to_server(self):
        '''register with the gateway, sending name, type and listening address'''
        
        load_balance_info = self.c0.register(self.ctype,self.name,self.localadd)
        self.cid = load_balance_info['id']
        self.server_to_connect= load_balance_info['assignedServer']

        #connect to server rpc client 
        self.c = xmlrpclib.ServerProxy("http://"+self.server_to_connect[0]+":"+str(self.server_to_connect[1]))
        return 1

    def start_listen(self):
        '''To enable communication with the gateway, start a server to catch queries and instructions'''
        self.s = SimpleXMLRPCServer.SimpleXMLRPCServer(self.localadd,logRequests=False)#zerorpc.Server(self)
        self.s.register_instance(self)
        self.s.serve_forever()

    def query_state(self):
        
        return self.state

    def set_state(self,state):

        '''set state from test case'''
        self.state = state
        return 1

    def set_state_push(self,state):
        '''set the state of sensor from test case, push to the gateway if state changed'''
        if self.state != state:
            self.state = state
            self.report_to_server()
        return 1

    def report_to_server(self):
        '''Push to the server'''
        print "############"
        self.c.report_state(self.cid, self.state)
        return 1




