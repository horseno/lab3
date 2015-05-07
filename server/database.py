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
 
