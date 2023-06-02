from time import ticks_ms, sleep_ms, ticks_diff
start = ticks_ms()

import network
import usocket as socket
from machine import SDCard, I2C, Pin, RTC, deepsleep, ADC, reset_cause, SOFT_RESET
import os
import datalog_lib as dlog
import ds3231
import sht75
#from netinfo import *
import bmp180
from time import sleep_ms

rtc = RTC()
date = rtc.datetime()
minute = date[5]
second = date[6]

print('minute: ', minute)
print('second: ', second)

#para deep_sleep
#if (second<45):
#    print('sleep ', 45-second)
#    deepsleep((45-second)*1000)
#sleep_ms(1000)
#reset = reset_cause()
#print('reset: ', reset)
#
#if (reset == SOFT_RESET):
#    print('soft reset' + '*'*10)
#    sleep_ms(5000)
    
#Non-volatile Storage
#from esp32 import NVS
#nvs = NVS("ref")
#try:
#    count = nvs.get_i32('count')
#except:
#    count = 0

#count += 1
#print('count:', count)
#nvs.set_i32('count', count)

#nvs.commit()



#tiempo de medición
time_delta = 60000

sht_dat = Pin(26, Pin.OUT, Pin.PULL_UP)
sht_clk = Pin(27, Pin.OUT, Pin.PULL_UP)
# punto de acceso
#ap= network.WLAN(network.AP_IF)
#ap.active(True)
#ap.config(essid='esp32', password='testesp32' )
#print(ap.ifconfig())

i2c = I2C(0, scl =Pin(22, Pin.OPEN_DRAIN), sda = Pin(21, Pin.OPEN_DRAIN) )
i2c_dev = i2c.scan()
print('i2c:', i2c_dev)
#canales analógicos
adc_wd = ADC(Pin(33))
adc_wd.atten(ADC.ATTN_11DB)
adc_uv= ADC(Pin(34))
adc_uv.atten(ADC.ATTN_11DB)
adc_sun = ADC(Pin(35))
adc_sun.atten(ADC.ATTN_11DB)
adc_v = ADC(Pin(13, Pin.IN))
adc_v.atten(ADC.ATTN_11DB)
R1 = 2000
R2 = 1000
kbat =(R1+R2)/R2
kbat *= (2.45-.15)/65535
print('kbat:', kbat)

while (True):
    #sólo para sleep_ms
    start = ticks_ms()
    date = rtc.datetime()
    minute = date[5]
    second = date[6]
    if (second<45):
        print('sleep ', 45-second)
        sleep_ms((45-second)*1000)

    vbat = adc_v.read_u16()*kbat
    sht75.get_T(sht_dat, sht_clk)
    Tp, p =bmp180.pressure(i2c)
    t = sht75.lee_2bytes( sht_dat, sht_clk )
    print('t:', t)
    sht75.get_RH(sht_dat, sht_clk)
    wd = adc_wd.read()
    uv = adc_uv.read()
    sun = adc_sun.read()
    rh = sht75.lee_2bytes( sht_dat, sht_clk )
    T, RH = sht75.convert_trh( t, rh)

    print(date)
    var_txt = ''
    var_txt += '{:02}/{:02}/{:02} {:02}:{:02}:{:02},'.format(date[0], date[1], date[2], date[4], date[5], date[6])
    var_txt += '{:.2f},{:.1f},{:.2f},{:.2f},{:d},{:d},{:d},{:.2f}'.format(T, RH, p/100, Tp/10, wd, uv, sun, vbat)
    print(var_txt)
    with open('data.csv', 'a') as fp:
        print(var_txt, file=fp)

    time_proc = ticks_diff(ticks_ms(), start)
    print('delta:', time_proc)
    sleep_ms(time_delta - time_proc - 1000)


deepsleep(time_delta - time_proc - 1000)

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

sd = SDCard( slot =2, freq =1000000)
os.mount(sd, '/sd')
    
print('SD files:')
print(os.listdir('/sd'))
os.umount('/sd')
print('desmontado')
