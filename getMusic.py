import requests
from bs4 import BeautifulSoup
import re
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import random

base_url = 'http://www.22a5.com/singerlist/huayu/index/index/index.html'
# headers = {
#     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
# }
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': 'http://www.22a5.com/singerlist/huayu/index/index/index.html',
    'Origin': 'http://www.22a5.com',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}
service = Service(executable_path='D:\chrome\chromedriver-win64\chromedriver.exe')
driver = webdriver.Chrome(service=service)
save_path = "downloads"
os.makedirs(save_path, exist_ok=True)

response = requests.get(base_url, headers=headers)

# 检查是否请求成功
if response.status_code == 200:
    print("Successfully fetched the singer list page!")
    soup = BeautifulSoup(response.text, 'html.parser')  # 解析 HTML 内容
    singer_links = soup.find_all('a', href=True)  # 找到所有歌手链接的 <a> 标签
    
    # 遍历所有链接，获取每个歌手的页面链接
    for link in singer_links:
        singer_url = link['href']  # 歌手页面的相对 URL

        if "/singer/" in singer_url:  # 过滤出只包含歌手页面链接（比如 "/singer/xxx.html" 的链接）
            singer_name = link.get_text(strip=True)

            if not singer_url or not singer_name:  # 跳过没有 href 或歌手名称为空的链接
                continue
            
            full_singer_url = f"http://www.22a5.com{singer_url}"  # 拼接完整的 URL
            print(f"Fetching songs for {singer_name} from {full_singer_url}")  # 打印每个歌手的名称和页面链接

            # 获取该歌手页面的所有歌曲
            response_singer = requests.get(full_singer_url, headers=headers)            
            if response_singer.status_code == 200:
                singer_soup = BeautifulSoup(response_singer.text, 'html.parser')
                song_list = singer_soup.find('div', class_='play_list')
                
                if song_list:  # 确保找到了歌曲列表部分
                    song_links = song_list.find_all('a', href=True)
                    for song in song_links:
                        song_url = song['href']
                        match = re.search(r'《(.*?)》', song.get_text())
                        if not match:
                            continue
                        song_name = match.group(1)

                        if "/mp3/" in song_url:  # 过滤出歌曲链接（例如 `/mp3/admgc.html`）
                            full_song_url = f"http://www.22a5.com{song_url}"
                            print(f"Found song: {song_name} at {full_song_url}")

                            driver.get(full_song_url)
                            
                            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, 'audio')))
                            time.sleep(3)  # 确保音频元素已经完全加载
                            page_source = driver.page_source # 获取页面的HTML
                            song_soup = BeautifulSoup(page_source, 'html.parser')
                            
                            audio_tag = driver.find_element(By.TAG_NAME, 'audio')
                            print(audio_tag)

                            audio_url = audio_tag.get_attribute('src')
                            print(f"音频文件的URL: {audio_url}")
                            
                            file_name = os.path.join(save_path, f'{singer_name}-{song_name}.mp3')
                            response_song = requests.get(audio_url, stream=True)
                            
                            if response_song.status_code == 200:
                                with open(file_name, 'wb') as f:
                                    for chunk in response_song.iter_content(chunk_size=1024):
                                        if chunk:
                                            f.write(chunk)
                                print("MP3 downloaded successfully!")
                            else:
                                print("Failed to download MP3.")

                            wait_time = random.uniform(1, 3)
                            print(f"Waiting for {wait_time:.2f} seconds before downloading the next song...")
                            time.sleep(wait_time)

                else:
                    print("No song list found on this page.")

            else:
                print(f"Failed to fetch singer's page for {singer_name}")
else:
    print(f"Failed to retrieve the singer list page. Status code: {response.status_code}")
