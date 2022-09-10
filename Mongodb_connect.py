from pymodbus.client.sync import ModbusSerialClient as ModbusClient
# from pymodbus.register_read_message import ReadInputRegisterResponse
import pymodbus#.register_read_message import ReadInputRegisterResponse
#DB -----------
import time
import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId
from pymongo.errors import ConnectionFailure
import json

from datetime import datetime
import datetime

#-------
client = ModbusClient(method = 'rtu', port = 'COM3', stopbits=1 , bytesize=8, parity='N', baudrate=9600, timeout = 1)

connection = client.connect()
# print (connection)
# value = client.read_input_registers(2, count=10, unit = 0x02)
#for i in range(999):
# a = len(client.read_holding_registers(0x2, count=10, unit = 2))
# a2= client.read_coils(0,10,unit=2)
# print (x)
# print (y*100)
# time.sleep(1)

MONGO_IP='localhost'
MongoPort=27017
MONGO_DB='delta' #資料庫
MongoUser="root"#帳號
MongoPassword="pc152"#密碼
db=[{'host':MONGO_IP,'port':MongoPort,'db':MONGO_DB,'user':MongoUser,'pass':MongoPassword}]
Successful_connection=True
#endregion 
#連線資料庫 6
try:  
    # Successful_connection=Compulsory_connect_mongodb(MONGO_IP,MongoPort,MongoUser,MongoPassword)#mongodb連線測試
    if Successful_connection==True:
        conn_local=MongoClient(db[0]['host'],db[0]['port'],serverSelectionTimeoutMS=1)
        conn_local.admin.authenticate(db[0]['user'],db[0]['pass'])
        mongodbObj = conn_local[db[0]['db']]
        print ('mongo 連線正常 ')
except Exception as e:
    Successful_connection=False
    print(e)

def mongo_find (mongoDB,collection,DBfilter,limitt): #輸入指定的資料庫 資料集 指定條件 數量 ，回傳符合這些條件的 list，最新的放在前面 (按照時間降序排列)
    try:
        collect=mongoDB[collection]
        data_upload=list(collect.find(DBfilter, {'_id':0 }).sort('time', pymongo.DESCENDING).limit(limitt)) #state 0.本地有 伺服器未確認 1.本地有 伺服器有 2.本地有 伺服器上傳失敗
        print('data_upload',data_upload)
        print('grekojgok')
        return data_upload
    except Exception as e:
        # print_function('unknow error',select,'mongo_find',e,1) 
        print('Exception',e)
        return [] #如果找不到資料會回傳空集合

Year =2021
Month =7
Day =8
Hour =15
Minute = 43
collection_PCS='command_pcs'
pcs_ID ="pcs_set_q"

# pcs_filter={"ID":pcs_ID,'time':{'$gte':datetime.datetime(Year, Month, Day, Hour, Minute)}

# data1 = mongodbObj.command_pcs.find().sort("time",1)
data1 = mongo_find(mongodbObj,collection=collection_PCS ,DBfilter= {},limitt= 10)
while True: 
    value = client.read_holding_registers(0, count=10, unit = 2)
    x = value.registers[1]
    x = x/100

    if (x<=59.75):
        y = -2.08*x+124.76

    elif (59.75<x<=59.98):
        y=(-0.48/0.23)*x+125.17565217391

    elif (59.98<x<=60.02):
        y=0

    elif (60.02<x<=60.25):
        y=(-0.48/0.23)*x+125.25913043478

    else:
        y= -2.08*x+124.84

    # my_date = datetime.now()
    my_date = datetime.datetime.now()
    y=y*100
    mongodbObj.pre_data.insert_one({"time": my_date,"frequency":x, "power":y,"ID":"meter"})
    print('',my_date)
    time.sleep(.941478)
    

print('data1 ',data1 )

print(type(data1))

print('',data1[0])
# for i in range(len(data1)):
#     print('i',i)
# for i in range(10):
#     print(value.registers[i])



# for x in range(10):
#     print (a[x])
#     print (a.registers)

# xxx =[]
# xxx.append(a)
# print('xxx  ',xxx)
# for i in range(len(a)):
#     print('ytry',xxx[i])
# a =5
# aa=[1,2,3,4]
# print(aa)


