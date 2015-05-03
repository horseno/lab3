import socket
import time

sadd = '127.0.0.1' 
port = 18000

period = 5.0

hbmsg = "I am alive too!"

flag = True
hbskt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
hbskt.bind((sadd,port))


msg,add = hbskt.recvfrom(2048)
print msg,add

hbskt.settimeout(period)
while flag:
    t0 = time.time()
    hbskt.sendto(hbmsg,add)
    t1 = time.time()-t0
    time.sleep(max(0,period-t1))
    try:
        msg = hbskt.recv(2048)
    except:
        print "time out"
        break
    if msg != "I am alive!":
        print "wrong msg"
        break
    print msg
    
