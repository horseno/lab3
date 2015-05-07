import xmlrpclib 
import SimpleXMLRPCServer
import time
import sys
sys.path.append("./")
import setting
import socket
import select
import time
import random

class SmartDev:
    ''' Represents any smart device'''
    def __init__(self,name,serveradd,localadd):
        self.name = name
        self.ctype = 'device'
        self.localadd = localadd
        self.c0 = xmlrpclib.ServerProxy("http://"+serveradd[0]+":"+str(serveradd[1]),verbose=0)#rpc server
        self.state = '1'
        filename = "results/devout-" + self.name + '.txt' 
        f = open(filename,"w+")
        f.close()
    
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
    
    def change_server(self,new_server_add):
        self.c = xmlrpclib.ServerProxy("http://"+new_server_add[0]+":"+str(new_server_add[1]))
        print self.name,"change to new server","http://"+new_server_add[0]+":"+str(new_server_add[1])
        return 1
        
    def set_state(self,state):
        '''function used to debug and test'''
        self.state = state
        return 1

    def change_state(self, state):
        '''change state according to the request of the gateway, write change to file'''
        self.state = state
        cur_t = time.time() 
        timestamp = round(cur_t - setting.start_time, 2)
        filename = "results/devout-" + self.name + '.txt' 
        content = str(timestamp) + ',' + str(self.state)+ '\n'
        with open(filename, 'a') as f:
            f.write(content)
        return 1



        