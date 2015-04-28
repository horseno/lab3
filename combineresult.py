import csv
import time
time.sleep(25)
testinput = open('test-input.csv', 'rb')
gateway_log = open('results/server_log.txt', 'r')
useroutput = open('results/user_output.txt', 'r')
bulb_log =  open('results/devout-bulb.txt', 'r')
outlet_log = open('results/devout-outlet.txt', 'r')

reader = csv.reader(testinput, delimiter=',', quotechar='|')

head = reader.next()
head.append('ServerOutput')
head.append('UserOutput')
head.append('Bulb')
head.append('Outlet')

table = []
for row in reader:
	table.append(row)


reader = csv.reader(gateway_log, delimiter=',', quotechar='|')
preline = -1
tem = '0'
mo = '0'
ll = len(table[0])
for row in reader:
    if row[1] == "temperature":
        line = -1
        for i in range(len(table)-1):
            if float(row[0])>= float(table[i][0]) and float(row[0])< float(table[i+1][0]):
		    	line = i
		    	if i == 0:
		    		if len(table[i]) == ll:
		    			table[i].append(row[0]+':'+tem+';'+mo)
		    	else:
		    		tem = row[2]
		    		if len(table[i]) == ll:
		    			table[i].append(row[0]+':'+tem+';'+mo)
		    		else:
		    			table[i][5] = row[0]+':'+tem+';'+mo
        if line == -1:
			tem = row[2]
			if len(table[len(table)-1]) == ll:
				if len(table[len(table)-1]) == ll:
		    			table[len(table)-1].append(row[0]+':'+tem+';'+mo)
		    		else:
		    			table[len(table)-1][ll] = row[0]+':'+tem+';'+mo
    elif row[1] == "motion":
        line = -1
        for i in range(len(table)-1):
             if float(row[0])>= float(table[i][0]) and float(row[0])< float(table[i+1][0]):
		    	line = i
		    	if i == 0:
		    		if len(table[i]) == ll:
		    			table[i].append(row[0]+':'+tem+';'+mo)
		    	else:
		    		mo = row[2]
		    		if len(table[i]) == ll:
		    			table[i].append(row[0]+':'+tem+';'+mo)
		    		else:
		    			table[i][ll] = row[0]+':'+tem+';'+mo
        if line == -1:
			mo = row[2]
			if len(table[len(table)-1]) == ll:
				if len(table[len(table)-1]) == ll:
		    			table[len(table)-1].append(str(row[0])+':'+tem+';'+mo)
		    		else:
		    			table[len(table)-1][ll] = str(row[0])+':'+tem+';'+mo
ll=ll+1	    			
for l in range(len(table)):
	if len(table[l])<ll:
		table[l].append('')
	
reader = csv.reader(useroutput, delimiter=',', quotechar='|')
for row in reader:
	line = -1
	for i in range(len(table)-1):
		if float(row[0])>= float(table[i][0]) and float(row[0])< float(table[i+1][0]):
		    line = i
		    table[i].append(row[1])
	if line == -1:
		table[len(table)-1].append(row[1])
ll=ll+1
for l in range(len(table)):
	if len(table[l])<ll:
		table[l].append('')
		
reader = csv.reader(bulb_log, delimiter=',', quotechar='|')
for row in reader:
	line = -1
	for i in range(len(table)-1):
		if float(row[0])>= float(table[i][0]) and float(row[0])< float(table[i+1][0]):
		    line = i
		    table[i].append(row[1])
	if line == -1:
		table[len(table)-1].append(row[1])
ll=ll+1
for l in range(len(table)):
	if len(table[l])<ll:
		table[l].append('')


reader = csv.reader(outlet_log, delimiter=',', quotechar='|')
for row in reader:
	line = -1
	for i in range(len(table)-1):
		if float(row[0])>= float(table[i][0]) and float(row[0])< float(table[i+1][0]):
		    line = i
		    table[i].append(row[1])
	if line == -1:
		table[len(table)-1].append(row[1])
ll=ll+1	
for l in range(len(table)):
	if len(table[l])<ll:
		table[l].append('')

textoutput = open("test-output.csv",'w+')

textoutput.write(head[0])
for l in range(1,len(head)):
	textoutput.write(','+head[l])
textoutput.write('\n')

for row in table:
    textoutput.write(row[0])
    for l in range(1,len(row)):
	    textoutput.write(','+row[l])
    textoutput.write('\n')
