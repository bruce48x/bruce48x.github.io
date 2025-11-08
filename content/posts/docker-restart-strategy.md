---
title: docker 的 restart 策略
date: '2022-11-12T15:34:25+08:00'
slug: docker-restart-strategy
draft: true
author: bruce
---

docker 的 restart 策略有3种

- on-failure
- unless-stopped
- always

看文字描述总是不够清晰

我做了测试，列出以下表格，明确他们之间的区别

|---|
|-----|
|  | app 正常退出 |  | no |  | yes |  | yes |  |
|  | app 异常退出 |  | yes |  | yes |  | yes |  |
|  | 手动 stop |  | no |  | no |  | no |  |
|  | docker daemon 重启 (app running) |  | yes |  | yes |  | yes |  |
|  | docker daemon 重启 (app stopped) |  | yes |  | no |  | yes |  |
|  | 机器重启 (app running) |  | yes |  | yes |  | yes |  |
|  | 机器重启 (app 手动 stop) |  | yes |  | no |  | yes |  |

可能比较需要关注的是 docker 或机器在重启后，容器会不会重启

一般情况下设置 restart 为 unless-stopped 即可。