import connect
import parameters
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QComboBox, QPushButton

from PyQt5 import QtCore, QtGui

from PyQt5.QtCore import pyqtSlot


from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import os
import re

from c_Thread import *


from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import random

import numpy as np

from datetime import datetime


class Example(QWidget):
    
    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)
        
        self.COMM_Port = 'XXX'
        self.BaudRate  = '9600'
        
        self.dt = 1.0
        
        self.pH_measued = 0.00
        self.ToC_measured = 0.00
        self.Time_measured = 'XXXXXXX'
        self.Time_measured_tm1 = 'XXXXXXX'
        self.Data_measured = 'XXXXXXX'
        
        self.pH_targ_txt = 7.00
        self.pH_Hyst_txt = 0.20
        
        self.PID_K_P_txt = 3.8
        self.PID_K_I_txt = 0.10
        self.PID_K_D_txt = 1.00
        self.PID_Reg_Tsaw_txt = 10.00
        
        self.pH_sender_is_active = False
        self.timer_saw = 0
        self.timer_pH_sender = 0
        self.Timer_pH_LIM = 40 / self.dt

#============================================================================        
# Parameters for Graphics
        N_max = 30000
        self.N_grph = 600
        # Parameters for Comp+Hyst, graph
        self.pH_history = np.zeros(N_max)
        self.Motor_history = np.zeros(N_max)
        self.grph_k = 0
#============================================================================        
# PID regulator parameters
        self.Err_P = 0.0
        self.Err_I = 0.0
        self.Err_D = 0.0
        self.d_Saw = self.dt / self.PID_Reg_Tsaw_txt
        self.Saw_t = 0.0

        self.pH_Err = 0.0
        self.pH_Err_tm1 = 0.0
        self.PID_Err = 0.0

        self.Saw_history = np.zeros(N_max)
        self.Err_P_history = np.zeros(N_max)
        self.Err_I_history = np.zeros(N_max)
        self.Err_D_history = np.zeros(N_max)
        self.Err_S_history = np.zeros(N_max)

#============================================================================        

        self.Auto_Control = False
        self.CSV_file_opened_successfully = False
        self.Comm_Port_opened_successfully = False
        self.Thread_is_active = False
#        self.Time_from_Ph = 'XXXX'       
#        self.Time_from_Ph_tm1 = 'XXXX'       
        self.CSV_pH_file_path = 'XXXX'        
        
        self.Motor_Active = False
        OutFile = open('Motor_Imitation.txt', 'w')
        print('0', file = OutFile)
        OutFile.close()          
        
        # Regulator variables
        self.Caustic = 1
        self.Acid    = 2
        self.CompHyst = 3
        self.PID_reg  = 4
        
        self.pH_measured = 6.8
        
        self.pH_pump_substance = self.Caustic
        self.Regulator_type = self.CompHyst
        
        self.Create_Elements()
        self.Place_Elements()
        
        

        self.qlabel = QLabel(self)
        self.qlabel.move(50,16)



#        combo.activated[str].connect(self.onChanged)      

        self.setGeometry(50,50,750,800)
        self.setWindowTitle("QLineEdit Example")
        self.show()

    def Create_Elements(self):
        global portinfo
        portinfo = connect.getOpenPorts()

        # COMM Port selection ComboBox        
        self.COMM_select  = QComboBox(self)
        self.BaudRate_Sel = QComboBox(self)
        self.COMM_Update         = QPushButton('Ports state Upd', self)
        self.pH_Sensor_File_Open = QPushButton('Open CSV file', self)
        self.COMM_Connect        = QPushButton('Pump Connect', self)
        self.Button_Pmp_Strt     = QPushButton('Start', self)
        self.Button_Pmp_Stop     = QPushButton('Stop', self)
        self.Control_Run         = QPushButton('Control Run', self)
        self.Control_Stop        = QPushButton('Control Stop', self)

        self.pH_plus        = QPushButton('pH+', self)
        self.pH_minus       = QPushButton('pH-', self)
        self.Comp_Hyst      = QPushButton('Comp Hyst', self)
        self.PID_Reg_btn        = QPushButton('PID reg', self)


        self.Comm_Explanation    = QLabel('1. Select COMM port Pump connected to, \n' +
                                          'Select baudrate if neceessary (9600bps by definition),\n' +
                                          'then Connect Pump with button. If you plug in Pump to USB,\n' +
                                          'press Ports state Upd button to update COMM configuration', self)
        self.Comm_Explanation.setFont(QFont('Arial', 8))
        self.Explanation_2    = QLabel('2. After Connecting pomp via COMM port  \n' +
                                          'manual pump On/Off is available.', self)
        self.Explanation_2.setFont(QFont('Arial', 8))
        self.Explanation_3    = QLabel('3. To run pump control with pH sensor  \n' +
                                          'choose the *.csv file generated with pH sensor.', self)
        self.Explanation_3.setFont(QFont('Arial', 8))
        self.Explanation_4    = QLabel('4. Run pH measurement module (pH transmitter). When it active,  \n' +
                                          'transmitter measures pH, temperature and provide it to *.csv file\n' + 
                                          'selected in point 3. Auto control is possible only when new pH\n' +
                                          ' measurement is provided every 40 sec or more often.', self)
        self.Explanation_4.setFont(QFont('Arial', 8))
        self.Explanation_5    = QLabel('5. To stabilize pH, we control Pump using data from pH-meter.\n' +
                                       ' We have two cases: 1) pump increase pH (pH+, pump adds caustic substance) (By definition);\n' +
                                       '                    2) pump decrease pH (pH-, pump adds acid substance).\n' +
                                       'Select the mode using corresponding button.', self)
        self.Explanation_5.setFont(QFont('Arial', 8))
        self.Explanation_6    = QLabel('6. We have two algorithms of control: 1)Comparator with hysteresis (By definition), 2) PID-regulator.\n' +
                                       '   Comparator with hysteresis uses pH target value (pH_targ) and histeresis (pH_hyst). In case when pump adds to reactor \n' +
                                       '   caustic solution it turns pump On when pH less than (pH_targ - pH_hyst) and turns Off when it exceeds (pH_targ + pH_hyst).\n' +
                                       '   PID-regulator theory is explained in https://en.wikipedia.org/wiki/PID_controller (When I find better link Ill share).\n'
                                       '   It have three control parameters: Proportionoal (P), Integral (I) and Differential (D) and saw period (T_saw)', self)
        self.Explanation_6.setFont(QFont('Arial', 8))
        
        self.Pump_Manual_Label   = QLabel('Manual control', self)
        self.Pump_Manual_Label.setFont(QFont('Arial', 12))
        self.Pump_Auto_Labell   = QLabel('Auto control', self)
        self.Pump_Auto_Labell.setFont(QFont('Arial', 12))

        self.Regulator_Description   = QLabel('Regulator type: Comp+Hyst, control pH- (pump adds alkali)', self)
        self.Regulator_Description.setFont(QFont('Arial', 12))
        
        self.Comp_Hyst_Params   = QLabel('Comp Hyst\nparameters ', self)
        self.Comp_Hyst_Params.setFont(QFont('Arial', 10))
        self.PID_Reg_Params   = QLabel('PID-reg\nparameters', self)
        self.PID_Reg_Params.setFont(QFont('Arial', 10))
        self.Motor_State   = QLabel('Motor Off', self)
        self.Motor_State.setFont(QFont('Arial', 10))
        self.Control_State   = QLabel('Control Off', self)
        self.Control_State.setFont(QFont('Arial', 10))
        
# PID Reg Parameters show
        self.PID_Err_P   = QLabel('E_P = 0.0', self)
        self.Control_State.setFont(QFont('Arial', 7))
        self.PID_Err_I   = QLabel('E_I = 0.0', self)
        self.Control_State.setFont(QFont('Arial', 7))
        self.PID_Err_D   = QLabel('E_D = 0.0', self)
        self.Control_State.setFont(QFont('Arial', 7))
        self.PID_Err_S   = QLabel('E_S = 0.0', self)
        self.Control_State.setFont(QFont('Arial', 7))
        
        
        
        self.Message_about_CSV_file   = QLabel(' ', self)
        self.Message_about_CSV_file.setFont(QFont('Arial', 12))
        self.Data_from_pH   = QLabel(' ', self)
        self.Data_from_pH.setFont(QFont('Arial', 12))        
        self.Time_from_pH   = QLabel(' ', self)
        self.Time_from_pH.setFont(QFont('Arial', 12))        
        self.Temperature    = QLabel(' ', self)
        self.Temperature.setFont(QFont('Arial', 12))        
        self.pH             = QLabel(' ', self)
        self.pH.setFont(QFont('Arial', 16))        
        
        # Parameters for Comparator with Hysteresis
        self.CompHyst_pH_Targ = QLineEdit(str(self.pH_targ_txt), self)
        self.CompHyst_pH_Hyst = QLineEdit(str(self.pH_Hyst_txt), self)
        self.CompHyst_pH_Targ_Lbl   = QLabel('pH targ = ', self)
        self.CompHyst_pH_Targ_Lbl.setFont(QFont('Arial', 8))
        self.CompHyst_pH_Hyst_Lbl   = QLabel('pH Hyst = ', self)
        self.CompHyst_pH_Hyst_Lbl.setFont(QFont('Arial', 8))
        
        # Parameters for PID-Regulator     
        self.PID_Reg_eP   = QLineEdit(str(self.PID_K_P_txt), self)
        self.PID_Reg_eI   = QLineEdit(str(self.PID_K_I_txt), self)
        self.PID_Reg_eD   = QLineEdit(str(self.PID_K_D_txt), self)
        self.PID_Reg_Tsaw = QLineEdit(str(self.PID_Reg_Tsaw_txt), self)
        self.PID_Reg_eP_Lbl   = QLabel('K_P = ', self)
        self.PID_Reg_eP_Lbl.setFont(QFont('Arial', 8))
        self.PID_Reg_eI_Lbl   = QLabel('K I = ', self)
        self.PID_Reg_eI_Lbl.setFont(QFont('Arial', 8))
        self.PID_Reg_eD_Lbl   = QLabel('K D = ', self)
        self.PID_Reg_eD_Lbl.setFont(QFont('Arial', 8))
        self.PID_Reg_Tsaw_Lbl   = QLabel('Tsaw =', self)
        self.PID_Reg_Tsaw_Lbl.setFont(QFont('Arial', 8))
        self.PID_Reg_Tsaw_Lbl_s   = QLabel('s', self)
        self.PID_Reg_Tsaw_Lbl_s.setFont(QFont('Arial', 8))
                        
#=========================================================================        
        for port in portinfo:
            self.COMM_select.addItem(port)

        self.BaudRate_Sel.addItem('9600')
        self.BaudRate_Sel.addItem('38400')

        self.COMM_select.activated[str].connect(self.click_COMM_select)
        self.BaudRate_Sel.activated[str].connect(self.click_BaudRate_Sel)
        self.COMM_Update.clicked.connect(self.click_COMM_Update)
        self.pH_Sensor_File_Open.clicked.connect(self.click_pH_Sensor_File_Open)
        self.COMM_Connect.clicked.connect(self.click_COMM_Connect)

        self.COMM_Connect.setEnabled(False)
        self.Button_Pmp_Strt.setEnabled(False)
        self.Button_Pmp_Stop.setEnabled(False)

        self.Button_Pmp_Strt.clicked.connect(self.click_Pump_Manual_Start)
        self.Button_Pmp_Stop.clicked.connect(self.click_Pump_Manual_Stop)

        self.Control_Run.clicked.connect(self.click_Control_Run)
        self.Control_Stop.clicked.connect(self.click_Control_Stop)
        self.Control_Run.setEnabled(False)
        self.Control_Stop.setEnabled(False)
        
        self.pH_plus.clicked.connect(self.click_pH_plus)
        self.pH_minus.clicked.connect(self.click_pH_minus)
        self.Comp_Hyst.clicked.connect(self.click_Comp_Hyst)
        self.PID_Reg_btn.clicked.connect(self.click_PID_Reg)
        
        self.pH_plus.setEnabled(False)
        self.Comp_Hyst.setEnabled(False)

        
        self.myConnection = connect.Connection(port=self.COMM_Port,
                                               baudrate='9600', x='Single Pump', mode=1)
        self.connected = False
        


    def Check_Comm_Settings(self):

        if self.COMM_Port[0] == 'C':
            if self.BaudRate[0] == '9' or self.BaudRate[0] == '3':
                print('It is possible to try to open Comm Port')
                self.COMM_Connect.setEnabled(True)
                
                

       

    def Place_Elements(self):
        self.COMM_select.move(20, 110)
        self.COMM_Update.move(20, 80)
        self.BaudRate_Sel.move(20, 140)
        self.pH_Sensor_File_Open.move(390, 80)
#        self.COMM_Connect.move(100, 110)
        self.COMM_Connect.setGeometry(100, 110, 100, 40)
        
        self.Comm_Explanation.move(20, 20)
        self.Explanation_2.move(20,  180)
        self.Explanation_3.move(320,  40)
        self.Explanation_4.move(280, 110)
        self.Explanation_5.move(230, 220)
        self.Explanation_6.move(20,  320)

        self.Pump_Manual_Label.move(45, 220)
        self.Message_about_CSV_file.setGeometry(330, 175, 290, 40)
        self.Button_Pmp_Strt.move(20, 240)
        
        self.Button_Pmp_Stop.move(100, 240)
        
#        self.Pump_Auto_Labell.move(375, 550)
#        self.Control_Run.move(330, 570)
#        self.Control_Stop.move(420, 570)

        self.Pump_Auto_Labell.move(610, 625)
        self.Control_Run.move(620, 645)
        self.Control_Stop.move(620, 670)

        posy = 280
        self.Data_from_pH.setGeometry(20, posy, 190, 40)        
        self.Time_from_pH.setGeometry(160, posy, 190, 40)        
        self.Temperature.setGeometry(280, posy, 190, 40)        
        self.pH.setGeometry(400, posy, 190, 40)   

        posy = 410
        self.pH_minus.setGeometry(20, posy, 140, 40)
        self.pH_plus.setGeometry(160, posy, 140, 40)
        self.PID_Reg_btn.setGeometry(350, posy, 150, 40)
        self.Comp_Hyst.setGeometry(500, posy, 150, 40)
        
        self.Regulator_Description.setGeometry(140, 450, 450, 40)
        
        self.Comp_Hyst_Params.move(620, 475)
        self.PID_Reg_Params.move(20, 475)
        
        # Parameters for Comparator with Hysteresis
        self.CompHyst_pH_Targ.setGeometry(640, 510, 50, 20)
        self.CompHyst_pH_Hyst.setGeometry(640, 540, 50, 20)
        self.CompHyst_pH_Targ_Lbl.move(590, 512)
        self.CompHyst_pH_Hyst_Lbl.move(590, 542)

        # Parameters for PID-Regulator
        posx = 20
        posy = 510
        self.PID_Reg_eP.setGeometry(  posx + 30, posy +  0, 35, 20)
        self.PID_Reg_eI.setGeometry(  posx + 30, posy + 20, 35, 20)
        self.PID_Reg_eD.setGeometry(  posx + 30, posy + 40, 35, 20)
        self.PID_Reg_Tsaw.setGeometry(posx + 30, posy + 60, 35, 20)
        self.PID_Reg_eP_Lbl.move(  posx, posy +  3)
        self.PID_Reg_eI_Lbl.move(  posx, posy + 23)
        self.PID_Reg_eD_Lbl.move(  posx, posy + 43)
        self.PID_Reg_Tsaw_Lbl.move(posx - 10, posy + 63)
        self.PID_Reg_Tsaw_Lbl_s.move(posx - 10 + 76, posy + 63)

        self.Motor_State.setGeometry(  620, 730, 65, 20)
        self.Control_State.setGeometry(  620, 750, 65, 20)

        posy = 660
        self.PID_Err_P.setGeometry( 10, posy +  0, 55, 20)
        self.PID_Err_I.setGeometry( 10, posy + 15, 55, 20)
        self.PID_Err_D.setGeometry( 10, posy + 30, 55, 20)
        self.PID_Err_S.setGeometry( 10, posy + 45, 55, 20)


#        self.canvas.setGeometry(  130, 490, 105, 120)
        
#        self.main_widget = QWidget(self)
#        self.plot_widget = QWidget(self.main_widget)
        self.plot_widget = QWidget(self)
        self.plot_widget.setGeometry(90,480,500,320)
        self.figure = plt.figure()
        self.plotting = FigureCanvas(self.figure)
        self.plot()
        plot_box = QVBoxLayout()
        plot_box.addWidget(self.plotting)
        self.plot_widget.setLayout(plot_box)
        
#        data = [random.random() for i in range(10)]
#        self.plot_box.clear()
#        ax = self.plot_box.add_subplot(111)
#        ax.plot(data, '*-')
#        self.canvas.draw()

    def plot(self):
        ''' plot some random stuff '''
        data = [random.random() for i in range(10)]
        self.ax = self.figure.add_subplot(111)
#        ax.hold(False)
        self.ax.plot(data, '*-')
        self.plotting.draw()


    def click_COMM_select(self, text):

        self.COMM_Port = text
        print(self.COMM_Port)
        self.Check_Comm_Settings()
            
    @pyqtSlot()
    def click_COMM_Update(self):
        portinfo = connect.getOpenPorts()
        self.COMM_select.clear()
        for port in portinfo:
            self.COMM_select.addItem(port)
        print('PyQt5 button click')
#        open_file()

    def click_BaudRate_Sel(self, text):
        global BaudRate
        self.BaudRate = text
        self.Check_Comm_Settings()
        
        
    def Pump_Start(self):
        if self.connected:
            if self.Motor_Active == False:
                print("Start")
                self.Motor_Active = True
                self.myConnection.startPump()  
                self.Motor_State.setText('Motor On') 
                OutFile = open('Motor_Imitation.txt', 'w')
                print('1', file = OutFile)
                OutFile.close()                
                
    def Pump_Stop(self):
        if self.connected:
            if self.Motor_Active == True:
                self.Motor_Active = False
                print("Stop")
                self.myConnection.stopPump()
                self.Motor_State.setText('Motor Off') 
                OutFile = open('Motor_Imitation.txt', 'w')
                print('0', file = OutFile)
                OutFile.close()     



    @pyqtSlot()
    def click_COMM_Connect(self):
        if not self.connected:
            try:
                self.myConnection.baudrate = self.BaudRate
                self.myConnection.port = self.COMM_Port
                self.myConnection.openConnection()
                self.COMM_Connect.setText("Pump Disconnect")
#                self.connectBtn.setText("Disconnect")
                self.connected = True
                self.Button_Pmp_Strt.setEnabled(True)
                self.Button_Pmp_Stop.setEnabled(True)
                self.COMM_select.setEnabled(False)
                self.BaudRate_Sel.setEnabled(False)
                self.COMM_Update.setEnabled(False)
                self.Comm_Port_opened_successfully = True
                self.check_Auto_pH_Control_Possible()

            except TypeError as e:
                print(e)
                self.Comm_Port_opened_successfully = False
                self.check_Auto_pH_Control_Possible()
        else:
            self.myConnection.closeConnection()
#            self.connectLbl.setText("Disconnected")
            self.COMM_Connect.setText("Pump Connect")
            self.connected = False
#            self.connected = False
            self.Button_Pmp_Strt.setEnabled(False)
            self.Button_Pmp_Stop.setEnabled(False)
            self.COMM_select.setEnabled(True)
            self.BaudRate_Sel.setEnabled(True)
            self.COMM_Update.setEnabled(True)
            self.Comm_Port_opened_successfully = False
            self.check_Auto_pH_Control_Possible()
        
           

    @pyqtSlot()
    def click_Pump_Manual_Start(self):
        Pump_Start()        
    @pyqtSlot()
    def click_Pump_Manual_Stop(self):
        Pump_Stop()


            
    def run_pH_Auto_Reading_Run(self):
        if self.CSV_file_opened_successfully == False:
            if self.Thread_is_active == False:
                self.Thread_is_active = True
                print('Startnig cycle')
                @setInterval(self.dt)
                def funct():
                    global pH_
                    [pH, Temp, Data, Time, res] = self.Read_pH_value_csv(self.CSV_pH_file_path, 0)
                    self.Data_from_pH.setText('Data: ' + Data)        
                    self.Time_from_pH.setText('Time: '  + Time)        
                    self.Temperature.setText('t,oC = ' + Temp)        
                    self.pH.setText('pH = ' + pH) 
                    
                    self.ToC_measured = float(Temp)
                    self.Time_measured = Time
                    self.Data_measured = Data
                    self.pH_measured = float(pH)
#                    self.pH_measured = self.pH_measured - 0.008 + int(self.Motor_Active) * 0.015
                    
                    self.Check_pH_measuring_transmitter_activity()
                    
                    if self.Auto_Control == True:
                        self.run_Regulator()
                stop = funct()
        

    @pyqtSlot()
    def click_pH_Sensor_File_Open(self):
        title = "Select a docuement to load"
        filters = "*.csv"
        self.CSV_pH_file_path, filetype = QFileDialog.getOpenFileName(self, title, '', filters)
        print(self.CSV_pH_file_path)
        [pH, Temp, Data, Time, res] = self.Read_pH_value_csv(self.CSV_pH_file_path, 1)
        if res == 1:
            self.run_pH_Auto_Reading_Run()
            self.CSV_file_opened_successfully = True
            self.check_Auto_pH_Control_Possible()
        else:
            self.CSV_file_opened_successfully = False
            self.check_Auto_pH_Control_Possible()

        
        
    def Read_pH_value_csv(self, path, mode):
        res = 0
        with open(path , 'r')as f:
            lines = f.readlines()
            N = len(lines)
            if N <= 4:
               self.Message_about_CSV_file.setText('File has wrong format \n or no data yet')
               pH   = '0.00'
               Temp = '-273.15'
               Data = '-15.4 bln yrs'
               Time = 'Bulls hour'
               
               self.CSV_file_opened_successfully = False
               self.check_Auto_pH_Control_Possible()
            else:
                Final_Line = lines[N - 1]
                fields = re.split('[, ]|[,  ]|[,   ]|[?? ]', Final_Line)
#                n = 0
#                for field in fields:
#                    print(str(n) + '  ' + field)
#                    n += 1      
                if mode == 1:
                    if fields[11] == 'pH' and fields[16] == 'DegC':
                        self.Message_about_CSV_file.setText('File opened successfully')
                        print('Data readed successfully')
                        res = 1
                    else:
                        self.Message_about_CSV_file.setText('File has wrong format')
                        print('File has wrong format')
                        self.CSV_file_opened_successfully = False
               
                Data = fields[0]
                Time = fields[4]
                pH   = fields[7]
                Temp = fields[14]
    
            return pH, Temp, Data, Time, res
        
    def check_Auto_pH_Control_Possible(self):
        out = True
        if self.CSV_file_opened_successfully ==  False:
            print('.CSV file not opened')
            out = False
        if self.Comm_Port_opened_successfully == False:
            print('Comm Port closed')
            out = False
        
        if out == True:
            self.Control_Run.setEnabled(True)
            self.Control_Stop.setEnabled(False)
        if out == False:
            self.Control_Run.setEnabled(False)
            self.Control_Stop.setEnabled(False)        
        return out
            
    def click_Control_Run(self):
        self.Auto_Control = True
        print('Auto Control On')
        self.Control_Run.setEnabled(False)
        self.Control_Stop.setEnabled(True)     
        self.Control_State.setText('Control On')        
#        self.timer_pH_sender = 0

        today = datetime.now()
        today = str(today)
        today = today.replace("-", "_").replace(" ", "___").replace(":", "_")
        today = today.split('.')
        today = today[0]
        
        
        if self.Regulator_type == self.CompHyst:
            self.LOG_filename = 'CmpHyst_' + today + '.txt'
            self.File_LOG = open(self.LOG_filename, "w")
            self.File_LOG.write('   Data,      Time,   pH, Motor, pH_target \n')
            
        if self.Regulator_type == self.PID_reg:
            self.LOG_filename = 'PID_reg_' + today + '.txt'
            self.File_LOG = open(self.LOG_filename, "w")
            self.File_LOG.write('   Data,      Time,    pH,  Mtr, ErP, ErI, ErD, ErSum, Saw \n')
            
        print('Auto control started. Data logging to file: ' + self.LOG_filename)
        self.File_LOG.close()
                
    def fnc_Control_Stop(self):        
        self.Auto_Control = False
        self.Control_Run.setEnabled(True)
        self.Control_Stop.setEnabled(False)   
        self.Control_State.setText('Control Off')        
        self.Pump_Stop()        
        
    def click_Control_Stop(self):
        self.fnc_Control_Stop()
        print('Auto Control Off')    


    def compile_Regulator(self):
        if self.pH_pump_substance == self.Acid:
            if self.Regulator_type == self.CompHyst:
                self.Regulator_Description.setText('Regulator type: Comp+Hyst, control pH- (pump adds acid)')
            if self.Regulator_type == self.PID_reg:
                self.Regulator_Description.setText('Regulator type: PID-regulator, control pH- (pump adds acid)')
        if self.pH_pump_substance == self.Caustic:
            if self.Regulator_type == self.CompHyst:
                self.Regulator_Description.setText('Regulator type: Comp+Hyst, control pH- (pump adds alkali)')
            if self.Regulator_type == self.PID_reg:
                self.Regulator_Description.setText('Regulator type: PID-regulator, control pH- (pump adds alkali)')



    def click_pH_plus(self):
        self.pH_pump_substance = self.Caustic
        self.pH_plus.setEnabled(False)
        self.pH_minus.setEnabled(True)
        self.compile_Regulator()
    def click_pH_minus(self):
        self.pH_pump_substance = self.Acid
        self.pH_plus.setEnabled(True)
        self.pH_minus.setEnabled(False)
        self.compile_Regulator()
    def click_Comp_Hyst(self):
        self.Regulator_type = self.CompHyst
        self.PID_Reg_btn.setEnabled(True)
        self.Comp_Hyst.setEnabled(False)
        self.compile_Regulator()
    def click_PID_Reg(self):
        self.Regulator_type = self.PID_reg
        self.PID_Reg_btn.setEnabled(False)
        self.Comp_Hyst.setEnabled(True)           
        self.compile_Regulator()
        
    def run_Comp_Hist_Controller(self):
        self.pH_targ_txt = float( self.CompHyst_pH_Targ.text() )
        self.pH_Hyst_txt = float( self.CompHyst_pH_Hyst.text() )
        
        if self.pH_sender_is_active == True:
            if self.pH_pump_substance == self.Caustic:
                if self.pH_measured > self.pH_targ_txt + self.pH_Hyst_txt:
                    self.Pump_Stop() 
                    print('+++')                    
                if self.pH_measured < self.pH_targ_txt - self.pH_Hyst_txt:                  
                    self.Pump_Start()  
                    print('---')                    
            if self.pH_pump_substance == self.Acid:
                if self.pH_measured > self.pH_targ_txt + self.pH_Hyst_txt:
                    self.Pump_Start()  
                if self.pH_measured < self.pH_targ_txt - self.pH_Hyst_txt:                  
                    self.Pump_Stop()                   
#        print(self.pH_measured)


        today = datetime.now()
        today = str(today)
        today = today.replace("-", "_").replace(" ", "___").replace(":", "_")
        today = today.split('.')
        today = today[0]
        self.File_LOG = open(self.LOG_filename, "a")
        self.File_LOG.write(today + ' ' + str( round(self.pH_measured, 3) ) + ', ' + str( int(self.Motor_Active) ) + ', ' + str( int(self.pH_targ_txt) ) + '\n')
        self.File_LOG.close()

        self.grph_k += 1
        if self.grph_k < self.N_grph:
            pH_disp = self.pH_history[0: self.grph_k]
            Motor_disp = self.Motor_history[0: self.grph_k]
            time_disp = np.arange(0, self.grph_k)
            
            time_disp_f = np.zeros(self.grph_k, dtype=float)            
            for k_t in range(0, len(Motor_disp)):
                time_disp_f[k_t] = float(time_disp[k_t]) * self.dt
        else:
            pH_disp = self.pH_history[self.grph_k - self.N_grph: self.grph_k]
            Motor_disp = self.Motor_history[self.grph_k - self.N_grph: self.grph_k]
            time_disp = np.arange(self.grph_k - self.N_grph, self.grph_k)
            
            time_disp_f = np.zeros(self.N_grph, dtype=float)            
            for k_t in range(0, len(Motor_disp)):
                time_disp_f[k_t] = float(time_disp[k_t]) * self.dt

#        print(time_disp_f)
        self.ax.clear()
        self.ax.plot(time_disp_f, pH_disp, '-', label = 'pH')
        self.ax.plot(time_disp_f, Motor_disp, '-', label = 'motor')
        
        pH_up = self.pH_targ_txt + self.pH_Hyst_txt
        pH_dn = self.pH_targ_txt - self.pH_Hyst_txt
        self.ax.plot([  time_disp_f[0], time_disp_f[len(Motor_disp) - 1]  ], [pH_up, pH_up], ':')
        self.ax.plot([  time_disp_f[0], time_disp_f[len(Motor_disp) - 1]  ], [pH_dn, pH_dn], ':')
        
        if self.grph_k < self.N_grph:
            plt.axis([0, float(self.N_grph) * self.dt, 0, 14])
        else:
            plt.axis([time_disp_f[0], time_disp_f[len(Motor_disp) - 1], 0, 14])
        
#        self.plotting.legend()
        self.plotting.draw()
        
#==================================================================================================================                
# PID-Regulator PID-Regulator PID-Regulator PID-Regulator PID-Regulator PID-Regulator PID-Regulator PID-Regulator 
#==================================================================================================================                
    def run_PID_Reg_Controller(self):
        self.PID_K_P_txt   = ( self.PID_Reg_eP.text()      )
        self.PID_K_I_txt   = ( self.PID_Reg_eI.text()      )
        self.PID_Reg_Tsaw_txt = ( self.PID_Reg_Tsaw.text() )
        self.PID_K_D_txt   = ( self.PID_Reg_eD.text()      )
        
        self.Saw_t = self.Saw_t + self.d_Saw
        if self.Saw_t > 1.0:
            self.Saw_t = 0.0
            if self.PID_Err > 0.05:
                if self.pH_pump_substance == self.Caustic:
                    self.Pump_Stop()
                else:
                    self.Pump_Start()
            
        if self.pH_sender_is_active == True:
            self.PID_Err_tm1 = self.pH_Err 
            self.pH_Err = self.pH_measured - self.pH_targ_txt
            self.Err_P = self.pH_Err
            self.Err_I = self.Err_I + self.Err_P
            self.Err_D = self.pH_Err - self.pH_Err_tm1 
            self.PID_Err = float(self.PID_K_P_txt) * float(self.Err_P)
            self.PID_Err = self.PID_Err + float(self.PID_K_I_txt) * float(self.Err_I) 
            self.PID_Err = self.PID_Err + float(self.PID_K_D_txt) * float(self.Err_D)
        
            if self.Err_P > 14.0:
                self.Err_P = 14.0
#            elif self.Err_P < 0.0:
#                self.Err_P = 0.0
            if self.Err_I > 14.0:
                self.Err_I = 14.0
            elif self.Err_I < 0.0:
                self.Err_I = 0.0
            if self.Err_D > 14.0:
                self.Err_D = 14.0
#            elif self.Err_D < 0.0:
#                self.Err_D = 0.0
            if self.PID_Err > 14.0:
                self.PID_Err = 14.0
            elif self.PID_Err < 0.0:
                self.PID_Err = 0.0
            
        today = datetime.now()
        today = str(today)
        today = today.replace("-", "_").replace(" ", "___").replace(":", "_")
        today = today.split('.')
        today = today[0]
        self.File_LOG = open(self.LOG_filename, "a")
        self.File_LOG.write(today + ' ' + str( round(self.pH_measured, 3) ) + ', ' + str( int(self.Motor_Active) ) + ', ' + str( round(self.Err_P, 2) ) + ', ' + str( round(self.Err_I, 2) ) + ', ' + str( round(self.Err_D, 2) ) + ', ' + str( round(self.PID_Err, 2) ) + ', ' + str( round(self.Saw_t, 2) ) + '\n')
        self.File_LOG.close()
        
        
        self.Saw_history[self.grph_k] = self.Saw_t
        self.Err_P_history[self.grph_k] = self.Err_P
        self.Err_I_history[self.grph_k] = self.Err_I
        self.Err_D_history[self.grph_k] = self.Err_D
        self.Err_S_history[self.grph_k] = self.PID_Err
        
        if self.PID_Err < self.Saw_t:
            if self.pH_pump_substance == self.Caustic:
                self.Pump_Start()
            else:
                self.Pump_Stop()
#        else:
#            if self.pH_pump_substance == self.Caustic:
#                self.Pump_Start()
#            else:
#                self.Pump_Stop()
                
 
        self.grph_k += 1
        if self.grph_k < self.N_grph:
            pH_disp = self.pH_history[0: self.grph_k]
            Motor_disp = self.Motor_history[0: self.grph_k]
            
            Saw_disp   = self.Saw_history[0: self.grph_k]
            Err_P_disp = self.Err_P_history[0: self.grph_k]
            Err_I_disp = self.Err_I_history[0: self.grph_k]
            Err_D_disp = self.Err_D_history[0: self.grph_k]
            Err_S_disp = self.Err_S_history[0: self.grph_k]
            
            time_disp = np.arange(0, self.grph_k)
            time_disp_f = np.zeros(self.grph_k, dtype=float)            
            for k_t in range(0, len(Motor_disp)):
                time_disp_f[k_t] = float(time_disp[k_t]) * self.dt
        else:
            pH_disp    = self.pH_history[self.grph_k - self.N_grph: self.grph_k]
            Motor_disp = self.Motor_history[self.grph_k - self.N_grph: self.grph_k]
            
            Saw_disp   = self.Saw_history[self.grph_k - self.N_grph: self.grph_k]
            Err_P_disp = self.Err_P_history[self.grph_k - self.N_grph: self.grph_k]
            Err_I_disp = self.Err_I_history[self.grph_k - self.N_grph: self.grph_k]
            Err_D_disp = self.Err_D_history[self.grph_k - self.N_grph: self.grph_k]
            Err_S_disp = self.Err_S_history[self.grph_k - self.N_grph: self.grph_k]
            
            
            time_disp = np.arange(self.grph_k - self.N_grph, self.grph_k)          
            time_disp_f = np.zeros(self.N_grph, dtype=float)            
            for k_t in range(0, len(Motor_disp)):
                time_disp_f[k_t] = float(time_disp[k_t]) * self.dt

        self.ax.clear()
        self.ax.plot(time_disp_f, pH_disp, '-', label = 'pH')
        self.ax.plot(time_disp_f, Motor_disp, '-', label = 'motor')

        self.ax.plot(time_disp_f, Saw_disp  , '-', label = 'saw')
        self.ax.plot(time_disp_f, Err_P_disp, '-', label = 'Err_P')
        self.ax.plot(time_disp_f, Err_I_disp, '-', label = 'Err_I')
        self.ax.plot(time_disp_f, Err_D_disp, '-', label = 'Err_D')
        self.ax.plot(time_disp_f, Err_S_disp, '-', label = 'Err SUM')

        self.ax.legend()
        pH_marker = self.pH_targ_txt
        self.ax.plot([  time_disp_f[0], time_disp_f[len(Motor_disp) - 1]  ], [pH_marker, pH_marker], ':')
        
        if self.grph_k < self.N_grph:
            plt.axis([0, float(self.N_grph) * self.dt, 0, 14])
        else:
            plt.axis([time_disp_f[0], time_disp_f[len(Motor_disp) - 1], 0, 14])
        self.plotting.draw()

        self.PID_Err_P.setText('E_P: ' + str(self.Err_P))
        self.PID_Err_I.setText('E_I: ' + str(self.Err_I))
        self.PID_Err_D.setText('E_D: ' + str(self.Err_D))
        self.PID_Err_S.setText('E_S: ' + str(self.PID_Err))















 
                
                
# PID-Regulator PID-Regulator PID-Regulator PID-Regulator PID-Regulator PID-Regulator PID-Regulator PID-Regulator 
#==================================================================================================================                
                
    def run_Regulator(self):
        self.pH_history[self.grph_k] = self.pH_measured
        self.Motor_history[self.grph_k] = int(self.Motor_Active)
        if self.Auto_Control == True:
            if self.Regulator_type == self.CompHyst:
                self.run_Comp_Hist_Controller()
            if self.Regulator_type == self.PID_reg:
                self.run_PID_Reg_Controller()
            
    def Check_pH_measuring_transmitter_activity(self):
        if self.Time_measured_tm1 != self.Time_measured:
            self.Time_measured_tm1 = self.Time_measured
            self.timer_pH_sender = 0;
            self.pH_sender_is_active = True
            print('Data from pH sender received')
            self.Message_about_CSV_file.setText('pH sensor is ACTIVE')
            self.CSV_file_opened_successfully = True
            if self.Auto_Control == False:
                self.check_Auto_pH_Control_Possible()
            
            
    
        elif self.timer_pH_sender == self.Timer_pH_LIM:
            self.fnc_Control_Stop()              
            self.pH_sender_is_active = False
            self.Pump_Stop() 
            print('Auto Control Stopped, pH sensor is NOT ACTIVE')
            self.Message_about_CSV_file.setText('pH sensor is NOT ACTIVE')
            self.timer_pH_sender += 1
        elif self.timer_pH_sender < self.Timer_pH_LIM + 3:
            self.timer_pH_sender += 1
#            print('pH timer: ' + str(self.timer_pH_sender))
            
            
   

        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    

   
    
    ex = Example()
    sys.exit(app.exec_())

#https://www.pythonguis.com/tutorials/plotting-matplotlib/