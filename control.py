from control_gui import *
import PyQt5
import pyqtgraph
import sys
import glob
import serial
import asyncio
import serial_asyncio
from threading import Thread

class UartCom():
    connect_port=[]
    def __init__(self, ui):
        self.ui=ui
        self.get_com()
        self.connect_serial()
        self.sendUart()
        # ui.comboBox.activated[str].connect(self.connect_serial)
        ui.pushButton_comconnect.clicked.connect(self.connect_serial)
        ui.pushButton_check.clicked.connect(self.sendUart)
        
        self.uart =None

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
            self.coro = serial_asyncio.create_serial_connection(self.loop, lambda: UartProtocol(self.app), self.mcuPort, baudrate=115200)
            print('Connected mcu port = '+self.mcuPort)
        else:
            print(str(com_no)+' connected')
            self.coro = serial_asyncio.create_serial_connection(self.loop, lambda: UartProtocol(self), com_no, baudrate=115200)
        self.loop.run_until_complete(self.coro)

        t = Thread(target=self.run, args=(self.loop,))
        t.start()
        #self.loop.call_soon_threadsafe(asyncio.async , self.coro)
        pass


    def printLog(self, msg):
        print('<{!r}> {!r}'.format(self.getTimeStamp(), msg))


    def sendUart(self):
        msg = '\x02WATER?\x03\x0A\x0D'
        print(msg)
        if self.uart != None:
            self.uart.write(msg.encode())        
        else : 
            print('Not Connected')

class UartProtocol(asyncio.Protocol):
    def __init__(self, ui):
        self.ui = ui
        self.rcvParser = RcvParser(ui)

    def connection_made(self, transport):
        self.transport = transport
        print('port opened', transport)
        # rts (Request to Send) : 송신 요청
        # cts (Clear to Send) : 송신 확인
        transport.serial.rts = False  # You can manipulate Serial object via transport
        # transport.write(b'Hello, World!\r\n')  # Write serial data via transport
        self.ui.uart = transport

    def data_received(self, data):
        message = data.decode() # repr(data)
        print('data received', message)
        self.rcvParser.parsing(message)

        
        # print('data received', repr(data))
        # self.app.log('serial :{!r}'.format(data.decode()))
        # self.app.rcvUart(message)
        # if b'\n' in data:
            # self.transport.close()

    def connection_lost(self, exc):
        print('port closed')
        self.transport.loop.stop()

    def pause_writing(self):
        print('pause writing')
        print(self.transport.get_write_buffer_size())

    def resume_writing(self):
        print(self.transport.get_write_buffer_size())
        print('resume writing')


class RcvParser():
    def __init__(self, ui):
        self.ui = ui
        self.initProtocol()

    def parsing(self, pkt):

        self.command = pkt.strip("\x02\x03\n\r")
        cmd = self.command[0]
        if (cmd == 'T'):
            cmd = self.command[0:2]

        try:
            func = self.protocol.get(cmd)
            return func()
        except Exception as e:
            print("type error: " + str(e))

    # def rcvOK(self):        
    #     return 'OK'

    # def rcvAlarm(self):
    #     rcvData = self.command.split("=")[1]
    #     self.app.updateAlarm(rcvData[0],rcvData[1],rcvData[2])

    # def rcvSwitch(self):
    #     rcvData = self.command.split("=")[1]
    #     self.app.updateSwitch(rcvData[0],rcvData[1],rcvData[2])

    # def rcvState(self):
    #     return 'OK'

    # def rcvTemp(self):
    #     rcvData = self.command.split("=")[1]
    #     tempAndHumi =  rcvData.replace(';',',').split(',');
    #     # print("??????????>>>>>>>>>>>"+tempAndHumi[0]+','+tempAndHumi[1])
    #     self.app.updateTemp(tempAndHumi[0],tempAndHumi[1])
    #     pass

    def rcvT1(self):
        ID = int(self.command[1])
        TMP = int(self.command[3:8])
        
        print(ID, TMP)
        #self.signal.emit()
        print('rcvT1 Data')

    # def received(self, ID, TMP):
    #     self.rcvT1signal.emit(ID,TMP)

    def rcvT2(self):
        ID = self.command[1]
        TMP = self.command[3:8]
        Humid = self.command[9:11]
        Co2 = self.command[12:16]
        I = self.command[17:20]
        self.ui.pushButton_check.setChecked()

    def rcvWater(self):
        ID = self.command[1]
        TMP = self.command[3:8]
        DO = self.command[9:13]
        pH = self.command[14:18]
        Level = self.command[19:23]
        

    def rcvLED(self):
        OKID = self.command[1:3]

    def initProtocol(self):
        self.protocol = {
        'T1': self.rcvT1,
        'T2': self.rcvT2,
        'W': self.rcvWater
        # 'H':
        # 'P':
        # 'B':
        # 'F':
        # 'L': self.rcvLED
        # 'U': 
        # 'OK' : self.rcvOK,
        # 'ALARM' : self.rcvAlarm,
        # 'SWITCH' : self.rcvSwitch,
        # 'STATE' : self.rcvState,
        # 'TEMP' : self.rcvTemp
        }    


#QThread를 상속받는 타임 ui 업데이트 스레드
class TimeUpdateThread(PyQt5.QtCore.QThread):
    def __init__(self, ui):
        self.ui = ui
        super().__init__()
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

        


class EventThread(PyQt5.QtCore.QThread):
    stylesheet_pushButton = 'QPushButton{border: 1px solid grey; border-radius:4px;' \
                                        +'background-color:qlineargradient(spread:pad, x1:0.5, y1:0, x2:0.5, y2:1,'\
                                        +'stop:0.6 rgba(255, 255, 255, 255), stop:0.95 rgb(155, 214, 255),' \
                                        +'stop:0.983425 rgba(255, 255, 255, 255), stop:1 rgba(0, 0, 0, 0))}' \
                        +'QPushButton:pressed{border : 1px solid grey;' \
                                            'border-radius : 4px;' \
                                            'background-color: rgb(155, 214, 255)}'
    stylesheet_normalback = 'QGraphicsView{border : transparent;' \
                                            +'border-radius : 4px;' \
                                            + 'background-color :qlineargradient(spread:pad, x1:0.5, y1:0.7, x2:0.5, y2:1,'\
                                            + 'stop:0 rgba(160, 234, 31, 255), stop:1 rgba(127, 183, 23, 247))}'

    stylesheet_abnormalback = 'QGraphicsView{border : transparent;'\
                                            +'border-radius : 4px;'\
                                            +'background-color :qlineargradient(spread:pad, x1:0.5, y1:0.7, x2:0.5, y2:1,'\
                                            +'stop:0 rgba(255, 106, 106, 255), stop:1 rgba(195, 67, 67, 255))}'

    stylesheet_mainButton = 'QPushButton{background-color:rgb(52, 56, 56);'\
                                        +'color : white}'\
                            +'QPushButton:checked{background-color:rgb(0, 145, 255);'\
                                                +'color : white;'\
                                                +'border : 1px solid grey;}'

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
                                ui.pushButton_intmpsave, ui.pushButton_co2save, ui.pushButton_co2save, ui.pushButton_ecsave,
                                ui.pushButton_inhumidsave, ui.pushButton_amoniasave, ui.pushButton_electronsave, ui.pushButton_othersave]

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
        for pushButton in self.pushButton_list:
            pushButton.setStyleSheet(EventThread.stylesheet_pushButton)
        for mainButton in self.mainButton_list:
            mainButton.setStyleSheet(EventThread.stylesheet_mainButton)
        # changePage
        ui.pushButton_main.clicked.connect(lambda x: ui.stackedWidget.setCurrentIndex(0))
        ui.pushButton_watertmp.clicked.connect(lambda x: ui.stackedWidget.setCurrentIndex(1))
        ui.pushButton_do.clicked.connect(lambda x: ui.stackedWidget.setCurrentIndex(2))
        ui.pushButton_ph.clicked.connect(lambda x: ui.stackedWidget.setCurrentIndex(3))
        ui.pushButton_aircondition.clicked.connect(lambda x: ui.stackedWidget.setCurrentIndex(4))
        ui.pushButton_electron.clicked.connect(lambda x: ui.stackedWidget.setCurrentIndex(5))
        ui.pushButton_settings.clicked.connect(lambda x: ui.stackedWidget.setCurrentIndex(6))
        # changeSubPage
        ui.pushButton_tmpvalue.clicked.connect(lambda x : ui.stackedWidget_1.setCurrentIndex(0))
        ui.pushButton_tmpgraph.clicked.connect(lambda x : ui.stackedWidget_1.setCurrentIndex(1))
        ui.pushButton_dovalue.clicked.connect(lambda x : ui.stackedWidget_2.setCurrentIndex(0))
        ui.pushButton_dograph.clicked.connect(lambda x : ui.stackedWidget_2.setCurrentIndex(1))
        ui.pushButton_phvalue.clicked.connect(lambda x : ui.stackedWidget_3.setCurrentIndex(0))
        ui.pushButton_phgraph.clicked.connect(lambda x : ui.stackedWidget_3.setCurrentIndex(1))
#Ui_MainWindow.signals = signals

if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    # thread = threading.Thread(target=settimer)
    # thread.daemon = True
    # thread.start()
    timeUpdateThread = TimeUpdateThread(ui)
    eventThread = EventThread(ui)
    MainWindow.show()
    UartCom(ui)
    sys.exit(app.exec_())