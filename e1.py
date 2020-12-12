#Termometro
from w1thermsensor import W1ThermSensor
#Oximetro
import max30102
import hrcalc
#ADC raspberry
import Adafruit_ADS1x15
#pupilometro
import RPi.GPIO as GPIO
from picamera import PiCamera
#sistema
import serial
import time
import sqlite3
import datetime
from threading import Thread
import pyaudio
import wave
import sys

#from tornado import gen
#import serial / bokeh apps
from bokeh.models import ColumnDataSource , PreText, Button, CheckboxGroup, PasswordInput, DataTable, DateFormatter, TableColumn, TextAreaInput
from bokeh.layouts import layout
from bokeh.plotting import curdoc, figure


class Paciente():
    def __init__(self,Name,fecha):
        self.Name = Name
        self.fecha = fecha
        #self.LA = 60000 
        #self.LB = 14400 
        self.time = 0  #actual time 
        self.HS = 13080 #Heart Signal last value
        self.HC = 75   #Last Day Record Buffer --> Used to save last day Cardiac Rate
        self.FR = 15   #Last Day Record Buffer --> Used to save last day Respiratory Rate
        self.OX = 100   #Last Day Record Buffer --> Used to save last day Saturation Level 
        self.TM = 36   #Last Day Record Buffer --> Used to save last day Temperatures
        self.PersonalComentary = str(self.Name) #Phisician can leave some messages for his colleagues
        self.Messages =str("")
        self.TAlarm = [datetime.datetime.now()]
        self.Alarm = ["First connection"]
        
#################################################################################################################################
################################### Main Program Using bokeh#######################################################
sistema = Paciente("Alvaro",datetime.datetime.now())
inicio = time.time()
conn = sqlite3.connect('pacient.db')
c = conn.cursor()
sensor = W1ThermSensor()
m = max30102.MAX30102()
adc = Adafruit_ADS1x15.ADS1115()
n = 0 #manipular el stream de la tabla de alarmas
doc = curdoc()
t0 = inicio
ser = serial.Serial("/dev/ttyS0", baudrate=115200,timeout=0.1)

#####Respiratorio####
inicio = time.time()
lis = []
fc = 0
for i in range(1,20):
    lis.append(0)
ltr = inicio
tr0 = ltr

################Bokeh application ######################
DataSource = ColumnDataSource(dict(time=[], HC= [], FR= [], OX = [], TM= []))#slower Sensors
DataSource2 = ColumnDataSource(dict(time=[],HS=[]))#quicker sensors
DataSource3 = ColumnDataSource(dict(i = [n], Hours=[datetime.datetime.now()],Events=["First connection"]))

#Monitor Cardiaco
Eplot= figure(title='Monitor Cardiaco',plot_width=1200 , plot_height =500 , tools="reset,xpan,xwheel_zoom,xbox_zoom",y_axis_location="left" )
Eplot.line(x='time', y='HS', alpha =0.8 , line_width=3, color='blue' , source=DataSource2 , legend_label='Signal' )
Eplot.xaxis.axis_label = 'Tiempo (S)'
Eplot.yaxis.axis_label = '16 bits ADC value'

# day plot 

Cplot = figure(title='Registro de Frecuencia Cardiaca',plot_width=600 , plot_height =250 , tools="reset,xpan,xwheel_zoom,xbox_zoom",y_axis_location="left" )
Cplot.line(x='time', y='HC', alpha =0.8 , line_width=3, color='blue' , source=DataSource , legend_label='Frecuencia Cardiaca' )
Cplot.xaxis.axis_label = 'Tiempo (S)'
Cplot.yaxis.axis_label = 'Frecuencia Cardiaca bpm'

Rplot = figure(title='Registro de Frecuencia Respiratoria',plot_width=600 , plot_height =250 , tools="reset,xpan,xwheel_zoom,xbox_zoom",y_axis_location="left" )
Rplot.line(x='time', y='FR', alpha =0.8 , line_width=3, color='blue' , source=DataSource , legend_label='Frecuencia Respiratoria' )
Rplot.xaxis.axis_label = 'Tiempo (S)'
Rplot.yaxis.axis_label = 'Frecuencia Respiratoria bpm'

Splot = figure(title='Registro de Saturacion de Oxigeno',plot_width=600 , plot_height =250 , tools="reset,xpan,xwheel_zoom,xbox_zoom",y_axis_location="left" )
Splot.line(x='time', y='OX', alpha =0.8 , line_width=3, color='blue' , source=DataSource , legend_label='Saturacion de Oxigeno' )
Splot.xaxis.axis_label = 'Tiempo (S)'
Splot.yaxis.axis_label = 'Porcentaje %'

Tplot = figure(title='Registro de Temperatura' , plot_width=600 , plot_height =250 , tools="reset,xpan,xwheel_zoom,xbox_zoom",y_axis_location="left" )
Tplot.line(x='time', y='TM', alpha =0.8 , line_width=3, color='blue' , source=DataSource , legend_label='Temperatura' )
Tplot.xaxis.axis_label = 'Tiempo (S)'
Tplot.yaxis.axis_label = 'Temperatura en Celsius'
#Actual value sensed#
estilo= {'color' : 'white' , 'font' : '18px bold arial, sans-serif' , 'background-color' : 'blue' , 'text-align' : 'center' , 'border-radius' : '17px' }
SinText = PreText(text='Frecuencia Cardiaca : 0.00' , width=360 , style=estilo)
FRText = PreText(text='Frecuencia Respiratoria: 0.00', width=360, style = estilo)
OxText = PreText(text= 'Saturación de Oxígeno: 0.00',width=360,style = estilo)
TMPText = PreText(text='Temperatura °C: 0.00',width=360,style = estilo)

#Otros widgets
Hi = PreText(text ="Hora de inicio de sesión:    "+ str(datetime.datetime.now()),width = 300)
MedicText = TextAreaInput(value="Acá puede dejar sus notas",rows=30,title="Notas Medicas")
InstrText = TextAreaInput(value="Desea enviar algún mensaje al paciente",rows=30,title= "Instrucciones")
dbtn = Button(label="Download as csv",button_type="success")
def callback():
    global conn, c
    file = open('Pacient_Data.csv','w')
    data = c.execute("SELECT * FROM data")
    row = c.fetchall()
    for row in data:
        file.write(str(row)+"\n")
    file.close()
    
dbtn.on_click(callback)
formatter = DateFormatter()
formatter.format = "%R"
columnas = [
    TableColumn(field='i',title='index'),
    TableColumn(field="Hours",title="Hora del Evento",formatter = formatter),
    TableColumn(field="Events",title="Evento")] 
Tabla = DataTable(source= DataSource3,columns=columnas,width=480,height=320)#cambiarlo al otro diccionario
#Funciones externas que deben ser corridas
def Pupil():
    camera = PiCamera()
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(18, GPIO.OUT, initial=GPIO.LOW)
    try:
        camera.start_preview()
        camera.start_recording('pupil.h264')
        camera.wait_recording(2)
        GPIO.output(18,GPIO.HIGH)
        camera.wait_recording(5)
        camera.stop_recording()
        camera.stop_preview()
        GPIO.output(18,GPIO.LOW)
    finally:
        camera.close()
def record(): 
    CHUNK = 512
    FORMAT = pyaudio.paInt16#paInt8
    CHANNELS = 1
    RATE = 44100
    RECORD_SECONDS = 10
    WAVE_OUTPUT_FILENAME = "output.wav"
    if sys.platform == 'darwin':
        CHANNELS = 1
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    print("* recording")
    frames = []
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
    print("* done recording")
    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    
def Quick_sensors():
    global sistema, inicio,lis,fc,ltr,tr0,conn,c,n
    sistema.time = time.time()-inicio
    try:
        sistema.HS = adc.read_adc(0, gain=1,data_rate=860)
        rsin = adc.read_adc(1,gain=1,data_rate=860)
    except:
        rsin = 0
    if rsin>4300:
        peak = 1
    else:
        peak = 0
    lis.pop(0)
    lis.append(peak)
    if time.time()-ltr>1.5:
        cor = sum(lis)
        if cor>15:
            fc+=1
            ltr = time.time()
    if time.time()-tr0>59.9:
        tr0 =time.time()
        sistema.FR = fc
        fc = 0
        new = dict(time =[sistema.time],HC= [sistema.HC], FR= [sistema.FR], OX = [sistema.OX], TM= [sistema.TM])
        DataSource.stream(new_data=new)
        SinText.text = 'Frecuencia Cardiaca :{} bpm'.format(str(sistema.HC))
        FRText.text = 'Frecuencia Respiratoria: {} bpm'.format(str(sistema.FR))
        OxText.text = 'Saturación de Oxígeno: {} %'.format(str(sistema.OX))
        TMPText.text = 'Temperatura:{}°C'.format(str(sistema.TM))
        while len(sistema.Alarm)>n+1:
            n+=1
            data = dict(i=[n],Hours = [sistema.TAlarm[n]],Events=[sistema.Alarm[n]])
            DataSource3.stream(data,20)
    c.execute("INSERT INTO data VALUES (?,?,?,?,?,?)",(sistema.time,sistema.HS,sistema.HC,sistema.FR,sistema.OX, sistema.TM))
    update = dict(time=[sistema.time], HS=[sistema.HS])
    DataSource2.stream(new_data=update, rollover=150) # Se ven los ultimos 5

def Slower_sensors():
    global sistema,m,sensor, inicio,t0,ser
    while True:
        #time.sleep(59.99)
        while time.time()-t0< 59.99:
            try:
                ins = str(ser.read_until())
                if ins[2] =='1':
                    sistema.TAlarm.append(datetime.datetime.now())
                    sistema.Alarm.append('Bathroom')
                elif ins[2] == '2':
                    sistema.TAlarm.append(datetime.datetime.now())
                    sistema.Alarm.append('Consumo de Farmacos')
                elif ins[2] == '3':
                    sistema.TAlarm.append(datetime.datetime.now())
                    sistema.Alarm.append('Alimentos')
                elif ins[2] == '4':
                    sistema.TAlarm.append(datetime.datetime.now())
                    sistema.Alarm.append('Nueva grabacion en camino')
                    #grabar de alguna manera no se cual
                elif ins[2] == '5':
                    sistema.TAlarm.append(datetime.datetime.now())
                    sistema.Alarm.append('Nueva prueba de Pupilometro realizada')
                    #Escribir y correr prueba del pupilometro a pesar de lo que sea
                    Pupil()
            except:
                pass
        last = sistema.HC
        sistema.time = time.time()-inicio
        print(sistema.time)
        best1 = [70] ###se setea el 70% como minimo
        best2 = [60]
        for i in range(1,10):
            try:
                red, ir = m.read_sequential()
                hr, hrv, O, Ov = hrcalc.calc_hr_and_spo2(ir, red)
            except:
                pass
            if Ov == True and hrv == True and O>70 and hr>60:
                best1.append(O)
                best2.append(hr)
        O = max(best1)
        i=0
        for e in best1:
            if e == O:
                hr = best2[i]
            i+=1
        if hr!=60 and O!=70:
            sistema.OX = O
            sistema.HC = hr
    #Alarmas Saturometria
        if sistema.OX < 80:
            sistema.TAlarm.append(datetime.datetime.now())
            sistema.Alarm.append("Danger <80% Oxygen level")
        elif sistema.OX <90:
            sistema.TAlarm.append(datetime.datetime.now())
            sistema.Alarm.append("Caution <90% Oxygen level")
    #Alarmas Cardiacas
        if sistema.HC> last + 10:
            sistema.TAlarm.append(datetime.datetime.now())
            sistema.Alarm.append("Incremento brusco de frecuencia cardiaca")
        elif sistema.HC+10<last:
            sistema.TAlarm.append(datetime.datetime.now())
            sistema.Alarm.append("Caida brusca de frecuencia cardiaca")
    #obtener Temperatura
        try:
            sistema.TM = sensor.get_temperature() + 1
        except:
            pass
        if sistema.TM< 35:
            sistema.TAlarm.append(datetime.datetime.now())
            sistema.Alarm.append('Hipotermia')
        elif sistema.TM > 37.5:
            sistema.TAlarm.append(datetime.datetime.now())
            sistema.Alarm.append('Fiebre')
        t0 = time.time()
l = layout ([
        [Eplot],
        [SinText,TMPText],
        [FRText,OxText],
        [Cplot,Rplot],
        [Splot,Tplot],
        [dbtn],
        [MedicText,InstrText,Tabla]
        ])

doc.add_root(l)
doc.title = "Monitor Remoto"
doc.add_periodic_callback(Quick_sensors,1)
thread = Thread(target=Slower_sensors)
thread.start()   
