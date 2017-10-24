# -*- coding: utf-8 -*-

import os 
import logging
from ConfigParser import ConfigParser

class Log(logging.Logger):
	''' Log tool for printing message to console and log flie '''
	def __init__(self, name, level='INFO', fileName='myapp.log', fileMode='a'):
		'''
		@name: string, logger name
		@level: string, console level
		'''
		# 自定义一个可定向输出到终端和日志文件的Logger
		logging.Logger.__init__(self, name, logging.DEBUG)

		# 定义文件日志处理
		fileFormat = logging.Formatter('%(levelname)-7s %(asctime)s %(filename)-12s [line: %(lineno)d] %(message)s', 
									   '%y-%m-%d %H:%M:%S')
		fileHdlr = logging.FileHandler(fileName, fileMode)
		fileHdlr.setFormatter(fileFormat)
		self.addHandler(fileHdlr)

		# 定义终端输出处理
		consoleformat = logging.Formatter('%(levelname)-7s %(name)-7s [line: %(lineno)d]: %(message)s')
		consoleHdlr = logging.StreamHandler()
		consoleHdlr.setLevel(logging._checkLevel(level))
		consoleHdlr.setFormatter(consoleformat)
		self.addHandler(consoleHdlr)

class Config(object):
	''' Config Parser '''
	def __init__(self, fileName = None):
		
		self.log = Log('Config', 'INFO', 'spider.log', 'a')
		if fileName == None:
			self.log.info('Use default config file ./spider.conf')
			fileName = 'spider.conf'
		if not os.path.exists(fileName):
			self.log.info('Use default config file ./spider.conf')
			fileName = 'spider.conf'
		self.config = ConfigParser()
		self.config.read(fileName)
		self.args = dict((key, True if value is None else value)
						  for key, value in self.config.items('spider'))

	def get(self, key):
		try:
			if str(self.args[key]).isdigit():
				return int(self.args[key])
			return self.args[key]
		except Exception, e:		
			self.log.warning('Key %s dose not exist! %s'%(key, e.message))
			return None

	def merge(self, args):
		"""
		  Merge two dictionaries.
		  Values that evaluate to true take priority over falsy values.
		  `dict_1` takes priority over `dict_2`.
		"""
		self.args = dict((str(key), self.args.get(key) or args.get(key))
						   for key in set(args) | set(self.args))
	
