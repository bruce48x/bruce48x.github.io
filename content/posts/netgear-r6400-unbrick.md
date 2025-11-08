---
title: 网件 r6400 变砖
date: '2022-11-12T15:41:52+08:00'
slug: netgear-r6400-unbrick
draft: false
author: bruce
---

本篇记录一次r6400变砖后的救机过程 之前刷机玩，刷错固件，导致路由变砖 一度以为没救了 实际是因为搜索的质量不高，没有按照正确的做法来操作 只要按照 [nmrpflash](https://github.com/jclehner/nmrpflash) 所教的方法来操作，救砖是很轻松的，而且不需要别的工具，只要一根网线把路由器跟电脑连起来就可以

准备的软件：

1. windows 系统（其实 Mac 和 Linux 都是可以的，由于我是在 win10 上操作，所以这里列出的是 windows）
2. nmrpflash.exe [下载](https://github.com/jclehner/nmrpflash/releases/tag/v0.9.16)
3. Npcap [下载](https://npcap.com/dist/npcap-1.60.exe)
4. R6400 的固件 [下载](https://www.netgear.com/support/product/r6400.aspx#Firmware%20Version%201.0.1.76)

操作步骤

1. 安装 Npcap
2. 用网线连接路由器和你的电脑，路由器的部分连接在1号lan口
3. 把 nmrpflash.exe 和固件文件放到 D 盘根目录下（其实哪个盘都可以，我这里按自己的操作过程来说明）
4. 以管理员权限运行 cmd，输入命令 `D:` 进入D盘
5. 在 cmd 中输入命令 `nmrpflash.exe -L`，会列出当前路由器的列表 类似这样的结果 `eth10      0.0.0.0      ca:fe:ba:be:45:67`
6. 把路由器关机
7. 输入命令 `nmrpflash.exe -i eth10 -f <固件文件名>`会看到 `Waiting for Ethernet connection.` 这个提示
8. 把路由器开机 等待运行结束，当看到最后有这么一句 `Reboot your device now`就说明成功了 
```txt
  Advertising NMRP server on eth2 ... /
  Received configuration request from fe:ed:1b:ad:f0:0d
  Sending configuration: 10.164.183.252/24
  Received upload request: filename 'firmware'.
  Uploading EX2700-V1.0.1.8.img ... OK (3539077 b)
  Waiting for remote to respond.
  Received keep-alive request (11).
  Remote finished. Closing connection.
  Reboot your device now.
```
  
  此时只要重启路由器，就完成整个过程 连接上去，根据向导的提示，重新进行网络设置吧