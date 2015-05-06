import xmlrpclib 
import SimpleXMLRPCServer
import time
import threading
import csv
import socket
import select
import sys
sys.path.append("./")
import setting
import random

#class for user process
class UserProcess(object):
	#initial
    def __init__(self,localadd,devNum):
        self._isLeader = 0 #whether it is leader
        self._electID = random.random() #id for election
        self._timeoffset = 0 #synchronized time offset
        
        self._mode = "HOME"
        self._gid = -1 #global id 
        self._localadd = localadd
        self.log=open("results/user_output.txt",'w+') #output file
    
    #thread for listening 
    def start_listen(self):
        self.s = SimpleXMLRPCServer.SimpleXMLRPCServer(self._localadd,logRequests=False)#zerorpc.Server(self)
        self.s.register_instance(self)
        self.s.serve_forever()
    	#s = zerorpc.Server(self)
        #s.bind(self._localadd)
        #s.run()
    
    #rpc call for register
    def register(self):
        self.c = xmlrpclib.ServerProxy("http://"+setting.serveradd[0]+":"+str(setting.serveradd[1]))
        self._gid = self.c.register("user","user",self._localadd)
        return 1

    #rpc interface for text message
    def text_message(self,msg):
        self.log.write(msg+'\n')
        return 1

    #rpc call for change mode 
    def change_mode(self,mode):
        self.c.change_mode(mode)
        self._mode = self.c.change_mode(mode)
        return 1



#thread for listening   			
class user(threading.Thread):
    def __init__(self,user):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self._user = user
    def run(self):
        self._user.start_listen()
#read test case
def readTest(filename,col):
        with open(filename, 'rb') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
            time=[]
            action=[]
            spamreader.next()
            for row in spamreader:
            	#print row,row[0],len(
                time.append(row[0])
                action.append(row[col])     
            return time, action    
        
timel,action = readTest('test-input.csv',6)
devNum = setting.devNum
myuser = UserProcess(setting.localadd["user"],devNum)

#myuser.leader_elect()
#myuser.time_syn()
listen_thread = user(myuser)
listen_thread.start()


#calculate start time
current_time = int(time.time())
waitT = setting.start_time - current_time
time.sleep(waitT)

if action[0]!='Register':
            print "Error: register client first"
myuser.register()
waitTime = float(timel[1])+float(setting.start_time) - time.time()
if waitTime>0:
    time.sleep(waitTime)
for index in range(1,len(timel)):
    if  action[index] == "HOME" or action[index] == "AWAY":
        if myuser._mode != action[index]:
        	myuser.change_mode(action[index])
    if index+1<len(timel):
        waitTime = float(timel[index+1])+float(setting.start_time) - time.time()
        if waitTime>0:
            time.sleep(waitTime)

