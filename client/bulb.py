import smartDev
import threading
import time
import os
import csv
import sys
sys.path.append("./")
import setting

#get ip information from setting file 
serveradd = setting.serveradd
localadd = setting.localadd[os.path.basename(__file__).split('.',1)[0]]
devNum = setting.devNum

class temperature (threading.Thread):
    def __init__(self,client):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.client = client

    def run(self):
        self.client.start_listen()


def main(): 
    def start_sync():
        '''sync time of different process before running'''
        current_time = int(time.time())
        waitT = setting.start_time - current_time
        time.sleep(waitT)

    temp = smartDev.SmartDev("bulb",serveradd,localadd,devNum)
    
    # create a thread to listen, deal with server pulls
    #temp.leader_elect()
    #temp.time_syn()
    listen_thread = temperature(temp)
    listen_thread.start()
    
    
    start_sync()
    temp.register_to_server() 

    #wait for query and change instruction
    time.sleep(30)


if __name__ == "__main__":
    main()