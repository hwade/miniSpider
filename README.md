# Mini Spider v0.1.0

## 文件结构

```
|-mini_spider.py: 执行模块，读取命令行参数、读取本地文件配置、执行爬取操作
|-util.py: 工具模块，提供读取配置工具和日志工具
|-spider.py: 爬虫模块，提供递归爬取的方法
|-spider.conf: 配置文件，用来设置爬虫的参数
|-spider.log: 日志文件，默认的日志文件，初始为不存在，运行后自动创建
|-package.sh: 包管理文件，提供下载第三方包下载入口
|-README.md: 说明文件，
|-urls: 种子文件，提供种子链接
|-output: 页面文件存储目录，初始为不存在，运行后自动创建
    |-.*.(htm|html): 页面文件，匹配到的页面
```

## 使用说明

&emsp;克隆这个项目后，先加载依赖的包
```
bash package.sh
```

&emsp;查看帮助
```
python mini_spider.py -h
```

&emsp;查看版本
```
python mini_spider.py -v
```

&emsp;指定配置文件，若未指定配置文件则会使用默认的配置文件spider.conf
```
python mini_spider.py -c spider.conf
```

