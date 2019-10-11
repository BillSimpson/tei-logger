#!/usr/bin/python3
#
# Bill Simpson (wrsimpson@alaska.edu) 8 Oct 2019
#
# This logger captures data from TEI instruments on a RPi
# It uses the serial port connections of these instruments.
# It also uses the "tei" low driver for these instruments

import tei
import time
import datetime
import os

# control variables
write_interval_secs = 30 # will write a data line about this often

time_exception_secs = 100 # if time shifts more than this, there will
# be a time exception and a new file will begin

flush_interval_secs = 75 # this is how often the file actually writes to disk

# newfile file path: if you "touch" this filename, the program will close the
# current file
newfile_path = os.path.expanduser('~/new_file')

# put the output into the report directory
reppath = os.path.expanduser('~/rep/')

# set time format for datetime string in file
timeformat = '%Y-%m-%d %H:%M:%S'

# specifics for time
basevarnames = ['datetime']

# specifics for instruments
varnames = ['CO_ppb','CO_flow_lpm','CO_pres_torr','CO_temp_C','SO2_ppb','SO2_flow_lpm','SO2_pres_torr','SO2_temp_C']

try:
    co = tei.TEInst(48)
    so2 = tei.TEInst(43)

except:
    print('Cannot open serial port connections to instruments')
    exit(1)

# create full header for file
headernames = basevarnames + varnames

# set last write monotonic time to now
lastwrite_monotonic = time.monotonic()

# indicate outfile is not open
outfile_open = False

while True:
    # now read instrument data
    serialvector = []
    # get CO data
    serialvector.append(str(co.conc()))
    serialvector.append(str(co.flow()))
    serialvector.append(str(co.pres()))
    serialvector.append(str(co.temp()))
    # now SO2
    serialvector.append(str(so2.conc()))
    serialvector.append(str(so2.flow()))
    serialvector.append(str(so2.pres()))
    serialvector.append(str(so2.temp()))

    secs_since_write = time.monotonic() - lastwrite_monotonic
    while secs_since_write < write_interval_secs:
        time.sleep(0.5)
        secs_since_write = time.monotonic() - lastwrite_monotonic

    # write some new data
    if not outfile_open:
        outfilename = datetime.datetime.now().strftime('tei-log-%Y%m%dT%H%M%S.txt')
        outfile = open(os.path.join(reppath, outfilename), 'w')
        # write the header line
        outfile.write('\t'.join(headernames)+'\n')
        outfile_open = True
        # set last datetime to now
        last_dt = datetime.datetime.now()
        secs_since_write = 0
        lastflush_monotonic = time.monotonic() 
    # write the data line
    pred_dt = last_dt + datetime.timedelta(seconds=secs_since_write)
    # build the base data
    basedata = []
    basedata.append(pred_dt.strftime(timeformat))
    # concatenate to total vector of base + serial vector
    totalvector = basedata + serialvector
    # write totaldata vector
    outfile.write('\t'.join(totalvector)+'\n')
    # output to console in case anybody is there
    print('\t'.join(totalvector))
    # check if time shifted by more than allowed
    curr_dt = datetime.datetime.now()
    diff_secs = (curr_dt - pred_dt).total_seconds()

    if abs(diff_secs) > time_exception_secs:
        exception_string = 'Time shift exception -- computer time is: '
        exception_string += curr_dt.strftime(timeformat)
        exception_string += ' predicted time was: '
        exception_string += pred_dt.strftime(timeformat)
        exception_string += ' seconds time shifted = '
        exception_string += str(diff_secs)+'\n'
        outfile.write(exception_string)
        outfile.close()
        outfile_open = False
    else:
       # if a new file is requested, do that
       newfile_request = os.path.exists(newfile_path) and os.path.isfile(newfile_path)
       # if date changes, close the old file and let a new one open
       if newfile_request or last_dt.date() < curr_dt.date():
           outfile.close()
           outfile_open = False
           if newfile_request:
               os.remove(newfile_path)

    # set last_dt from current write time
    last_dt = curr_dt
    # set the lastwrite seconds to now
    lastwrite_monotonic = time.monotonic() 

    # check if we should flush (write the file to disk)
    secs_since_flush = time.monotonic() - lastflush_monotonic
    if secs_since_flush > flush_interval_secs:
        try:
            outfile.flush()
            lastflush_monotonic = time.monotonic()
        except:
            outfile_open = False
