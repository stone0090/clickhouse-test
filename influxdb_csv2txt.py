import os
import csv
import time

def fix_tag(tagString):
    if len(tagString) == 0:
        return '-'
    else:
        return tagString;

def fix_value(valueString):
    if len(valueString) == 0:
        return '0.0'
    else:
        return valueString;

def fix_time(timeString):
    timeArray = time.strptime(timeString[0:19], "%Y-%m-%d %H:%M:%S")
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
                    txt.write(',callsign=' + fix_tag(row[0]))
                    txt.write(',number=' + fix_tag(row[1]))
                    txt.write(',icao24=' + fix_tag(row[2]))
                    txt.write(',registration=' + fix_tag(row[3]))
                    txt.write(',typecode=' + fix_tag(row[4]))
                    txt.write(',origin=' + fix_tag(row[5]))
                    txt.write(',destination=' + fix_tag(row[6]))
                    txt.write(',firstseen=' + fix_time(row[7]))
                    txt.write(',lastseen=' + fix_time(row[8]))
                    txt.write(',day=' + fix_time(row[9]))
                    txt.write(' latitude_1=' + fix_value(row[10]))
                    txt.write(',longitude_1=' + fix_value(row[11]))
                    txt.write(',altitude_1=' + fix_value(row[12]))
                    txt.write(',latitude_2=' + fix_value(row[13]))
                    txt.write(',longitude_2=' + fix_value(row[14]))
                    txt.write(',altitude_2=' + fix_value(row[15]))
                    ts_temp = ts_temp + 1 
                    txt.write(' ' + str(ts_temp))
            txt.write('\n')
        txt.close()