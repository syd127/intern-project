import requests
import json
from bs4 import BeautifulSoup


#　response = requests.get('https://api.solcast.com.au/world_radiation/estimated_actuals?latitude=-33.86882&longitude=151.209295&hours=168​&api_key=d6bCVBojFZoURiPMkzv-zKfkUrsPIiZb')\
# response = requests.get('https://api.solcast.com.au/world_pv_power/estimated_actuals?latitude=-33.86882&longitude=151.209295&capacity=5&tilt=30&azimuth=0&hours=168&api_key=5HT7S_Gum5Qf4XQybnJs5MH-3tf_gxxX')
# print(response.status_code)                               &api_key=5HT7S_Gum5Qf4XQybnJs5MH-3tf_gxxX
response = requests.get('https://api.solcast.com.au/world_radiation/estimated_actuals?latitude=-33.86882&longitude=151.209295&hours=168&format=json&api_key=5HT7S_Gum5Qf4XQybnJs5MH-3tf_gxxX')

# response = requests.get('https://www.flickr.com/services/rest/?method=flickr.test.echo&format=json&nojsoncallback=1&api_key=46b92b9b29613407e51c86aa4c047fea')
# response = requests.get('https://books.toscrape.com/catalogue/page-1.html')

print(response.status_code)
# soup = BeautifulSoup(response.text, "html.parser")
#  print(soup.prettify())  #輸出排版後的HTML內容

# print('',)
# # print("response ",response)

# print("response ",response.text )
# print('',)
                #他回傳的是一個網頁不是資料 ，這裡需要的東西應該是想辦法把資料從網頁擷取出來 
# lm_json = requests.get(response).json()
# soup = BeautifulSoup(lm_json["content_html"])
# jsonData_sort = json.dumps(soup, indent=4)
# print(jsonData_sort)
# print('soup',soup)
                                                                           
                         



