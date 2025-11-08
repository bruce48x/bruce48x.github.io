---
title: 让 pinus 运行在 k8s 中
date: '2022-11-12T15:40:25+08:00'
slug: pinus-on-k8s-guide
draft: true
author: bruce
---

pinus 在 k8s 中运行很简单 只要让 master 可以被其他进程发现就行 具体做法是通过 k8s service 作为 master 的地址 然后修改 `master.json` 和 `servers.json` 即可。

详细说明待补充，现在懒得写...