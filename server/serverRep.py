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
class Gateway_Rep(object):
	#initial class
    def __init__(self):
        self._n = 2 #number of registered devices
        self._idlist = [["gateway","gateway",setting.serveradd,0],["gateway","replica",setting.replicaadd,1]]#list for registered devices
        self._mode = "HOME"
        self.serveradd = setting.serveradd #server address
        self.Dbadd = setting.DbRepadd
        self.lasttime = -1 #last time the motion sensor was on
        self.log = open("results/serverRep_log.txt",'w+') #server log file
        self._idx = {"gateway":0,"replica":1} #index for global id
        self.replicaadd = setting.replicaadd
        self.cacheSize = setting.cacheSize
        self.cache = []

    #lookup the cache to see if a client has its state in cache
    def cache_lookup(self,id):
        for i in range(len(self.cache)):
            if self.cache[i][0] == id:
                return i
        #cache miss
        return -1
    #update the cache if the state of a client changes
    def cache_update(self,id,state,timestamp):
        index = self.cache_lookup(id)
        if index >= 0:
            self.cache[index] = [id,state,timestamp]
            return 1
        else:
            return -1

    #load data into cache after read from the database. If cache is full, replace using random replacement strategy.
    def cache_load(self,id, state, timestamp): 
        if len(self.cache)<self.cacheSize:
            self.cache.append([id,state,timestamp])
        else:
            replace = random.randint(0,len(self.cache)-1)
            self.cache[replace] = [id,state,timestamp]
        return 1
        
    # thread for server listening
    def start_listen(self):
        self.s = SimpleXMLRPCServer.SimpleXMLRPCServer(self.replicaadd,logRequests=False)#start a RPC Server
        self.s.register_instance(self)# register RPC bject
        self.s.serve_forever()# start listening
        
    #heart beat protocol
    def heartbeat(self):
        period = 2.0
        hbskt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        hbskt.settimeout(period)
        while True:
            hbskt.sendto("Gateway 1 alive!",setting.heartport)
            try:
                msg = hbskt.recv(2048)
            except:
                print round(time.time()-setting.start_time,2),"Gateway 0 failure!"
                self.notifyclients()
                break
            print msg
            time.sleep(period)
    
    #notify clients the failure of the other gateway
    def notifyclients(self):
        for i in range(2,self._n):
            if i%2 == 0:
                c = xmlrpclib.ServerProxy(self._idlist[i][2])
                c.change_server(self.replicaadd)
    
    #rpc call for query state
    def query_state(self,id):
    	# checking invalidate id
        if id >= self._n:
            print "GateWay 1: Wrong Id"
            print "GateWay 1: Wrong Id" + "id: "+ str(id) + "self_N: "+ str(self._n)
            return -1
        #set up connection
        c = xmlrpclib.ServerProxy(self._idlist[id][2])
        #rpc call
        state = c.query_state()
        #get timestamp
        timestmp = round(time.time()-setting.start_time,2)
        t1 = time.time()
        self.writedb(id,state,timestmp)
        #print "GateWay 1: writedb takes",time.time()-t1
        #log
        self.log.write(str(round(time.time()-setting.start_time,2))+','+self._idlist[id][1]+','+state+'\n')
        print "GateWay 1: "+str(round(time.time()-setting.start_time,2))+','+self._idlist[id][1]+','+state+'\n'
        #record the last time motion sensor was on 
        if self._idlist[id][1] == "motion":
            if server._mode == "HOME":
                if "bulb" not in server._idx:
                    print "GateWay 1: No bulb"
                    return state
                if state == '1':
                    self.lasttime = time.time()
                    self.change_state(self._idx["bulb"],'1')
                else:
                    if self.lasttime != -1 and time.time()-self.lasttime > 3:
                        self.change_state(self._idx["bulb"],'0')
            #away mode set message if there is motion
            else:
                if state == '1':
                    print "GateWay 1: Server: Someone in your room!"
                    self.text_message("Someone in your room!")
        return state
    
    #write to db
    def writedb(self,id,state,timestmp):
        self.writedb_local(id,state,timestmp)

        #remote write on the master server
        try: 
            rc = xmlrpclib.ServerProxy("http://"+self.serveradd[0]+":"+str(self.serveradd[1]))
            rc.writedb_local(id,state,timestmp)
        except:
            pass
        self.cache_update(id,state,timestmp)
        return 1

    def writedb_local(self,id,state,timestmp):
        c = xmlrpclib.ServerProxy("http://"+self.Dbadd[0]+":"+str(self.Dbadd[1]))
        c.write(id,state,timestmp)
        return 1

    #read from db    
    def readdb(self,id,timestmp):
        idx = self.cache_lookup(id)
        if idx >-1:
            state = 0
            thit = time.time()
            if abs(self.cache[idx][2]-timestmp)<2:
                state = self.cache[idx][2]
            print "Gateway 1: cache hit takes",(time.time()-thit)*1000,"ms"
        else:
            tmiss=time.time()
            c = xmlrpclib.ServerProxy("http://"+setting.Dbadd[0]+":"+str(setting.Dbadd[1]))
            state = c.read_offset(id,timestmp,2)
            self.cache_load(id,state,timestmp)
            print "Gateway 1: cache miss takes",(time.time()-tmiss)*1000,"ms"
        return state
        
    #rpc interface for report state
    def report_state(self, id, state):
    	#checking invalidate id
        if id >= self._n:
            print "GateWay 1: Wrong Id"
            print "GateWay 1: Wrong Id" + "id: "+ str(id) + "self_N: "+ str(self._n)
            return -1
        #get timestamp
        timestmp = round(time.time()-setting.start_time,2)
        t1 =time.time()
        self.writedb(id,state,timestmp)
        #print "GateWay 1: writedb takes",time.time()-t1
        #log
        self.log.write(str(round(time.time()-setting.start_time,2))+','+self._idlist[id][1]+','+state+'\n')
        print "GateWay 1: "+str(timestmp)+','+self._idlist[id][1]+','+state+'\n'
    	#event ordering
        if state == '1' and (self._idlist[id][1] == "motion" or self._idlist[id][1] == "door"):
            if self._idlist[id][1] == "motion":
                t0 = time.time()
                ds = self.readdb(self._idx["door"],timestmp)
                bs = self.readdb(self._idx["beacon"],timestmp)
                #print "GateWay 1: readdb takes",time.time()-t0
                if ds == 1 and bs == 1 and self._mode == "AWAY":
                    self._mode = "HOME"
            else:
                t0 = time.time()   
                ms = self.readdb(self._idx["motion"],timestmp)
                #print "GateWay 1: readdb takes",time.time()-t0
                if ms == 1 and self._mode == "HOME":
                    self._mode = "AWAY" 
            print "GateWay 1: Server mode:",server._mode

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
                    print "GateWay 1: Server: Someone in your room!"
                    self.text_message("Someone in your room!")
        return 1
        
    #rpc call for change state    
    def change_state(self, id, state):
    	#checking invalidate id
        if id >= self._n:
            print "GateWay 1: Wrong Id"
            print "GateWay 1: Wrong Id" + "id: "+ str(id) + "self_N: "+ str(self._n)
            return -1
        #set up connection
        c = xmlrpclib.ServerProxy(self._idlist[id][2])
        flag = 0
        
        #rpc call
        if c.change_state(state):
            flag = 1
        return flag

    #receiving register information from the master server
    def recieve_register_info(self,cid,type,name,address,n):
        self._idlist.append([type,name,"http://"+address[0]+":"+str(address[1])])
        self._idx[name] = cid
        self._n =n 
        if cid %2 == 1:
            self.log.write(str(round(time.time()-setting.start_time,2))+','+name+','+str(self._n - 1)+'\n')
            print "Gateway 1: "+str(round(time.time()-setting.start_time,2))+','+name+','+str(self._n - 1)+'\n'
        return 1
    
    #rpc call for text message    
    def text_message(self,msg):
    	#checking invalidate id
        if "user" not in self._idx:
            print "GateWay 1: No user process"
            return
        #set up connection
        c = xmlrpclib.ServerProxy(self._idlist[self._idx["user"]][2])
        #rpc call
        c.text_message(str(round(time.time()-setting.start_time,2))+","+msg)
        
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

#thread for hearbeat
class hb(threading.Thread):
    def __init__(self,server):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.server = server
    def run(self):
        self.server.heartbeat()

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


timel,action = readTest(setting.testcase,6)

server = Gateway_Rep()
listen_thread = myserver(server)
listen_thread.start()
time.sleep(0.5)
hb_thread = hb(server)
hb_thread.start()

#calcuate start time
current_time = int(time.time())
waitT = setting.start_time - current_time
time.sleep(waitT)

for index in range(len(timel)):
    at = action[index].split(';')
    
    #query beacon sensor
    if  'Q(Beacon)' in at:
        if "beacon" not in server._idx:
            print "No beacon sensor"
            continue
        tem = server.query_state(server._idx["beacon"])
    
    if 'Fault' in at:
        #print "Fault"
        break
        
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




