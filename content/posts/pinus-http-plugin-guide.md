---
title: 使用 pinus-http-plugin
date: '2022-12-19T10:56:09+08:00'
slug: pinus-http-plugin-guide
draft: false
author: bruce
---

# 引言

pinus-http-plugin 是为了让 pinus 进程可以处理 http 协议而做的一个插件

然而文档较少，具体使用步骤如下

# 创建新项目

通过以下命令来初始化项目

```sh
# 创建目录并进入目录
mkdir demo
cd demo
# 创建 pinus 项目
pinus init
# 安装依赖
cd game-server
yarn install
```

# 安装 pinus-http-plugin 插件

在 game-server 目录下执行

```sh
# game-server/
yarn add pinus-http-plugin
```

# 创建 http.json 配置文件

创建配置文件 game-server/config/http.json

```json
{
  "development": {
    "gamehttp": {
      "host": "127.0.0.1",
      "port": 3001
    }
  }
}
```

# 修改 servers.json

修改配置文件 game-server/config/servers.json 加入以下配置

```json
"gamehttp": [
    { "id": "gamehttp", "port": 3002, "host": "127.0.0.1" }
]
```

# 修改 app.ts

加入以下的代码

```typescript
import { createPinusHttpPlugin } from 'pinus-http-plugin';
import * as path from 'path';

app.configure('development', 'gamehttp', function() {
    app.loadConfig('httpConfig', path.resolve(app.getBase(), 'config/http.json'));
    app.use(createPinusHttpPlugin(), app.get('httpConfig')[app.getServerId()]);
});
```

# 创建对外提供访问的接口

创建 game-server/app/servers/gamehttp/route/testRoute.ts

```typescript
import { Application } from 'pinus';
import * as express from 'express';

export = function (app: Application, http: express.Express) {

    http.get('/test', async function (req, res) {
        res.send('hello world');
    });

};
```

# 启动服务器，进行测试

在 game-server 目录下启动服务器

```sh
# 执行以下命令启动
yarn start
```

在浏览器输入 `http://127.0.0.1:3001/test` 即可看到结果

```txt
hello world
```