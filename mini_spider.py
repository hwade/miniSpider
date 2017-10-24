# -*- coding: utf-8 -*-

"""Mini spider 0.1.0
Usage: 
  mini_spider.py [-s]
  mini_spider.py -c  <FILE>
  mini_spider.py -v | --version
  mini_spider.py -h | --help

Arguments:
  -c --config <FILE>   Load config file.
  -h --help            Show this screen.
  -v --version	       Show version.

Options:
  -s --silent          Silent mode.
""" 

from util import Config
from docopt import docopt
from spider import Spider


if __name__ == '__main__':
	# 读取命令行参数
	args = docopt(__doc__, version='Mini spider 0.1.0')
	# 读取配置文件参数
	conf = Config(args['--config'])	
	# 合并两类参数
	conf.merge(args)	
	
	# 初始化爬虫
	spider = Spider(
				name = 'Spider',
				url_list_file = conf.get('url_list_file'),
				output_path = conf.get('output_directory'),
				interval = conf.get('crawl_interval'),
				timeout = conf.get('crawl_timeout'),
				silent = conf.get('--silent')
			 )
	# 递归爬取网页
	spider.crawlDeeply(conf.get('thread_count'), conf.get('target_url'), conf.get('max_depth'))

