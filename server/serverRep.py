import time
import threading
import csv
import random
import xmlrpclib 
import SimpleXMLRPCServer
import sys
sys.path.append("./")
import setting

import select
import socket


#class for Gateway
class Gateway(object):
	#initial class
    def __init__(self,sadd,devNum):
        self._isLeader = 0 #whether it is leader
        self._electID = random.random() #id for election
        self._timeoffset = 0 #synchronized time offset
        self._n = 2 #number of registered devices
        self._idlist = [["gateway","gateway",sadd,0]]#list for registered devices
        self._mode = "HOME"
        self.serveradd = sadd #server address
        self._idx = {"gatewat":0} #index for global id
        self.lasttime = -1 #last time the motion sensor was on
        self.log = open("results/serverRep_log.txt",'w+') #server log file

        self._idlist,append(["gateway","replica",settings.replicaadd,1])
        self._idx = {"replica":1} #index for global id
        self.replicaadd = settings.replicaadd
        
    #leader election
    def leader_elect(self):
        elect_list = ["server"] #candidate list for election
        elect_dict = {"server":('', setting.eleport)} #address for candidate
        elt_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        elt_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
        elt_socket.bind(('', setting.eleport)) #broadcast port for registering election
        n = 1
        print "Server waiting for registration"
        while n<setting.devNum:
            #Listening for register
            recv_data, addr = elt_socket.recvfrom(2048) #get candidate address
            print recv_data,addr,"registered"
            if recv_data not in elect_list:
                elect_list.append(recv_data)
                elect_dict[recv_data] = addr
                n = n+1
        #building ring topology by telling each candidate it successor
        for k in range(1,n):
            elt_socket.sendto(str(elect_dict[elect_list[(k+1)%n]]),elect_dict[elect_list[k]])
        
        #election message token
        msg = "ele#"+str(self._electID)
        elt_socket.sendto(msg,elect_dict[elect_list[1]])
        #waiting for the election token coming back
        recv_data, addr = elt_socket.recvfrom(2048)
        ld = -1
        eidlist = recv_data.split("#")
        if eidlist[0] == "ele":
            eidlist = eidlist[1:]
            maxid = -1
            #find the candidate with the maximum election id
            for i in range(n):
               if float(eidlist[i])>maxid:
                   maxid = float(eidlist[i])
                   ld = i #election result
        if ld == 0:
            self._isLeader = 1
        # tell each candidate the election result
        for i in range(1,n): 
            if ld == i:
                elt_socket.sendto("1",elect_dict[elect_list[i]])
            else:
                elt_socket.sendto("0",elect_dict[elect_list[i]])
        elt_socket.close()
        if self._isLeader == 1:
            print "Gateway is Leader"
        return 1
            
    #time synchronization
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
        print "Gateway time offset",self._timeoffset
        
    # thread for server listening
    def start_listen(self):
        self.s = SimpleXMLRPCServer.SimpleXMLRPCServer(self.replicaadd,logRequests=False)#zerorpc.Server(self)
        self.s.register_instance(self)#self.s.bind(self.serveradd)
        self.s.serve_forever()#self.s.run()
    
    #rpc call for query state
    def query_state(self,id):
    	# checking invalidate id
        if id >= self._n:
            print "Wrong Id"
            return -1
        #set up connection
        c = xmlrpclib.ServerProxy(self._idlist[id][2])
        #update vector clock
        #self.vector[self.cid] = self.vector[self.cid]+1
        #multicast update
        #multicast.multicast(self.serveradd, self.vector)
        #rpc call
        state = c.query_state()
        #get timestamp
        timestmp = round(time.time()+self._timeoffset-setting.start_time,2)
        t1 = time.time()
        self.writedb(id,state,timestmp,self.vector)
        print "writedb takes",time.time()-t1
        #log
        self.log.write(str(round(time.time()+self._timeoffset-setting.start_time,2))+','+self._idlist[id][1]+','+state+'\n')
        print str(round(time.time()+self._timeoffset-setting.start_time,2))+','+self._idlist[id][1]+','+state+'\n'
        #record the last time motion sensor was on 
        if self._idlist[id][1] == "motion":
            if server._mode == "HOME":
                if "bulb" not in server._idx:
                    print "No bulb"
                    return state
                if state == '1':
                    self.lasttime = time.time()+self._timeoffset
                    self.change_state(self._idx["bulb"],'1')
                else:
                    if self.lasttime != -1 and time.time()+self._timeoffset-self.lasttime > 4:
                        self.change_state(self._idx["bulb"],'0')
            #away mode set message if there is motion
            else:
                if state == '1':
                    print "Server: Someone in your room!"
                    self.text_message("Someone in your room!")
        return state
    
    #write to db
    def writedb(self,id,state,timestmp,vector):
        c = xmlrpclib.ServerProxy("http://"+setting.Dbadd[0]+":"+str(setting.Dbadd[1]))
        c.write(id,state,timestmp,vector)
        return 1
    
    #read from db    
    def readdb(self,id,timestmp):
        c = xmlrpclib.ServerProxy("http://"+setting.Dbadd[0]+":"+str(setting.Dbadd[1]))
        state = c.read_offset(id,timestmp,1)
        return state
        
    #rpc interface for report state
    def report_state(self, id, state):
    	#checking invalidate id
        if id >= self._n:
            print "Wrong Id"
            return -1
        #get timestamp
        timestmp = round(time.time()+self._timeoffset-setting.start_time,2)
        t1 =time.time()
        self.writedb(id,state,timestmp,self.vector)
        print "writedb takes",time.time()-t1
        #log
        self.log.write(str(round(time.time()-setting.start_time,2))+','+self._idlist[id][1]+','+state+'\n')
        print str(timestmp)+','+self._idlist[id][1]+','+state+'\n'
    	#event ordering
        if state == '1' and (self._idlist[id][1] == "motion" or self._idlist[id][1] == "door"):
            if self._idlist[id][1] == "motion":
                t0 = time.time()
                ds = self.readdb(self._idx["door"],timestmp)
                bs = self.readdb(self._idx["beacon"],timestmp)
                print "readdb takes",time.time()-t0
                if ds == 1 and bs == 1 and self._mode == "AWAY":
                    self._mode = "HOME"
            else:
                t0 = time.time()   
                ms = self.readdb(self._idx["motion"],timestmp)
                print "readdb takes",time.time()-t0
                if ms == 1 and self._mode == "HOME":
                    self._mode = "AWAY" 
            print "Server mode:",server._mode

        if self._idlist[id][1] == "motion":
            #home mode 
            if server._mode == "HOME":
                if "bulb" not in server._idx:
                    print "No bulb"
                    return 1
                if state == '1':
                    self.lasttime = time.time()
                    self.change_state(self._idx["bulb"],'1')
                else:
                    if self.lasttime != -1 and time.time()-self.lasttime> 5:
                        self.change_state(self._idx["bulb"],'0')
            #away mode send message if there is motion
            else:
                if state == '1':
                    print "Server: Someone in your room!"
                    self.text_message("Someone in your room!")
        return 1
        
    #rpc call for change state    
    def change_state(self, id, state):
    	#checking invalidate id
        if id >= self._n:
            print "Wrong Id"
            return -1
        #set up connection
        c = xmlrpclib.ServerProxy(self._idlist[id][2])
        flag = 0
        #update vector clock
        #self.vector[self.cid] = self.vector[self.cid]+1
        #multicast vector
        #multicast.multicast(self.serveradd, self.vector)
        #rpc call
        if c.change_state(state):
            flag = 1
        return flag
    
    #rpc interface for register
    def register(self,type,name,address):
    	#register device
        self._idlist.append([type,name,"http://"+address[0]+":"+str(address[1])])
        #assign global id
        self._idx[name] = self._n
        #increase number of registed device
        self._n =self._n + 1
        #log
        self.log.write(str(round(time.time()+self._timeoffset-setting.start_time,2))+','+name+','+str(self._n - 1)+'\n')
        print str(round(time.time()+self._timeoffset-setting.start_time,2))+','+name+','+str(self._n - 1)+'\n'
        #return global id
        return self._n - 1
    #receiving register information from the master server
    def recieve_register_info(self,cid,type,name,address):
        self._idlist.append([type,name,"http://"+address[0]+":"+str(address[1])])
        self._idx[name] = cid



        return 1

    
    #rpc call for text message    
    def text_message(self,msg):
    	#checking invalidate id
        if "user" not in self._idx:
            print "No user process"
            return
        #set up connection
        c = xmlrpclib.ServerProxy(self._idlist[self._idx["user"]][2])
        #rpc call
        c.text_message(str(round(time.time()+self._timeoffset-setting.start_time,2))+","+msg)
        
    #rpc interface for change mode
    def change_mode(self,mode):
        self._mode = mode
        return self._mode
    

		
#thread for listening
class myserver(threading.Thread):
    def __init__(self,server):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.server = server
    def run(self):
        self.server.start_listen()

#read certain column in test case file
def readTest(filename,col):		
       with open(filename, 'rb') as csvfile:
           spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
           time=[]
           action=[]
           spamreader.next()
           for row in spamreader:
               time.append(row[0])
               action.append(row[col])     
           return time, action


timel,action = readTest('test-input.csv',5)

devNum = setting.devNum 
server = Gateway(setting.serveradd,devNum)
server.leader_elect()
server.time_syn()
listen_thread = myserver(server)
listen_thread.start()


#calcuate start time
current_time = int(time.time())
waitT = setting.start_time - current_time
time.sleep(waitT)

for index in range(len(timel)):
    at = action[index].split(';')
    
    #query temperature sensor
    if  'Q(Temp)' in at:
        if "temperature" not in server._idx:
            print "No temperature sensor"
            continue
        tem = server.query_state(server._idx["temperature"])
        if "outlet" not in server._idx:
            print "No outlet"
            continue
        #print "temperature ",tem
        if int(tem) < 1:
            server.change_state(server._idx["outlet"],1)
        elif int(tem) >= 2:
            server.change_state(server._idx["outlet"],0)
    #query motion sensor
    if  'Q(Motion)' in at:
        if "motion" not in server._idx:
            print "No montion sensor"
            continue
        mo = server.query_state(server._idx["motion"])
        
    
    if index+1<len(timel):
        waitTime = float(timel[index+1])+float(setting.start_time) - time.time()+random.random()/50.0
        #print "wt: ",waitTime
        if waitTime>0:
            time.sleep(waitTime)




