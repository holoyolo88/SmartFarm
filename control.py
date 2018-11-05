from control_gui import *
from DEF import *
from StyleSheet import *
import PyQt5
import pyqtgraph as pg
import sys
import glob
import serial
import asyncio
import serial_asyncio
from threading import Thread
import time
import datetime
import json



class UartCom():
    connect_port=[]
    def __init__(self, ui, eventThred):
        self.ui=ui
        self.get_com()
                            
        ui.pushButton_comconnect.clicked.connect(lambda x:self.connect_serial())
        ui.pushButton_check.clicked.connect(lambda x: self.sendUart())
        ui.pushButton_airpower.clicked.connect(lambda x: self.controlAirpower())
        ui.pushButton_windpower.clicked.connect(lambda x: self.controlWindpower())
        ui.pushButton_ledpower.clicked.connect(lambda x: self.controlLEDpower())
        ui.pushButton_uvpower.clicked.connect(lambda x: self.controlUVpower())

        ui.pushButton_pumppower1.clicked.connect(lambda x: self.controlPumppower(1, BATH1))
        ui.pushButton_heaterpower1.clicked.connect(lambda x: self.controlHeaterpower(1, BATH1))
        ui.pushButton_pumppower2.clicked.connect(lambda x: self.controlPumppower(2, BATH2))
        ui.pushButton_heaterpower2.clicked.connect(lambda x: self.controlHeaterpower(2, BATH2))
        ui.pushButton_pumppower3.clicked.connect(lambda x: self.controlPumppower(3, BATH3))
        ui.pushButton_heaterpower3.clicked.connect(lambda x: self.controlHeaterpower(3, BATH3))
        ui.pushButton_pumppower4.clicked.connect(lambda x: self.controlPumppower(4, BATH4))
        ui.pushButton_heaterpower4.clicked.connect(lambda x: self.controlHeaterpower(4, BATH4))
        self.uart = None

    def get_com(self):
        if sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            self.isLinux = True
        else:
            self.isLinux = False

        COM_Ports=self.serial_ports()
        for port in COM_Ports:
            if port.find('COM') > -1:
                self.connect_port.append(port)
        print (self.connect_port)
        for comport in self.connect_port:
            ui.comboBox_coms.addItem(comport)

    def serial_ports(self):  
        if sys.platform.startswith('win'):   
            ports = ['COM%s' % (i + 1) for i in range(256)]   
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):   
            # this excludes your current terminal "/dev/tty"   
            ports = glob.glob('/dev/tty[A-Za-z]*')   
        elif sys.platform.startswith('darwin'):   
            ports = glob.glob('/dev/tty.*')   
        else:   
            raise EnvironmentError('Unsupported platform')   
        result = []   
        for port in ports:   
            try:   
                s = serial.Serial(port)   
                s.close()   
                result.append(port)   
            except (OSError, serial.SerialException):  
                pass
                #print ('OSError')   
        return result

    def run(self, loop):
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        print("Closed Uart thread!")


    def connect_serial(self):
        print('connect_serial_called')
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        com_no = str(ui.comboBox_coms.currentText())

        if self.isLinux:
            self.coro = serial_asyncio.create_serial_connection(self.loop, lambda: UartProtocol(self, eventThread), self.mcuPort, baudrate=115200)
            print('Connected mcu port = '+self.mcuPort)
        else:
            print(str(com_no)+' connected')
            self.coro = serial_asyncio.create_serial_connection(self.loop, lambda: UartProtocol(self, eventThread), com_no, baudrate=115200)
        self.loop.run_until_complete(self.coro)

        t = Thread(target=self.run, args=(self.loop,))
        t.start()
        #self.loop.call_soon_threadsafe(asyncio.async , self.coro)
        pass


    def printLog(self, msg):
        print('<{!r}> {!r}'.format(self.getTimeStamp(), msg))


    def sendUart(self):
        self.sendT1()
        time.sleep(.2)
        self.sendT2()
        time.sleep(.3)
        self.sendWater()
        time.sleep(.5)
    
    def sendT1(self):
        msg = '\x02T1TEMP?\x03\x0A\x0D'
        print(msg)
        if self.uart != None:
            self.uart.write(msg.encode())        
        else : 
            print('Not Connected')

    def sendT2(self):
        msg = '\x02T2TEMP?\x03\x0A\x0D'
        print(msg)
        if self.uart != None:
            self.uart.write(msg.encode())        
        else : 
            print('Not Connected')

    def sendWater(self):
        msg = '\x02WNWATER?\x03\x0A\x0D'
        print(msg)
        if self.uart != None:
            for i in range(1,5):
                self.uart.write(msg.replace('N', str(i)).encode())
                time.sleep(.02)      
        else : 
            print('Not Connected')
    
    def controlAirpower(self):
        if ACTUATOR.AIR['power'] == 'OFF':
            msg = '\x02B1BO\x03\x0A\x0D'
        else:
            msg = '\x02B1BX\x03\x0A\x0D'
        if self.uart != None:
                self.uart.write(msg.encode())    
        else : 
            print('Not Connected')

    def controlWindpower(self):
        if ACTUATOR.WIND['power'] == 'OFF':
            msg = '\x02F1FO\x03\x0A\x0D'
        else:
            msg = '\x02F1FX\x03\x0A\x0D'
        if self.uart != None:
                self.uart.write(msg.encode())    
        else : 
            print('Not Connected')

    def controlLEDpower(self):
        if ACTUATOR.LED['power'] == 'OFF':
            msg = '\x02L00W255R255G255B255\x03\x0A\x0D'
        else:
            msg = '\x02L00W000R000G000B000\x03\x0A\x0D'
        if self.uart != None:
                self.uart.write(msg.encode())    
        else : 
            print('Not Connected')

    def controlUVpower(self):
        if ACTUATOR.UV['power'] == 'OFF':
            msg = '\x02U1UO\x03\x0A\x0D'
        else:
            msg = '\x02U1UX\x03\x0A\x0D'
        if self.uart != None:
                self.uart.write(msg.encode())    
        else : 
            print('Not Connected')

    def controlHeaterpower(self, ID, BATH):
        if BATH.HEATER == 'OFF':
            msg = '\x02H'+str(ID)+'HO\x03\x0A\x0D'
        else:
            msg = '\x02H'+str(ID)+'HX\x03\x0A\x0D'
        if self.uart != None:
                self.uart.write(msg.encode())    
        else : 
            print('Not Connected')

    def controlPumppower(self, ID, BATH):
        if BATH.PUMP == 'OFF':
            msg = '\x02P'+str(ID)+'PO\x03\x0A\x0D'
        else:
            msg = '\x02P'+str(ID)+'PX\x03\x0A\x0D'
        if self.uart != None:
                self.uart.write(msg.encode())    
        else : 
            print('Not Connected')


class UartProtocol(asyncio.Protocol):
    def __init__(self, uartCom, eventThread):
        self.uartCom = uartCom
        self.rcvParser = RcvParser(uartCom, eventThread)
        print(self.uartCom)

    def connection_made(self, transport):
        self.transport = transport
        print('port opened', transport)
        # rts (Request to Send) : 송신 요청
        # cts (Clear to Send) : 송신 확인
        transport.serial.rts = False 
        self.uartCom.uart = transport

    def data_received(self, data):
        message = data.decode()
        print('data received', message)
        self.rcvParser.parsing(message)


    def connection_lost(self, exc):
        print('port closed')
        self.transport.loop.stop()

    def pause_writing(self):
        print('pause writing')
        print(self.transport.get_write_buffer_size())

    def resume_writing(self):
        print(self.transport.get_write_buffer_size())
        print('resume writing')


class RcvParser(PyQt5.QtCore.QObject):

    rcvSensorSignal = PyQt5.QtCore.pyqtSignal(str)
    rcvPowerSignal = PyQt5.QtCore.pyqtSignal(str)
    rcvHeaterPowerSignal = PyQt5.QtCore.pyqtSignal(str)
    rcvPumpPowerSignal = PyQt5.QtCore.pyqtSignal(str)
    rcvWaterConditionSignal = PyQt5.QtCore.pyqtSignal(str)

    def __init__(self, uartCom, eventThread):
        super().__init__()
        self.uartCom = uartCom
        self.initProtocol()
        self.rcvSensorSignal.connect(eventThread.updateSensor)
        self.rcvPowerSignal.connect(eventThread.updateActuator)
        self.rcvHeaterPowerSignal.connect(eventThread.updateHeater)
        self.rcvPumpPowerSignal.connect(eventThread.updatePump)
        self.rcvWaterConditionSignal.connect(eventThread.updateWaterCondition)


    def parsing(self, pkt):
        self.command = pkt.strip("\x02\x03\n\r")
        cmd = self.command[0]
        try:
            func = self.protocol.get(cmd)
            return func(self.command)
        except Exception as e:
            print("type error: " + str(e))

    def rcvT(self, command):
        if command[1] == '1':
            SENSOR.OUTTMP_list.append(float(command[3:]))
            self.rcvSensorSignal.emit('outside')
        elif command[1] == '2':
            SENSOR.INTMP_list.append(float(command[3:8]))
            SENSOR.INHUMID_list.append(float(command[9:11]))
            SENSOR.CO2_list.append(float(command[12:16]))
            SENSOR.LUX_list.append(float(command[17:]))                
            SENSOR.Timestamp_list.append(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            self.rcvSensorSignal.emit('inside')

    def rcvWater(self, command):
        print('data parsed ', command)
        index = int(command[1])-1
        bathDef_list[index].TMP_list.append(float(command[3:8]))
        bathDef_list[index].DO_list.append(float(command[9:13]))
        bathDef_list[index].PH_list.append(float(command[14:18]))
        bathDef_list[index].Level = float(command[19:])
        bathDef_list[index].Timestamp_list.append(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.rcvWaterConditionSignal.emit('BATH'+command[1])

    def rcvAirpower(self, command):
        print('data parsed ', command)
        ACTUATOR.AIR['power'] = 'ON' if command[3]=='O' else 'OFF'
        self.rcvPowerSignal.emit('air')

    def rcvWindpower(self, command):
        print('data parsed ', command)
        ACTUATOR.WIND['power'] = 'ON' if command[3]=='O' else 'OFF'
        self.rcvPowerSignal.emit('wind')

    def rcvLEDpower(self, command):
        print('data parsed ', command)
        ACTUATOR.LED['power'] = 'ON' if command[3]=='O' else 'OFF'
        self.rcvPowerSignal.emit('led')

    def rcvUVpower(self, command):
        print('data parsed ', command)
        ACTUATOR.UV['power'] = 'ON' if command[3]=='O' else 'OFF'
        self.rcvPowerSignal.emit('uv')


    def rcvHeaterpower(self, command):
        print('data parsed ', command)
        if command[1] == '1':
            BATH1.HEATER = 'ON' if command[3]=='O' else 'OFF'
            self.rcvHeaterPowerSignal.emit('BATH1')
        elif command[1] == '2':
            BATH2.HEATER = 'ON' if command[3]=='O' else 'OFF'
            self.rcvHeaterPowerSignal.emit('BATH2')
        elif command[1] == '3':
            BATH3.HEATER = 'ON' if command[3]=='O' else 'OFF'
            self.rcvHeaterPowerSignal.emit('BATH3')
        elif command[1] == '4':
            BATH4.HEATER = 'ON' if command[3]=='O' else 'OFF'
            self.rcvHeaterPowerSignal.emit('BATH4')

    def rcvPumppower(self, command):
        print('data parsed ', command)
        if command[1] == '1':
            BATH1.PUMP = 'ON' if command[3]=='O' else 'OFF'
            self.rcvPumpPowerSignal.emit('BATH1')
        elif command[1] == '2':
            BATH2.PUMP = 'ON' if command[3]=='O' else 'OFF'
            self.rcvPumpPowerSignal.emit('BATH2')
        elif command[1] == '3':
            BATH3.PUMP = 'ON' if command[3]=='O' else 'OFF'
            self.rcvPumpPowerSignal.emit('BATH3')
        elif command[1] == '4':
            BATH4.PUMP = 'ON' if command[3]=='O' else 'OFF'
            self.rcvPumpPowerSignal.emit('BATH4')
        

    def initProtocol(self):
        self.protocol = {
        'T': self.rcvT,
        'W': self.rcvWater,
        'H': self.rcvHeaterpower,
        'P': self.rcvPumppower,
        'B': self.rcvAirpower,
        'F': self.rcvWindpower,
        'L': self.rcvLEDpower,
        'U': self.rcvUVpower
        }    


#QThread를 상속받는 시계 ui 업데이트 스레드
class TimeUpdateThread(PyQt5.QtCore.QThread):
    def __init__(self, ui):
        super().__init__()
        self.ui = ui
        self.timer = PyQt5.QtCore.QTimer()
        self.timer.timeout.connect(self.changeTime)
        self.timer.start(1000)
        self.start()

    def changeTime(self):
        cur_time = PyQt5.QtCore.QTime.currentTime()
        ui.lcdNumber_hour.display(cur_time.toString('hh'))
        ui.lcdNumber_minute.display(cur_time.toString('mm'))
        ui.lcdNumber_second.display(cur_time.toString('ss'))
        cur_date = PyQt5.QtCore.QDate.currentDate()
        ui.label_timetitle.setText(cur_date.toString('yyyy년   MM월   dd일'))

class ValueUpdateThread(PyQt5.QtCore.QThread):
    def __init__(self, ui, uartcom, eventThread):
        super().__init__()
        self.ui = ui
        self.uartcom = uartcom
        self.eventThread = eventThread
        self.INITILIZED_dict = {'tmpgraph' : False , 'dograph' : False, 'phgraph' : False} 
        self.timer1 = PyQt5.QtCore.QTimer()
        self.timer1.timeout.connect(self.updateValue)
        self.timer1.timeout.connect(self.updateTMPPlot)
        self.timer1.timeout.connect(self.updateDOPlot)
        self.timer1.timeout.connect(self.updatePHPlot)
        self.timer1.timeout.connect(self.updateAirConditionPlot)
        self.timer1.start(SETTINGS.FREQ/2)
        self.start()

    def updateValue(self):
        self.uartcom.sendUart()
        self.ui.label_lastchecktime.setText(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.eventThread.plotting(0)
        
    def updateTMPPlot(self):
        if not self.INITILIZED_dict['tmpgraph']:
            for i, BATH in enumerate([BATH1, BATH2, BATH3, BATH4]):
                ui.graphicsView_tmpgraph1.plot(BATH.TMP_list[-48:],pen=pg.mkPen(color=(27,119,208), width=3),
                        style=QtCore.Qt.DashLine, antialias =True)
            self.INITILIZED_dict['tmpgraph'] = True#, symbol=('o'), symbolSize=4,symbolBrush=(27,119,208),antialias=True)
            
            # or ui.pushButton_tmpgraph.isChecked():
            # ui.graphicsView_tmpgraph1.clear()
            
            # ui.graphicsView_tmpgraph2.clear()
            # ui.graphicsView_tmpgraph2.plot(BATH2.TMP_list[-48:],pen=pg.mkPen(color=(27,119,208), width=3),
            #             style=QtCore.Qt.DashLine, antialias = True) #symbol=('o'), symbolSize=4,symbolBrush=(27,119,208),antialias=True)
            # ui.graphicsView_tmpgraph3.clear()
            # ui.graphicsView_tmpgraph3.plot(BATH3.TMP_list[-48:],pen=pg.mkPen(color=(27,119,208), width=3),
            #             style=QtCore.Qt.DashLine, antialias = True)#symbol=('o'), symbolSize=4,symbolBrush=(27,119,208),antialias=True)
            # ui.graphicsView_tmpgraph4.clear()
            # ui.graphicsView_tmpgraph4.plot(BATH4.TMP_list[-48:],pen=pg.mkPen(color=(27,119,208), width=3),
            #             style=QtCore.Qt.DashLine, antialias = True)#symbol=('o'), symbolSize=4,symbolBrush=(27,119,208),antialias=True)

    def updateDOPlot(self):
        if ui.pushButton_dograph.isChecked():
            lineColor = [(245,183,0),(137,252,0),(0,161,232),(147,0,252)]
            ui.graphicsView_dograph1.clear()
            ui.graphicsView_dograph1.setYRange(0, 30)
            for i,BATH in enumerate([BATH1, BATH2, BATH3, BATH4]):
                ui.graphicsView_dograph1.plot(BATH.DO_list[-48:], pen=pg.mkPen(color=lineColor[i], width=4),
                style=QtCore.Qt.DashLine, antialias =True)#symbol=('o'), symbolSize=7,symbolBrush=(33+i*15,94-i*10,162-i*10),antialias=True)(33+i*30,94+i*20,162+i*30)
                ui.graphicsView_dograph1.addItem(pg.InfiniteLine(SETTINGS.BATH_dict['BATH'+str(i+1)]['DO']['from'],angle=0, movable=False,pen=pg.mkPen(color=lineColor[i], width=2)))
                ui.graphicsView_dograph1.addItem(pg.InfiniteLine(SETTINGS.BATH_dict['BATH'+str(i+1)]['DO']['to'],angle=0, movable=False,pen=pg.mkPen(color=lineColor[i], width=2)))
    
    # def updatePHPlot(self):
    #     if ui.pushButton_phgraph.isChecked():
    #         ui.graphicsView_phgraph1.clear()
    #         ui.graphicsView_phgraph1.plot(BATH1.PH_list[-48:],pen=pg.mkPen(color=(33,71,119), width=3),
    #                     tyle=QtCore.Qt.DashLine, antialias = True) #symbol=('o'), symbolSize=4,symbolBrush=(33,71,119),antialias=True)
    #         ui.graphicsView_phgraph2.clear()
    #         ui.graphicsView_phgraph2.plot(BATH2.PH_list[-48:],pen=pg.mkPen(color=(33,71,119), width=3),
    #                     tyle=QtCore.Qt.DashLine, antialias = True) #symbol=('o'), symbolSize=4,symbolBrush=(33,71,119),antialias=True)
    #         ui.graphicsView_phgraph3.clear()
    #         ui.graphicsView_phgraph3.plot(BATH3.PH_list[-48:],pen=pg.mkPen(color=(33,71,119), width=3),
    #                     tyle=QtCore.Qt.DashLine, antialias = True) #symbol=('o'), symbolSize=4,symbolBrush=(33,71,119),antialias=True)
    #         ui.graphicsView_phgraph4.clear()
    #         ui.graphicsView_phgraph4.plot(BATH4.PH_list[-48:],pen=pg.mkPen(color=(33,71,119), width=3),
    #                     tyle=QtCore.Qt.DashLine, antialias = True) #symbol=('o'), symbolSize=4,symbolBrush=(33,71,119),antialias=True)


    def updatePHPlot(self):
        if ui.pushButton_phgraph.isChecked():
            ui.graphicsView_phgraph1.clear()

            for BATH in [BATH1, BATH2, BATH3, BATH4]:
                ui.graphicsView_phgraph1.plot(BATH.PH_list[-48:],pen=pg.mkPen(color=(33,71,119), width=3),
                        tyle=QtCore.Qt.DashLine, antialias = True) #symbol=('o'), symbolSize=4,symbolBrush=(33,71,119),antialias=True)
    
    
    def updateAirConditionPlot(self):
        ui.graphicsView_aircondition1.clear()
        ui.graphicsView_aircondition2.clear()
        if ui.checkBox_outtmp.isChecked():
            ui.graphicsView_aircondition1.plot(SENSOR.OUTTMP_list[-48:],pen=pg.mkPen(color=(24,32,98), width=3),
                    style=QtCore.Qt.DashLine, antialias =True)
        if ui.checkBox_intmp.isChecked():
            ui.graphicsView_aircondition1.plot(SENSOR.INTMP_list[-48:],pen=pg.mkPen(color=(33,71,119), width=3),
                    style=QtCore.Qt.DashLine, antialias = True)
        if ui.checkBox_inhumid.isChecked():
            ui.graphicsView_aircondition1.plot(SENSOR.INHUMID_list[-48:],pen=pg.mkPen(color=(33,94,162), width=3),
                    tyle=QtCore.Qt.DashLine, antialias = True)
        if ui.checkBox_lux.isChecked():
            ui.graphicsView_aircondition1.plot(SENSOR.LUX_list[-48:],pen=pg.mkPen(color=(27,119,208), width=3),
                    tyle=QtCore.Qt.DashLine, antialias = True)
        if ui.checkBox_co2.isChecked():
            ui.graphicsView_aircondition2.plot(SENSOR.CO2_list[-48:],pen=pg.mkPen(color=(27,119,208), width=3),
                    style=QtCore.Qt.DashLine, antialias =True)
        if ui.checkBox_ammonia.isChecked():
            ui.graphicsView_aircondition2.plot(SENSOR.EC_list[-48:],pen=pg.mkPen(color=(33,94,162), width=3),
                    style=QtCore.Qt.DashLine, antialias = True)
    

class EventThread(PyQt5.QtCore.QThread):

    def __init__(self, ui):
        super().__init__()
        self.ui = ui        
        self.mainButton_list = [ui.pushButton_main,
                                ui.pushButton_watertmp, ui.pushButton_do, ui.pushButton_ph,
                                ui.pushButton_aircondition, ui.pushButton_electron, ui.pushButton_settings]
        self.pushButton_list =[ui.pushButton_check,
                                ui.pushButton_tmpvalue, ui.pushButton_tmpgraph,
                                ui.pushButton_dovalue, ui.pushButton_dograph,
                                ui.pushButton_phvalue, ui.pushButton_phgraph,
                                ui.pushButton_comconnect, ui.pushButton_sensorsave1, ui.pushButton_sensorsave2,
                                ui.pushButton_applyall, ui.pushButton_save,
                                ui.pushButton_intmpsave, ui.pushButton_co2save, ui.pushButton_luxsave, ui.pushButton_ecsave,
                                ui.pushButton_inhumidsave, ui.pushButton_ammoniasave, ui.pushButton_electronsave, ui.pushButton_othersave]

        self.tmplabel_list = [[ui.label_maintmp1,ui.label_maintmp2,ui.label_maintmp3,ui.label_maintmp4,
                            ui.label_maintmp5,ui.label_maintmp6,ui.label_maintmp7,ui.label_maintmp8],
                            [ui.label_lowtmp1, ui.label_lowtmp2, ui.label_lowtmp3, ui.label_lowtmp4,
                            ui.label_lowtmp5, ui.label_lowtmp6, ui.label_lowtmp7, ui.label_lowtmp8],
                            [ui.label_hightmp1, ui.label_hightmp2, ui.label_hightmp3, ui.label_hightmp4,
                            ui.label_hightmp5, ui.label_hightmp6, ui.label_hightmp7, ui.label_hightmp8]]
        self.dolabel_list =[[ui.label_maindo1,ui.label_maindo2,ui.label_maindo3,ui.label_maindo4,
                            ui.label_maindo5,ui.label_maindo6,ui.label_maindo7,ui.label_maindo8],
                            [ui.label_lowdo1, ui.label_lowdo2, ui.label_lowdo3, ui.label_lowdo4,
                            ui.label_lowdo5, ui.label_lowdo6, ui.label_lowdo7, ui.label_lowdo8],
                            [ui.label_highdo1, ui.label_highdo2, ui.label_highdo3, ui.label_highdo4,
                            ui.label_highdo5, ui.label_highdo6, ui.label_highdo7, ui.label_highdo8]]
        self.phlabel_list = [[ui.label_mainph1,ui.label_mainph2,ui.label_mainph3,ui.label_mainph4,
                            ui.label_mainph5,ui.label_mainph6,ui.label_mainph7,ui.label_mainph8],
                            [ui.label_lowph1, ui.label_lowph2, ui.label_lowph3, ui.label_lowph4,
                            ui.label_lowph5, ui.label_lowph6, ui.label_lowph7, ui.label_lowph8],
                            [ui.label_highph1, ui.label_highph2, ui.label_highph3, ui.label_highph4,
                            ui.label_highph5, ui.label_highph6, ui.label_highph7, ui.label_highph8]]

        self.bathlabel_list = [[ui.label_watertmp1, ui.label_do1,ui.label_ph1,ui.label_level1],
                                [ui.label_watertmp2, ui.label_do2,ui.label_ph2,ui.label_level2],
                                [ui.label_watertmp3, ui.label_do3,ui.label_ph3,ui.label_level3],
                                [ui.label_watertmp4, ui.label_do4,ui.label_ph4,ui.label_level4]]
        self.bathcheckbox_list = [ui.checkBox_1, ui.checkBox_2, ui.checkBox_3, ui.checkBox_4,
                                ui.checkBox_5, ui.checkBox_6, ui.checkBox_7, ui.checkBox_8]

        self.bathSpinBox_list = [[ui.doubleSpinBox_fromtmp1, ui.doubleSpinBox_totmp1,
                                ui.doubleSpinBox_fromdo1, ui.doubleSpinBox_todo1,
                                ui.doubleSpinBox_fromph1, ui.doubleSpinBox_toph1],
                                [ui.doubleSpinBox_fromtmp2, ui.doubleSpinBox_totmp2,
                                ui.doubleSpinBox_fromdo2, ui.doubleSpinBox_todo2,
                                ui.doubleSpinBox_fromph2, ui.doubleSpinBox_toph2],
                                [ui.doubleSpinBox_fromtmp3, ui.doubleSpinBox_totmp3,
                                ui.doubleSpinBox_fromdo3, ui.doubleSpinBox_todo3,
                                ui.doubleSpinBox_fromph3, ui.doubleSpinBox_toph3],
                                [ui.doubleSpinBox_fromtmp4, ui.doubleSpinBox_totmp4,
                                ui.doubleSpinBox_fromdo4, ui.doubleSpinBox_todo4,
                                ui.doubleSpinBox_fromph4, ui.doubleSpinBox_toph4]]

        for pushButton in self.pushButton_list:
            pushButton.setStyleSheet(StyleSheet.pushButton)
        for mainButton in self.mainButton_list:
            mainButton.setStyleSheet(StyleSheet.mainButton)

        #ui.pushButton_check.clicked.connect(lambda x: ui.label_lastchecktime.setText(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        ui.pushButton_comconnect.clicked.connect(lambda x: ui.pushButton_comconnect.setText('연결 완료'))

        # changePage
        ui.pushButton_main.clicked.connect(lambda x: ui.stackedWidget.setCurrentIndex(0))
        ui.pushButton_watertmp.clicked.connect(lambda x: ui.stackedWidget.setCurrentIndex(1))
        ui.pushButton_watertmp.clicked.connect(self.updateTmp)
        ui.pushButton_do.clicked.connect(lambda x: ui.stackedWidget.setCurrentIndex(2))
        ui.pushButton_do.clicked.connect(self.updateDO)
        ui.pushButton_ph.clicked.connect(lambda x: ui.stackedWidget.setCurrentIndex(3))
        ui.pushButton_ph.clicked.connect(self.updatePH)
        ui.pushButton_aircondition.clicked.connect(lambda x: ui.stackedWidget.setCurrentIndex(4))
        ui.pushButton_aircondition.clicked.connect(self.updateAirconditon)
        ui.pushButton_aircondition.clicked.connect(lambda x: self.plotting(5))
        ui.pushButton_electron.clicked.connect(lambda x: ui.stackedWidget.setCurrentIndex(5))
        #ui.pushButton_electron.clicked.connect(self.updateElectron)
        ui.pushButton_settings.clicked.connect(lambda x: ui.stackedWidget.setCurrentIndex(6))
        ui.pushButton_settings.clicked.connect(lambda x : self.updateSettings(False))
        # changeSubPage
        ui.pushButton_tmpvalue.clicked.connect(lambda x : ui.stackedWidget_1.setCurrentIndex(0))
        ui.pushButton_tmpgraph.clicked.connect(lambda x : ui.stackedWidget_1.setCurrentIndex(1))
        ui.pushButton_dovalue.clicked.connect(lambda x : ui.stackedWidget_2.setCurrentIndex(0))
        ui.pushButton_dograph.clicked.connect(lambda x : ui.stackedWidget_2.setCurrentIndex(1))
        ui.pushButton_phvalue.clicked.connect(lambda x : ui.stackedWidget_3.setCurrentIndex(0))
        ui.pushButton_phgraph.clicked.connect(lambda x : ui.stackedWidget_3.setCurrentIndex(1))
        # saveSettings
        ui.pushButton_save.clicked.connect(lambda x: self.saveSettings('save'))
        ui.pushButton_intmpsave.clicked.connect(lambda x: self.saveSettings('intmp'))
        ui.pushButton_co2save.clicked.connect(lambda x: self.saveSettings('co2'))
        ui.pushButton_luxsave.clicked.connect(lambda x: self.saveSettings('lux'))
        ui.pushButton_ecsave.clicked.connect(lambda x: self.saveSettings('ec'))
        ui.pushButton_inhumidsave.clicked.connect(lambda x: self.saveSettings('inhumid'))
        ui.pushButton_ammoniasave.clicked.connect(lambda x: self.saveSettings('ammonia'))
        ui.pushButton_electronsave.clicked.connect(lambda x: self.saveSettings('electron'))

        ui.pushButton_applyall.clicked.connect(lambda x: self.updateSettings(True))
        ui.pushButton_sensorsave1.clicked.connect(lambda x: self.updateSettings('freq'))

        ui.tabWidget.tabBarClicked.connect(lambda x :self.plotting(0))
        self.INITILIZED1 = False
        self.INITILIZED2 = False
        self.INITILIZED3 = False
        self.INITILIZED4 = False

        self.updateActuator('all')
        self.updateSensor('outside')
        self.updateSensor('inside')
        self.updatePump('BATH1')
        self.updateHeater('BATH1')
        self.plotting(5)
        self.plotting(1)
        self.plotting(2)
        self.plotting(3)
        self.plotting(4)
        

    @PyQt5.QtCore.pyqtSlot(str) 
    def updateActuator(self, actuator):
        if actuator == 'all':
            ui.pushButton_airpower.setText(ACTUATOR.AIR['power'])
            ui.pushButton_airpower.setStyleSheet(StyleSheet.normallabel_whitebg + StyleSheet.abnormaltext)\
            if ACTUATOR.AIR['power'] == 'ON' else ui.pushButton_airpower.setStyleSheet(StyleSheet.normallabel_whitebg)
            ui.pushButton_windpower.setText(ACTUATOR.WIND['power'])
            ui.pushButton_windpower.setStyleSheet(StyleSheet.normallabel_greybg + StyleSheet.abnormaltext)\
            if ACTUATOR.WIND['power'] == 'ON' else ui.pushButton_windpower.setStyleSheet(StyleSheet.normallabel_greybg)
            ui.pushButton_ledpower.setText(ACTUATOR.LED['power'])
            ui.pushButton_ledpower.setStyleSheet(StyleSheet.normallabel_whitebg + StyleSheet.abnormaltext)\
            if ACTUATOR.LED['power'] == 'ON' else ui.pushButton_ledpower.setStyleSheet(StyleSheet.normallabel_whitebg)
            ui.pushButton_uvpower.setText(ACTUATOR.UV['power'])
            ui.pushButton_uvpower.setStyleSheet(StyleSheet.normallabel_greybg + StyleSheet.abnormaltext)\
            if ACTUATOR.UV['power'] == 'ON' else ui.pushButton_uvpower.setStyleSheet(StyleSheet.normallabel_greybg)
        elif actuator == 'air':
            ui.pushButton_airpower.setText(ACTUATOR.AIR['power'])
            ui.pushButton_airpower.setStyleSheet(StyleSheet.normallabel_whitebg + StyleSheet.abnormaltext)\
            if ACTUATOR.AIR['power'] == 'ON' else ui.pushButton_airpower.setStyleSheet(StyleSheet.normallabel_whitebg)
        elif actuator == 'wind':
            ui.pushButton_windpower.setText(ACTUATOR.WIND['power'])
            ui.pushButton_windpower.setStyleSheet(StyleSheet.normallabel_greybg + StyleSheet.abnormaltext)\
            if ACTUATOR.WIND['power'] == 'ON' else ui.pushButton_windpower.setStyleSheet(StyleSheet.normallabel_greybg)
        elif actuator == 'led':
            ui.pushButton_ledpower.setText(ACTUATOR.LED['power'])
            ui.pushButton_ledpower.setStyleSheet(StyleSheet.normallabel_whitebg + StyleSheet.abnormaltext)\
            if ACTUATOR.LED['power'] == 'ON' else ui.pushButton_ledpower.setStyleSheet(StyleSheet.normallabel_whitebg)
        elif actuator == 'uv':
            ui.pushButton_uvpower.setText(ACTUATOR.UV['power'])
            ui.pushButton_uvpower.setStyleSheet(StyleSheet.normallabel_greybg + StyleSheet.abnormaltext)\
            if ACTUATOR.UV['power'] == 'ON' else ui.pushButton_uvpower.setStyleSheet(StyleSheet.normallabel_greybg)


    @PyQt5.QtCore.pyqtSlot(str) 
    def updateSensor(self, sensor):
        if sensor == 'outside':
            ui.label_outtmp.setText(str(SENSOR.OUTTMP_list[-1]))
        elif sensor == 'inside':
            ui.label_intmp.setText(str(SENSOR.INTMP_list[-1]))
            if SENSOR.INTMP_list[-1] > SETTINGS.INTMP['to'] or SENSOR.INTMP_list[-1] < SETTINGS.INTMP['from']:
                ui.label_intmp.setStyleSheet(StyleSheet.normallabel_greybg + StyleSheet.abnormaltext)
            else :
                ui.label_intmp.setStyleSheet(StyleSheet.normallabel_greybg)
            ui.label_humid.setText(str(SENSOR.INHUMID_list[-1]))
            if SENSOR.INHUMID_list[-1] > SETTINGS.INHUMID['to'] or SENSOR.INHUMID_list[-1] < SETTINGS.INHUMID['from']:
                ui.label_humid.setStyleSheet(StyleSheet.normallabel_whitebg + StyleSheet.abnormaltext)
            else :
                ui.label_humid.setStyleSheet(StyleSheet.normallabel_whitebg)
            ui.label_co2.setText(str(SENSOR.CO2_list[-1]))
            if SENSOR.CO2_list[-1] > SETTINGS.CO2['to'] or SENSOR.CO2_list[-1] < SETTINGS.CO2['from']:
                ui.label_co2.setStyleSheet(StyleSheet.normallabel_whitebg + StyleSheet.abnormaltext)
            else :
                ui.label_co2.setStyleSheet(StyleSheet.normallabel_whitebg)
            ui.label_lux.setText(str(SENSOR.LUX_list[-1]))
            if SENSOR.LUX_list[-1] > SETTINGS.INLUX['to'] or SENSOR.LUX_list[-1] < SETTINGS.INLUX['from']:
                ui.label_lux.setStyleSheet(StyleSheet.normallabel_whitebg + StyleSheet.abnormaltext)
            else :
                ui.label_lux.setStyleSheet(StyleSheet.normallabel_whitebg)
            ui.label_ammonia.setText(str(SENSOR.AMMONIA_list[-1]))
            if SENSOR.AMMONIA_list[-1] > SETTINGS.AMMONIA['to'] or SENSOR.AMMONIA_list[-1] < SETTINGS.AMMONIA['from']:
                ui.label_ammonia.setStyleSheet(StyleSheet.normallabel_greybg + StyleSheet.abnormaltext)
            else :
                ui.label_ammonia.setStyleSheet(StyleSheet.normallabel_greybg)
            ui.label_ec.setText(str(SENSOR.EC_list[-1]))
            if SENSOR.EC_list[-1] > SETTINGS.EC['to'] or SENSOR.EC_list[-1] < SETTINGS.EC['from']:
                ui.label_ec.setStyleSheet(StyleSheet.normallabel_whitebg + StyleSheet.abnormaltext)
            else :
                ui.label_ec.setStyleSheet(StyleSheet.normallabel_whitebg)
            ui.label_blackout.setText(str(SENSOR.BLACKOUT))


    @PyQt5.QtCore.pyqtSlot(str)
    def updatePump(self, BATH):
        '''if BATH == 'all':
            ui.pushButton_pumppower1.setText(BATH1.PUMP)
            ui.pushButton_pumppower2.setText(BATH2.PUMP)
            ui.pushButton_pumppower3.setText(BATH3.PUMP)
            ui.pushButton_pumppower4.setText(BATH4.PUMP)'''
        if BATH == 'BATH1':
            print("bath1 calleded")
            ui.pushButton_pumppower1.setText(BATH1.PUMP)
            ui.pushButton_pumppower1.setStyleSheet(StyleSheet.normallabel_whitebg + StyleSheet.abnormaltext)\
            if BATH1.PUMP == 'ON' else ui.pushButton_pumppower1.setStyleSheet(StyleSheet.normallabel_whitebg)
        elif BATH == 'BATH2':
            print("bath2 calleded")
            ui.pushButton_pumppower2.setText(BATH2.PUMP)
            ui.pushButton_pumppower2.setStyleSheet(StyleSheet.normallabel_whitebg + StyleSheet.abnormaltext)\
            if BATH2.PUMP == 'ON' else ui.pushButton_pumppower2.setStyleSheet(StyleSheet.normallabel_whitebg)
        elif BATH == 'BATH3':
            ui.pushButton_pumppower3.setText(BATH3.PUMP)
            ui.pushButton_pumppower3.setStyleSheet(StyleSheet.normallabel_whitebg + StyleSheet.abnormaltext)\
            if BATH3.PUMP == 'ON' else ui.pushButton_pumppower3.setStyleSheet(StyleSheet.normallabel_whitebg)
        elif BATH == 'BATH4':
            ui.pushButton_pumppower4.setText(BATH4.PUMP)
            ui.pushButton_pumppower4.setStyleSheet(StyleSheet.normallabel_whitebg + StyleSheet.abnormaltext)\
            if BATH4.PUMP == 'ON' else ui.pushButton_pumppower4.setStyleSheet(StyleSheet.normallabel_whitebg)

    @PyQt5.QtCore.pyqtSlot(str)
    def updateHeater(self, BATH):
        '''if BATH == 'all':
            ui.pushButton_heaterpower1.setText(BATH1.HEATER)
            ui.pushButton_heaterpower2.setText(BATH2.HEATER)
            ui.pushButton_heaterpower3.setText(BATH3.HEATER)
            ui.pushButton_heaterpower4.setText(BATH4.HEATER)'''
        if BATH == 'BATH1':
            ui.pushButton_heaterpower1.setText(BATH1.HEATER)
            ui.pushButton_heaterpower1.setStyleSheet(StyleSheet.normallabel_whitebg + StyleSheet.abnormaltext)\
            if BATH1.HEATER == 'ON' else ui.pushButton_heaterpower1.setStyleSheet(StyleSheet.normallabel_whitebg)
        elif BATH == 'BATH2':
            ui.pushButton_heaterpower2.setText(BATH2.HEATER)
            ui.pushButton_heaterpower2.setStyleSheet(StyleSheet.normallabel_whitebg + StyleSheet.abnormaltext)\
            if BATH2.HEATER == 'ON' else ui.pushButton_heaterpower2.setStyleSheet(StyleSheet.normallabel_whitebg)
        elif BATH == 'BATH3':
            ui.pushButton_heaterpower3.setText(BATH3.HEATER)
            ui.pushButton_heaterpower3.setStyleSheet(StyleSheet.normallabel_whitebg + StyleSheet.abnormaltext)\
            if BATH3.HEATER == 'ON' else ui.pushButton_heaterpower3.setStyleSheet(StyleSheet.normallabel_whitebg)
        elif BATH == 'BATH4':
            ui.pushButton_heaterpower4.setText(BATH4.HEATER)
            ui.pushButton_heaterpower4.setStyleSheet(StyleSheet.normallabel_whitebg + StyleSheet.abnormaltext)\
            if BATH4.HEATER == 'ON' else ui.pushButton_heaterpower4.setStyleSheet(StyleSheet.normallabel_whitebg)


    @PyQt5.QtCore.pyqtSlot(str)
    def updateWaterCondition(self, BATH):
        '''if BATH == 'all':
            ui.label_watertmp1.setText(str(float(BATH1.TMP_list[-1])))
            ui.label_do1.setText(str(float(BATH1.DO_list[-1])))
            ui.label_ph1.setText(str(float(BATH1.PH_list[-1])))
            ui.label_level1.setText(str(float(BATH1.Level)))
            ui.label_watertmp2.setText(str(float(BATH2.TMP_list[-1])))
            ui.label_do2.setText(str(float(BATH2.DO_list[-1])))
            ui.label_ph2.setText(str(float(BATH2.PH_list[-1])))
            ui.label_level2.setText(str(float(BATH2.Level)))
            ui.label_watertmp3.setText(str(float(BATH3.TMP_list[-1])))
            ui.label_do3.setText(str(float(BATH3.DO_list[-1])))
            ui.label_ph3.setText(str(float(BATH3.PH_list[-1])))
            ui.label_level3.setText(str(float(BATH3.Level)))
            ui.label_watertmp4.setText(str(float(BATH4.TMP_list[-1])))
            ui.label_do4.setText(str(float(BATH4.DO_list[-1])))
            ui.label_ph4.setText(str(float(BATH4.PH_list[-1])))
            ui.label_level4.setText(str(float(BATH4.Level)))'''
        if BATH == 'BATH1':
            ui.label_watertmp1.setText(str(BATH1.TMP_list[-1]))
            if BATH1.TMP_list[-1] > SETTINGS.BATH_dict['BATH1']['TMP']['to'] or \
                BATH1.TMP_list[-1] < SETTINGS.BATH_dict['BATH1']['TMP']['from']:
                self.bathlabel_list[0][0].setStyleSheet(StyleSheet.normallabel_whitebg + StyleSheet.abnormaltext)
            else :
                self.bathlabel_list[0][0].setStyleSheet(StyleSheet.normallabel_whitebg)
            ui.label_do1.setText(str(BATH1.DO_list[-1]))
            if BATH1.DO_list[-1] > SETTINGS.BATH_dict['BATH1']['DO']['to'] or \
                BATH1.DO_list[-1] < SETTINGS.BATH_dict['BATH1']['DO']['from']:
                self.bathlabel_list[0][1].setStyleSheet(StyleSheet.normallabel_whitebg + StyleSheet.abnormaltext)
            else :
                self.bathlabel_list[0][1].setStyleSheet(StyleSheet.normallabel_whitebg)
            ui.label_ph1.setText(str(BATH1.PH_list[-1]))
            if BATH1.PH_list[-1] > SETTINGS.BATH_dict['BATH1']['PH']['to'] or \
                BATH1.PH_list[-1] < SETTINGS.BATH_dict['BATH1']['PH']['from']:
                self.bathlabel_list[0][2].setStyleSheet(StyleSheet.normallabel_whitebg + StyleSheet.abnormaltext)
            else :
                self.bathlabel_list[0][2].setStyleSheet(StyleSheet.normallabel_whitebg)
            ui.label_level1.setText(str(BATH1.Level))
            ui.label_level1.setStyleSheet(StyleSheet.normallabel_whitebg)
        elif BATH == 'BATH2':
            ui.label_watertmp2.setText(str(BATH2.TMP_list[-1]))
            if BATH2.TMP_list[-1] > SETTINGS.BATH_dict['BATH2']['TMP']['to'] or \
                BATH2.TMP_list[-1] < SETTINGS.BATH_dict['BATH2']['TMP']['from']:
                self.bathlabel_list[1][0].setStyleSheet(StyleSheet.normallabel_whitebg + StyleSheet.abnormaltext)
            else :
                self.bathlabel_list[1][0].setStyleSheet(StyleSheet.normallabel_whitebg)
            ui.label_do2.setText(str(BATH2.DO_list[-1]))
            if BATH2.DO_list[-1] > SETTINGS.BATH_dict['BATH2']['DO']['to'] or \
                BATH2.DO_list[-1] < SETTINGS.BATH_dict['BATH2']['DO']['from']:
                self.bathlabel_list[1][1].setStyleSheet(StyleSheet.normallabel_whitebg + StyleSheet.abnormaltext)
            else :
                self.bathlabel_list[1][1].setStyleSheet(StyleSheet.normallabel_whitebg)
            ui.label_ph2.setText(str(BATH2.PH_list[-1]))
            if BATH2.PH_list[-1] > SETTINGS.BATH_dict['BATH2']['PH']['to'] or \
                BATH2.PH_list[-1] < SETTINGS.BATH_dict['BATH2']['PH']['from']:
                self.bathlabel_list[1][2].setStyleSheet(StyleSheet.normallabel_whitebg + StyleSheet.abnormaltext)
            else :
                self.bathlabel_list[1][2].setStyleSheet(StyleSheet.normallabel_whitebg)
            ui.label_level2.setText(str(BATH2.Level))
            ui.label_level2.setStyleSheet(StyleSheet.normallabel_whitebg)
        elif BATH == 'BATH3':
            ui.label_watertmp3.setText(str(BATH3.TMP_list[-1]))
            if BATH3.TMP_list[-1] > SETTINGS.BATH_dict['BATH3']['TMP']['to'] or \
                BATH3.TMP_list[-1] < SETTINGS.BATH_dict['BATH3']['TMP']['from']:
                self.bathlabel_list[2][0].setStyleSheet(StyleSheet.normallabel_whitebg + StyleSheet.abnormaltext)
            else :
                self.bathlabel_list[2][0].setStyleSheet(StyleSheet.normallabel_whitebg)
            ui.label_do3.setText(str(BATH3.DO_list[-1]))
            if BATH3.DO_list[-1] > SETTINGS.BATH_dict['BATH3']['DO']['to'] or \
                BATH3.DO_list[-1] < SETTINGS.BATH_dict['BATH3']['DO']['from']:
                self.bathlabel_list[2][1].setStyleSheet(StyleSheet.normallabel_whitebg + StyleSheet.abnormaltext)
            else :
                self.bathlabel_list[2][1].setStyleSheet(StyleSheet.normallabel_whitebg)
            ui.label_ph3.setText(str(BATH3.PH_list[-1]))
            if BATH3.PH_list[-1] > SETTINGS.BATH_dict['BATH3']['PH']['to'] or \
                BATH3.PH_list[-1] < SETTINGS.BATH_dict['BATH3']['PH']['from']:
                self.bathlabel_list[2][2].setStyleSheet(StyleSheet.normallabel_whitebg + StyleSheet.abnormaltext)
            else :
                self.bathlabel_list[2][2].setStyleSheet(StyleSheet.normallabel_whitebg)
            ui.label_level3.setText(str(BATH3.Level))
            ui.label_level3.setStyleSheet(StyleSheet.normallabel_whitebg)
        elif BATH == 'BATH4':
            ui.label_watertmp4.setText(str(BATH4.TMP_list[-1]))
            if BATH4.TMP_list[-1] > SETTINGS.BATH_dict['BATH4']['TMP']['to'] or \
                BATH4.TMP_list[-1] < SETTINGS.BATH_dict['BATH4']['TMP']['from']:
                self.bathlabel_list[3][0].setStyleSheet(StyleSheet.normallabel_whitebg + StyleSheet.abnormaltext)
            else :
                self.bathlabel_list[3][0].setStyleSheet(StyleSheet.normallabel_whitebg)
            ui.label_do4.setText(str(BATH4.DO_list[-1]))
            if BATH4.DO_list[-1] > SETTINGS.BATH_dict['BATH4']['DO']['to'] or \
                BATH4.DO_list[-1] < SETTINGS.BATH_dict['BATH4']['DO']['from']:
                self.bathlabel_list[3][1].setStyleSheet(StyleSheet.normallabel_whitebg + StyleSheet.abnormaltext)
            else :
                self.bathlabel_list[3][1].setStyleSheet(StyleSheet.normallabel_whitebg)
            ui.label_ph4.setText(str(BATH4.PH_list[-1]))
            if BATH4.PH_list[-1] > SETTINGS.BATH_dict['BATH4']['PH']['to'] or \
                BATH4.PH_list[-1] < SETTINGS.BATH_dict['BATH4']['PH']['from']:
                self.bathlabel_list[3][2].setStyleSheet(StyleSheet.normallabel_whitebg + StyleSheet.abnormaltext)
            else :
                self.bathlabel_list[3][2].setStyleSheet(StyleSheet.normallabel_whitebg)
            ui.label_level4.setText(str(BATH4.Level))
            ui.label_level4.setStyleSheet(StyleSheet.normallabel_whitebg)


    def updateTmp(self):
        for i in range(4):
            self.tmplabel_list[0][i].setText(str(bathDef_list[i].TMP_list[-1]))
            self.tmplabel_list[1][i].setText(str(SETTINGS.BATH_dict['BATH'+str(i+1)]['TMP']['from']))
            self.tmplabel_list[2][i].setText(str(SETTINGS.BATH_dict['BATH'+str(i+1)]['TMP']['to'])) 
            if float(self.tmplabel_list[0][i].text()) > float(self.tmplabel_list[2][i].text()) or \
                float(self.tmplabel_list[0][i].text()) < float(self.tmplabel_list[1][i].text()):
                self.tmplabel_list[0][i].setStyleSheet(StyleSheet.abnormalback)
            else :
                self.tmplabel_list[0][i].setStyleSheet(StyleSheet.normalback)

    def updateDO(self):
        for i in range(4):
            self.dolabel_list[0][i].setText(str(bathDef_list[i].DO_list[-1]))
            self.dolabel_list[1][i].setText(str(SETTINGS.BATH_dict['BATH'+str(i+1)]['DO']['from']))
            self.dolabel_list[2][i].setText(str(SETTINGS.BATH_dict['BATH'+str(i+1)]['DO']['to']))
            if float(self.dolabel_list[0][i].text()) > float(self.dolabel_list[2][i].text()) or \
                float(self.dolabel_list[0][i].text()) < float(self.dolabel_list[1][i].text()):
                self.dolabel_list[0][i].setStyleSheet(StyleSheet.abnormalback)
            else :
                self.dolabel_list[0][i].setStyleSheet(StyleSheet.normalback)

    def updatePH(self):
        for i in range(4):
            self.phlabel_list[0][i].setText(str(float(bathDef_list[i].PH_list[-1])))
            self.phlabel_list[1][i].setText(str(SETTINGS.BATH_dict['BATH'+str(i+1)]['PH']['from']))
            self.phlabel_list[2][i].setText(str(SETTINGS.BATH_dict['BATH'+str(i+1)]['PH']['to'])) 
            if float(self.phlabel_list[0][i].text()) > float(self.phlabel_list[2][i].text()) or \
                float(self.phlabel_list[0][i].text()) < float(self.phlabel_list[1][i].text()):
                self.phlabel_list[0][i].setStyleSheet(StyleSheet.abnormalback)
            else :
                self.phlabel_list[0][i].setStyleSheet(StyleSheet.normalback)
      

    def updateAirconditon(self):
        ui.label_outtmp2.setText(str(float(SENSOR.OUTTMP_list[-1])))
        ui.label_intmp2.setText(str(float(SENSOR.INTMP_list[-1])))
        if SENSOR.OUTTMP_list[-1] > SETTINGS.INTMP['to'] or SENSOR.OUTTMP_list[-1] < SETTINGS.INTMP['from']:
            ui.label_intmp2.setStyleSheet(StyleSheet.normallabel_whitebg + StyleSheet.abnormaltext)
        else :
            ui.label_intmp2.setStyleSheet(StyleSheet.normallabel_whitebg)
        ui.label_humid2.setText(str(float(SENSOR.INHUMID_list[-1])))
        if SENSOR.INHUMID_list[-1] > SETTINGS.INHUMID['to'] or SENSOR.INHUMID_list[-1] < SETTINGS.INHUMID['from']:
            ui.label_humid2.setStyleSheet(StyleSheet.normallabel_whitebg + StyleSheet.abnormaltext)
        else :
            ui.label_humid2.setStyleSheet(StyleSheet.normallabel_whitebg)
        ui.label_co22.setText(str(float(SENSOR.CO2_list[-1])))
        if SENSOR.CO2_list[-1] > SETTINGS.CO2['to'] or SENSOR.CO2_list[-1] < SETTINGS.CO2['from']:
            ui.label_co22.setStyleSheet(StyleSheet.normallabel_whitebg + StyleSheet.abnormaltext)
        else:
            ui.label_co22.setStyleSheet(StyleSheet.normallabel_whitebg)
        ui.label_ammonia2.setText(str(float(SENSOR.AMMONIA_list[-1])))
        if SENSOR.AMMONIA_list[-1] > SETTINGS.AMMONIA['to'] or SENSOR.AMMONIA_list[-1] < SETTINGS.AMMONIA['from']:
            ui.label_ammonia2.setStyleSheet(StyleSheet.normallabel_whitebg + StyleSheet.abnormaltext)
        else:
            ui.label_ammonia2.setStyleSheet(StyleSheet.normallabel_whitebg)
        ui.label_lux2.setText(str(float(SENSOR.LUX_list[-1])))
        if SENSOR.LUX_list[-1] > SETTINGS.INLUX['to'] or SENSOR.LUX_list[-1] < SETTINGS.INLUX['from']:
            ui.label_lux2.setStyleSheet(StyleSheet.normallabel_whitebg + StyleSheet.abnormaltext)
        else :
            ui.label_lux2.setStyleSheet(StyleSheet.normallabel_whitebg)

    def saveSettings(self, setting):
        with open ('config.json', 'r+') as jsonFile:
            data = json.load(jsonFile)
            if setting == 'save':
                for index in range(1,5):
                    data["SETTINGS"]["BATH"+str(index)]["TMP"]["from"] = \
                    SETTINGS.BATH_dict['BATH'+str(index)]['TMP']['from'] = self.bathSpinBox_list[index-1][0].value()
                    data["SETTINGS"]["BATH"+str(index)]["TMP"]["to"] = \
                    SETTINGS.BATH_dict['BATH'+str(index)]['TMP']['to'] = self.bathSpinBox_list[index-1][1].value()
                    data["SETTINGS"]["BATH"+str(index)]["DO"]["from"] = \
                    SETTINGS.BATH_dict['BATH'+str(index)]['DO']['from'] = self.bathSpinBox_list[index-1][2].value()
                    data["SETTINGS"]["BATH"+str(index)]["DO"]["to"] = \
                    SETTINGS.BATH_dict['BATH'+str(index)]['DO']['to'] = self.bathSpinBox_list[index-1][3].value()
                    data["SETTINGS"]["BATH"+str(index)]["PH"]["from"] = \
                    SETTINGS.BATH_dict['BATH'+str(index)]['PH']['from'] = self.bathSpinBox_list[index-1][4].value()
                    data["SETTINGS"]["BATH"+str(index)]["PH"]["to"] = \
                    SETTINGS.BATH_dict['BATH'+str(index)]['PH']['to'] = self.bathSpinBox_list[index-1][5].value()
            elif setting == 'intmp':
                data["SETTINGS"]["INTMP"]["from"] = \
                SETTINGS.INTMP['from'] = ui.doubleSpinBox_intmp1.value()
                data["SETTINGS"]["INTMP"]["to"] = \
                SETTINGS.INTMP['to'] = ui.doubleSpinBox_intmp2.value()
            elif setting == 'co2':
                data["SETTINGS"]["CO2"]["from"] = \
                SETTINGS.CO2['from'] = ui.doubleSpinBox_co21.value()
                data["SETTINGS"]["CO2"]["to"] = \
                SETTINGS.CO2['to'] = ui.doubleSpinBox_co22.value()
            elif setting == 'lux':
                SETTINGS.INLUX['from'] = ui.doubleSpinBox_lux1.value()
                SETTINGS.INLUX['to'] = ui.doubleSpinBox_lux2.value()
            elif setting == 'ec':
                data["SETTINGS"]["EC"]["from"] = \
                SETTINGS.EC['from'] = ui.doubleSpinBox_ec1.value()
                data["SETTINGS"]["EC"]["to"] = \
                SETTINGS.EC['to'] = ui.doubleSpinBox_ec2.value()
            elif setting == 'inhumid':
                data["SETTINGS"]["INHUMID"]["from"] = \
                SETTINGS.INHUMID['from'] = ui.doubleSpinBox_inhumid1.value()
                data["SETTINGS"]["INHUMID"]["to"] = \
                SETTINGS.INHUMID['to'] = ui.doubleSpinBox_inhumid2.value()
            elif setting == 'ammonia':
                data["SETTINGS"]["AMMONIA"]["from"] = \
                SETTINGS.AMMONIA['from'] = ui.doubleSpinBox_ammonia1.value()
                data["SETTINGS"]["AMMONIA"]["to"] = \
                SETTINGS.AMMONIA['to'] = ui.doubleSpinBox_ammonia2.value()
            elif setting == 'electron':
                data["SETTINGS"]["ELECTRON"]["delay"] = \
                SETTINGS.ELECTRON['delay'] = 'O' if ui.checkBox_dayelecalert.isChecked() else 'X'
                data["SETTINGS"]["ELECTRON"]["month"] = \
                SETTINGS.ELECTRON['month'] = 'O' if ui.checkBox_monthelecalert.isChecked() else 'X'
                data["SETTINGS"]["ELECTRON"]["blackout"] = \
                SETTINGS.ELECTRON['blackout'] = 'O' if ui.checkBox_blackoutalert.isChecked() else 'X'
            elif setting == 'freq':
                if ui.comboBox_sensorunits1.value() == '초':
                    data["SETTINGS"]["FREQ"] = \
                    SETTINGS.FREQ = ui.spinBox_sensorfreq1.value() * 1000
                elif ui.comboBox_sensorunits1.value() == '분':
                    data["SETTINGS"]["FREQ"] = \
                    SETTINGS.FREQ = ui.spinBox_sensorfreq1.value() * 60 * 1000
                elif ui.comboBox_sensorunits1.value() == '시':
                    data["SETTINGS"]["FREQ"]
                    SETTINGS.FREQ = ui.spinBox_sensorfreq1.value() * 60 * 60 * 1000
        with open("config.json", "w") as jsonFile:
                json.dump(data, jsonFile, indent = 4)


    def plotting(self, graph):
        x = [(datetime.datetime.now() + datetime.timedelta(minutes=i)).strftime('%H:%M:%S') for i in range(48)]
        xdict = dict(enumerate(x))
        stringaxis = pg.AxisItem(orientation='bottom')
        stringaxis.setTicks([xdict.items()]) 
        stringaxis.setTickSpacing(5)
        font = font=QtGui.QFont('맑은 고딕', 11)
        print('called',graph)
        if graph == 1 or ui.tabWidget.currentIndex() == 0:
            if not self.INITILIZED1 :
                self.TMPgraph1 = ui.graphicsView_bathgraph1.addPlot(row = 0, col = 0, rowspan = 1, title = '수온',axisItems = {'bottom': stringaxis})
                self.TMPgraph1.getAxis('bottom').tickFont = font
                self.TMPgraph1.getAxis('left').tickFont = font
                self.DOgraph1 = ui.graphicsView_bathgraph1.addPlot(row =1, col = 0, rowspan = 1, title = 'DO',axisItems = {'bottom': stringaxis})
                self.PHgraph1 = ui.graphicsView_bathgraph1.addPlot(row =2, col = 0, rowspan = 1, title = 'pH',axisItems = {'bottom': stringaxis})
                self.INITILIZED1 = True
            self.TMPgraph1.clear()
            self.TMPgraph1.plot(list(xdict.keys()),BATH1.PH_list[-48:], pen=pg.mkPen(color=(27,119,208), width=3),
                        style=QtCore.Qt.DashLine, symbol=('o'), symbolSize=4,symbolBrush=(27,119,208),antialias=True)
            self.DOgraph1.clear()
            self.DOgraph1.plot(list(xdict.keys()),BATH1.DO_list[-48:], pen=pg.mkPen(color=(33,94,162), width=3),
                        style=QtCore.Qt.DashLine, symbol=('o'), symbolSize=4,symbolBrush=(33,94,162),antialias=True)
            self.PHgraph1.clear()
            self.PHgraph1.plot(list(xdict.keys()),BATH1.PH_list[-48:], pen=pg.mkPen(color=(33,71,119), width=3),
                        tyle=QtCore.Qt.DashLine, symbol=('o'), symbolSize=4,symbolBrush=(33,71,119),antialias=True)
        elif graph == 2 or ui.tabWidget.currentIndex() == 1:
            if not self.INITILIZED2:
                self.TMPgraph2 = ui.graphicsView_bathgraph2.addPlot(row = 0, col = 0, rowspan = 1, title = '수온',axisItems = {'bottom': stringaxis})
                self.TMPgraph2.getAxis('bottom').tickFont = font
                self.TMPgraph2.getAxis('left').tickFont = font
                self.DOgraph2 = ui.graphicsView_bathgraph2.addPlot(row =1, col = 0, rowspan = 1, title = 'DO',axisItems = {'bottom': stringaxis})
                self.PHgraph2 = ui.graphicsView_bathgraph2.addPlot(row =2, col = 0, rowspan = 1, title = 'pH',axisItems = {'bottom': stringaxis})
                self.INITILIZED2 = True
            self.TMPgraph2.clear()
            self.TMPgraph2.plot(list(xdict.keys()),BATH2.TMP_list[-48:], pen=pg.mkPen(color=(27,119,208), width=3),
                        style=QtCore.Qt.DashLine, symbol=('o'), symbolSize=4,symbolBrush=(27,119,208),antialias=True)
            self.DOgraph2.clear()
            self.DOgraph2.plot(list(xdict.keys()),BATH2.DO_list[-48:], pen=pg.mkPen(color=(33,94,162), width=3),
                        style=QtCore.Qt.DashLine, symbol=('o'), symbolSize=4,symbolBrush=(33,94,162),antialias=True)
            self.PHgraph2.clear()
            self.PHgraph2.plot(list(xdict.keys()),BATH2.PH_list[-48:], pen=pg.mkPen(color=(33,71,119), width=3),
                        tyle=QtCore.Qt.DashLine, symbol=('o'), symbolSize=4,symbolBrush=(33,71,119),antialias=True)
        elif graph == 3 or ui.tabWidget.currentIndex() == 2:
            if not self.INITILIZED3 :
                self.TMPgraph3 = ui.graphicsView_bathgraph3.addPlot(row = 0, col = 0, rowspan = 1, title = '수온',axisItems = {'bottom': stringaxis})
                self.TMPgraph3.getAxis('bottom').tickFont = font
                self.TMPgraph3.getAxis('left').tickFont = font
                self.DOgraph3 = ui.graphicsView_bathgraph3.addPlot(row =1, col = 0, rowspan = 1, title = 'DO',axisItems = {'bottom': stringaxis})
                self.PHgraph3 = ui.graphicsView_bathgraph3.addPlot(row =2, col = 0, rowspan = 1, title = 'pH',axisItems = {'bottom': stringaxis})
                self.INITILIZED3 = True
            self.TMPgraph3.clear()
            self.TMPgraph3.plot(list(xdict.keys()),BATH3.TMP_list[-48:], pen=pg.mkPen(color=(27,119,208), width=3),
                        style=QtCore.Qt.DashLine, symbol=('o'), symbolSize=4,symbolBrush=(27,119,208),antialias=True)
            self.DOgraph3.clear()
            self.DOgraph3.plot(list(xdict.keys()),BATH3.DO_list[-48:], pen=pg.mkPen(color=(33,94,162), width=3),
                        style=QtCore.Qt.DashLine, symbol=('o'), symbolSize=4,symbolBrush=(33,94,162),antialias=True)
            self.PHgraph3.clear()
            self.PHgraph3.plot(list(xdict.keys()),BATH3.PH_list[-48:], pen=pg.mkPen(color=(33,71,119), width=3),
                        tyle=QtCore.Qt.DashLine, symbol=('o'), symbolSize=4,symbolBrush=(33,71,119),antialias=True)
        elif graph == 4 or ui.tabWidget.currentIndex() == 3:
            if not self.INITILIZED4 :
                self.TMPgraph4 = ui.graphicsView_bathgraph4.addPlot(row = 0, col = 0, rowspan = 1, title = '수온',axisItems = {'bottom': stringaxis})
                self.TMPgraph4.getAxis('bottom').tickFont = font
                self.TMPgraph4.getAxis('left').tickFont = font
                self.DOgraph4 = ui.graphicsView_bathgraph4.addPlot(row =1, col = 0, rowspan = 1, title = 'DO',axisItems = {'bottom': stringaxis})
                self.PHgraph4 = ui.graphicsView_bathgraph4.addPlot(row =2, col = 0, rowspan = 1, title = 'pH',axisItems = {'bottom': stringaxis})
                self.INITILIZED4 = True
            self.TMPgraph4.clear()
            self.TMPgraph4.plot(list(xdict.keys()),BATH4.TMP_list[-48:], pen=pg.mkPen(color=(27,119,208), width=3),
                        style=QtCore.Qt.DashLine, symbol=('o'), symbolSize=4,symbolBrush=(27,119,208),antialias=True)
            self.DOgraph4.clear()
            self.DOgraph4.plot(list(xdict.keys()),BATH4.DO_list[-48:], pen=pg.mkPen(color=(33,94,162), width=3),
                        style=QtCore.Qt.DashLine, symbol=('o'), symbolSize=4,symbolBrush=(33,94,162),antialias=True)
            self.PHgraph4.clear()
            self.PHgraph4.plot(list(xdict.keys()),BATH4.PH_list[-48:], pen=pg.mkPen(color=(33,71,119), width=3),
                        tyle=QtCore.Qt.DashLine, symbol=('o'), symbolSize=4,symbolBrush=(33,71,119),antialias=True)


    def updateSettings(self, applyall_clicked):
        if not applyall_clicked:
            for index in range(4):
                self.bathSpinBox_list[index][0].setValue(SETTINGS.BATH_dict['BATH'+str(index+1)]['TMP']['from'])
                self.bathSpinBox_list[index][1].setValue(SETTINGS.BATH_dict['BATH'+str(index+1)]['TMP']['to'])
                self.bathSpinBox_list[index][2].setValue(SETTINGS.BATH_dict['BATH'+str(index+1)]['DO']['from'])
                self.bathSpinBox_list[index][3].setValue(SETTINGS.BATH_dict['BATH'+str(index+1)]['DO']['to'])
                self.bathSpinBox_list[index][4].setValue(SETTINGS.BATH_dict['BATH'+str(index+1)]['PH']['from'])
                self.bathSpinBox_list[index][5].setValue(SETTINGS.BATH_dict['BATH'+str(index+1)]['PH']['to'])
            ui.doubleSpinBox_intmp1.setValue(SETTINGS.INTMP['from'])
            ui.doubleSpinBox_intmp2.setValue(SETTINGS.INTMP['to'])
            ui.doubleSpinBox_co21.setValue(SETTINGS.CO2['from'])
            ui.doubleSpinBox_co22.setValue(SETTINGS.CO2['to'])
            ui.doubleSpinBox_lux1.setValue(SETTINGS.INLUX['from'])
            ui.doubleSpinBox_lux2.setValue(SETTINGS.INLUX['to'])
            ui.doubleSpinBox_ec1.setValue(SETTINGS.EC['from'])
            ui.doubleSpinBox_ec2.setValue(SETTINGS.EC['to'])
            ui.doubleSpinBox_inhumid1.setValue(SETTINGS.INHUMID['from'])
            ui.doubleSpinBox_inhumid2.setValue(SETTINGS.INHUMID['to'])
            ui.doubleSpinBox_ammonia1.setValue(SETTINGS.AMMONIA['from'])
            ui.doubleSpinBox_ammonia2.setValue(SETTINGS.AMMONIA['to'])

            ui.checkBox_dayelecalert.setCheckState(2) if SETTINGS.ELECTRON['delay'] == 'O' else 'X'
            ui.checkBox_monthelecalert.setCheckState(2) if SETTINGS.ELECTRON['month'] == 'O' else 'X'
            ui.checkBox_blackoutalert.setCheckState(2) if SETTINGS.ELECTRON['blackout'] == 'O' else 'X'
        #Qt.Unchecked 0 Qt.Checked 2  
            for i in range(8):
                self.bathcheckbox_list[i].setCheckState(2) if SETTINGS.BATH_dict['BATH'+str(i+1)]['check'] == 'O' else self.bathcheckbox_list[i].setCheckState(0)
        else :
            index = ui.tabWidget_2.currentIndex()
            for i in range(4):    
                self.bathSpinBox_list[i][0].setValue(self.bathSpinBox_list[index][0].value())
                self.bathSpinBox_list[i][1].setValue(self.bathSpinBox_list[index][1].value())
                self.bathSpinBox_list[i][2].setValue(self.bathSpinBox_list[index][2].value())
                self.bathSpinBox_list[i][3].setValue(self.bathSpinBox_list[index][3].value())
                self.bathSpinBox_list[i][4].setValue(self.bathSpinBox_list[index][4].value())
                self.bathSpinBox_list[i][5].setValue(self.bathSpinBox_list[index][5].value())

    # def updateElectron(self):
    #     ui.label_elec1hour.setText()
    #     ui.label_elec1day.setText()
    #     ui.label_elec1week.setText()
    #     ui.label_elec1month.setText()

if __name__ == '__main__':
    import sys
    pg.setConfigOption('background', 'w')
    pg.setConfigOption('foreground', 'k')
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    timeUpdateThread = TimeUpdateThread(ui)
    eventThread = EventThread(ui)
    uartCom = UartCom(ui, eventThread)
    valueUpdateThread = ValueUpdateThread(ui, uartCom, eventThread)
    sys.exit(app.exec_())