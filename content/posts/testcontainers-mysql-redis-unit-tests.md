---
title: 利用 Testcontainers 在测试中模拟 MySQL / Redis
date: '2025-04-10T10:55:00+08:00'
slug: testcontainers-mysql-redis-unit-tests
draft: false
author: bruce
---

Node.js 项目一旦接入 MySQL 或 Redis，测试就很容易从“验证业务逻辑”变成“先把环境搭起来”。本机手工跑一套数据库当然能测，但它依赖开发机状态；mock 跑得快，但很多真实问题根本测不出来，比如连接参数、SQL 语句、驱动配置、Redis 过期行为。

`Testcontainers` 的做法是：测试开始时临时启动 Docker 容器，测试结束后自动销毁。这样代码连的是真实的 MySQL 和 Redis，但环境仍然由测试自己管理。

严格来说，这类测试更接近**集成测试**。不过在实际项目里，它通常就是和单元测试一起放在测试工程里跑的那一层。

这篇文章以 **Node.js** 为主，示例用 `jest`，最后补一个 `.NET` 版本做对照。

## 为什么在 Node.js 里值得用 Testcontainers

Node.js 项目里，下面这些场景尤其适合用它：

- Repository 层要验证真实 SQL 是否能跑通
- Redis 缓存逻辑依赖过期时间、key 结构、序列化结果
- 本地开发和 CI 的环境不一致
- 测试里不想为了数据库和缓存维护一堆脚本

mock 能解决“接口有没有被调用”的问题，但解决不了这些问题：

- 连接串到底对不对
- SQL 在真实 MySQL 里能不能执行
- Redis key 是否真的写进去了
- ORM / 驱动的配置有没有写错

所以只要测试目标里包含“和真实 MySQL / Redis 能不能工作”，`Testcontainers` 就比 fake 或 mock 更合适。

## 先安装依赖

下面用 `jest` 举例，也可以换成 `vitest` 或 `node:test`，核心思路是一样的。

先装依赖：

```sh
npm install -D testcontainers jest
npm install mysql2 ioredis
```

这几个包分别负责：

- `testcontainers`：Node.js 版本的容器测试库
- `jest`：测试框架
- `mysql2`：连接 MySQL
- `ioredis`：连接 Redis

前提条件也很简单：本机或者 CI 环境里要能访问 Docker daemon。

## Node.js 版：MySQL 示例

先看一个最小可用的 MySQL 测试。

```js
const { GenericContainer, Wait } = require("testcontainers");
const mysql = require("mysql2/promise");

describe("mysql with testcontainers", () => {
  let container;
  let connection;

  beforeAll(async () => {
    container = await new GenericContainer("mysql", "8.0")
      .withEnvironment({
        MYSQL_ROOT_PASSWORD: "123456",
        MYSQL_DATABASE: "testdb",
      })
      .withExposedPorts(3306)
      .withWaitStrategy(Wait.forLogMessage(/ready for connections/i))
      .start();

    connection = await mysql.createConnection({
      host: container.getHost(),
      port: container.getMappedPort(3306),
      user: "root",
      password: "123456",
      database: "testdb",
    });
  });

  afterAll(async () => {
    if (connection) {
      await connection.end();
    }

    if (container) {
      await container.stop();
    }
  });

  test("should insert and query user", async () => {
    await connection.execute(`
      create table if not exists users (
        id bigint primary key auto_increment,
        name varchar(64) not null
      )
    `);

    await connection.execute(
      "insert into users(name) values (?)",
      ["bruce"]
    );

    const [rows] = await connection.execute(
      "select count(*) as count from users"
    );

    expect(rows[0].count).toBe(1);
  });
});
```

这个测试里最关键的点有几个：

- 通过 `GenericContainer("mysql", "8.0")` 启动真实 MySQL
- 用环境变量初始化 root 密码和数据库
- 用 `getHost()` 和 `getMappedPort(3306)` 组装连接参数
- 直接跑真实建表、插入和查询 SQL

如果你的项目已经用了 `knex`、`sequelize`、`typeorm` 或 `prisma`，把这里的 `mysql2` 换成自己的数据访问层就行，容器启动方式不需要改。

## Node.js 版：Redis 示例

Redis 写法通常更简单：

```js
const { GenericContainer, Wait } = require("testcontainers");
const Redis = require("ioredis");

describe("redis with testcontainers", () => {
  let container;
  let redis;

  beforeAll(async () => {
    container = await new GenericContainer("redis", "7.2")
      .withExposedPorts(6379)
      .withWaitStrategy(Wait.forLogMessage(/Ready to accept connections/i))
      .start();

    redis = new Redis({
      host: container.getHost(),
      port: container.getMappedPort(6379),
    });
  });

  afterAll(async () => {
    if (redis) {
      redis.disconnect();
    }

    if (container) {
      await container.stop();
    }
  });

  test("should write and read redis key", async () => {
    await redis.set("user:1:name", "bruce");
    const value = await redis.get("user:1:name");

    expect(value).toBe("bruce");
  });
});
```

这段代码已经足够覆盖很多真实场景，比如：

- 缓存读写
- key 命名是否统一
- 过期时间逻辑
- JSON 序列化和反序列化

## Node.js 版：同时启动 MySQL 和 Redis

很多服务同时依赖数据库和缓存，这时可以在同一个测试套件里一起启动：

```js
const { GenericContainer, Wait } = require("testcontainers");
const mysql = require("mysql2/promise");
const Redis = require("ioredis");

describe("app with mysql and redis", () => {
  let mysqlContainer;
  let redisContainer;
  let db;
  let redis;

  beforeAll(async () => {
    mysqlContainer = await new GenericContainer("mysql", "8.0")
      .withEnvironment({
        MYSQL_ROOT_PASSWORD: "123456",
        MYSQL_DATABASE: "testdb",
      })
      .withExposedPorts(3306)
      .withWaitStrategy(Wait.forLogMessage(/ready for connections/i))
      .start();

    redisContainer = await new GenericContainer("redis", "7.2")
      .withExposedPorts(6379)
      .withWaitStrategy(Wait.forLogMessage(/Ready to accept connections/i))
      .start();

    db = await mysql.createConnection({
      host: mysqlContainer.getHost(),
      port: mysqlContainer.getMappedPort(3306),
      user: "root",
      password: "123456",
      database: "testdb",
    });

    redis = new Redis({
      host: redisContainer.getHost(),
      port: redisContainer.getMappedPort(6379),
    });
  });

  afterAll(async () => {
    if (db) {
      await db.end();
    }

    if (redis) {
      redis.disconnect();
    }

    if (mysqlContainer) {
      await mysqlContainer.stop();
    }

    if (redisContainer) {
      await redisContainer.stop();
    }
  });

  test("should save user to mysql and cache to redis", async () => {
    await db.execute(`
      create table if not exists users (
        id bigint primary key auto_increment,
        name varchar(64) not null
      )
    `);

    await db.execute("insert into users(name) values (?)", ["alice"]);
    await redis.set("user:latest", "alice");

    const [rows] = await db.execute("select name from users limit 1");
    const cached = await redis.get("user:latest");

    expect(rows[0].name).toBe("alice");
    expect(cached).toBe("alice");
  });
});
```

这样写的好处很直接：

- 测到的是更接近真实应用的链路
- 本地和 CI 的依赖启动方式一致
- 不需要在测试机上提前准备固定端口的 MySQL / Redis

## 在 Node.js 项目里怎么组织

一个实用的分层方式是：

- 纯逻辑测试继续用普通单元测试，不访问数据库，不访问 Redis，也不启动容器
- 依赖外部组件的测试再用 `Testcontainers`，例如 Repository、Cache、初始化流程、和 SQL / Redis 协议强相关的逻辑

这样不会把所有测试都拖慢，但最容易出真实问题的那一层仍然能测到。

## Node.js 里几个很实用的建议

### 1. 固定镜像版本

不要偷懒用 `latest`，测试环境最怕漂移。像 `mysql:8.0`、`redis:7.2` 这种固定版本更稳定。

### 2. 显式初始化数据库结构

不要依赖“本地数据库之前已经有表”。测试里自己建表，或者启动后跑 migration，行为更可控。

### 3. 给容器启动留出明确的等待条件

像 MySQL、Redis 这种服务，容器进程启动了，不代表已经能接请求。`Wait.forLogMessage(...)` 这类等待条件很重要，不然测试偶尔就会在 CI 里抖动。

### 4. 尽量复用容器

如果一个 `describe` 里有多个测试，共用同一套容器通常更合理。每个 `test` 都重新拉起容器，速度会明显变慢。

### 5. 在 CI 里也跑

`Testcontainers` 的真正价值，不只是本地方便，而是让 CI 也能按同样方式启动依赖。这样更容易避免“我本地能跑，CI 不行”。

## 和 mock 的边界

两者不是互相替代，而是分工不同。

- mock 适合验证调用路径、参数传递、异常分支
- `Testcontainers` 适合验证代码和真实依赖能不能协同工作

下面这些问题，mock 很难帮你发现：

- SQL 语法写错
- 字段类型不匹配
- 连接参数配置错误
- Redis key 过期逻辑写反
- 驱动升级后行为变化

所以比较合理的做法通常不是“全部改成容器测试”，而是把最需要真实依赖参与的那一部分交给 `Testcontainers`。

## .NET 版本补充

如果你的项目是 `.NET`，思路其实完全一样，只是 API 不同。

先安装依赖：

```sh
dotnet add package Testcontainers.MySql
dotnet add package Testcontainers.Redis
dotnet add package MySqlConnector
dotnet add package StackExchange.Redis
dotnet add package xunit
```

MySQL 示例：

```csharp
using MySqlConnector;
using Testcontainers.MySql;
using Xunit;

public sealed class MySqlTests : IAsyncLifetime
{
    private readonly MySqlContainer _mySql = new MySqlBuilder()
        .WithImage("mysql:8.0")
        .Build();

    public async Task InitializeAsync()
    {
        await _mySql.StartAsync();
    }

    public async Task DisposeAsync()
    {
        await _mySql.DisposeAsync();
    }

    [Fact]
    public async Task Should_Query_MySql()
    {
        await using var connection = new MySqlConnection(_mySql.GetConnectionString());
        await connection.OpenAsync();

        await using var create = new MySqlCommand(
            """
            create table if not exists users (
                id bigint primary key auto_increment,
                name varchar(64) not null
            );
            """,
            connection);
        await create.ExecuteNonQueryAsync();

        await using var insert = new MySqlCommand(
            "insert into users(name) values ('bruce');",
            connection);
        await insert.ExecuteNonQueryAsync();

        await using var query = new MySqlCommand(
            "select count(*) from users;",
            connection);
        var count = Convert.ToInt32(await query.ExecuteScalarAsync());

        Assert.Equal(1, count);
    }
}
```

Redis 示例：

```csharp
using StackExchange.Redis;
using Testcontainers.Redis;
using Xunit;

public sealed class RedisTests : IAsyncLifetime
{
    private readonly RedisContainer _redis = new RedisBuilder()
        .WithImage("redis:7.2")
        .Build();

    public async Task InitializeAsync()
    {
        await _redis.StartAsync();
    }

    public async Task DisposeAsync()
    {
        await _redis.DisposeAsync();
    }

    [Fact]
    public async Task Should_Read_And_Write_Redis()
    {
        await using var connection = await ConnectionMultiplexer.ConnectAsync(
            _redis.GetConnectionString());

        var db = connection.GetDatabase();

        await db.StringSetAsync("user:1:name", "bruce");
        var value = await db.StringGetAsync("user:1:name");

        Assert.Equal("bruce", value.ToString());
    }
}
```

如果你本来就是 Node.js 项目，这一节看个思路就够了，重点还是前面的 Node.js 写法。

## 小结

如果你的 Node.js 测试要碰 MySQL 或 Redis，`Testcontainers` 基本是一个很实用的方案：

- 不需要长期维护本地依赖
- 跑的是真实 MySQL / Redis
- 本地和 CI 更一致
- 比 mock 更容易暴露真实配置错误

我的建议很简单：

- 纯业务逻辑，继续用普通单元测试
- 需要数据库 / 缓存参与的测试，用 `Testcontainers`

这样通常能在测试速度、真实性和维护成本之间拿到一个比较平衡的结果。
