import Adafruit_ADS1x15
import time
adc = Adafruit_ADS1x15.ADS1115()
GAIN = 1
###Testing new cardiac filter and Cardiac frequency algoritm###
t = open('time.txt','w')
ECG = open('Cardiac.txt','w')
sin = open('cardiac.txt','w')
FC = open('Frecuency.txt','w')
cc = open('Contador.txt','w')

#testeo de la funcion y algoritmo
n = 0  #contador de ciclos
p = 0  #contador de pulsos
lp = 0 # valor del ultimo valor de frecuencia cardiaca
lt = 0 #  valor del tiempo del ultimo pulso
lv = 13080 #valor de la senal anterior del ECG
FilterBuffer = [13080,13080,13080,13080,13080] #Buffer del filtro 
Vf = 13080  #suma rapida del filtro
t0 = time.time() #tiempo de inicio de sesion
s10 = t0
while n<20000:
    value = adc.read_adc(0, gain=GAIN,data_rate=860)
    print(value)
    t.write(str(time.time()-t0)+'\n')
    ECG.write(str(value)+'\n')
    FilterBuffer.append(value)
    Vf =  Vf - FilterBuffer.pop(0)/5 + value/5
    sin.write(str(Vf)+ '\n')
    if Vf>15000 and time.time()-lt>0.1 and Vf>lv:
        p+=1
        lt = time.time()
    lv=Vf
    cc.write(str(p)+'\n')
    if time.time()-m >10:
        m = time.time()
        FC.write(str(6*p)+ '\n')
        p = 0
    n+=1
t.close()
FC.close()
cc.close()
sin.close()
ECG.close()

def ECG():
    global p, lp, lt, B, FilterBuffer, Vf, t0, m #paciente = Alvaro
    
    value = adc.read_adc(0, gain=1,data_rate=860)
    FilterBuffer.append(value)
    Vf =  Vf - FilterBuffer.pop(0)/5 + value/5
    #append value to Cardiac Monitor list
    if Vf>15000 and time.time()-lt>0.1 and Vf>lv:
        p+=1
        lt = time.time()
    B=Vf
    if time.time()-m >10:
        m = time.time()
        #append value to cardiac frecuency list remeber multiply by 6
        p = 0