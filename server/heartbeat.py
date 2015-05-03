import socket
import time

add = '127.0.0.1'
port = 18000

period = 5.0
hbmsg = "I am alive!"
hbskt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
hbskt.settimeout(period)

while True:
    #t0 = time.time()
    hbskt.sendto(hbmsg,(add,port))
    try:
        msg = hbskt.recv(2048)
    except:
        print "time out"
        break
    if msg != "I am alive too!":
        print "wrong msg"
        break
    print msg
    #t1 = time.time()-t0
    time.sleep(period)
