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
        
        
        self.Create_Elements()
        self.Place_Elements()

        self.qlabel = QLabel(self)
        self.qlabel.move(50,16)
   

        self.setGeometry(50,50,350,300)
        self.setWindowTitle("pH sender")
        self.show()

    def Create_Elements(self):
    
        self.pH = 7.00
        self.Period = 10.00
        
        self.d_pH_dt_motor_ON = 0.01
        self.d_pH_dt_motor_OFF = -0.01
        
        self.dt = 1.0
        
        self.N_cnt = self.Period / self.dt
        
        self.Active = False
        self.Initial = False
    
        self.Set1        = QPushButton('Set', self)
        self.Set2        = QPushButton('Set', self)
        self.Start_Stop      = QPushButton('Start', self)
        
        # Parameters for Reactor     
        self.pH_set_Qline   = QLineEdit(str(self.pH), self)
        self.Period_set_Qline   = QLineEdit(str(self.Period), self)
        self.d_pH_dt_motor_ON_Qline    = QLineEdit(str(self.d_pH_dt_motor_ON), self)
        self.d_pH_dt_motor_OFF_Qline   = QLineEdit(str(self.d_pH_dt_motor_OFF), self)
        
        self.Set_pH_lbl   = QLabel('Set pH', self)
        self.Set_pH_lbl.setFont(QFont('Arial', 8))
        
        self.Set_Period_lbl   = QLabel('Set period', self)
        self.Set_Period_lbl.setFont(QFont('Arial', 8))
        
        self.Reactor_lbl   = QLabel('d pH / dt [sec] ', self)
        self.Reactor_lbl.setFont(QFont('Arial', 10))
        self.d_pH_Motor_On__lbl   = QLabel('when motor On', self)
        self.d_pH_Motor_On__lbl.setFont(QFont('Arial', 8))
        self.d_pH_Motor_Off_lbl   = QLabel('when motor Off', self)
        self.d_pH_Motor_Off_lbl.setFont(QFont('Arial', 8))
        
        self.pH_view   = QLabel('pH = ' + str(self.pH), self)
        self.pH_view.setFont(QFont('Arial', 20))
        
        self.Motor_view   = QLabel('Motor unknown', self)
        self.Motor_view.setFont(QFont('Arial', 12))
        
        self.Set1.clicked.connect(self.click_Set1)
        self.Set2.clicked.connect(self.click_Set2)
        self.Start_Stop.clicked.connect(self.click_Start_Stop)
        
        
        # Reactor processing variables
        
        self.Timer = 0.0

        self.FileName = 'pH_meter_imitation.csv'

    def Place_Elements(self):
        self.pH_view.setGeometry(30, 30, 150, 30)
        self.Motor_view.setGeometry(220, 33, 130, 30)
        
        self.Set_pH_lbl.move(70, 170)
        self.Set_Period_lbl.move(170, 170)   
        
        self.pH_set_Qline.setGeometry(70, 190, 50, 20)
        self.Period_set_Qline.setGeometry(180, 190, 50, 20)     
        
        
        self.Reactor_lbl.move( 150, 90)   
        self.d_pH_Motor_On__lbl.move(70, 110)   
        self.d_pH_Motor_Off_lbl.move(170, 110)   
        self.d_pH_dt_motor_ON_Qline.setGeometry(70, 130, 50, 20)
        self.d_pH_dt_motor_OFF_Qline.setGeometry(180, 130, 50, 20)     
        
        self.Set1.move(250, 130)
        self.Set2.move(250, 190)
        self.Start_Stop.move(220, 250)
        
        
    def click_Set2(self):
        self.pH = float(self.pH_set_Qline.text())
        self.Period = float(self.Period_set_Qline.text())
        
    def click_Set1(self):
        self.d_pH_dt_motor_ON = float(self.d_pH_dt_motor_ON_Qline.text())
        self.d_pH_dt_motor_OFF = float(self.d_pH_dt_motor_OFF_Qline.text())
        self.N_cnt = float(self.Period) / self.dt
        
    def pH_sender_imitator(self):
        if self.Active == True:
            self.Timer += self.dt
            if self.Timer >= float(self.Period):
                self.Timer = 0.0
                self.Measurement_imitation()
                
        with open('Motor_Imitation.txt') as f:
            Motor_condition = int(f.read())
            
        if Motor_condition == 1:
            self.pH += float(self.d_pH_dt_motor_ON)
            self.Motor_view.setText('Motor ON')
            print('Motor On')
        if Motor_condition == 0:
            self.pH += float(self.d_pH_dt_motor_OFF)  
            self.Motor_view.setText('Motor OFF')     
            print('Motor Off')            
        self.pH_view.setText("pH = %.3f"%(self.pH))          
                
        if self.pH > 14.0:
            self.pH = 14.0
        if self.pH < 0.0:
            self.pH = 0.0
            
    def Measurement_imitation(self):
    
        today = datetime.now()
        today = str(today)
#        today = today.replace("-", "_").replace(" ", "___").replace(":", "_")
        today = today.replace(" ", ",?? ")
        today = today.split('.')
        today = today[0]
        today = today + ',  ' + "%.3f"%(self.pH)
        today = today + ',   pH,  21.32, DegC, ******,   pH, ******, DegC,'
        print(today)
        OutFile = open(self.FileName, 'a')
        print(today, file = OutFile)
        OutFile.close()        
        
  
            
    def click_Start_Stop(self):      
        if self.Active == False:
            self.Active = True
            self.Start_Stop.setText('Stop')
            print('Process started')
        else:
            self.Active = False
            self.Start_Stop.setText('Start')
            print('Process stopped')
    
        if self.Initial == False:
            print('Thread Start')
            
            OutFile = open(self.FileName, 'w')
            print('METTLER TOLEDO M300/M300ISM', file = OutFile)
            print('M300 Data Collection', file = OutFile)
            print('Date, Time, a Value, a Units,b Value, bUnits, c Value, c Units,d Value, d Units \n', file = OutFile)
            OutFile.close()
            
            self.Initial = True
            @setInterval(self.dt)
            def funct():
                self.pH_sender_imitator()
            stop = funct()

            




        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    ex = Example()
    sys.exit(app.exec_())

#https://www.pythonguis.com/tutorials/plotting-matplotlib/