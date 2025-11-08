---
title: 通过 docker 运行 mysql
date: '2022-11-12T16:12:29+08:00'
slug: docker-mysql-guide
draft: true
author: bruce
---

本文介绍通过 docker 来运行 mysql 的方法

目的是仅用于**开发**，生产环境的话题不在此文的范围内

## 运行 mysql

运行 mysql 分两步

首先，创建一个持久卷

```sh
docker volume create mysql-data
```

然后，启动 mysql 实例

```sh
docker run \
--name mysql \
--init \
--restart=always \
-v mysql-data:/var/lib/mysql \
-e MYSQL_ROOT_PASSWORD=123456 \
-p 3306:3306 \
-d mysql:8
```

这样就可以通过账号 root，密码 123456 来连接上 mysql 了

## 作为 mysql 客户端

运行 MySQL 之后，需要验证一下是否成功

```sh
docker run -it --rm mysql:8 mysql -h192.168.1.2 -uroot -p123456
```

如果只用于本机开发，不考虑其他方面，往下都内容都不用看了

## 给 mysql 设置其他用户

如果不想用 root 用户，也可以另外设置新的用户

```sh
docker run \
--name mysql \
--init --restart=always \
-v mysql-data:/var/lib/mysql \
-e MYSQL_ROOT_PASSWORD=123456 \
-e MYSQL_USER=someuser \
-e MYSQL_PASSWORD=123456 \
-p 3306:3306 \
-d mysql:8
```

要点就在于 MYSQL\_USER 和 MYSQL\_PASSWORD 两个环境变量

这样就可以通过 账号 someuser 密码 123456 来连接 mysql

当然， MYSQL\_ROOT\_PASSWORD 是不能缺的

## 设置 max\_connection

有几种方法

### 第一种方法 用 my.cnf 配置的方式

定义一个配置文件 `custom.cnf`

```ini
[mysqld] 
max_connections=1000
```

在启动时将文件映射到配置文件的目录下

```sh
docker run -v ./custom.cnf:/etc/mysql/conf.d/custom.cnf -d mysql:8
```

### 第二种方法 不用配置文件，用命令的方式

```sh
docker run -d mysql:8 --max_connections=1000
```

通过增加 `--max_connections` 参数

### 第三种方法 通过 SQL 语句修改

```sql
# 修改最大值
SET GLOBAL max_connections = 1000;
# 确认修改结果
SHOW VARIABLES LIKE 'max_connections';
```

## 设置 sql-mode

将 MySQL 设置为严格模式是一个好的习惯，无论是开发还是生产环境 通过以下选项可以进行设定

```sh
docker run -d mysql:8 --sql-mode="STRICT_TRANS_TABLES"
```

## 设置 事务隔离级别

MySQL的默认隔离级别是 repeatable read， 也许你想要设定为 read commited 通过以下选项可以进行设定

```sh
docker run -d mysql:8 --transaction-isolation="READ-COMMITTED"
```

## 懒人的启动选项

以下是我常用的启动选项，就是把上面几个都包括了 视情况修改为真正要用的，特别是用户名和密码的部分

```sh
docker run \
--name mysql \
--init \
--restart=always \
-v mysql-data:/var/lib/mysql \
-e MYSQL_ROOT_PASSWORD=123456 \
-e MYSQL_USER=someuser \
-e MYSQL_PASSWORD=123456 \
-p 3306:3306 \
-d mysql:8 --max_connections=1000 --sql-mode="STRICT_TRANS_TABLES" --transaction-isolation="READ-COMMITTED"
```