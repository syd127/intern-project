import pymongo
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from bson.objectid import ObjectId
import os
import time
import random
import numpy as np
from dateutil.relativedelta import relativedelta

conn = pymongo.MongoClient('mongodb://root:pc152@127.0.0.1:27017/') 
db = conn['delta']

while True:
    print("AA")
    db.pcs.insert({
        "ID":"c1_pcs",
        "time": datetime.datetime.now(),
        "p_sum":random.randint(0,100),
        "q_sum":random.randint(0,100)
        
    })
    db.acm.insert({
        "ID":"c1_acm1",
        "time": datetime.datetime.now(),
        "p":random.randint(0,100),
    })
    db.acm.insert({
        "ID":"c1_acm2",
        "time": datetime.datetime.now(),
        "p":random.randint(0,100),
    })
    db.acm.insert({
        "ID":"c1_acm4",
        "time": datetime.datetime.now(),
        "v":random.randint(0,100),
    })
    time.sleep(1)
