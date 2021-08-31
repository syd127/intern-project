# -*- coding: utf-8 -*-
#! /usr/bin/env python3
from flask import Flask,jsonify,render_template,request,redirect,url_for,flash,send_from_directory,Response,send_file,session,g,make_response
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_compress import Compress
from werkzeug.contrib.cache import SimpleCache
import pymongo
import re #like find
from bson.objectid import ObjectId
import os
from config import DevConfig
import json
import time
import datetime
from dateutil.relativedelta import relativedelta
import math
import csv
import io
import prepareplot as t
import current as c
import datetime             #added by柯柯
import time                 #added by柯柯
import threading            #added by柯柯
from bson.objectid import ObjectId   #added by柯柯  0310
from pm_import_test import caculate_pm, avg_pm
from shutil import copyfile #added by柯柯 0409
import history_plot as plot_one_day #added by 睿彬
#------------------------------------------------------------------------------
## added by 柯柯 0323 ##
# variable declaration
now = datetime.datetime.now()
print_mode = "wp"
SystemControlList = "./SystemControlList.txt"    #儲存內部錯誤的文件
log = "./log.txt"    #儲存內部錯誤的文件
## end ##
#-------------------------------------------------------------------------------
app = Flask(__name__)
Compress(app)
app.config.from_object(DevConfig)

UPLOAD_FOLDER='upload'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
app.config['UPLOAD_FOLDER']=UPLOAD_FOLDER
ALLOWED_EXTENSIOS= set(['txt'])
datetime_for_url = 0
#-------------------------------------------------------------------------------
app.secret_key='fsdfsdfsdf154z'
login_manger=LoginManager()
login_manger.session_protection='strong'
login_manger.init_app(app)
#-------------------------------------------------------------------------------
# conn = pymongo.MongoClient('mongodb://root:pc152@140.118.171.124:27017/')
# conn = pymongo.MongoClient('mongodb://cckuoLab:FourthFloor4Database@140.118.171.124:27017/')
conn = pymongo.MongoClient('mongodb://root:pc152@127.0.0.1:27017/')
#-------------------------------------------------------------------------------
cache=SimpleCache()
#--------------------------------------------------------------------------------------------------
# 寫出error的子程式     by 柯柯0323
# >usage: "w":only write/ "p": only print/ "wp" or "pw": write and print
def print_function(content, select="p", file=SystemControlList):
    if select == "w":
        try:
            with open(file, "a") as f:
                f.write(content + "\n")
        except Exception as e:
            print(e)
    elif select == "p":
        print(content)
    elif select == "pw" or select == "wp":
        try:
            with open(file, "a") as f:
                f.write(content + "\n")
        except Exception as e:
            print(e)
        print(content)
#-------------------------------------------------------------------------------
class User(UserMixin):
    pass
 
#-------------------------------------------------------------------------------
@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = datetime.timedelta(minutes=60)
    session.modified = True
    g.user = current_user
#-------------------------------------------------------------------------------
#對照是否有此用戶
def user_list(user_id):
    _user=user_id.split('_')
    db =conn[_user[0]]
    for user in db.users.find({'username':_user[1]}):
        return user
#-------------------------------------------------------------------------------
#如果用戶存在則構建一新用戶類對象，並使用user_id當id
@login_manger.user_loader
def load_user(user_id):
    user=user_list(user_id)
    if user is not None:
        curr_user = User()
        curr_user.id = user['user_id']
        return curr_user
#-------------------------------------------------------------------------------
#當沒登入時導入login頁面
@login_manger.unauthorized_handler
def unauthorized_handler():
    flash('You need login!!')
    return render_template('login.html')
#-------------------------------------------------------------------------------
def check_user():
    user = current_user.get_id()
    print("current_user: ",user)
    try:
        user = user.split('_')
    except:
        # logout() 無意義
        return None,None
    db = conn[user[0]]
    return user,db
#-----------------------------------------------------------------------------------
#網頁不緩存
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cahe,no-store,must-revalidate"
    return response
#404錯誤頁面
#@app.errorhandler(404)
#def page_not_founf(error):
#    return render_template(''),404
#-------------------------------------------------------------------------------
#login
@app.route('/login',methods=['POST'])
def login():
  if request.method == 'POST':
    username = request.form.get('username',type=str)
    company = request.form.get('company',type=str)
    print(username,company)
    if(username!='' and company!=''):
      user_id=company+'_'+username
      user = user_list(user_id)
      #驗證帳號
      if (user!=None) and (request.form['password'] == user['password']):
        print(session)
        curr_user = User()
        curr_user.id = user['user_id']
        #通過flask-login的login_user方法登入用戶
        login_user(curr_user)
        db = conn[company]
        now = datetime.datetime.now()
        db.soe.insert({"ID":"system","time":now,"event":"使用者:"+username+' 登入'})
        return redirect('/')
  flash('Wrong infornation!!')
  return render_template('login.html')
#-------------------------------------------------------------------------------
#logout
@app.route('/logout')
def logout():
  user,db = check_user()
  if(db!=None):
    now = datetime.datetime.now()
    db.soe.insert({"ID":"system","time":now,"event":"使用者:"+user[1]+' 登出'})
  user = current_user
  user.authenticated = False
  logout_user()
  flash('Welcome')
  return render_template('login.html')
#----------------------------------------------------------------------------------
#######################################################################################################################
@app.route('/ShowTime')
def ShowTime():
    now = datetime.datetime.now()
    now = datetime.datetime.strftime(now,"%Y-%m-%d %H:%M:%S")
    return jsonify(now = now)
#######################################################################################################################
#-----------------------------------------------------------------------------------
#計算總電錶值 added by 柯柯 0326
def get_acm_data():
    total_meter = {}
    db = conn['delta']
    #--從資料庫抓取資料
    mbms = c.current_data(db,'mbms','c1_mbms',{"ID":0})[0]  #電池資訊
    pcs = c.current_data(db,'pcs','c1_pcs',{"operation_mode":1,"p_sum":1,"q_sum":1,"v_grid":1,"f_grid":1,"v_bat":1,"chg_kwh":1,"dis_kwh":1,"pf":1,"switch_DC":1,"switch_AC":1})[0]
    pcs_meter = c.current_data(db,'acm','c1_acm3',{"ID":0})[0]   #PCS電錶資訊
    PV = c.current_data(db,'sim','sim_meter',{"ID":0})[0]   #PV資訊
    load = c.current_data(db,'simLoad','sim_Load',{"ID":0})[0] #load資訊

    total_meter['v'] = pcs_meter['v']
    total_meter['p'] = load['p'] - PV['p'] - pcs['p_sum']
    total_meter['q'] = load['q'] - PV['q'] - pcs['q_sum']
    total_meter['f'] = pcs_meter['f']
    
    return total_meter

#-----------------------------------------------------------------------------------
@app.route('/index_data')       #edit by 柯柯0326
def index_data():
    data = {}
    db = conn['delta']
    data['rio'] = c.current_data(db,'c_state','c1_state',{"vcb":1,"acb":1})[0]
    data['mbms'] = c.current_data(db,'mbms','c1_mbms',{"ID":0})[0]
    #data['acm1'] = c.current_data(db,'acm','c1_acm1',{"ID":0})[0]
    data['acm1'] = c.current_data(db,'sim','sim_meter',{"ID":0})[0]     #PV
    data['acm2'] = c.current_data(db,'acm','c1_acm2',{"ID":0})[0]       #no data in delta
    data['acm3'] = c.current_data(db,'acm','c1_acm3',{"ID":0})[0]       #PCS 電錶 in delta case
    data['acm4'] = c.current_data(db,'acm','c1_acm4',{"ID":0})[0]       #no data in delta
    #data['load'] = c.current_data(db,'load','c1_load',{"ID":0})[0] 
    data['load'] = c.current_data(db,'simLoad','sim_Load',{"ID":0})[0]      #load     
    data['pcs'] = c.current_data(db,'pcs','c1_pcs',{"operation_mode":1,"p_sum":1,"q_sum":1,"v_grid":1,"f_grid":1,"v_bat":1,"chg_kwh":1,"dis_kwh":1,"pf":1,"switch_DC":1,"switch_AC":1})[0]
    data['acm4'] = get_acm_data()                                       #總電錶(低壓側)
    mode_data = c.current_data(db,'site_control','c1_pcs')[0]
    data['pcs']['mode'] = mode_data['mode']
    try:
        data['bms_total_connect'] = db.status.find_one({"name":"BMS Total"},{"status":1}).get('status',1)
    except:
        data['bms_total_connect'] = 1
    try:
        data['device_total_connect'] = db.status.find_one({"name":"Device Total"},{"status":1}).get('status',1)
    except:
        data['device_total_connect'] = 1
    try:
        data['pcs_connect'] = db.status.find_one({"name":"PCS"},{"status":1}).get('status',1)
    except:
        data['pcs_connect'] = 1
    try:
        data['pcs_controller_connect'] = db.status.find_one({"name":"PCS Controller"},{"status":1}).get('status',1)
    except:
        data['pcs_controller_connect'] = 1
    return jsonify(data = data)
#######################################################################################################################
#取得 ess 一種類所有設備equip
@app.route('/ess_getone_equip')
def ess_getone_equip():
    db = conn['delta']
    containter = request.args.get('containter', type=str)
    equip_type = request.args.get('equip_type', type=str)
    print(containter,equip_type)
    equip_data = list(db.equipment.find({'containter':{'$all':[containter]},'type':equip_type},{"_id":0}))
    return jsonify(equip_data = equip_data)
#----------------------------------------------------------------------------------------------------------
#取得 mbms 和 rack資訊
@app.route('/ess_mbms_rack_data')
def ess_mbms_rack_data():
    db = conn['delta']
    mbms_ID = request.args.get('mbms_ID', type=str)
    project = {
        "time":1,
        "mbms_onoff":1,
        "mbms_status":1,
        "mbms_protection":1,
        "mbms_v":1,
        "mbms_i":1,
        "mbms_p":1,
        "mbms_soc":1,
        "mbms_soh":1,
        "mbms_v_max":1,
        "mbms_v_min":1,
        "mbms_temp_max":1,
        "mbms_temp_min":1,
        "mbms_v_max_index":1,
        "mbms_v_min_index":1,
        "mbms_temp_max_index":1,
        "mbms_temp_min_index":1,
        "rack_onoff":1,
        "rack_status":1,
        "rack_protection":1,
        "rack_v":1,
        "rack_i":1,
        "rack_p":1,
        "rack_soc":1,
        "rack_soh":1,
        "rack_pc":1,
        "rack_nc":1,

    }

    data = c.current_data(db,'mbms',mbms_ID,project)[0]
    connect_data = db.equipment.find_one({"ID":mbms_ID},{"_id":0,"rack_trip":1,"rack_online":1})

    return jsonify(data = data,connect_data=connect_data)
#----------------------------------------------------------------------------------------------------------
#取得 rack 和 mod資訊
@app.route('/ess_rack_mod_data')
def ess_rack_mod_data():
    db = conn['delta']
    mbms_ID = request.args.get('mbms_ID', type=str)
    rack = request.args.get('rack', type=int)
    # print(mbms_ID,rack)
    try:
        data = c.rack_data(db,mbms_ID,rack)[0]
    except:
        data = {}
    return jsonify(data = data)
#----------------------------------------------------------------------------------------------------------
#取得 cell資訊
#global starttime 
#starttime = datetime.datetime.strptime('2021-04-20-14:12:24',"%Y-%m-%d-%H:%M:%S")
@app.route('/ess_cell_data')
def ess_cell_data():
    global starttime
    db = conn['delta']
    mbms_ID = request.args.get('mbms_ID', type=str)
    rack = request.args.get('rack', type=int)
    module_num =  request.args.get('module_num', type=int)
    #starttime = starttime + relativedelta(seconds=1)
    starttime = datetime.datetime.now() - relativedelta(seconds=60)         # reviced by 柯柯 0516
    endtime = datetime.datetime.now() + relativedelta(seconds=5)
    print(starttime)
    print(endtime)
    # print(module_num)
    try:
        data = c.cell_data(db=db,ID=mbms_ID,rack_index=rack,mod_index=module_num,starttime=starttime,endtime=endtime)
        # print(data)
    except:
        data = {}
    return jsonify({'data':data})
#----------------------------------------------------------------------------------------------------------
#取得 rack 和 mod資訊
# @app.route('/ess_mod_cell_data')
# def ess_mod_cell_data():
#     db = conn['delta']
#     mbms_ID = request.args.get('mbms_ID', type=str)
#     rack = request.args.get('rack', type=int)
#     mod = request.args.get('mod', type=int)
#     print(rack,mod)
#     try:
#         data = c.mod_data(db,mbms_ID,rack,mod)[0]
#     except:
#         data = {}
#     return jsonify(data = data)
#----------------------------------------------------------------------------------------------------------
@app.route('/ess_csv_output')
def ess_csv_output():
    db = conn['delta']
    mbms_ID = request.args.get('mbms_ID', type=str)
    datepicker1 = request.args.get('datepicker1', type=str)
    datepicker1_hr = request.args.get('datepicker1_hr', type=str)
    starttime = datetime.datetime.strptime(datepicker1+" "+datepicker1_hr+":00:00","%Y-%m-%d %H:%M:%S")
    mbms_info = db.equipment.find_one({"ID":mbms_ID,"type":"mbms"},{"rack":1,"rack_start":1})

    csvList = []
    project = {
        "time":1,
        "rack_onoff":1,
        "rack_status":1,
        "rack_protection":1,
        "rack_pc":1,
        "rack_nc":1,
        "rack_v":1,
        "rack_i":1,
        "rack_p":1,
        "rack_soc":1,
        "rack_soh":1,
        'mod_v':1,
        'mod_temp':1,
        'cell_v':1
    }

    key = ["rack_onoff","rack_status","rack_protection","rack_pc","rack_nc","rack_v","rack_i","rack_p","rack_soc","rack_soh"]
    key2 = ["mod_v","mod_temp"]
    key3 = ["cell_v"]
    key_name = [
        "電池櫃","時間","電源狀態","工作狀態","保護狀態","Realy+","Realy-","電壓(V)","電流(A)","功率(kW)","SOC(%)","SOH(%)",
        "mod1電壓(V)","mod1溫度(°C)","mod2電壓(V)","mod2溫度(°C)","mod3電壓(V)","mod3溫度(°C)","mod4電壓(V)","mod4溫度(°C)","mod5電壓(V)","mod5溫度(°C)",
        "mod6電壓(V)","mod6溫度(°C)","mod7電壓(V)","mod7溫度(°C)","mod8電壓(V)","mod8溫度(°C)","mod9電壓(V)","mod9溫度(°C)","mod10電壓(V)","mod10溫度(°C)",
        "mod11電壓(V)","mod11溫度(°C)","mod12電壓(V)","mod12溫度(°C)","mod13電壓(V)","mod13溫度(°C)","mod14電壓(V)","mod14溫度(°C)","mod15電壓(V)","mod15溫度(°C)",
        "mod16電壓(V)","mod16溫度(°C)","mod17電壓(V)","mod17溫度(°C)","mod18電壓(V)","mod18溫度(°C)",
        "mod1-cell1電壓(V)","mod1-cell2電壓(V)","mod1-cell3電壓(V)","mod1-cell4電壓(V)","mod1-cell5電壓(V)","mod1-cell6電壓(V)","mod1-cell7電壓(V)","mod1-cell8電壓(V)",
        "mod1-cell9電壓(V)","mod1-cell10電壓(V)","mod1-cell11電壓(V)","mod1-cell12電壓(V)","mod1-cell13電壓(V)","mod1-cell14電壓(V)","mod1-cell15電壓(V)","mod1-cell16電壓(V)",
        "mod2-cell1電壓(V)","mod2-cell2電壓(V)","mod2-cell3電壓(V)","mod2-cell4電壓(V)","mod2-cell5電壓(V)","mod2-cell6電壓(V)","mod2-cell7電壓(V)","mod2-cell8電壓(V)",
        "mod2-cell9電壓(V)","mod2-cell10電壓(V)","mod2-cell11電壓(V)","mod2-cell12電壓(V)","mod2-cell13電壓(V)","mod2-cell14電壓(V)","mod2-cell15電壓(V)","mod2-cell16電壓(V)",
        "mod3-cell1電壓(V)","mod3-cell2電壓(V)","mod3-cell3電壓(V)","mod3-cell4電壓(V)","mod3-cell5電壓(V)","mod3-cell6電壓(V)","mod3-cell7電壓(V)","mod3-cell8電壓(V)",
        "mod3-cell9電壓(V)","mod3-cell10電壓(V)","mod3-cell11電壓(V)","mod3-cell12電壓(V)","mod3-cell13電壓(V)","mod3-cell14電壓(V)","mod3-cell15電壓(V)","mod3-cell16電壓(V)",
        "mod4-cell1電壓(V)","mod4-cell2電壓(V)","mod4-cell3電壓(V)","mod4-cell4電壓(V)","mod4-cell5電壓(V)","mod4-cell6電壓(V)","mod4-cell7電壓(V)","mod4-cell8電壓(V)",
        "mod4-cell9電壓(V)","mod4-cell10電壓(V)","mod4-cell11電壓(V)","mod4-cell12電壓(V)","mod4-cell13電壓(V)","mod4-cell14電壓(V)","mod4-cell15電壓(V)","mod4-cell16電壓(V)",
        "mod5-cell1電壓(V)","mod5-cell2電壓(V)","mod5-cell3電壓(V)","mod5-cell4電壓(V)","mod5-cell5電壓(V)","mod5-cell6電壓(V)","mod5-cell7電壓(V)","mod5-cell8電壓(V)",
        "mod5-cell9電壓(V)","mod5-cell10電壓(V)","mod5-cell11電壓(V)","mod5-cell12電壓(V)","mod5-cell13電壓(V)","mod5-cell14電壓(V)","mod5-cell15電壓(V)","mod5-cell16電壓(V)",
        "mod6-cell1電壓(V)","mod6-cell2電壓(V)","mod6-cell3電壓(V)","mod6-cell4電壓(V)","mod6-cell5電壓(V)","mod6-cell6電壓(V)","mod6-cell7電壓(V)","mod6-cell8電壓(V)",
        "mod6-cell9電壓(V)","mod6-cell10電壓(V)","mod6-cell11電壓(V)","mod6-cell12電壓(V)","mod6-cell13電壓(V)","mod6-cell14電壓(V)","mod6-cell15電壓(V)","mod6-cell16電壓(V)",
        "mod7-cell1電壓(V)","mod7-cell2電壓(V)","mod7-cell3電壓(V)","mod7-cell4電壓(V)","mod7-cell5電壓(V)","mod7-cell6電壓(V)","mod7-cell7電壓(V)","mod7-cell8電壓(V)",
        "mod7-cell9電壓(V)","mod7-cell10電壓(V)","mod7-cell11電壓(V)","mod7-cell12電壓(V)","mod7-cell13電壓(V)","mod7-cell14電壓(V)","mod7-cell15電壓(V)","mod7-cell16電壓(V)",
        "mod8-cell1電壓(V)","mod8-cell2電壓(V)","mod8-cell3電壓(V)","mod8-cell4電壓(V)","mod8-cell5電壓(V)","mod8-cell6電壓(V)","mod8-cell7電壓(V)","mod8-cell8電壓(V)",
        "mod8-cell9電壓(V)","mod8-cell10電壓(V)","mod8-cell11電壓(V)","mod8-cell12電壓(V)","mod8-cell13電壓(V)","mod8-cell14電壓(V)","mod8-cell15電壓(V)","mod8-cell16電壓(V)",
        "mod9-cell1電壓(V)","mod9-cell2電壓(V)","mod9-cell3電壓(V)","mod9-cell4電壓(V)","mod9-cell5電壓(V)","mod9-cell6電壓(V)","mod9-cell7電壓(V)","mod9-cell8電壓(V)",
        "mod9-cell9電壓(V)","mod9-cell10電壓(V)","mod9-cell11電壓(V)","mod9-cell12電壓(V)","mod9-cell13電壓(V)","mod9-cell14電壓(V)","mod9-cell15電壓(V)","mod9-cell16電壓(V)",
        "mod10-cell1電壓(V)","mod10-cell2電壓(V)","mod10-cell3電壓(V)","mod10-cell4電壓(V)","mod10-cell5電壓(V)","mod10-cell6電壓(V)","mod10-cell7電壓(V)","mod10-cell8電壓(V)",
        "mod10-cell9電壓(V)","mod10-cell10電壓(V)","mod10-cell11電壓(V)","mod10-cell12電壓(V)","mod10-cell13電壓(V)","mod10-cell14電壓(V)","mod10-cell15電壓(V)","mod10-cell16電壓(V)",
        "mod11-cell1電壓(V)","mod11-cell2電壓(V)","mod11-cell3電壓(V)","mod11-cell4電壓(V)","mod11-cell5電壓(V)","mod11-cell6電壓(V)","mod11-cell7電壓(V)","mod11-cell8電壓(V)",
        "mod11-cell9電壓(V)","mod11-cell10電壓(V)","mod11-cell11電壓(V)","mod11-cell12電壓(V)","mod11-cell13電壓(V)","mod11-cell14電壓(V)","mod11-cell15電壓(V)","mod11-cell16電壓(V)",
        "mod12-cell1電壓(V)","mod12-cell2電壓(V)","mod12-cell3電壓(V)","mod12-cell4電壓(V)","mod12-cell5電壓(V)","mod12-cell6電壓(V)","mod12-cell7電壓(V)","mod12-cell8電壓(V)",
        "mod12-cell9電壓(V)","mod12-cell10電壓(V)","mod12-cell11電壓(V)","mod12-cell12電壓(V)","mod12-cell13電壓(V)","mod12-cell14電壓(V)","mod12-cell15電壓(V)","mod12-cell16電壓(V)",
        "mod13-cell1電壓(V)","mod13-cell2電壓(V)","mod13-cell3電壓(V)","mod13-cell4電壓(V)","mod13-cell5電壓(V)","mod13-cell6電壓(V)","mod13-cell7電壓(V)","mod13-cell8電壓(V)",
        "mod13-cell9電壓(V)","mod13-cell10電壓(V)","mod13-cell11電壓(V)","mod13-cell12電壓(V)","mod13-cell13電壓(V)","mod13-cell14電壓(V)","mod13-cell15電壓(V)","mod13-cell16電壓(V)",
        "mod14-cell1電壓(V)","mod14-cell2電壓(V)","mod14-cell3電壓(V)","mod14-cell4電壓(V)","mod14-cell5電壓(V)","mod14-cell6電壓(V)","mod14-cell7電壓(V)","mod14-cell8電壓(V)",
        "mod14-cell9電壓(V)","mod14-cell10電壓(V)","mod14-cell11電壓(V)","mod14-cell12電壓(V)","mod14-cell13電壓(V)","mod14-cell14電壓(V)","mod14-cell15電壓(V)","mod14-cell16電壓(V)",
        "mod15-cell1電壓(V)","mod15-cell2電壓(V)","mod15-cell3電壓(V)","mod15-cell4電壓(V)","mod15-cell5電壓(V)","mod15-cell6電壓(V)","mod15-cell7電壓(V)","mod15-cell8電壓(V)",
        "mod15-cell9電壓(V)","mod15-cell10電壓(V)","mod15-cell11電壓(V)","mod15-cell12電壓(V)","mod15-cell13電壓(V)","mod15-cell14電壓(V)","mod15-cell15電壓(V)","mod15-cell16電壓(V)",
        "mod16-cell1電壓(V)","mod16-cell2電壓(V)","mod16-cell3電壓(V)","mod16-cell4電壓(V)","mod16-cell5電壓(V)","mod16-cell6電壓(V)","mod16-cell7電壓(V)","mod16-cell8電壓(V)",
        "mod16-cell9電壓(V)","mod16-cell10電壓(V)","mod16-cell11電壓(V)","mod16-cell12電壓(V)","mod16-cell13電壓(V)","mod16-cell14電壓(V)","mod16-cell15電壓(V)","mod16-cell16電壓(V)",
        "mod17-cell1電壓(V)","mod17-cell2電壓(V)","mod17-cell3電壓(V)","mod17-cell4電壓(V)","mod17-cell5電壓(V)","mod17-cell6電壓(V)","mod17-cell7電壓(V)","mod17-cell8電壓(V)",
        "mod17-cell9電壓(V)","mod17-cell10電壓(V)","mod17-cell11電壓(V)","mod17-cell12電壓(V)","mod17-cell13電壓(V)","mod17-cell14電壓(V)","mod17-cell15電壓(V)","mod17-cell16電壓(V)",
        "mod18-cell1電壓(V)","mod18-cell2電壓(V)","mod18-cell3電壓(V)","mod18-cell4電壓(V)","mod18-cell5電壓(V)","mod18-cell6電壓(V)","mod18-cell7電壓(V)","mod18-cell8電壓(V)",
        "mod18-cell9電壓(V)","mod18-cell10電壓(V)","mod18-cell11電壓(V)","mod18-cell12電壓(V)","mod18-cell13電壓(V)","mod18-cell14電壓(V)","mod18-cell15電壓(V)","mod18-cell16電壓(V)",
    ]
    csvList.append(key_name)

    for i in range(3600):
        endtime = starttime+datetime.timedelta(seconds=1)
        data = db.mbms.find_one({"ID":mbms_ID,"time":{"$gte":starttime,"$lte":endtime}},project)

        for j in range(int(mbms_info["rack"])):
            csvdata = ["電池櫃"+str(int(mbms_info["rack_start"])+j),datetime.datetime.strftime(starttime,"%Y-%m-%dT%H:%M:%S")]
            for k in key:
                try:
                    csvdata.append(data[k][j])
                except:
                    csvdata.append('NaN')

            for m in range(18):
                for k in key2:
                    try:
                        csvdata.append(data[k][j][m])
                    except:
                        csvdata.append('NaN')

            for m in range(18):
                for n in range(16):
                    for k in key3:
                        try:
                            csvdata.append(data[k][j][m][n])
                        except:
                            csvdata.append('NaN')
            csvList.append(csvdata)
        starttime = endtime

    #print(csvList)

    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerows(csvList)

    mem = io.BytesIO()
    mem.write(si.getvalue().encode('utf-8-sig'))
    mem.seek(0)
    si.close()

    return send_file(
        mem,
        as_attachment=True,
        attachment_filename='export.csv',
        mimetype='text/csv'
    )
#------------------------------------------------------------------------------------------------------
#取得acm資料
@app.route('/ess_acm_data')
def ess_acm_data():
    db  = conn["delta"]
    acm_ID = request.args.get('acm_ID', type=str)
    print(acm_ID)
    acm_data = c.current_data(db,'acm',acm_ID)[0]
    return jsonify(acm_data=acm_data)
#------------------------------------------------------------------------------------------------------
#取得load資料
@app.route('/ess_load_data')
def ess_load_data():
    db  = conn["delta"]
    load_ID = request.args.get('load_ID', type=str)
    print(load_ID)
    load_data = c.current_data(db,'load',load_ID)[0]
    return jsonify(load_data=load_data)
#------------------------------------------------------------------------------------------------------
#取得dcm資料
@app.route('/ess_dcm_data')
def ess_dcm_data():
    db  = conn["delta"]
    dcm_ID = request.args.get('dcm_ID', type=str)
    print(dcm_ID)
    dcm_data = c.current_data(db,'dcm',dcm_ID)[0]
    return jsonify(dcm_data=dcm_data)
#----------------------------------------------------------------------------------------------------------
#取得air資料
@app.route('/ess_air_data')
def ess_air_data():
    db  = conn["delta"]
    air_ID = request.args.get('air_ID', type=str)
    print(air_ID)
    air_data = c.current_data(db,'air',air_ID)[0]
    return jsonify(air_data=air_data)
#----------------------------------------------------------------------------------------------------------
#取得ups資料
@app.route('/ess_ups_data')
def ess_ups_data():
    db  = conn["delta"]
    ups_ID = request.args.get('ups_ID', type=str)
    print(ups_ID)
    ups_data = c.current_data(db,'ups',ups_ID)[0]
    return jsonify(ups_data=ups_data)
#----------------------------------------------------------------------------------------------------------
#取得c_env資料
@app.route('/ess_env_data')
def ess_env_data():
    db  = conn["delta"]
    env_ID = request.args.get('env_ID', type=str)
    print(env_ID)
    env_data = c.current_data(db,'c_env',env_ID)[0]
    return jsonify(env_data=env_data)
#----------------------------------------------------------------------------------------------------------
#取得c_state資料
@app.route('/ess_state_data')
def ess_state_data():
    db  = conn["delta"]
    state_ID = request.args.get('state_ID', type=str)
    print(state_ID)
    state_data = c.current_data(db,'c_state',state_ID)[0]
    return jsonify(state_data=state_data)
#----------------------------------------------------------------------------------------------------------
#取得relay資料
@app.route('/ess_relay_data')
def ess_relay_data():
    db  = conn["delta"]
    relay_ID = request.args.get('relay_ID', type=str)
    relay_data = c.current_data(db,'relay',relay_ID)[0]
    return jsonify(relay_data=relay_data)
#----------------------------------------------------------------------------------------------------------
#取得ess equip(control)
@app.route('/ess_equip')
def ess_equip():
    db = conn['delta']
    containter = request.args.get('containter', type=str)
    equip_mbms = db.equipment.find_one({'containter':{'$all':[containter]},'type':'mbms'},{"_id":0})
    equip_air = list(db.equipment.find({'containter':{'$all':[containter]},'type':'air'},{"_id":0}))
    return jsonify(equip_mbms = equip_mbms,equip_air=equip_air)
#----------------------------------------------------------------------------------------------------------
#取得 ess set
@app.route('/ess_set_get')
def ess_set_get():
    db = conn['delta']
    mbms_ID = request.args.get('mbms_ID', type=str)
    air_ID = request.args.get('air_ID', type=str).split(',')
    mbms_set = c.current_data(db,'mbms_control',mbms_ID)[0]
    air_set = c.current_data(db,'air_control',air_ID)
    return jsonify(mbms_set = mbms_set,air_set=air_set)
#----------------------------------------------------------------------------------------------------------
#ess set設定
@app.route('/ess_set')
def ess_set():
    db = conn['delta']
    set_data = json.loads(request.args.get('set_data', type=str))
    col = request.args.get('col', type=str)
    now = datetime.datetime.now()
    limit_over2v = c.current_data(db,'sys_mbms','sys_mbms',{"limit_over2v":1})[0].get("limit_over2v",None)
    if(col=='air_control'):
        for i in set_data:
            statusTable = {0:"關閉",1:"開啟"}
            event = "設定空調參數(狀態:"+statusTable[i['onoff']]+", 溫度:"+i['temp']+"°C)"
            i['time'] = now
            i['onoff'] = c.tonum(i['onoff'],None)
            i['temp'] = c.tonum(i['temp'],None)
            newOne = 0
            try:
                latest = db.air_control.find_one({"ID":i["ID"]},{"_id":0,"time":0},sort=[( 'time', pymongo.DESCENDING )])
                latest["time"] = now
                if i == latest:
                    newOne = 0
                else:
                    newOne = 1
            except:
                newOne = 1
            if(newOne == 1):
                db.soe.insert({"ID":i["ID"],"time":now,"event":event})
                db.air_control.insert(i)
    elif(col=='mbms_control'):
        for i in set_data:
            event = "設定電池組參數(狀態:"+str(i['rack_onoff'])+", 復歸:"+str(i['rack_reset'])+")"
            i['time'] = now
            newOne = 0
            try:
                latest = db.mbms_control.find_one({"ID":i["ID"]},{"_id":0,"time":0},sort=[( 'time', pymongo.DESCENDING )])
                latest["time"] = now
                if i == latest:
                    newOne = 0
                else:
                    newOne = 1
            except:
                newOne = 1
            if(newOne == 1):
                # if(limit_over2v == 1):
                #     i["rack_onoff"] = [0 for j in range(len(i["rack_onoff"]))]
                #     db.mbms_control.insert(i)
                #     event = "僅設定電池組參數(復歸:"+str(i['rack_reset'])+"),原因為電池組2V電壓差保護中"
                #     db.soe.insert({"ID":i["ID"],"time":now,"event":event})
                #     return jsonify(status = "電池組2V電壓差保護中")
                # else:
                db.mbms_control.insert(i)
                db.soe.insert({"ID":i["ID"],"time":now,"event":event})

    return jsonify(status = "下達指令成功")
###################################################################################################
#取得 sys set
@app.route('/sys_set_get')
def sys_set_get():
    db = conn['delta']
    sys_set = c.current_data(db,'sys_control','system')[0]
    rio = c.current_data(db,'c_state','c1_state',{"acb":1,"vcb":1})[0]
    return jsonify(sys_set=sys_set,rio=rio)
#----------------------------------------------------------------------------------------------------------
#sys set
@app.route('/sys_set')
def sys_set():
    db = conn['delta']
    set_data = json.loads(request.args.get('set_data', type=str))
    print(set_data)
    now = datetime.datetime.now()
    old_sys_set = c.current_data(db,'sys_control','system')[0]

    pcs_operation_mode = c.current_data(db,"pcs","c1_pcs",{"operation_mode":1})[0].get("operation_mode",None)
    mbms_data1 = c.current_data(db,'mbms',"c1_mbms",{"rack_pc":1,"rack_nc":1})[0]
    mbms_data2 = c.current_data(db,'mbms',"c2_mbms",{"rack_pc":1,"rack_nc":1})[0]
    rack_relay = 0
    try:
        for i in mbms_data1["rack_pc"]:
            if i == 1:
                rack_relay = 1
        for i in mbms_data1["rack_nc"]:
            if i == 1:
                rack_relay = 1
        for i in mbms_data2["rack_pc"]:
            if i == 1:
                rack_relay = 1
        for i in mbms_data2["rack_nc"]:
            if i == 1:
                rack_relay = 1
    except:
        rack_relay = 1

    statusTable = {0:"開路",1:"閉合"}
    statusTable2 = {0:"Local",1:"Remote"}
    if(old_sys_set=={}):
        old_sys_set = {"ID":"system","remote":0,"protection":0,"acb":1,"vcb":1}
        try:
            event = "設定ACB參數(狀態:"+statusTable[set_data["acb"]]+")"
            db.soe.insert({"ID":"acb","time":now,"event":event})
        except:
            pass
        try:
            event = "設定VCB參數(狀態:"+statusTable[set_data["vcb"]]+")"
            db.soe.insert({"ID":"vcb","time":now,"event":event})
        except:
            pass
    else:
        try:
            if(old_sys_set["acb"] != set_data["acb"]):
                event = "設定ACB參數(狀態:"+statusTable[set_data["acb"]]+")"
                db.soe.insert({"ID":"acb","time":now,"event":event})
        except:
            pass
        try:
            if(old_sys_set["vcb"] != set_data["vcb"]):
                event = "設定VCB參數(狀態:"+statusTable[set_data["vcb"]]+")"
                db.soe.insert({"ID":"vcb","time":now,"event":event})
        except:
            pass
        try:
            if(old_sys_set["remote"] != set_data["remote"]):
                if(set_data["remote"] == 1 and pcs_operation_mode != 0 and rack_relay != 0):
                    status = "請初始化系統,再進行系統Remote切換"
                    status = "請初始化系統,再進行系統Remote切換"
                    event = "設定系統參數(狀態:Remote)失敗,原因為未初始化系統,直接進行系統Remote切換"
                    db.soe.insert({"ID":"system","time":now,"event":event})
                    return jsonify(status=status)
                else:
                    event = "設定系統參數(狀態:"+statusTable2[set_data["remote"]]+")"
                    db.soe.insert({"ID":"system","time":now,"event":event})
        except:
            pass

    old_sys_set.update(set_data)
    old_sys_set.update({"time":now})
    db.sys_control.insert(old_sys_set)
    status = "成功"
    return jsonify(status=status)
###################################################################################################
#取得pv資料
@app.route('/pv_pv_data')
def pv_pv_data():
    db  = conn["delta"]
    pv_ID = request.args.get('pv_ID', type=str)
    print(pv_ID)
    pv_data = c.current_data(db,'pv',pv_ID)[0]
    return jsonify(pv_data=pv_data)
###################################################################################################
#取得pcs須顯示資料
@app.route('/pcs_data_get')
def pcs_data_get():
    db = conn['delta']
    pcs_ID = request.args.get('pcs_ID', type=str)
    pcs_data = c.current_data(db,"pcs",pcs_ID)[0]
    mode_data = c.current_data(db,'site_control',pcs_ID)[0]
    return jsonify(pcs_data=pcs_data,mode_data=mode_data)
#---------------------------------------------------------------------------------
#取得pcs名稱
@app.route('/pcs_name')
def pcs_name():
    db  = conn["delta"]
    containter = request.args.get('containter', type=str)
    pcs = []
    for i in db.equipment.find({'containter':{'$all':[containter]},'type':'pcs'},{"_id":0,"ID":1,"name":1}):
        pcs.append(i)
    return jsonify(pcs=pcs)
#------------------------------------------------------------------------------------------------------
#取得pcs status資料
@app.route('/pcs_status_data')
def pcs_status_data():
    db  = conn["delta"]
    pcs_ID = request.args.get('pcs_ID', type=str)
    status_data = c.current_data(db,'pcs',pcs_ID,{"operation_mode":1,'trip_fault':1,'active_warning1':1})[0]
    try:
        pcs_connect = db.status.find_one({"name":"PCS"},{"status":1}).get('status',1)
    except:
        pcs_connect = 1
    try:
        pcs_controller_connect = db.status.find_one({"name":"PCS Controller"},{"status":1}).get('status',1)
    except:
        pcs_controller_connect = 1
    return jsonify(status_data=status_data,pcs_connect=pcs_connect,pcs_controller_connect=pcs_controller_connect)
#------------------------------------------------------------------------------------------------------
#取得pcs status資料
@app.route('/pcs_control_data')
def pcs_control_data():
    db  = conn["delta"]
    pcs_ID = request.args.get('pcs_ID', type=str)
    control_data = c.current_data(db,'pcs_control',pcs_ID)[0]
    return jsonify(control_data=control_data)
#------------------------------------------------------------------------------------------------------
#pcs status控制
@app.route('/pcs_status_control')
def pcs_status_control():
    db  = conn["delta"]
    pcs_ID = request.args.get('pcs_ID', type=str)
    control = request.args.get('control', type=int)
    now = datetime.datetime.now()
    statusTable = {0:"關閉",1:"開啟及併網"}

    sys_set = c.current_data(db,'sys_control','system')[0]
    mbms_data1 = c.current_data(db,'mbms',"c1_mbms",{"rack_pc":1,"rack_nc":1})[0]
    mbms_data2 = c.current_data(db,'mbms',"c2_mbms",{"rack_pc":1,"rack_nc":1})[0]
    rack_relay = 1
    try:
        for i in mbms_data1["rack_pc"]:
            if i == 0:
                rack_relay = 0
        for i in mbms_data1["rack_nc"]:
            if i == 0:
                rack_relay = 0
        for i in mbms_data2["rack_pc"]:
            if i == 0:
                rack_relay = 0
        for i in mbms_data2["rack_nc"]:
            if i == 0:
                rack_relay = 0
    except:
        rack_relay = 0

    try:
        old_data = c.current_data(db,'pcs_control',pcs_ID)[0]

        old_time = old_data["time"]
        protection = sys_set["protection"]
        if(protection == 1):
            status = 3
            db.soe.insert({"ID":pcs_ID,"time":now,"event":"設定PCS搭接參數失敗,原因為系統保護中"})
        elif(rack_relay == 0):
            # status = 4
            # db.soe.insert({"ID":pcs_ID,"time":now,"event":"設定PCS搭接參數失敗,原因為Rack1到Rack29無全數搭接"})
            status = 1
        elif(old_time< now - relativedelta(seconds=+5)):
            status = 1
        else:
            db.soe.insert({"ID":pcs_ID,"time":now,"event":"設定PCS搭接參數失敗,原因為5秒內不得連續設定"})
            status = 2
    except:
        print('first control!')
        status = 1
    if(status==1):
        event = "設定PCS搭接參數(狀態:"+statusTable[control]+")"
        db.soe.insert({"ID":pcs_ID,"time":now,"event":event})
        db.pcs_control.insert({"ID":pcs_ID,"time":now,"control":control,"reset":0,"reboot":0})

    return jsonify(status=status)
#------------------------------------------------------------------------------------------------------
#pcs reset控制
@app.route('/pcs_reset_control')
def pcs_reset_control():
    db  = conn["delta"]
    pcs_ID = request.args.get('pcs_ID', type=str)
    now = datetime.datetime.now()
    try:
        old_data = c.current_data(db,'pcs_control',pcs_ID)[0]
        old_time = old_data["time"]
        control = old_data["control"]
        if(control == 1):
            db.soe.insert({"ID":pcs_ID,"time":now,"event":"設定PCS復歸參數失敗,原因為PCS搭接中"})
            status = 3
        elif(old_time< now - relativedelta(seconds=+5)):
            status = 1
        else:
            db.soe.insert({"ID":pcs_ID,"time":now,"event":"設定PCS復歸參數失敗,原因為5秒內不得連續設定"})
            status = 2
    except:
        print('first control!')
        status = 1

    if(status==1):
        event = "設定PCS復歸參數"
        db.soe.insert({"ID":pcs_ID,"time":now,"event":event})
        db.pcs_control.insert({"ID":pcs_ID,"time":now,"control":0,"reset":1,"reboot":0})

    return jsonify(status=status)
#------------------------------------------------------------------------------------------------------
#pcs reboot控制
@app.route('/pcs_reboot_control')
def pcs_reboot_control():
    db  = conn["delta"]
    pcs_ID = request.args.get('pcs_ID', type=str)
    now = datetime.datetime.now()
    try:
        old_data = c.current_data(db,'pcs_control',pcs_ID)[0]
        old_time = old_data["time"]
        control = old_data["control"]
        if(control == 1):
            db.soe.insert({"ID":pcs_ID,"time":now,"event":"設定PCS重新開機參數失敗,原因為PCS搭接中"})
            status = 3
        elif(old_time< now - relativedelta(seconds=+5)):
            status = 1
        else:
            db.soe.insert({"ID":pcs_ID,"time":now,"event":"設定PCS重新開機參數失敗,原因為PCS搭接中"})
            status = 2
    except:
        print('first control!')
        status = 1

    if(status==1):
        event = "設定PCS重新開機參數"
        db.soe.insert({"ID":pcs_ID,"time":now,"event":event})
        db.pcs_control.insert({"ID":pcs_ID,"time":now,"control":0,"reset":0,"reboot":1})
    return jsonify(status=status)
#------------------------------------------------------------------------------------------------------
#取得確認pcs連線狀態
@app.route('/pcs_connect_check')
def pcs_connect_check():
    db  = conn["delta"]
    pcs_ID = request.args.get('pcs_ID', type=str)
    return jsonify(mode_data=mode_data)
#------------------------------------------------------------------------------------------------------
#取得pcs mode資料
@app.route('/pcs_mode_data')
def pcs_mode_data():
    db  = conn["delta"]
    pcs_ID = request.args.get('pcs_ID', type=str)
    print(pcs_ID)
    mode_data = c.current_data(db,'site_control',pcs_ID)[0]
    return jsonify(mode_data=mode_data)
#-------------------------------------------------------------------------------------------------------------------
#設定pcs 模式參數
@app.route('/pcs_set_mode')
def pcs_set_mode():
    db  = conn["delta"]
    pcs_ID = request.args.get('pcs_ID', type=str)
    mode_data = json.loads(request.args.get('mode_data', type=str))
    mode_data_old = c.current_data(db,'site_control',pcs_ID)[0]
    now = datetime.datetime.now()
    mode_data_old['ID'] = pcs_ID
    try:
        remote = c.current_data(db,"sys_control",'system')[0] ["remote"]
    except:
        remote = 0
    sys_set = c.current_data(db,'sys_control','system')[0]
    protection = sys_set.get("protection",0)

    if(protection==1):
        db.soe.insert({"ID":pcs_ID,"time":now,"event":"設定PCS模式參數失敗,原因為系統保護中"})
        status = "系統保護中"
    elif(remote==1):
        db.soe.insert({"ID":pcs_ID,"time":now,"event":"設定PCS模式參數失敗,原因為Remote控制中"})
        status = "Remote控制，不可設定"
    else:
        if(mode_data['mode']=='0'):
            mode_data_old['mode'] = 0
            mode_data_old['time'] = now
            event = "設定PCS模式參數(模式:停止模式)"
        else:
            # try:
            #     if(mode_data_old["bess_p_max"] != c.tonum(mode_data["bess_p_max"])):
            #         event = "設定PCS模式參數限制值(系統最大輸出功率:"+mode_data['bess_p_max']+"kW)"
            #         db.soe.insert({"ID":pcs_ID,"time":now,"event":event})
            # except:
            #     pass
            try:
                if(mode_data_old["soc_max"] != c.tonum(mode_data["soc_max"])):
                    event = "設定PCS模式參數限制值(最高SOC:"+mode_data['soc_max']+"%)"
                    db.soe.insert({"ID":"system","time":now,"event":event})
            except:
                pass
            try:
                if(mode_data_old["soc_min"] != c.tonum(mode_data["soc_min"])):
                    event = "設定PCS模式參數限制值(最低SOC:"+mode_data['soc_min']+"%)"
                    db.soe.insert({"ID":pcs_ID,"time":now,"event":event})
            except:
                pass
            try:
                if(mode_data_old["System_p_max"] != c.tonum(mode_data["System_p_max"])):
                    event = "設定PCS模式參數限制值(最高放電實功:"+mode_data['System_p_max']+"kW)"
                    db.soe.insert({"ID":pcs_ID,"time":now,"event":event})
            except:
                pass
            try:
                if(mode_data_old["System_p_min"] != c.tonum(mode_data["System_p_min"])):
                    event = "設定PCS模式參數限制值(最高充電實功:"+mode_data['System_p_min']+"kW)"
                    db.soe.insert({"ID":pcs_ID,"time":now,"event":event})
            except:
                pass
            try:
                if(mode_data_old["System_q_max"] != c.tonum(mode_data["System_q_max"])):
                    event = "設定PCS模式參數限制值(最高虛功:"+mode_data['System_q_max']+"kVAR)"
                    db.soe.insert({"ID":pcs_ID,"time":now,"event":event})
            except:
                pass
            try:
                if(mode_data_old["System_q_min"] != c.tonum(mode_data["System_q_min"])):
                    event = "設定PCS模式參數限制值(最低虛功:"+mode_data['System_q_min']+"kVAR)"
                    db.soe.insert({"ID":pcs_ID,"time":now,"event":event})
            except:
                pass

            # mode_data_old['bess_p_max'] = c.tonum(mode_data['bess_p_max'])
            mode_data_old['soc_max'] = c.tonum(mode_data['soc_max'])
            mode_data_old['soc_min'] =  c.tonum(mode_data['soc_min'])
            mode_data_old['System_p_max'] = c.tonum(mode_data['System_p_max'])
            mode_data_old['System_p_min'] = c.tonum(mode_data['System_p_min'])
            mode_data_old['System_q_max'] = c.tonum(mode_data['System_q_max'])
            mode_data_old['System_q_min'] = c.tonum(mode_data['System_q_min'])

            mode_data_old['time'] = now

            if(mode_data['mode']=='1'):
                mode_data_old['mode'] = 1
                mode_data_old['time'] = now
                mode_data_old['PF_p_ref'] = c.tonum(mode_data['PF_p_ref'])
                mode_data_old['PF_pf_ref'] = c.tonum(mode_data['PF_pf_ref'])
                event = "設定PCS模式參數(模式:固定功因模式, 實功:"+mode_data['PF_p_ref']+"kW, 功因:"+mode_data['PF_pf_ref']+")"
            elif(mode_data['mode']=='2'):
                mode_data_old['mode'] = 2
                mode_data_old['Vq_v1_set'] = c.tonum(mode_data['Vq_v1_set'])
                mode_data_old['Vq_v2_set'] = c.tonum(mode_data['Vq_v2_set'])
                mode_data_old['Vq_v3_set'] = c.tonum(mode_data['Vq_v3_set'])
                mode_data_old['Vq_v4_set'] = c.tonum(mode_data['Vq_v4_set'])
                mode_data_old['Vq_v5_set'] = c.tonum(mode_data['Vq_v5_set'])
                mode_data_old['Vq_v6_set'] = c.tonum(mode_data['Vq_v6_set'])
                mode_data_old['Vq_v7_set'] = c.tonum(mode_data['Vq_v7_set'])
                mode_data_old['Vq_q1_set'] = c.tonum(mode_data['Vq_q1_set'])
                mode_data_old['Vq_q2_set'] = c.tonum(mode_data['Vq_q2_set'])
                mode_data_old['Vq_q3_set'] = c.tonum(mode_data['Vq_q3_set'])
                mode_data_old['Vq_q4_set'] = c.tonum(mode_data['Vq_q4_set'])
                mode_data_old['Vq_q5_set'] = c.tonum(mode_data['Vq_q5_set'])
                mode_data_old['Vq_q6_set'] = c.tonum(mode_data['Vq_q6_set'])
                mode_data_old['Vq_q7_set'] = c.tonum(mode_data['Vq_q7_set'])
                mode_data_old['Vq_q_base'] = c.tonum(mode_data['Vq_q_base'])
                mode_data_old['Vq_v_base'] = c.tonum(mode_data['Vq_v_base'])
                event = "設定PCS模式參數(模式:電壓虛功模式, 電壓參考值:"+mode_data['Vq_v_base']+"kV, 虛功參考值:"+mode_data['Vq_q_base']+"kVAR"
                event += ", VQ1:("+mode_data['Vq_v1_set']+","+mode_data['Vq_q1_set']+")"
                event += ", VQ2:("+mode_data['Vq_v2_set']+","+mode_data['Vq_q2_set']+")"
                event += ", VQ3:("+mode_data['Vq_v3_set']+","+mode_data['Vq_q3_set']+")"
                event += ", VQ4:("+mode_data['Vq_v4_set']+","+mode_data['Vq_q4_set']+")"
                event += ", VQ5:("+mode_data['Vq_v5_set']+","+mode_data['Vq_q5_set']+")"
                event += ", VQ6:("+mode_data['Vq_v6_set']+","+mode_data['Vq_q6_set']+")"
                event += ", VQ7:("+mode_data['Vq_v7_set']+","+mode_data['Vq_q7_set']+")"
                event += " )"
            elif(mode_data['mode']=='3'):
                mode_data_old['mode'] = 3
                mode_data_old['time'] = now
                mode_data_old['Vp_v1_set'] = c.tonum(mode_data['Vp_v1_set'])
                mode_data_old['Vp_v2_set'] = c.tonum(mode_data['Vp_v2_set'])
                mode_data_old['Vp_v3_set'] = c.tonum(mode_data['Vp_v3_set'])
                mode_data_old['Vp_v4_set'] = c.tonum(mode_data['Vp_v4_set'])
                mode_data_old['Vp_v5_set'] = c.tonum(mode_data['Vp_v5_set'])
                mode_data_old['Vp_v6_set'] = c.tonum(mode_data['Vp_v6_set'])
                mode_data_old['Vp_p1_set'] = c.tonum(mode_data['Vp_p1_set'])
                mode_data_old['Vp_p2_set'] = c.tonum(mode_data['Vp_p2_set'])
                mode_data_old['Vp_p3_set'] = c.tonum(mode_data['Vp_p3_set'])
                mode_data_old['Vp_p4_set'] = c.tonum(mode_data['Vp_p4_set'])
                mode_data_old['Vp_p5_set'] = c.tonum(mode_data['Vp_p5_set'])
                mode_data_old['Vp_p6_set'] = c.tonum(mode_data['Vp_p6_set'])
                mode_data_old['Vp_p_base'] = c.tonum(mode_data['Vp_p_base'])
                mode_data_old['Vp_v_base'] = c.tonum(mode_data['Vp_v_base'])
                event = "設定PCS模式參數(模式:電壓實功模式, 電壓參考值:"+mode_data['Vp_v_base']+"kV, 實功參考值:"+mode_data['Vp_p_base']+"kW"
                event += ", VP1:("+mode_data['Vp_v1_set']+","+mode_data['Vp_p1_set']+")"
                event += ", VP2:("+mode_data['Vp_v2_set']+","+mode_data['Vp_p2_set']+")"
                event += ", VP3:("+mode_data['Vp_v3_set']+","+mode_data['Vp_p3_set']+")"
                event += ", VP4:("+mode_data['Vp_v4_set']+","+mode_data['Vp_p4_set']+")"
                event += ", VP5:("+mode_data['Vp_v5_set']+","+mode_data['Vp_p5_set']+")"
                event += ", VP6:("+mode_data['Vp_v6_set']+","+mode_data['Vp_p6_set']+")"
                event += " )"
            elif(mode_data['mode']=='4'):
                mode_data_old['mode'] = 4
                mode_data_old['time'] = now
                mode_data_old['Vpq_p_v1_set'] = c.tonum(mode_data['Vpq_p_v1_set'])
                mode_data_old['Vpq_p_v2_set'] = c.tonum(mode_data['Vpq_p_v2_set'])
                mode_data_old['Vpq_p_v3_set'] = c.tonum(mode_data['Vpq_p_v3_set'])
                mode_data_old['Vpq_p_v4_set'] = c.tonum(mode_data['Vpq_p_v4_set'])
                mode_data_old['Vpq_p_p1_set'] = c.tonum(mode_data['Vpq_p_p1_set'])
                mode_data_old['Vpq_p_p2_set'] = c.tonum(mode_data['Vpq_p_p2_set'])
                mode_data_old['Vpq_p_p3_set'] = c.tonum(mode_data['Vpq_p_p3_set'])
                mode_data_old['Vpq_p_p4_set'] = c.tonum(mode_data['Vpq_p_p4_set'])
                mode_data_old['Vpq_q_v1_set'] = c.tonum(mode_data['Vpq_q_v1_set'])
                mode_data_old['Vpq_q_v2_set'] = c.tonum(mode_data['Vpq_q_v2_set'])
                mode_data_old['Vpq_q_v3_set'] = c.tonum(mode_data['Vpq_q_v3_set'])
                mode_data_old['Vpq_q_v4_set'] = c.tonum(mode_data['Vpq_q_v4_set'])
                mode_data_old['Vpq_q_q1_set'] = c.tonum(mode_data['Vpq_q_q1_set'])
                mode_data_old['Vpq_q_q2_set'] = c.tonum(mode_data['Vpq_q_q2_set'])
                mode_data_old['Vpq_q_q3_set'] = c.tonum(mode_data['Vpq_q_q3_set'])
                mode_data_old['Vpq_q_q4_set'] = c.tonum(mode_data['Vpq_q_q4_set'])
                mode_data_old['Vpq_q_base'] = c.tonum(mode_data['Vpq_q_base'])
                mode_data_old['Vpq_p_base'] = c.tonum(mode_data['Vpq_p_base'])
                mode_data_old['Vpq_v_base'] = c.tonum(mode_data['Vpq_v_base'])
                event = "設定PCS模式參數(模式:電壓實虛功模式, 電壓參考值:"+mode_data['Vp_v_base']+"kV, 實功參考值:"+mode_data['Vp_p_base']+"kW, 虛功參考值:"+mode_data['Vq_q_base']+"kVAR"
                event += ", VP1:("+mode_data['Vpq_p_v1_set']+","+mode_data['Vpq_p_p1_set']+")"
                event += ", VP2:("+mode_data['Vpq_p_v2_set']+","+mode_data['Vpq_p_p2_set']+")"
                event += ", VP3:("+mode_data['Vpq_p_v3_set']+","+mode_data['Vpq_p_p3_set']+")"
                event += ", VP4:("+mode_data['Vpq_p_v1_set']+","+mode_data['Vpq_p_p4_set']+")"
                event += ", VQ1:("+mode_data['Vpq_q_v1_set']+","+mode_data['Vpq_q_q1_set']+")"
                event += ", VQ2:("+mode_data['Vpq_q_v2_set']+","+mode_data['Vpq_q_q2_set']+")"
                event += ", VQ3:("+mode_data['Vpq_q_v3_set']+","+mode_data['Vpq_q_q3_set']+")"
                event += ", VQ4:("+mode_data['Vpq_q_v4_set']+","+mode_data['Vpq_q_q4_set']+")"
                event += " )"
            elif(mode_data['mode']=='5'):
                mode_data_old['mode'] = 5
                mode_data_old['time'] = now
                mode_data_old['f1_line_set'] = c.tonum(mode_data['f1_line_set'])
                mode_data_old['f2_line_set'] = c.tonum(mode_data['f2_line_set'])
                mode_data_old['f3_line_set'] = c.tonum(mode_data['f3_line_set'])
                mode_data_old['f4_line_set'] = c.tonum(mode_data['f4_line_set'])
                mode_data_old['f5_line_set'] = c.tonum(mode_data['f5_line_set'])
                mode_data_old['f6_line_set'] = c.tonum(mode_data['f6_line_set'])
                mode_data_old['p1_line_set'] = c.tonum(mode_data['p1_line_set'])
                mode_data_old['p2_line_set'] = c.tonum(mode_data['p2_line_set'])
                mode_data_old['p3_line_set'] = c.tonum(mode_data['p3_line_set'])
                mode_data_old['p4_line_set'] = c.tonum(mode_data['p4_line_set'])
                mode_data_old['p5_line_set'] = c.tonum(mode_data['p5_line_set'])
                mode_data_old['p6_line_set'] = c.tonum(mode_data['p6_line_set'])
                mode_data_old['FP_line_p_base'] = c.tonum(mode_data['FP_line_p_base'])
                mode_data_old['FP_soc_goal_percent'] = c.tonum(mode_data['FP_soc_goal_percent'])
                event = "設定PCS模式參數(模式:頻率實功模式, 功率參考值:"+mode_data['Vp_v_base']+"kW"
                event += ", FP1:("+mode_data['f1_line_set']+","+mode_data['p1_line_set']+")"
                event += ", FP2:("+mode_data['f2_line_set']+","+mode_data['p2_line_set']+")"
                event += ", FP3:("+mode_data['f3_line_set']+","+mode_data['p3_line_set']+")"
                event += ", FP4:("+mode_data['f4_line_set']+","+mode_data['p4_line_set']+")"
                event += ", FP5:("+mode_data['f5_line_set']+","+mode_data['p5_line_set']+")"
                event += ", FP6:("+mode_data['f6_line_set']+","+mode_data['p6_line_set']+")"
                event += " )"
            elif(mode_data['mode']=='6'):
                mode_data_old['mode'] = 6
                mode_data_old['time'] = now
                mode_data_old['PQ_p_ref'] = c.tonum(mode_data['PQ_p_ref'])
                mode_data_old['PQ_q_ref'] = c.tonum(mode_data['PQ_q_ref'])
                event = "設定PCS模式參數(模式:實虛功控制模式, 實功:"+mode_data['PQ_p_ref']+"kW, 虛功:"+mode_data['PQ_q_ref']+"kVAR)"
            elif(mode_data['mode']=='7'):
                mode_data_old['mode'] = 7
                mode_data_old['time'] = now
                mode_data_old['Stable_p_tr_new'] = c.tonum(mode_data['Stable_p_tr_new'])
                mode_data_old['Stable_p_ramp'] = c.tonum(mode_data['Stable_p_ramp'])
                mode_data_old['PV_Steady_Capacity'] = c.tonum(mode_data['PV_Steady_Capacity'])
                event = "設定PCS模式參數(模式:穩定實功模式, PV_Steady_Capacity:"+mode_data['PV_Steady_Capacity']+"kW, 實功:"+mode_data['Stable_p_tr_new']+"kW, 升降載率:"+mode_data['Stable_p_ramp']+"%)"
            elif(mode_data['mode']=='8'):
                mode_data_old['mode'] = 8
                mode_data_old['time'] = now
                mode_data_old['Smooth_p_variance'] = c.tonum(mode_data['Smooth_p_variance'])
                mode_data_old['PV_Smooth_Capacity'] = c.tonum(mode_data['PV_Smooth_Capacity'])
                event = "設定PCS模式參數(模式:平滑化模式, PV_Smooth_Capacity:"+mode_data['PV_Smooth_Capacity']+"kW, 功率變動率:"+mode_data['Smooth_p_variance']+"%)"
            elif(mode_data['mode']=='9'):
                mode_data_old['mode'] = 9
                mode_data_old['time'] = now
                mode_data_old['Anti_p_limit_new'] = c.tonum(mode_data['Anti_p_limit_new'])
                mode_data_old['Power_Reverse_Watt_Limit'] = c.tonum(mode_data['Power_Reverse_Watt_Limit'])
                mode_data_old['PV_Reverse_Capacity'] = c.tonum(mode_data['PV_Reverse_Capacity'])
                event = "設定PCS模式參數(模式:功率逆送模式, PV_Reverse_Capacity:"+mode_data['PV_Reverse_Capacity']+"kW, 逆送實功限制:"+mode_data['Anti_p_limit_new']+"kW, 降載率:"+mode_data['Power_Reverse_Watt_Limit']+"%)"
            elif(mode_data['mode']=='11'):       #added by 柯柯0323
                mode_data_old['mode'] = 11
                mode_data_old['time'] = now
                mode_data_old['DM_p_ref'] = c.tonum(mode_data['DM_p_ref'])
                mode_data_old['DM_flexible_percent'] = c.tonum(mode_data['DM_flexible_percent'])
                event = "設定PCS模式參數(模式:需量控制模式, 需量控制值:"+mode_data['DM_p_ref']+"kW, 彈性區間:"+mode_data['DM_flexible_percent']+"%)"

        status = '成功'
        db.site_control.insert(mode_data_old)
        db.soe.insert({"ID":pcs_ID,"time":now,"event":event})

    return jsonify(status = status)
#------------------------------------------------------------------------------------------------------
#取得pcs set資料
@app.route('/pcs_set_data')
def pcs_set_data():
    db  = conn["delta"]
    pcs_ID = request.args.get('pcs_ID', type=str)
    set_data = c.current_data(db,'pcs_set',pcs_ID)[0]
    return jsonify(set_data=set_data)
#-------------------------------------------------------------------------------------------------------------------
#設定pcs set參數
@app.route('/pcs_set_set')
def pcs_set_set():
    db  = conn["delta"]
    pcs_ID = request.args.get('pcs_ID', type=str)
    set_data = json.loads(request.args.get('set_data', type=str))

    sys_set = c.current_data(db,'sys_control','system')[0]
    protection = sys_set["protection"]
    print(sys_set)
    now = datetime.datetime.now()
    if(protection==1):
        db.soe.insert({"ID":pcs_ID,"time":now,"event":"設定PCS內部參數失敗,原因為系統保護中"})
        status = "系統保護中"
    else:
        for key,value in set_data.items() :
            set_data[key] = c.tonum(value)
        set_data['ID'] = pcs_ID
        set_data['time'] = now
        db.soe.insert({"ID":pcs_ID,"time":now,"event":"設定PCS內部參數"})
        status = '成功'
        db.pcs_set.insert(set_data)
        print(set_data)
    return jsonify(status=status)
#####################################################################################################
#----------------------------------------------------------------------------------------------------
@app.route('/alarm_remove_test')
def alarm_remove_test():
    db = conn['delta']
    db.alarm.remove({})
    return jsonify()
#----------------------------------------------------------------------------------------------------
@app.route('/alarm_get')
def alarm_get():

    db = conn['delta']

    condition = json.loads(request.args.get('condition', type=str))
    skip = (request.args.get('page',1,type=int) -1) * 10 #data need to skip
    datepicker1 = request.args.get('datepicker1', type=str)
    datepicker2 = request.args.get('datepicker2', type=str)
    search = request.args.get('search', type=int)

    event_list=[]
    page_num = 1
    alarm_num = 0
    equipment_dict = {}

    if((condition['show']["1"]==False and condition['show']["2"]==False) or (condition['level']["1"]==False and condition['level']["2"]==False and condition['level']["3"]==False)):
        pass
    else:
        show = []
        level = []
        if(condition['show']["1"]==True):
            show.append(1)
        if(condition['show']["2"]==True):
            show.append(2)
        if(condition['level']["1"]==True):
            level.append(1)
        if(condition['level']["2"]==True):
            level.append(2)
        if(condition['level']["3"]==True):
            level.append(3)

        find = {}
        time_condiction = {}
        if(search==1):
            starttime = datetime.datetime.strptime(datepicker1+' 00:00:00', "%Y-%m-%d %H:%M:%S")
            endtime = datetime.datetime.strptime(datepicker2+' 00:00:00', "%Y-%m-%d %H:%M:%S")
            endtime = endtime + datetime.timedelta(days=1)
            time_condiction = {'time': {'$gte': starttime,'$lte':endtime}}
        elif(search==2):
            starttime = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
            endtime = starttime + datetime.timedelta(days=1)
            time_condiction = {'time': {'$gte': starttime,'$lte':endtime}}

        condiction_list = []
        equip_list = list(db.equipment.find(find,{'_id':0}))
        equip_list.append({"ID":"status",'name':'通訊狀態'})
        equip_list.append({"ID":"SMS",'name':'簡訊機'})
        equip_list.append({"ID":"sys_mbms",'name':'電池組'})

        for i in equip_list:
            equipment_dict[i['ID']] = i
            for j in show:
                for k in level:
                    condiction_list.append({'ID':i['ID'],'show':j,'level':k})

        if(condiction_list !=[]):
            alarm_num = db.alarm.find({**time_condiction,'$or':condiction_list},{'show':0,'about':0}).sort([('show',pymongo.ASCENDING),('time',pymongo.DESCENDING)]).count()

            page_num = math.ceil(alarm_num/10)
            if(page_num<=0):
                page_num = 1
            for event in db.alarm.find({**time_condiction,'$or':condiction_list}).sort([('show',pymongo.ASCENDING),('time',pymongo.DESCENDING)]).skip(skip).limit(10):
                event['_id']=str(event['_id'])
                if(event['time']!=''):
                    event['time'] = datetime.datetime.strftime(event['time'],"%Y-%m-%d %H:%M:%S")
                if(event['returntime']!=''):
                    event['returntime']= datetime.datetime.strftime(event['returntime'],"%Y-%m-%d %H:%M:%S")
                event_list.append(event)
    return jsonify(event_list=event_list,equipment_dict=equipment_dict,page_num=page_num,alarm_num=alarm_num)
#----------------------------------------------------------------------------------------------------
#告警歸檔
@app.route('/alarm_save')
def alarm_save():
    db = conn['delta']
    event_id = request.args.get('event_id', type=str).split(',')
    for i in event_id:
        db.alarm.update({'_id':ObjectId(i)},{'$set':{'show':2}})
    return jsonify()
#----------------------------------------------------------------------------------------------------
#告警刪除
@app.route('/alarm_delete')
def alarm_delete():
    db = conn['delta']
    event_id = request.args.get('event_id', type=str).split(',')
    for i in event_id:
        db.alarm.update({'_id':ObjectId(i)},{'$set':{'show':0}})
    return jsonify()
#----------------------------------------------------------------------------------------------------
@app.route('/alarm_count')
def alarm_count():
    db = conn['delta']
    count = db.alarm.find({"returntime":"","show":1}).count()
    return jsonify(count=count)
#----------------------------------------------------------------------------------------------------
@app.route('/alarm_csv_output')
def alarm_csv_output():
    db = conn['delta']
    mbms_ID = request.args.get('mbms_ID', type=str)
    datepicker1 = request.args.get('datepicker1', type=str)
    datepicker2 = request.args.get('datepicker2', type=str)
    csvList = []
    key_name = ["貨櫃","設備","事件","事件時間","值","清除時間"]
    csvList.append(key_name)

    equipment_dict = {}

    time_condiction = {}
    starttime = datetime.datetime.strptime(datepicker1+' 00:00:00', "%Y-%m-%d %H:%M:%S")
    endtime = datetime.datetime.strptime(datepicker2+' 00:00:00', "%Y-%m-%d %H:%M:%S")
    endtime = endtime + datetime.timedelta(days=1)
    time_condiction = {'time': {'$gte': starttime,'$lte':endtime}}

    condiction_list = []
    equip_list = list(db.equipment.find({},{'_id':0}))
    equip_list.append({"ID":"status",'name':'通訊狀態'})
    equip_list.append({"ID":"SMS",'name':'簡訊機'})
    for i in equip_list:
        equipment_dict[i['ID']] = i
        for j in range(1,3):
            condiction_list.append({'ID':i['ID'],'show':j})

    if(condiction_list !=[]):
        for event in db.alarm.find({**time_condiction,'$or':condiction_list}).sort([('time',pymongo.DESCENDING)]).limit(1000):
            if(event['time']!=''):
                event['time'] = datetime.datetime.strftime(event['time'],"%Y-%m-%dT%H:%M:%S")
            if(event['returntime']!=''):
                event['returntime']= datetime.datetime.strftime(event['returntime'],"%Y-%m-%dT%H:%M:%S")
            equip = equipment_dict[event["ID"]]
            print(equip)
            if event.get('value',None) != None:
                value = str(round(event['value'],3))+event['unit']
            else:
                value = ""
            csvList.append([equip.get("place",""),equip['name'],event['event'],event['time'],value,event['returntime']])

    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerows(csvList)

    mem = io.BytesIO()
    mem.write(si.getvalue().encode('utf-8-sig'))
    mem.seek(0)
    si.close()

    return send_file(
        mem,
        as_attachment=True,
        attachment_filename='export.csv',
        mimetype='text/csv'
    )
#----------------------------------------------------------------------------------------------------
#remote or local
@app.route('/operate_check')
def operate_check():
    db = conn['delta']
    protection = 0
    data = c.current_data(db,'sys_control',"system",{"remote":1})[0]
    if 'remote' in data:
        remote = data["remote"]
    else:
        remote = 1

    if(db.sys_protect_log.find_one({"ID":"system","returntime":""}) != None):
        protection = 1

    return jsonify(remote=remote,protection=protection)
###################################################################################################
#設備狀態
@app.route('/status_data')
def status_data():
    db = conn['delta']
    status_data = list(db.status.find({"alarm":1},{'_id':0}))
    return jsonify(status_data=status_data)
#----------------------------------------------------------------------------------------------------
@app.route('/status_count')
def status_count():
    db = conn['delta']
    count = db.status.find({"status":1,"alarm":1}).count()
    return jsonify(count=count)
#----------------------------------------------------------------------------------------------------
@app.route('/soe_get')
def soe_get():
    db = conn['delta']

    skip = (request.args.get('page',1,type=int) -1) * 10 #data need to skip
    datepicker1 = request.args.get('datepicker1', type=str)
    datepicker2 = request.args.get('datepicker2', type=str)
    search = request.args.get('search', type=int)

    event_list=[]
    page_num = 1
    alarm_num = 0
    equipment_dict = {}
    equip_list = list(db.equipment.find({},{'_id':0}))
    equip_list.append({"ID":"status",'name':'通訊狀態'})
    equip_list.append({"ID":"SMS",'name':'簡訊機'})
    equip_list.append({"ID":"acb",'name':'ACB'})
    equip_list.append({"ID":"vcb",'name':'VCB'})
    equip_list.append({"ID":"system",'name':'SEMS系統'})
    equip_list.append({"ID":"sys_mbms",'name':'電池組'})
    for i in equip_list:
        equipment_dict[i['ID']] = i

    time_condiction = {}
    if(search==1):
        starttime = datetime.datetime.strptime(datepicker1+' 00:00:00', "%Y-%m-%d %H:%M:%S")
        endtime = datetime.datetime.strptime(datepicker2+' 00:00:00', "%Y-%m-%d %H:%M:%S")
        endtime = endtime + datetime.timedelta(days=1)
        time_condiction = {'time': {'$gte': starttime,'$lte':endtime}}
    elif(search==2):
        starttime = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
        endtime = starttime + datetime.timedelta(days=1)
        time_condiction = {'time': {'$gte': starttime,'$lte':endtime}}

    soe_num = db.soe.find({**time_condiction},{"_id":1}).count()
    page_num = math.ceil(soe_num/10)
    if(page_num<=0):
        page_num = 1
    for event in db.soe.find({**time_condiction}).sort('time',pymongo.DESCENDING).skip(skip).limit(10):
        event['_id']=str(event['_id'])
        if(event['time']!=''):
            event['time'] = datetime.datetime.strftime(event['time'],"%Y-%m-%d %H:%M:%S")
        event_list.append(event)
    return jsonify(event_list=event_list,equipment_dict=equipment_dict,page_num=page_num,soe_num=soe_num)
#----------------------------------------------------------------------------------------------------
@app.route('/web_status')
def web_status():
    return 'alive!!'
#----------------------------------------------------------------------------------------------------
@app.route('/get_PQ_plot')
def get_PQ_plot():
    db = conn['delta']
    datepicker = request.args.get('datepicker', type=str)
    datepicker = datetime.datetime.strptime(datepicker, "%Y-%m-%d")
    x_axis = t.fix_x_xis(datepicker)
    p = t.dayline_one(db,"pcs","c1_pcs","p_sum",datepicker)
    q = t.dayline_one(db,"pcs","c1_pcs","q_sum",datepicker)
    y_axis = [p,q]
    return jsonify(x_axis=x_axis,y_axis=y_axis)
#--------------------------------------------------------------------------------------------------
@app.route('/get_smooth_plot')
def get_smooth_plot():
    db = conn['delta']
    datepicker = request.args.get('datepicker', type=str)
    datepicker = datetime.datetime.strptime(datepicker, "%Y-%m-%d")
    x_axis = t.fix_x_xis(datepicker)
    pcs_p = t.dayline_one(db,"acm","c1_acm3","p",datepicker)
    pv1 = t.dayline_one(db,"sim","sim_meter","p",datepicker)

    # print("pcs",pcs_p)
    # print("pv1",pv1)
    pv = []
    total = []
    for i in range(0,len(x_axis)):
        try:
            pv.append(pv1[i])
        except:
            pv.append(None)
        try:
            total.append(pv1[i]+pcs_p[i])
        except:
            total.append(None)

    y_axis = [pcs_p,pv,total]
    return jsonify(x_axis=x_axis,y_axis=y_axis)
#----------------------------------------------------------------------------------------------------
@app.route('/get_DM_plot')                                                  #added by 睿彬 3/23
def get_DM_plot():
    db = conn['delta']
    datepicker = request.args.get('datepicker', type=str)
    datepicker = datetime.datetime.strptime(datepicker, "%Y-%m-%d")
    x_axis = t.fix_x_xis(datepicker)
    pcs_p = t.dayline_one(db,"acm","c1_acm3","p",datepicker)
    sim_Load = t.dayline_one(db,"simLoad","sim_Load","p",datepicker)
    #------------------暫時使用，因為資料庫只有 2021-03-22 16:58:37 有資料-----------
    collection = db['site_control']
    DM_p_ref = collection.find_one({"ID":"c1_pcs"},{"_id":0,"time":0},sort=[( 'time', pymongo.DESCENDING )])['DM_p_ref']
    DM_flexible_percent = collection.find_one({"ID":"c1_pcs"},{"_id":0,"time":0},sort=[( 'time', pymongo.DESCENDING )])['DM_flexible_percent']
    limit_p = DM_p_ref*(1-(DM_flexible_percent/100) )
    pv = []
    total = []
    for i in range(0,len(x_axis)):
        try:
            pv.append(sim_Load[i])
        except:
            pv.append(None)
        try:
            total.append(sim_Load[i]-pcs_p[i])
        except:
            total.append(None)
    DM_p_ref = [DM_p_ref]*len(total)
    limit_p = [limit_p]*len(total)
    y_axis = [pcs_p,pv,total,DM_p_ref,limit_p]
    return jsonify(x_axis=x_axis,y_axis=y_axis)
#----------------------------------------------------------------------------------------------------
app.route('/get_stable_plot')
def get_stable_plot():
    db = conn['delta']
    datepicker = request.args.get('datepicker', type=str)
    datepicker = datetime.datetime.strptime(datepicker, "%Y-%m-%d")
    x_axis = t.fix_x_xis(datepicker)
    pcs_p = t.dayline_one(db,"pcs","c1_pcs","p_sum",datepicker)
    pv1 = t.dayline_one(db,"acm","c1_acm1","p",datepicker)
    pv2 = t.dayline_one(db,"acm","c1_acm2","p",datepicker)
    pv = []
    total = []
    for i in range(0,len(x_axis)):
        try:
            pv.append(pv1[i]+pv2[i])
        except:
            pv.append(None)
        try:
            total.append(pv1[i]+pv2[i]+pcs_p[i])
        except:
            total.append(None)

    y_axis = [pcs_p,pv,total]
    return jsonify(x_axis=x_axis,y_axis=y_axis)
#----------------------------------------------------------------------------------------------------
@app.route('/get_VQ_plot')
def get_VQ_plot():
    db = conn['delta']
    datepicker = request.args.get('datepicker', type=str)
    datepicker = datetime.datetime.strptime(datepicker, "%Y-%m-%d")
    x_axis = t.fix_x_xis(datepicker)
    pcs_q = t.dayline_one(db,"pcs","c1_pcs","q_sum",datepicker)
    v = t.dayline_one(db,"acm","c1_acm4","v",datepicker)
    y_axis = [pcs_q,v]
    return jsonify(x_axis=x_axis,y_axis=y_axis)
#----------------------------------------------------------------------------------------------------
@app.route('/get_VP_plot')
def get_VP_plot():
    db = conn['delta']
    datepicker = request.args.get('datepicker', type=str)
    datepicker = datetime.datetime.strptime(datepicker, "%Y-%m-%d")
    x_axis = t.fix_x_xis(datepicker)
    pcs_p = t.dayline_one(db,"pcs","c1_pcs","p_sum",datepicker)
    v = t.dayline_one(db,"acm","c1_acm4","v",datepicker)
    y_axis = [pcs_p,v]
    return jsonify(x_axis=x_axis,y_axis=y_axis)
#----------------------------------------------------------------------------------------------------
@app.route('/get_schedule_plot')
def get_schedule_plot():
    db = conn['delta']
    datepicker = request.args.get('datepicker', type=str)
    datepicker = datetime.datetime.strptime(datepicker, "%Y-%m-%d")
    x_axis = t.fix_x_xis(datepicker)
    p = t.dayline_one(db,"pcs","c1_pcs","p_sum",datepicker)
    q = t.dayline_one(db,"pcs","c1_pcs","q_sum",datepicker)
    y_axis = [p,q]
    return jsonify(x_axis=x_axis,y_axis=y_axis)
#----------------------------------------------------------------------------------------------------
@app.route('/get_FP_plot', methods=['GET', 'POST'])
def get_FP_plot():
    try:
        datepicker = request.args.get('datepicker', type=str)
        time_hour =  request.args.get('time_hour', type=str)
        time_min = request.args.get('time_min', type=str)
        time_sec = request.args.get('time_sec', type=str)
        sec_interval = request.args.get('time_af_sec', type=str)
        capacity = request.args.get('sys_capacity', type=int)
        db = conn['delta']
        x_axis =[]
        if ( time_hour == '請選擇時間區段'):
            datepicker = datetime.datetime.strptime(datepicker,"%Y-%m-%d")
            nexttime = datetime.datetime.now()- relativedelta(hours=1,microsecond=0)
        else:
            if( (time_min != '請選擇開始分鐘') and (time_sec != '請輸入開始秒數') and ((sec_interval != '請輸入所需的資料長度(秒)') and (sec_interval != '')) ):
                datepicker = datepicker + '-' + time_hour + ':' + time_min + ':' + time_sec
                nexttime = datetime.datetime.strptime(datepicker,"%Y-%m-%d-%H:%M:%S")
                for i in range(int(sec_interval)):
                    x_axis.append(datetime.datetime.strftime(nexttime,"%H:%M:%S.%f"))
                    nexttime  = nexttime + relativedelta(microseconds=1000000)
                p = t.user_set_secondline(db,"acm","c1_acm3","p",nexttime,interval=1,after_secs=int(sec_interval) )
                f = t.user_set_secondline(db,"acm","c1_acm3","f",nexttime,interval=1,after_secs=int(sec_interval) )
                ideal_p =t.user_set_secondline(db,"afc_ideal","c1_acm3","ideal_p",nexttime,interval=1,after_secs=int(sec_interval) )
                #pm =t.user_set_secondline(db,"pm","pm","pm",nexttime,interval=1,after_secs=int(sec_interval) )
                pm =caculate_pm(f,p,capacity=capacity) 

                pm_avg = avg_pm(pm[0]) #edit by 睿彬 3/23

                fix1 =[60.02]*3600#*2
                fix2 =[59.98]*3600#*2
                fix3 =[59.75]*3600#*2
                fix4 =[60.25]*3600#*2
                y_axis = [p,ideal_p,pm[0],f,fix1,fix2,fix3,fix4]
                # y_axis = [p,f,fix1,fix2,fix3,fix4]
                return jsonify(x_axis=x_axis,y_axis=y_axis,pm_avg=pm_avg)
            else:
                if((time_min != '請選擇開始分鐘')):    #edit by 睿彬3/26
                    datepicker = datepicker + '-' + time_hour + ':' + time_min
                    nexttime = datetime.datetime.strptime(datepicker,"%Y-%m-%d-%H:%M")
                    datepicker = nexttime + datetime.timedelta(hours=1) #資料在時間區段終點
                else:
                    datepicker = datepicker + '-' + time_hour
                    nexttime = datetime.datetime.strptime(datepicker,"%Y-%m-%d-%H")
                    datepicker = nexttime + datetime.timedelta(hours=1) #資料在時間區段終點
        #做X軸
        for i in range(int(86400*1/24)): #1個小時共3600秒 若區間為0.5sec則*2
            x_axis.append(datetime.datetime.strftime(nexttime,"%H:%M:%S.%f"))
            nexttime  = nexttime + relativedelta(microseconds=1000000)
        # for i in range(int(86400*2/24)): #兩個小時共7200秒
        #     x_axis.append(datetime.datetime.strftime(nexttime,"%H:%M:%S.%f"))
        #     nexttime  = nexttime + relativedelta(microseconds=500000)
        #做Y軸
        p = t.hourline_one(db,"acm","c1_acm3","p",nexttime,interval=1)
        f = t.hourline_one(db,"acm","c1_acm3","f",nexttime,interval=1)
        # p_p =t.hourline_one(db,"acm","c1_acm3","P_P",datepicker,interval=1)
        ideal_p =t.hourline_one(db,"afc_ideal","c1_acm3","ideal_p",nexttime,interval=1)
        #pm =t.hourline_one(db,"pm","pm","pm",datepicker,interval=1)
        
        pm =caculate_pm(f,p,capacity=capacity)
        pm_avg = avg_pm(pm[0]) #edit by 睿彬 3/23
        # ideal_p.insert(0,0)
        
        fix1 =[60.02]*3600#*2
        fix2 =[59.98]*3600#*2
        fix3 =[59.75]*3600#*2
        fix4 =[60.25]*3600#*2
        y_axis = [p,ideal_p,pm[0],f,fix1,fix2,fix3,fix4]
        # y_axis = [p,f,fix1,fix2,fix3,fix4]
        # y_axis = [p,f,[],[],[],[]]
    except (AttributeError,TypeError) as error_message:
        return jsonify(error=str(error_message),x_axis=0,y_axis=0,pm_avg=0)
    else:
        return jsonify(x_axis=x_axis,y_axis=y_axis,error=0,pm_avg=pm_avg)
#==================================================================================================
#新增AFC曲線模式(OneDay Mode) added by 睿彬 5/22
@app.route('/get_FP_plot_OneDay', methods=['GET', 'POST'])
def get_FP_plot_OneDay():
    try:
        datepicker = request.args.get('datepicker', type=str)
        datepicker = datetime.datetime.strptime(datepicker, "%Y-%m-%d") 
        capacity = request.args.get('sys_capacity', type=int)
        db = conn['delta']
        # 做y軸
        # 跟prepareplopt裡的dayline一樣
        p = plot_one_day.y_one_day_line(db=db,collection="acm",ID="c1_acm3",datatype="p",date=datepicker,interval=1)
        f = plot_one_day.y_one_day_line(db=db,collection="acm",ID="c1_acm3",datatype="f",date=datepicker,interval=1)
        # ideal_p =plot_one_day.y_one_day_line(db=db,collection="afc_ideal",ID="c1_acm3",datatype="ideal_p",date=datepicker,interval=1)
        pm =caculate_pm(f=f,p=p,capacity=capacity)
        pm_avg = avg_pm(pm[0])
        soc = plot_one_day.y_one_day_line(db=db,collection="mbms",ID="c1_mbms",datatype="mbms_soc",date=datepicker,interval=1)
        soc_goal = plot_one_day.soc_goal_line(db=db, collection='site_control',ID='c1_pcs', datatype='FP_soc_goal_percent', date=datepicker, interval=1)          
    except (AttributeError,TypeError,Exception) as e:
        return jsonify(y_axis = 0,x_axis = 0,error = str(e),pm_avg=0)
    else:
        # 做一天的x軸
        #跟prepareplopt裡的fix_x_xis一樣
        # fix1 =[60.02]*86400#*2
        # fix2 =[59.98]*86400#*2
        # fix3 =[59.75]*86400#*2
        # fix4 =[60.25]*86400#*2
        x_axis = plot_one_day.x_one_day_line(date=datepicker,interval=1)
        # y_axis = [p,pm[0],f,soc,soc_goal,fix1,fix2,fix3,fix4]
        y_axis = [p,pm[0],f,soc,soc_goal,[],[],[],[]]
        return jsonify(y_axis = y_axis,x_axis = x_axis,pm_avg = pm_avg)

#==================================================================================================
@app.route('/modeChart/<time>')      #有改動 3/24 by 睿彬 #還不能輸入容量
@login_required
def modeChartbyurl(time):
    try:
        db = conn['delta']
        x_axis =[]
        if ( len(time) >= 22 ):
            starttime = datetime.datetime.strptime(time[0:19],"%Y-%m-%d-%H:%M:%S")
            x_len = int(time[20:])
            nexttime = starttime + relativedelta(seconds=x_len)
            p = t.user_set_secondline(db,"acm","c1_acm3","p",nexttime,interval=1,after_secs=x_len )
            f = t.user_set_secondline(db,"acm","c1_acm3","f",nexttime,interval=1,after_secs=x_len )
            ideal_p =t.user_set_secondline(db,"afc_ideal","c1_acm3","ideal_p",nexttime,interval=1,after_secs=x_len )
            pm =caculate_pm(f,p)
            pm_avg = avg_pm(pm[0]) #edit by 睿彬 3/23

        else:                      #畫一小時的
            time = time[0:13]
            starttime = datetime.datetime.strptime(time,"%Y-%m-%d-%H")
            x_len = int(86400*1/24)
            nexttime = starttime + datetime.timedelta(hours=1) #資料在時間區段終點
            p = t.hourline_one(db,"acm","c1_acm3","p",nexttime,interval=1)
            f = t.hourline_one(db,"acm","c1_acm3","f",nexttime,interval=1)
            ideal_p =t.hourline_one(db,"afc_ideal","c1_acm3","ideal_p",nexttime,interval=1)
            pm =caculate_pm(f,p)
            
            pm_avg = avg_pm(pm[0]) #edit by 睿彬 3/23
            
        for i in range(x_len):
            x_axis.append(datetime.datetime.strftime(starttime,"%H:%M:%S.%f"))
            starttime  = starttime + relativedelta(microseconds=1000000)
    except (AttributeError,TypeError) as error_message:
        return render_template('modeChartbyurl.html' , data={'x': [],'y': [],'pm_avg':0,'error_message':str(error_message)})
    else:
        fix1 =[60.02]*3600#*2
        fix2 =[59.98]*3600#*2
        fix3 =[59.75]*3600#*2
        fix4 =[60.25]*3600#*2
        y_axis = [p,ideal_p,pm[0],f,fix1,fix2,fix3,fix4]
        # y_axis = [p,f,fix1,fix2,fix3,fix4]
        return render_template('modeChartbyurl.html' , data={'x': x_axis,'y': y_axis,'pm_avg':pm_avg})
#==================================================================================================
#Schedule 20210323 by柯柯#
#--------------------------------------------------------------------------------------------------
#schedule子程式1. check conflict time
# return 0: ok!, 1: time repeat, 2:time range overlapping, 3:endTime smaller than or equal to startTime
def CheckConflictTime(col, startTime, endTime):
    if startTime >= endTime:
        return 3            # endTime smaller than startTime
    try:
        data = col.find({"start_time":startTime})
        if data.count() == 0:
            if col.find({"start_time":{"$lt":startTime}, "end_time":{"$gt":startTime}}).count() + \
                col.find({"start_time":{"$lt":endTime}, "end_time":{"$gt":startTime}}).count() == 0 :
                #db.schedule.find({"start_time":endTime}).count() + db.schedule.find({"end_time":startTime}).count() == 0 :
                return 0    # ok!
            else:
                return 2    # time range overlapping
        else:    # time repeat
            return 1
    except:     #首次插入
        return 0
#--------------------------------------------------------------------------------------------------
#schedule-1
@app.route('/schedule')
def schedule():
    return render_template('schedule.html')
#--------------------------------------------------------------------------------------------------
#schedule-2
@app.route('/sechedule_pcs_control_data')
def sechedule_pcs_control_data():
    ID = request.args.get('pcs_ID', type=str)
    db = conn['delta']
    previous_data = c.current_data(db,'site_control',ID)[0]
    return jsonify(schedule_previous_data = previous_data)
#--------------------------------------------------------------------------------------------------
#schedule-3. 將排程寫入資料庫
@app.route('/schedule_set_control')
def schedule_set_control():
    ID = request.args.get('pcs_ID', type=str)                                                   #format:str
    start_time = datetime.datetime.strptime(request.args.get('start_time'), "%Y/%m/%d %H:%M")   #format:class 'datetime.datetime'
    end_time = datetime.datetime.strptime(request.args.get('end_time'), "%Y/%m/%d %H:%M")       #format:class 'datetime.datetime'
    schedule_set_data = eval(request.args.get('schedule_set_data'))                             #format:dict
    mode = eval(request.args.get('mode'))                                                       #format:int
    #--整理寫入資料
    for key in schedule_set_data.keys():
        schedule_set_data[key] = float(schedule_set_data[key])
    #--寫入資料庫
    insertStatusTable = {0:"排程成功!", 
                         1:"排程失敗：排程時間重複，請重新確認。", 
                         2:"排程失敗：排程時間範圍重疊，請重新確認。",
                         3:"排程失敗：結束時間不可小於開始時間。"}
    try:
        db = conn['delta']
        col = db.schedule
        #----確認是否可被寫入
        check_time = CheckConflictTime(col, start_time, end_time)
        if check_time == 0:
            if mode == 0:
                schedule_set_data = {"PQ_p_ref":float(0), "PQ_q_ref":0}
                col.insert_one({"ID":ID, "schedule_mode":mode, "set_data":schedule_set_data, "start_time":start_time,
                                    "end_time":end_time, "status":0})
            else:
                col.insert_one({"ID":ID, "schedule_mode":mode, "set_data":schedule_set_data, "start_time":start_time,
                                        "end_time":end_time, "status":0})
            print("Successfully updated schedule!")
        else:
            pass    #時間檢查錯誤，不寫入。
    except Exception as e:
        print("error: ", e)
    return jsonify(result = insertStatusTable[check_time])
#--------------------------------------------------------------------------------------------------
##schedule-4. 取得排程資訊
@app.route('/schedule_chart_fill')
def schedule_chart_fill():
    # 模式名稱對照表，可根據不同案場調整內容
    mode_dict = {0:"停止模式", 1:"", 2:"電網電壓調節模式", 3:"棄電改善模式",
                 4:"", 5:"頻率實功模式", 6:"實虛功控制模式", 7:"穩定實功模式",
                 8:"平滑化模式", 9:"", 11:"需量控制模式"} 

    db = conn['delta']
    if(db==None):
        return logout() 
    pcs_ID = request.args.get('pcs_ID', type=str)
    starttime = request.args.get('starttime', type=str)
    endtime = request.args.get('endtime', type=str)
    starttime = datetime.datetime.strptime(starttime,"%Y-%m-%d")
    endtime = datetime.datetime.strptime(endtime,"%Y-%m-%d")
    schedule_data = c.schedule_query(db,pcs_ID,starttime,endtime,mode_dict)
    return jsonify(schedule_data=schedule_data)  
#--------------------------------------------------------------------------------------------------
##schedule-5. 刪除排程資訊      0323
@app.route('/schedule_event_delete')
def schedule_event_delete():
    pcs_ID = request.args.get('pcs_ID', type=str)
    event_id = request.args.get('event_id', type=str)
    event_id = ObjectId(event_id)
    mode = int(request.args.get('schedule_mode', type=str))

    db = conn['delta']
    try:
        db.schedule.delete_one({"_id":event_id})
        return({"status":"success"})
    except:
        print_function("No. schedule_event_delete: "+str(event_id)+" deleted failed.", print_mode, SystemControlList)

#==================================================================================================
#Setting 20210409 by柯柯#
#--------------------------------------------------------------------------------------------------
# setting-1. 更改logo
@app.route('/set_logo')
def set_logo():
    logo_table = {1:"static/images/ntust.png",
                  2:"static/images/foxlink-logo.png",
                  3:"static/images/billion.png",
                  4:"static/images/leader.png"}
    logo_num = request.args.get('logo_num', type=int)
    status = "failed"
    try:
        copyfile(logo_table[logo_num], "static/images/logo.png")
        status = "success"
    except Exception as e:
        print(e)
    return jsonify({"status":status})
#--------------------------------------------------------------------------------------------------
#==================================================================================================

#==================================工程頁面撈資料edited by睿彬-=====================================
@app.route('/get_history_plot') 
def get_history_plot():
    db = conn[ 'school' ]
    db1 = conn['delta']
    interval = 1
    y_axis = []
    #-------------------------------接收輸入資料 ----------------------------
    datepickerstart = request.args.get('datepickerstart',type = str)
    starttime = datetime.datetime.strptime(datepickerstart, "%Y-%m-%d")
    content_list = eval( request.args.get('list',type= str) )
    #-------------------------------傳送預設資料到mongodb-------------------- 
    plot_one_day.save_pre_data(db=db,collection='pre_data',content_list=content_list)
    #-----------------------------------------------------------------------
    x_axis = plot_one_day.x_one_day_line(starttime) # 生成X軸(區間為一天)
    for content in content_list:
        if(content != []):
            data = plot_one_day.y_one_day_line(
                db=db1,
                collection=content[0],
                ID=content[1],
                datatype=content[2],
                date=starttime,
                interval=interval
            )
            y_axis.append(data)
        else:
            y_axis.append([])
    return jsonify(x_axis=x_axis,y_axis=y_axis) #edit by 睿彬
#==================================================================================================

#================================歷史曲線匯出CSV by睿彬=============================================
@app.route('/history_csv_OneDay')
def history_csv_one_day():
    try:
        db0 = conn[ 'school' ]
        db1 = conn['delta']
        data_list = []
        csvList = []
        #===第一行為時間========#
        data_tag = ['Date/Time']
        #====================#
        content_list = eval(request.args.get('list', type=str))   #contain [[col_name, device_id, prepare_data], [...], ...]
        date = request.args.get('date', type=str)
        starttime = datetime.datetime.strptime(date+' 00:00:00', "%Y-%m-%d %H:%M:%S")
        endtime = starttime + datetime.timedelta(days=1)
        Time = plot_one_day.time_interval(starttime=starttime,endtime=endtime)
        for num,content in enumerate(content_list):
            data = plot_one_day.get_data(db=db1,collection=content[0],ID=content[1],key=content[2],starttime=starttime,endtime=endtime )
            data_list.append(data)
            data_tag.append( content[0] + ' / ' + content[1] + ' / ' + content[2])
        csvList.append(data_tag)
        for i,time in enumerate(Time): 
            row = []
            row.append(time)
            for index in range(0,len(data_list)):
                row.append(data_list[index][i])
            csvList.append(row)

        si = io.StringIO()
        cw = csv.writer(si)
        cw.writerows(csvList)

        mem = io.BytesIO()
        mem.write(si.getvalue().encode('utf-8-sig'))
        mem.seek(0)
        si.close()
        #---------------用DataFrame輸出csv------------------------------
        # for i in range(0, len(data_list[0])):
        #     line = [time[i]]
        #     for j in range(0, len(data_list)):
        #         line.append(data_list[j][i])
        #     csvList.append(line)


        # dic = {
        #     "Date/Time": Time, 
        # }
        # for i,tag_data in enumerate(content_list):
        #     dic[tag_data[0]+'_'+tag_data[2]] = data_list[i]
            
        # df = pd.DataFrame(dic)
        # df.to_csv('./output.csv',index=False,encoding="utf_8_sig")
        #--------------------------------------------------------------
    except (AttributeError,TypeError,Exception) as e:
        print(e)
        return jsonify(result = 0 ,error = str(e) )
    else:
        return send_file(
        mem,
        as_attachment=True,
        attachment_filename= date+'_history.csv',
        mimetype='text/csv'
        )
#==================================================================================================
@app.route('/')
@login_required
def index():
    CurrentUser = user_list(current_user.get_id())
    return render_template('index2.html',level = int(CurrentUser['level']))       
#--------------------------------------------------------------------------------------------------
@app.route('/bess_data')
@login_required
def bess_data():
    return render_template('bess_data.html')
#--------------------------------------------------------------------------------------------------
@app.route('/acm_data')
@login_required
def acm_data():
    ID = request.args.get('ID', type=str)
    print(ID)
    return render_template('acm_data.html',ID=ID)
#--------------------------------------------------------------------------------------------------
@app.route('/load_data')
@login_required
def load_data():
    ID = request.args.get('ID', type=str)
    print(ID)
    return render_template('load_data.html',ID=ID)
#--------------------------------------------------------------------------------------------------
@app.route('/bess_control')
@login_required
def bess_control():
    return render_template('bess_control.html')
#--------------------------------------------------------------------------------------------------
@app.route('/pcs_data')
@login_required
def pcs_data():
    return render_template('pcs_data.html')
#--------------------------------------------------------------------------------------------------
@app.route('/pcs_control')
@login_required
def pcs_control():
    return render_template('pcs_control.html')
#--------------------------------------------------------------------------------------------------
@app.route('/pv_data')
@login_required
def pv_data():
    return render_template('pv_data.html')
#--------------------------------------------------------------------------------------------------
@app.route('/alarm')
@login_required
def alarm():
    return render_template('alarm.html')
#--------------------------------------------------------------------------------------------------
@app.route('/status')
@login_required
def status():
    return render_template('status.html')
#--------------------------------------------------------------------------------------------------
@app.route('/soe')
@login_required
def soe():
    return render_template('soe.html')
#--------------------------------------------------------------------------------------------------
@app.route('/modeChart')
@login_required
def modeChart():
    return render_template('modeChart.html')
#--------------------------------------------------------------------------------------------------
@app.route('/modeChart1')
@login_required
def modeChart1():
    return render_template('modeChart1.html')
#--------------------------------------------------------------------------------------------------
@app.route('/setting')   #更改網頁logo，added by 柯柯0409
@login_required
def setting():
    return render_template('setting.html')
#--------------------------------------------------------------------------------------------------
@app.route('/history') # 新增工程頁面 by 睿彬
@login_required
def history():
    db = conn['school'] 
    collection = db['pre_data']
    pre_data = collection.find_one()
    # print(pre_data)
    return render_template('history.html',pre_data=pre_data )
#--------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0',port='4000')

