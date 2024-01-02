import sys
import ctypes
import datetime
import time

########################################################################
# D2XX definitions
def check(f):
    if f != 0:
        names = [
            "FT_OK",
            "FT_INVALID_HANDLE",
            "FT_DEVICE_NOT_FOUND",
            "FT_DEVICE_NOT_OPENED",
            "FT_IO_ERROR",
            "FT_INSUFFICIENT_RESOURCES",
            "FT_INVALID_PARAMETER",
            "FT_INVALID_BAUD_RATE",
            "FT_DEVICE_NOT_OPENED_FOR_ERASE",
            "FT_DEVICE_NOT_OPENED_FOR_WRITE",
            "FT_FAILED_TO_WRITE_DEVICE",
            "FT_EEPROM_READ_FAILED",
            "FT_EEPROM_WRITE_FAILED",
            "FT_EEPROM_ERASE_FAILED",
            "FT_EEPROM_NOT_PRESENT",
            "FT_EEPROM_NOT_PROGRAMMED",
            "FT_INVALID_ARGS",
            "FT_NOT_SUPPORTED",
            "FT_OTHER_ERROR"]
        raise IOError("Error: (status %d: %s)" % (f, names[f]))
    
FT_BAUDRATE=12000000
FT_PROG_BAUDRATE=500000
FT_DATA_BITS=8
FT_STOP_BITS_1=0
FT_PARITY=0
LATENCY_STD=16
LATENCY_RT=0   


########################################################################
# Main Program
#
# Implements simple GetComPortNumber example from D2XX programmers guide

class D2XXTest(object):
    def __init__(self):
        #Load driver binaries
        if sys.platform.startswith('linux'):
            self.d2xx = ctypes.cdll.LoadLibrary("libftd2xx.so")
        elif sys.platform.startswith('darwin'):
            self.d2xx = ctypes.cdll.LoadLibrary("libftd2xx.dylib")
        else:
            self.d2xx = ctypes.windll.LoadLibrary("ftd2xx")
        print('D2XX library loaded OK')
        print
        sys.stdout.flush()

    def openDev(self, baudrate=FT_BAUDRATE, latency=LATENCY_STD):
        #create FT Handle variable
        self.ftHandle = ctypes.c_void_p()
        #Open the first device on the system
        check(self.d2xx.FT_Open( 1, ctypes.byref(self.ftHandle)))
        #check(self.d2xx.FT_OpenEx(ctypes.byref(ctypes.c_wchar_p("Digilent Adept USB Device B")), ctypes.c_double(2), ctypes.byref(self.ftHandle)))
        print('Device opened OK')
        check(self.d2xx.FT_SetBaudRate( self.ftHandle, ctypes.c_ulong(baudrate)))
        check(self.d2xx.FT_SetDataCharacteristics( self.ftHandle, ctypes.c_byte(8), ctypes.c_byte(0), ctypes.c_byte(0)))
        check(self.d2xx.FT_SetTimeouts( self.ftHandle, ctypes.c_ulong(10), ctypes.c_ulong(30)))
        check(self.d2xx.FT_SetLatencyTimer( self.ftHandle, ctypes.c_ubyte(latency)))
        check(self.d2xx.FT_SetUSBParameters( self.ftHandle, ctypes.c_ulong(4096), 0))
        print('Device configured OK')

    def closeDev(self):
        check(self.d2xx.FT_SetTimeouts( self.ftHandle, ctypes.c_ulong(10), ctypes.c_ulong(30)))
        check(self.d2xx.FT_Close(self.ftHandle))
        print('Device closed OK')

    def drainInput(self):
        readBuffer = ctypes.create_string_buffer(10)
        bytesReturned = ctypes.c_ulong()
        bytesAvailable = ctypes.c_ulong()
        totalDrained = 0
        tries = 0
        check(self.d2xx.FT_GetQueueStatus(self.ftHandle, ctypes.byref(bytesAvailable)))
        if bytesAvailable.value > 0:
            check(self.d2xx.FT_Read(self.ftHandle, ctypes.byref(readBuffer), bytesAvailable, ctypes.byref(bytesReturned)))
            totalDrained += bytesReturned.value
        tries += 1
        #time.sleep(0.05)
        print("Drained %d bytes" % totalDrained)
        #print("%s" % readBuffer[0].hex())

    def writeParameter(self, parameter, value):
        # we don't get anything back from the device
        # so just a write here.
        writeBuffer = ctypes.create_string_buffer(4)
        writeBuffer[0] = ctypes.c_char(0x73) # 's'
        if(parameter > 254):
            writeBuffer[1] = ctypes.c_char(255)
            writeBuffer[2] = ctypes.c_char(parameter - 256)
            writeBuffer[3] = ctypes.c_char(value)
            toSend = 4
        else:
            writeBuffer[1] = ctypes.c_char(parameter)
            writeBuffer[2] = ctypes.c_char(value)
            toSend = 3

        bytesWritten = ctypes.c_ulong()
        check(self.d2xx.FT_Write(self.ftHandle, ctypes.byref(writeBuffer), toSend, ctypes.byref(bytesWritten)))
        print("Parameter written: %d %d" % (parameter, value))

        #self.drainInput()
        # this thing is so fast we can read it back to verify
        #print("Parameter read back: %d %d" % (parameter, self.getParameter(parameter)))

    def getParameter(self, parameter):
        writeBuffer = ctypes.create_string_buffer(3)
        writeBuffer[0] = ctypes.c_char(0x67) # 'g'
        if(parameter > 254):
            writeBuffer[1] = ctypes.c_char(255)
            writeBuffer[2] = ctypes.c_char(parameter - 256)
            toSend = 3
        else:
            writeBuffer[1] = ctypes.c_char(parameter)
            toSend = 2


        bytesWritten = ctypes.c_ulong()
        check(self.d2xx.FT_Write(self.ftHandle, ctypes.byref(writeBuffer), toSend, ctypes.byref(bytesWritten)))
        
        readBuffer = ctypes.create_string_buffer(1)
        bytesReturned = ctypes.c_ulong()
        bytesAvailable = ctypes.c_ulong()
        tries = 0
        while(tries < 10):
            check(self.d2xx.FT_GetQueueStatus(self.ftHandle, ctypes.byref(bytesAvailable)))
            if bytesAvailable.value > 0:
                check(self.d2xx.FT_Read(self.ftHandle, ctypes.byref(readBuffer), 1, ctypes.byref(bytesReturned)))
                break
            tries += 1
            time.sleep(0.05)

        print("Parameter read: %d %d %d" % (parameter, int.from_bytes(readBuffer[0]), tries))
        return int.from_bytes(readBuffer[0])
        
    def getAllParameters(self):
        writeBuffer = ctypes.create_string_buffer(1)
        writeBuffer[0] = ctypes.c_char(0x64) # 'd'
        toSend = 1

        bytesWritten = ctypes.c_ulong()
        check(self.d2xx.FT_Write(self.ftHandle, ctypes.byref(writeBuffer), toSend, ctypes.byref(bytesWritten)))
        
        readBuffer = ctypes.create_string_buffer(512)
        bytesReturned = ctypes.c_ulong()
        bytesAvailable = ctypes.c_ulong()
        bytesTotal = 0
        tries = 0
        while(bytesTotal < 512 and tries < 10):
            check(self.d2xx.FT_GetQueueStatus(self.ftHandle, ctypes.byref(bytesAvailable)))
            if bytesAvailable.value > 0:
                check(self.d2xx.FT_Read(self.ftHandle, ctypes.byref(readBuffer), 512, ctypes.byref(bytesReturned)))
                bytesTotal += bytesReturned.value
                if(bytesTotal >= 512):
                    break
            tries += 1
            time.sleep(0.05)
            

        print("Bytes read: %d in %d tries" % (bytesTotal, tries))
        patchDict = {}
        if(bytesTotal == 512):
            for i in range(0, 256):
                #print("%d %d" % (i, int.from_bytes(readBuffer[i])))
                patchDict[i] = int.from_bytes(readBuffer[i])

        return patchDict
    
    def loadPatch(self, patchNumber):

        start = datetime.datetime.now()
        #create read buffer
        readBuffer = ctypes.create_string_buffer(1)
        writeBuffer = ctypes.create_string_buffer(2)
        writeBuffer[0] = ctypes.c_char(0x72)
        writeBuffer[1] = ctypes.c_char(patchNumber)
        #create number of bytes variable
        bytesReturned = ctypes.c_ulong()
        bytesWritten = ctypes.c_ulong()
        bytesAvailable = ctypes.c_ulong()

        self.d2xx.FT_Write(self.ftHandle, ctypes.byref(writeBuffer), 2, ctypes.byref(bytesWritten))

        totalRead = 0
        tries = 0
        while(totalRead < 2 and tries < 10):
            check(self.d2xx.FT_GetQueueStatus(self.ftHandle, ctypes.byref(bytesAvailable)))
            if bytesAvailable.value > 0:
                check(self.d2xx.FT_Read(self.ftHandle, ctypes.byref(readBuffer), 1, ctypes.byref(bytesReturned)))
                totalRead += bytesReturned.value
            tries += 1
            time.sleep(0.05)

        #print(tries)

        print("Patch loaded: #%d (%s)" % (patchNumber, readBuffer[0].hex()))
    
    def monitorPort(self, duration):
        start = datetime.datetime.now()
        #create read buffer
        readBuffer = ctypes.create_string_buffer(3)
        #create number of bytes variable
        bytesReturned = ctypes.c_ulong()
        bytesAvailable = ctypes.c_ulong()

        # open the device
        self.openDev(FT_BAUDRATE, LATENCY_STD)

        #read three bytes at a time, coincidentally the size of MIDI
        # we exit once we've done our time
        while True:
            check(self.d2xx.FT_GetQueueStatus(self.ftHandle, ctypes.byref(bytesAvailable)))
            if bytesAvailable.value > 0:
                check(self.d2xx.FT_Read(self.ftHandle, ctypes.byref(readBuffer), 3, ctypes.byref(bytesReturned)))
                #print data
                print("Data read: ", end="")
                for i in range(0, bytesReturned.value):
                    print(' %s ' % readBuffer[i].hex(), end="")
                print()
                sys.stdout.flush()

            if datetime.datetime.now() - start > datetime.timedelta(seconds=duration):
                self.closeDev()
                return

    
if __name__ == '__main__':
 
    print("===== Python D2XX Get Com Port =====")
    print
    app = D2XXTest()
    app.loadPatch(53)
    #app.monitorPort(30)
