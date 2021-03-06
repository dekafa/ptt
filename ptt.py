# 05/24 Dekafa ptt爬蟲
import os
import datetime
import time
import random
import re
import json
import pandas as pd
import requests as rq
from bs4 import BeautifulSoup


# 爬蟲目標看板名稱(Ptt批踢踢)
# boardName = ''
# 要爬幾頁資料
# page = 

def pttdata(boardName, page):


# 儲存csv資料夾名稱
    filename = 'ptt-' + boardName


# 設定header與cookie
    my_headers = {'cookie': 'over18=1;', # Ptt網站 18歲的認證
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36'}

# 設定結束頁數
# 目前最新網頁頁數
    url = 'https://www.ptt.cc/bbs/' + boardName + '/index.html'
    res = rq.get(url, headers=my_headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    endPage = int(re.findall('index(\d+).html', soup.select('a.btn.wide')[1].get('href'))[0]) + 1

# 設定起始頁數(從資料庫取)
    startPage = endPage - int(page)

# 建立 Pandas DataFrame (先建立欄位 並排序欄位順序)
    df1 = pd.DataFrame(columns=["id", "board", "authors", "time", "url"])
    df2 = pd.DataFrame(columns=["title"])
    df3 = pd.DataFrame(columns=["content"])


    # 爬取 Ptt 第一層的資訊
    for page_number in range(startPage, endPage+1):
        print('目前正在爬取第 ', page_number, '個頁面 進度: ', page_number, ' / ', endPage)
        url1 = 'https://www.ptt.cc/bbs/' + boardName + '/index%s.html' % (page_number)
        res1 = rq.get(url1, headers=my_headers) # 使用requests的get方法把網頁內容載下來(第一層)


        # 轉為soup格式
        soup1 = BeautifulSoup(res1.text, 'html.parser')  # 使用 html.parser 作為解析器

        # -----------------------------取得Ptt第一層基本資訊----------------------------- #
        # 使用find_all()找出所有<div class="r-ent">區塊  並逐一訪問  取得資料
        r_ents = soup1.find_all("div", "r-ent")
        for r in r_ents:
            titles = r.find("div", "title")                    # 取得 Ptt標題 資訊
            # dates = r.find("div", "meta").find("div", "date")  # 取得 日期 資訊


            s2 = pd.Series([titles.text],
                        index=["title"])
            df2 = df2.append(s2, ignore_index=True) # df2 DataFrame中添加s2的數據  


    # 刪除文章標題內有'刪除'字眼的資料
            df2 = df2[ ~ df2['title'].str.contains('刪除') ]


        time.sleep(random.randint(0, 1))  # 怕資料庫會ban掉 因此休息0-1秒之間
        # -----------------------------取得Ptt第一層基本資訊----------------------------- #

        # 爬取 Ptt 第二層的資訊
        all_titles = soup1.select("div.title") # 爬取該頁所有的標題

    # 如果文章標題內有刪除 則不進迴圈 不取資料
        n = '刪除'
        for item in all_titles:
            if n in str(item):
                # print('123')
                continue
            else:
                a_item = item.select_one("a") # 爬取到該頁的所有連結    
                url2 = 'https://www.ptt.cc' + a_item.get('href')  # url2 用來爬取每一頁的所有文章連結
                print(f"正在處理的網址：{url2}")
                res2 = rq.get(url2, headers=my_headers) # 使用requests的get方法把網頁內容載下來(第二層)
                
                res404 = '<Response [404]>'
            # 如果有標題有網址但為404  則給所有值為空值
                if str(res2) == res404:
                    s1 = pd.Series([' ', ' ', ' ', '0000-00-00 00:00:00', ' '],
                                   index=["id", "authors", "board", "time", "url"])
                    df1 = df1.append(s1, ignore_index=True)            
                    s3 = pd.Series(' ',  index=["content"])
                    df3 = df3.append(s3, ignore_index=True) 
                    time.sleep(random.randint(3, 6))      
                    
                else:
                    # 轉為soup格式
                    soup2 = BeautifulSoup(res2.text, 'html.parser') # 使用 html.parser 作為解析器

                    # 取得 文章ID 資訊 (使用正規表達式 找出規則 並爬取到「文章ID」資訊)
                    id = re.findall(r'(\w+\.\w+\.\w+\.\w+).html', url2)[0]

                    # -------------------------------------取得文章資訊------------------------------------- #
                    main_content = soup2.select("#main-content")
                    for m in main_content:
                        infosTag = m.find_all("span", class_="article-meta-tag")
                        infos = m.find_all("span", class_="article-meta-value")

                        # 例外處理 (特殊情況 因為其中有幾篇文章 沒有作者...等資訊)
                        matchSite = [i for i, e in enumerate(infosTag) if e.text == '作者']
                        authors = infos[matchSite[0]].text if matchSite else None           # 取得 文章作者 資訊
                        matchSite = [i for i, e in enumerate(infosTag) if e.text == '看板']
                        board = infos[matchSite[0]].text if matchSite else None         # 取得 看板名稱 資訊
                        matchSite = [i for i, e in enumerate(infosTag) if e.text == '時間']
                        time_list = infos[matchSite[0]].text if matchSite else None         # 取得 文章時間 資訊

                        try:
                            if time_list:
                                time_list = datetime.datetime.strptime(time_list, '%a %b %d %H:%M:%S %Y')
                        except Exception as e:
                            time_list = None

                        s1 = pd.Series([id, authors, board, time_list, url2],
                                    index=["id", "authors", "board", "time", "url"])
                        df1 = df1.append(s1, ignore_index=True) # df1 DataFrame中添加s1的數據
                    time.sleep(random.randint(0, 1)) # 休息0-1秒之間
                    # -------------------------------------取得文章資訊------------------------------------- #

                    # -----------------------------------------文章內容----------------------------------------- #
                    # 先使用find() 是因為網頁中所得到的資料為一區塊
                    contents = soup2.find("div", id="main-content")

                    # 單用find_all()很難找到目標  因為文章內容and基本資訊...等都是混在一起  因此使用extract()把不要的東西去掉
                    msg1 = contents.find_all("div", class_="article-metaline")
                    for s in msg1:
                        s.extract()   # 去掉  作者 標題 時間

                    msg2 = contents.find_all("div", class_="article-metaline-right")
                    for s in msg2:
                        s.extract()   # 去掉  看板

                    # 取得文章內容
                    s3 = pd.Series([contents.text.split('--')[0]],  # split('--')[0] 去掉留言
                                index=["content"])
                    df3 = df3.append(s3, ignore_index=True) # df3 DataFrame中添加s3的數據
                    time.sleep(random.randint(0, 1)) # 休息0-1秒之間
                # -----------------------------------------文章內容----------------------------------------- #
            
         # df1.df2.df3 DataFrame合併  並匯出成csv檔
         dfs = [df1, df2, df3]
         mainTextDf = pd.concat(dfs, axis=1).reset_index(drop=True)
         mainTextDf.insert(0, 'page', page_number)
         mainTextDf.to_csv(filename + str(startPage - endPage) + ".csv",encoding="utf-8-sig", index=False, sep=',')
         print('目前正在儲存 ', str(page_number), ' .csv資料')

                # 清空資料
         df1 = pd.DataFrame(columns=["id", "board", "authors", "time", "url"])
         df2 = pd.DataFrame(columns=["title"])
         df3 = pd.DataFrame(columns=["content"])

if __name__ == '__main__':
    pttdata(boardName, page)
