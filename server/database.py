import xmlrpclib 
import SimpleXMLRPCServer
import time
import csv
import sys
sys.path.append("./")
import setting

def compare_float(f1, f2):
    return abs(f1 - f2) <= 0.001

class Database:
    '''Backend Database'''
    def __init__(self,Dbadd,IFRep):
        #store current state and history state in separate files
        if IFRep == 0:
            self.fname = "results/dbfile.csv"
        else:
            self.fname = "results/dbfile_rep.csv"
        f = open(self.fname,"w+")
        f.close()
        self._isLeader = 0 #whether it is leader
        self._electID = 0 #id for election
        
        self.s = SimpleXMLRPCServer.SimpleXMLRPCServer(Dbadd,logRequests=False)#rpc server
        self.s.register_instance(self)
        self.s.serve_forever()
    
    def str_to_vector(self,string):
        string = string[1:-1].split(',')
        for i in range(len(string)):
            string[i]= int(string[i])
        return string 

    def write(self, cid, state, timestamp):
        with open(self.fname, 'ab') as f:
            curWriter = csv.writer(f)
            curWriter.writerow([cid,state,timestamp])
        return 1
    
    def leader_elect(self):
        time.sleep(1+random.random())#wait for server setting up
        address = ('<broadcast>', setting.eleport) 
        clt_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        clt_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        clt_socket.sendto(self.name, address)#broadcast its address to register for election
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
            print "DB is Leader"
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
            while len(offsets)< setting.devNum-1:
                read_sockets,write_sockets,error_sockets = select.select(connect_list,[],[])#select a ready socket
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
        print "DB time offset",self._timeoffset

    def read(self, cid, timestamp):
        '''read the file to get current state/ all the states/ state at a particular time of a device
         timestamp == 0 -> return current state 
         timestamp >0 return state of time indicated by timestamp
         timestamp < 0 return all the state history of the device 
         return values are a list of tuple(state, timestamp)
         '''
        state_l=[]
        maxtime = 0 
        curState = '-1'
        with open(self.fname, 'rb') as f:
            curReader = csv.reader(f)
            for row in reversed(list(curReader)):
                qid = row[0]
                vector = self.str_to_vector(row[3])
                state = str(row[1])
                time = float(row[2])
                if int(qid)==cid:
                    if timestamp < 0:
                        state_l.append((state,time,vector))
                        #print state_l
                    elif timestamp >0 and compare_float(timestamp,time):
                        state_l.append((state,time,vector))
                    elif compare_float(timestamp,0) and time>maxtime:
                        curState = state
                        maxtime = time 
            if compare_float(timestamp,0) and curState != '-1':
                state_l.append((curState, maxtime,vector))   
        return state_l
    
    #get device state within an offset of the timestamp
    def read_offset(self, cid, timestamp, offset):
        li=[]
        with open(self.fname, 'rb') as f:
            reader = csv.reader(f)
            for row in reader:
                qid = int(row[0])
                state = str(row[1])
                time = float(row[2])
                if qid == cid and (time> timestamp - offset) and (time <timestamp):
                    if state == '1':
                        li.append(1)
                    else:
                        li.append(0)
        #print li
        if sum(li) > 0:
            return 1
        else:
            return 0
 
