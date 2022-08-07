import os
import csv
import time

def fix_string(value):
    if len(value) == 0:
        return '""'
    else:
        return value;

def fix_float(value):
    if len(value) == 0:
        return '0.0'
    else:
        return value;

def fix_time(value):
    timeArray = time.strptime(value[0:19], "%Y-%m-%d %H:%M:%S")
    timeStamp = int(time.mktime(timeArray))
    return str(timeStamp)

now = time.time()
ts_temp=int(now*1000000000)

files = os.listdir('/home/flightlist')
for file in files:
    if file.endswith('.csv'):
        with open('/home/flightlist/' + file[0:len(file)-4] + '.txt', 'w') as txt:
            txt.write('# DDL')
            txt.write('\n')
            txt.write('CREATE DATABASE test')
            txt.write('\n\n')
            txt.write('# DML')
            txt.write('\n')
            txt.write('# CONTEXT-DATABASE: test')
            txt.write('\n')  
            with open('/home/flightlist/' + file) as csvfile:
                isHead = True;
                readcsv = csv.reader(csvfile)
                for row in readcsv:
                    if isHead is True:
                        isHead = False;
                        continue;
                    txt.write('\n')
                    txt.write('opensky')
                    # txt.write(' callsign=' + fix_string(row[0]))
                    # txt.write(',number=' + fix_string(row[1]))
                    # txt.write(',icao24=' + fix_string(row[2]))
                    # txt.write(',registration=' + fix_string(row[3]))
                    # txt.write(',typecode=' + fix_string(row[4]))
                    txt.write(',origin=' + fix_string(row[5]))
                    txt.write(',destination=' + fix_string(row[6]))
                    txt.write(' firstseen=' + fix_time(row[7]))
                    txt.write(',lastseen=' + fix_time(row[8]))
                    txt.write(',day=' + fix_time(row[9]))
                    txt.write(',latitude_1=' + fix_float(row[10]))
                    txt.write(',longitude_1=' + fix_float(row[11]))
                    txt.write(',altitude_1=' + fix_float(row[12]))
                    txt.write(',latitude_2=' + fix_float(row[13]))
                    txt.write(',longitude_2=' + fix_float(row[14]))
                    txt.write(',altitude_2=' + fix_float(row[15]))
                    ts_temp = ts_temp + 1 
                    txt.write(' ' + str(ts_temp))
            txt.write('\n')
        txt.close()