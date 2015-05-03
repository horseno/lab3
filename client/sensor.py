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
        
        self.c.report_state(self.cid, self.state)
        return 1




