import requests
from selenium import webdriver
from bs4 import BeautifulSoup
import re
import os
import pymongo
import time
from multiprocessing.pool import Pool


# databse config
client = pymongo.MongoClient('localhost', 27017)
porn = client['porn']
details = porn['details']
urls = porn['urls']
details.create_index('url')
urls.create_index('url')


def updatedata(data):
    if data:
        if porn['details'].update({'url': data['url']}, {'$set': data}, True):
            print('===============================================\n')
            print('更新成功,目前文档数:{}\t\n'.format(porn['details'].find().count()))
            print('===============================================\n')
            print('数据展示:\n\n', data)
            return True
        else:
            print('数据不存在,无法存储到数据库,请检查是否匹配成功')


def downloadspider():
    list_num = [1, 2, 3, 4, 5]
    count = 0
    for item in details.find(no_cursor_timeout=True):
        robot = "E:/img/"
        for item_img, n in zip(item['picture'], list_num):
            path_img = robot + str(item['title']) + '-' + str(n) + '.jpg'
            html = requests.get(item_img)
            time.sleep(1)
            html.raise_for_status()
            html.encoding = html.apparent_encoding
            if not os.path.exists(robot):
                os.makedirs(robot)
            if not os.path.exists(path_img):
                count += 1
                print('正在下载{0}张图片:\t{1}'.format(count, item['title']))
                with open(path_img, 'wb') as i:
                    i.write(html.content)

        for item_file in item['torrent']:
            path_file = robot + str(item['title']) + '.torrent'
            htmls = requests.get(item_file)
            time.sleep(1)
            htmls.raise_for_status()
            htmls.encoding = htmls.apparent_encoding
            if not os.path.exists(path_file):
                print('正在下载{}种子'.format(item['title']))
                with open(path_file, 'wb') as f:
                    f.write(htmls.content)


# 反爬方法:获取源代码
def browser(url):
    prefs = {
        'profile.default_content_setting_values': {
            'images': 2
        }
    }
    options = webdriver.ChromeOptions()
    options.add_experimental_option('prefs', prefs)
    browser = webdriver.Chrome(chrome_options=options)
    browser.get(url)
    response = requests.get(url)
    if response.status_code == 200:
        source = browser.page_source
        browser.close()
    return source


# 获得一个类型下(比如说步兵)的所有页面的URL队列集
def basic_urls(url_):
    links = []
    html = browser(url_)
    content = BeautifulSoup(html, 'lxml')
    link = content.select('#fd_page_bottom > div > a.last')
    for item in link:
        page = int(item.get('href').split('-')[2].split('.')[0])
        cate = int(item.get('href').split('-')[1])
        for its in range(1, page):
            link = 'http://thz2.com/forum-{0}-{1}.html'.format(cate, its)
            links.append(link)
    return links


# 获得一个页面下的所有资讯的URL队列集
def pornUrl(urls):
    num = int(urls.split('-')[2].split('.')[0])
    html = browser(urls)
    response = BeautifulSoup(html, 'lxml')
    link_tb = response.find_all('tbody')
    pattern = re.compile(r'\w+thread_(\d+)')
    for item in link_tb:
        if re.search(pattern, str(item.get('id'))):
            result_all = re.search(pattern, str(item.get('id')))
            result = int(result_all.group(1))
            domain = 'http://taohuabt.cc/thread-{}-1-{}.html'.format(result, num)
            data = {
                'url': domain
            }
            updatedata(data)


# 获得一个资讯下所有的图片加种子的URL队列
def parse(url_next):
    pictures = []
    torrent = []
    pagecontents = browser(url_next)
    responses = BeautifulSoup(pagecontents, 'lxml')
    try:
        indexTitle = 'Taohuazu_桃花族 -  thz.la'
        title = responses.findAll('title')[0].get_text().replace(indexTitle, '')
        torrents = responses.select('p.attnm > a')
        _img = '^aimg_.*'
        for pic in responses.find_all(id=re.compile(_img)):
            if pic.get('file'):
                pic_url = pic.get('file')
                pictures.append(pic_url)
        for _file in torrents:
            bt = 'http://taohuabt.cc/forum.php?mod=attachment&'
            bt_url = bt + _file.get('href').split('?')[1]
            torrent.append(bt_url)
        data = {
            'title': title,
            'url': url_next,
            'picture': pictures,
            'torrent': torrent
        }
        updatedata(data)
    except IndexError:
        pass


def spider(cate_url):
    all_links = basic_urls(cate_url)
    pool = Pool(5)
    pool.map(pornUrl, all_links)
    time.sleep(10)
    if urls.find():
        for item in urls.find(no_cursor_timeout=True):
            parse(item['url'])


def Taohuazu():
    # 可自行添加属于该网站下的分类:
    as_wuma = 'http://taohuabt.cc/forum-181-1.html'
    as_youma = 'http://taohuabt.cc/forum-220-1.html'
    us_youma = 'http://taohuabt.cc/forum-182-1.html'
    print('===============================================\n')
    print('选项1:亚洲无码\n')
    print('选项2:亚洲有码\n')
    print('选项3:欧洲无码\n')
    print('选项4:下载图片和种子\n')
    print('选项5:退出\n')
    print('===============================================\n')
    cates = int(input('请输入你要爬取的类型:\n'))
    print('===============================================\n')
    if cates == 1:
        print('正在爬取亚洲无码')
        spider(as_wuma)
        print('完毕,仅供娱乐')
    elif cates == 2:
        print('正在爬取亚洲有码')
        spider(as_youma)
        print('完毕,仅供娱乐')
    elif cates == 3:
        print('正在爬取欧洲无码')
        spider(us_youma)
        print('完毕,仅供娱乐')
    elif cates == 4:
        downloadspider()
    elif cates == 5:
        for i in range(1, 100):
            print('\t\t苦海无涯,回头是岸,施主!善哉善哉')
            print('\n')
        print('\t\t皈依我佛\t\t')


if __name__ == '__main__':
    Taohuazu()
