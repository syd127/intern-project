# Import the required modules
import requests
import json
from bs4 import BeautifulSoup
'''
金門 學號帳號
Solar Radiation
website: https://api.solcast.com.au/world_radiation/estimated_actuals?latitude=24.208871&longitude=120.494658&capacity=5&tilt=23&azimuth=180&hours=168&format=json8&api_key=5HT7S_Gum5Qf4XQybnJs5MH-3tf_gxxX
API KEY: &api_key=5HT7S_Gum5Qf4XQybnJs5MH-3tf_gxxX

PV Power
website: https://api.solcast.com.au/world_pv_power/estimated_actuals?latitude=24.208871&longitude=120.494658&capacity=5&tilt=23&azimuth=180&hours=168&format=json&api_key=5HT7S_Gum5Qf4XQybnJs5MH-3tf_gxxX
API KEY: &api_key=5HT7S_Gum5Qf4XQybnJs5MH-3tf_gxxX
 '''
  
  
#　response = requests.get(website&api_key)
response = requests.get('https://api.solcast.com.au/world_pv_power/estimated_actuals?latitude=24.208871&longitude=120.494658&capacity=5&tilt=23&azimuth=180&hours=168&format=json&api_key=5HT7S_Gum5Qf4XQybnJs5MH-3tf_gxxX')
print(response.status_code)# check connection 
print("estimated_actuals", response.json())# change it to json file 
print(type(response.json()))# check type 





