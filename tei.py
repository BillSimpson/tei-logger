# use python3
#
# Module for running Thermo Environmental Instrument (TEI)
# instruments over serial interface
#
# wrsimpson@alaska.edu  
# 21 Sep 2019
#
# Note that the instrument ID, you can use the instrument number
# (e.g. 43 for SO2) or the binary number below.  The relationship
# is that the instrument ID is 128 + the model number.  The code
# interprets numbers <128 as model numbers and >128 as iids.
#
# for the TEI 42C = 0xAA
# for the SO2 monitor (43c) = 0xAB
# for the CO monitor (48c) = 0xB0
# for the TEI 49C = 0xB1
# 
# note that I found sending commands too rapidly can cause the
# analyzer to not respond.  I found that with a delay of 0.2 seconds
# nearly all the time it worked, so I made the command_delay = 0.5 seconds

command_delay = 0.5 

import serial
from serial.tools.list_ports import comports
import time

# low level commands  
def send_command(ser,iid,str):
    # wait for the "command delay" time, which is the time
    # needed to wait to get the analyzer ready to respond again
    time.sleep(command_delay)  
    inst_msg = chr(iid) + str + '\r'
    ser.write(inst_msg.encode())

def read_response(ser):
    response = ser.read_until(b'\r').decode()
    # print ('len='+str(len(response))+'<'+response.strip()+'>')
    return(response.strip())

def parse_response(command,response):
    # print('got <'+command+'> response <'+response+'>')
    try:
        return(float(response.partition(command)[2].strip().split(' ')[0]))
    except:
        return(float('NaN'))

# driver class
class TEInst:

    def __init__(self, instrumentID):
        if (instrumentID < 128):
            instrumentID += 128
        self.iid = instrumentID
        self.ser = None
        if self.iid == 0xAB:  # SO2 monitor
            self.conc_command = 'so2'
        else:
            self.conc_command = 'co'

        for try_port in comports():
            print('trying port '+try_port.device)
            self.ser = serial.Serial(port=try_port.device, baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=1, xonxoff=False, rtscts=False, dsrdtr=False)
            send_command(self.ser,self.iid,'instr name')
            response = read_response(self.ser)
            print('got response <'+response+'>')
            if response:
                print('port '+try_port.device+' matched instrument ID')
                break
            else:
                self.ser = None
                
    def conc(self):
        command = self.conc_command
        
        if self.ser:
            send_command(self.ser,self.iid,command)
            response = read_response(self.ser)
            return(parse_response(command,response))

    def flow(self):
        command = 'flow'
        
        if self.ser:
            send_command(self.ser,self.iid,command)
            response = read_response(self.ser)
            return(parse_response(command,response))
        
    def pres(self):
        command = 'pres'
        
        if self.ser:
            send_command(self.ser,self.iid,command)
            response = read_response(self.ser)
            return(parse_response(command,response))       
        
    def temp(self):
        command = 'internal temp'
        
        if self.ser:
            send_command(self.ser,self.iid,command)
            response = read_response(self.ser)
            return(parse_response(command,response))       
