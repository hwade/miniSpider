# -*- coding: utf-8 -*-

import os
import re
import time 
import chardet
import urllib2
import logging
import cookielib
import traceback
from util import Log
from Queue import Queue
from bs4 import BeautifulSoup
from threading import Thread, Lock

class UrlNode(object):
	''' Url Node '''
	def __init__(self, url, depth=0):
		self.url = url
		self.depth = depth

	@property
	def fileName(self):
		''' transfer ulr to file name '''
		# 提取第一个斜杠后面的部分，即url的路径，为文件命名
		name = re.findall(r'(https?:\/\/[a-z0-9\-\.]+\/)?([^\/].*)', self.url)[0][1]
		return name.replace('/','_')

class Spider(object):
	''' Spider '''
	def __init__(self, name = 'Spider', url_list_file = './urls', output_path='./output', 
					interval=1, timeout=1, silent=False):
		'''
		@name: string, 定向爬虫的名字
		@url_list_file: string, 种子文件
		@output_path: string, 输出文件路径
		@interval: int, 爬取间隔
		@timeout: int, 请求超时
		@silent: bool, 是否为静默打印
		'''
		# 设置保存爬取页面的coolie值（非必要）
		cj = cookielib.LWPCookieJar()
		cookie_support = urllib2.HTTPCookieProcessor(cj) 
		self.opener = urllib2.build_opener(cookie_support, urllib2.HTTPHandler)
		urllib2.install_opener(self.opener)

		# 设置请求头部（非必要）
		self.headers = {
			'Content-Type': 'application/x-www-form-urlencoded',
			'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.89 Safari/537.36'
		}

		self.url_list_file = url_list_file
		self.output_path = output_path
		self.interval = interval
		self.timeout = timeout
		
		level = 'INFO' if silent else 'DEBUG'
		self.log = Log(name, level, 'spider.log', 'a')

		# 定义一个多线程共享队列，存放需要加载的url
		self.queue = Queue()

		# 存放非重复url集合
		self.url_set = set()

		# 定义多线程访问锁
		self.lock = Lock()

		# 匹配根域名
		self.base_pattern = r'^(https?:\/\/[a-z0-9\-\.]+)[\/\?]?'

		if not os.path.exists(self.url_list_file):	
			# 种子文件不存在
			self.log.error('%s dose not exist. Exit program !'%(self.url_list_file))
			os._exit(0)
		if not os.path.exists(self.output_path):
			# 输出文件目录不存在
			self.log.info('Create new directory %s'%(self.output_path))
			os.makedirs(self.output_path)
	'''
	def __decodeHtml__(self, html):
		"""
		Decode Html
		@html: string, 原生html内容
		return: 返回解码后的html内容
		"""
		try:
			encoding = chardet.detect(html)['encoding']
			if encoding == 'GB2312':
				encoding = 'GBK'
			else:
				encoding = 'utf-8'
			return html.decode(encoding, 'ignore')
		except Exception, e:
			self.log.error("Decode error: %s.", e.message)
			return None
	'''

	def __request__(self, url, threadID=-1, data=None):
		'''
		Request URL
		@url: string, 指定抓取的url
		@data: object, POST方法发送的数据
		'''
		try:
			req = urllib2.Request(url, data, self.headers)
			res = urllib2.urlopen(req, timeout=self.timeout).read()
			self.log.debug('Thread-%d Get %s'%(threadID, url))
			return res
		except Exception, e:
			self.log.error('Thread-%d in __requests__: %s %s'%(threadID, e.message, url))
			return None
			
	def download(self, url_node, threadID):
		'''
		Download Url
		@url_node: object, url节点类对象，该url是已经匹配通过的
		return: 若成功下载则返回数据
		'''
		if not url_node.url in self.url_set:
			# 若该链接匹配，且该链接未被下载，则下载并保存该页面到磁盘		
			html = self.__request__(url_node.url, threadID=threadID)
			
			# 添加该链接到已下载的链接集合
			self.lock.acquire()
			self.url_set.add(url_node.url)
			self.lock.release()
			
			return html
		return None

	def getUrlsFromHtml(self, html, url, pattern):
		''' 
		Get url from html 
		@html: string, 解码后的html
		@url: string, 当前链接url
		@pattern: string, 匹配的url模式
		return: list, urls
		'''

		# 提取当前链接的根域名
		base_url = re.match(self.base_pattern, url).groups()[0]

		urls = []
		tag_obj = []
		tag_list = ['a', 'img', 'script', 'style']
		for tag in tag_list:
			# 找到所有a, img, script, style标签，他们都是用来存放链接的
			tag_obj.extend(BeautifulSoup(html).find_all(tag))

		def completeUrl(url):
			''' Complete Url Function'''
			if re.match(pattern, url):
				# 匹配到该链接
				if re.match(self.base_pattern, url):
					# 匹配到的链接完整
					return url
				elif url.startswith('//'):
					# 该链接不完整，缺少http/https协议头部
					return base_url.split('//')[0] + url
				else:
					# 该链接不完整，需要添加当前页面的根域名
					return os.path.join(base_url, url)
			return None

		for tag in tag_obj: 
			if 'href' in tag.attrs:
				url = tag.attrs.get('href')
				url = completeUrl(url)
				if url != None:
					urls.append(url)	
			if 'src' in tag.attrs:
				url = tag.attrs.get('src')
				url = completeUrl(url)
				if url != None:
					urls.append(url)

		return	urls

	def crawlThread(self, pattern, threadID):
		'''
		Crawler Thread
		@pattern: object, 提取目标内容的正则表达式
		'''
		self.log.info("Thread-%d start."%threadID)
		while True:
			try:
				url_node = self.queue.get(block=True, timeout=self.timeout)
			except Exception, e:
				self.log.info("Thread-%d done."%threadID)
				break

			# 向队列发送完成信号，让queue.join()时能判断出队列是否清空
			self.queue.task_done()

			try:
				# 下载链接
				html = self.download(url_node, threadID)
				
				# 链接匹配
				if re.match(pattern, url_node.url) and html != None:
					with open(os.path.join(self.output_path, url_node.fileName), 'w') as fp:
						fp.write(html)

				if html == None or url_node.depth <= 0:
					# 当返回的页面为空、请求出错、节点深度为0时，不做进一步处理
					continue
				
				urls = self.getUrlsFromHtml(html, url_node.url, pattern)
				for url in urls:
					if not url in self.url_set:
						# 将未下载过的url加入到队列中
						self.queue.put(UrlNode(url, url_node.depth-1))
				
				time.sleep(self.interval)
			except Exception, e:
				self.log.error('Thread-%d %s:\n%s'%(threadID, e.message, traceback.format_exc()))

	def crawlDeeply(self, thread_num=1, pattern=r'.*.(htm|html)$', max_depth=0):
		'''
		Spider multiple Thread runner
		为了使多线程爬虫更加灵活，同一个对象可同时爬取不同的pattern，pattern和thread不设为成员属性
		@thread_num: int, 线程数
		@pattern: string, 匹配的url模式
		@max_depth: int, 爬取的最大深度
		'''
		try:
			start_time = time.time()

			# 读取种子链接文件
			with open(self.url_list_file, 'r') as f:
				base_seeds = [url.strip('\n') for url in f.readlines()]
				for base_url in base_seeds:
					self.queue.put(UrlNode(url=base_url, depth=max_depth))

			threads = []
			for t in range(thread_num):
				# 创建多个线程
				thread = Thread(target=self.crawlThread, args=(pattern, t,))
				threads.append(thread)

			for thread in threads:
				# 启动线程，启动前将线程声明为守护线程，可以让父线程继续执行
				thread.setDaemon(True)
				thread.start()
			
			for t in range(len(threads)):
				# 保证父线程等待子线程结束，否则子线程会因父线程结束而被提前终止
				threads[t].join()

			self.queue.join()
			self.log.info('All Thread end.')
			self.log.info('Total link num: %d'%len(self.url_set))
			self.log.info('Cost time: %.4fs'%(time.time() - start_time))
		except Exception, e:
			self.log.error('%s: %s'%(e.message,traceback.format_exc()))
	
