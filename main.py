from time import ticks_ms, sleep_ms, ticks_diff
start = ticks_ms()

import network
import usocket as socket
from machine import SDCard, I2C, Pin, RTC, deepsleep, ADC, reset_cause, SOFT_RESET
import os, sys
import datalog_lib as dlog
import ds3231
import sht75
#from netinfo import *
import bmp180
from time import sleep_ms, sleep

test  = Pin(16, Pin.IN,  Pin.PULL_UP)
if test.value() == 0:


    print('saliendo')
    sys.exit()

rtc = RTC()
date = rtc.datetime()
minute = date[5]
second = date[6]

print('minute: ', minute)
print('second: ', second)

time_wind = 15
if (second< 60-time_wind):
    print('sleep ', 60-time_wind-second)
    deepsleep((60- time_wind -second)*1000)
reset = reset_cause()
print('reset: ', reset)

from netinfo import *
wlan = network.WLAN(network.STA_IF)
wlan.active( True )
wlan.connect(ssid ,password)
print("Conectando a", ssid, end =' ')

#tiempo de medición
time_delta = 60000

sht_dat = Pin(26, Pin.OUT, Pin.PULL_UP)
sht_clk = Pin(27, Pin.OUT, Pin.PULL_UP)

i2c = I2C(0, scl =Pin(22, Pin.OPEN_DRAIN), sda = Pin(21, Pin.OPEN_DRAIN) )

#canales analógicos
adc_wd = ADC(Pin(33))
adc_wd.atten(ADC.ATTN_11DB)
adc_uv= ADC(Pin(34))
adc_uv.atten(ADC.ATTN_11DB)
adc_sun = ADC(Pin(35))
adc_sun.atten(ADC.ATTN_11DB)
adc_v = ADC(Pin(32))
adc_v.atten(ADC.ATTN_11DB)

R1 = 2000
R2 = 2000
#kbat =(R1+R2)/R2
#kbat *= (2.45-.15)/65535
kbat = 1

vbat = adc_v.read_u16()*kbat
sht75.get_T(sht_dat, sht_clk)
Tp, p =bmp180.pressure(i2c)
t = sht75.lee_2bytes( sht_dat, sht_clk )
sht75.get_RH(sht_dat, sht_clk)
wd = adc_wd.read()
uv = adc_uv.read()
sun = adc_sun.read()
rh = sht75.lee_2bytes( sht_dat, sht_clk )
T, RH = sht75.convert_trh( t, rh)

var_txt = ''
var_txt += '{:02}/{:02}/{:02} {:02}:{:02}:{:02},'.format(date[0], date[1], date[2], date[4], date[5], date[6])
var_txt += '{:.2f},{:.1f},{:.2f},{:.2f},{:d},{:d},{:d},{:.2f}'.format(T, RH, p/100, Tp/10, wd, uv, sun, vbat)
print(var_txt)

try:
    sd = SDCard( slot =2, freq =1000000)
    os.mount(sd, '/sd')
            
    with open('/sd/data.csv', 'a') as fp:
        print(var_txt, file=fp)
        print('datos guardados')
        #print('SD files:')
        #print(os.listdir('/sd'))
        os.umount('/sd')
        print('desmontado')
except:
    print('Error al guardad en SD!')
    with open('data.csv', 'a') as fp:
        print(var_txt, file=fp)


n= 0
while not wlan.isconnected():
    print('*', end= '')
    sleep(1)
    n+= 1
    if n>7:
        break

if n>7:
    print('no hay conexión')
else:
    print('conectado!')

time_proc = ticks_diff(ticks_ms(), start)
time_sleep = time_delta - time_proc -1000
print('delta:', time_proc, time_sleep)
wlan.active(False)
deepsleep( time_sleep)



#sys.exit (0)

wlan= dlog.wlan_connect( ssid, password )
if wlan.isconnected() == True:
    print('IP:', wlan.ifconfig()[0])

    i2c = I2C(0, scl =Pin(22, Pin.OPEN_DRAIN), sda = Pin(21, Pin.OPEN_DRAIN) )
    print("I2C encontradas:", i2c.scan())

    rtc = RTC()
    if dlog.get_date_NTP(['1.mx.pool.ntp.org', 'cronos.cenam.mx']):
        #(year, month, day, weekday, hours, minutes, seconds, subseconds)
        print('hora NTP:', rtc.datetime())
        print('hora ds:', ds3231.get_time(i2c))
        ds3231.set_time(i2c)
        print('hora ds actualizada:', ds3231.get_time(i2c))
    else:
        print('No NTP')
        print('hora:', rtc.datetime())
        YY, MM, DD,wday, hh, mm, ss, _ = ds3231.get_time(i2c)
        rtc.datetime( (YY, MM, DD, wday, hh, mm, ss, 0))
        print('DS:', rtc.datetime())
else:
    print('No se pudo conectar!')
wlan.active(False)
