---
title: 通过 docker 运行 redis
date: '2023-07-09T16:38:45+08:00'
slug: docker-redis-guide
draft: true
author: bruce
---

此文介绍如何通过 docker 来运行 redis

目的是仅用于**开发**，生产环境的话题不在此文的范围内

## 本地运行 redis

很简单一行命令

```sh
docker run --name redis-6379 -p 6379:6379 --init --restart=always -d redis:6
```

这样， redis 实例就启动了

如果仅给本地开发访问，这样的设置就足够了

## 给 redis 设置持久化存储

```sh
# 创建持久卷
docker volume create redis-data-6379
# 启动 redis
docker run --name redis-6379 -p 6379:6379 --init --restart=always -v redis-data-6379:/data -d redis:6
```

要点就在于 `-v redis-data-6379:/data` 这个选项

## 给 redis 设定密码

```sh
docker run \
--name redis-6379 \
-p 6379:6379 \
--init \
--restart=always \
-d redis:6 \
redis-server --requirepass "123321"
```

相比于不设置密码的启动方式，就是多了最后这一段 `redis-server --requirepass "123321"`

## 将 redis 放在云服务器中提供给开发使用

就是综合以上3个设置

```sh
# 创建持久卷
docker volume create redis-data-6379
# 启动
docker run \
--name redis-6379 \
-p 6379:6379 \
--init \
--restart=always \
-v redis-data-6379:/data \
-d redis:6 \
redis-server --requirepass "123321"
```

## 作为 redis-cli 客户端

```sh
docker run -it --rm redis:6 redis-cli -h $host -p $port
```

如果设置了密码，则连接后输入 auth 命令来验证，之后就可以愉快的查询数据了

```sh
auth $password
```

## 给 redis 设置主从同步

#### 主库

不需要任何设置

#### 从库 启动同步

```sh
docker run \
--name redis-6379 \
-p 6379:6379 \
--init \
--restart=always \
-d redis:6 \
redis-server --masterauth "123321" --requirepass "123321"
```

关键就在于 `--masterauth` 这个参数 启动后，连接上从库，然后执行 `slaveof $host $port` 就可以开始同步

#### 从库 关闭同步

执行 `slaveof no one` 关闭