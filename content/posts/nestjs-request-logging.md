---
title: Nestjs 项目中如何统计接口的耗时，并且打印请求和响应的数据
date: '2023-08-18T01:28:29+08:00'
slug: nestjs-request-logging
draft: false
author: bruce
---

在项目中统计耗时和打印日志是非常常见的需求， Nestjs 项目中可以利用 Interceptor 非常方便的做到这一点， 本文就一步一步的记录其实现方法 首先打开终端，进入你的工作目录，创建一个全新的 Nestjs 项目 执行：

```sh
npx @nestjs/cli new demo-nestjs
```

随即根据提示选择包管理器，再等待一段时间安装依赖，项目就创建好了 在2023年8月，创建的是10.1.12版本

```log
Need to install the following packages:
  @nestjs/cli@10.1.12
Ok to proceed? (y) y
⚡  We will scaffold your app in a few seconds..

? Which package manager would you ❤️  to use? yarn
CREATE demo1/.eslintrc.js (663 bytes)
CREATE demo1/.prettierrc (51 bytes)
CREATE demo1/nest-cli.json (171 bytes)
CREATE demo1/package.json (1946 bytes)
CREATE demo1/README.md (3347 bytes)
CREATE demo1/tsconfig.build.json (97 bytes)
CREATE demo1/tsconfig.json (546 bytes)
CREATE demo1/src/app.controller.spec.ts (617 bytes)
CREATE demo1/src/app.controller.ts (274 bytes)
CREATE demo1/src/app.module.ts (249 bytes)
CREATE demo1/src/app.service.ts (142 bytes)
CREATE demo1/src/main.ts (208 bytes)
CREATE demo1/test/app.e2e-spec.ts (630 bytes)
CREATE demo1/test/jest-e2e.json (183 bytes)

✔ Installation in progress... ☕

🚀  Successfully created project demo-nestjs
```

接下来，运行项目，验证是否创建完成

```sh
yarn start:dev
```

会看到以下 log

```log
[01:08:05] Starting compilation in watch mode...

[01:08:08] Found 0 errors. Watching for file changes.

[Nest] 46620  - 2023/08/18 01:08:09     LOG [NestFactory] Starting Nest application...
[Nest] 46620  - 2023/08/18 01:08:09     LOG [InstanceLoader] AppModule dependencies initialized +8ms
[Nest] 46620  - 2023/08/18 01:08:09     LOG [RoutesResolver] AppController {/}: +33ms
[Nest] 46620  - 2023/08/18 01:08:09     LOG [RouterExplorer] Mapped {/, GET} route +2ms
[Nest] 46620  - 2023/08/18 01:08:09     LOG [NestApplication] Nest application successfully started +2ms
```

然后在浏览器输入 `localhost:3000`会看到 `Hello World!`，说明运行是OK的

接下来就创建 interceptor 来实现本文的第一个目的：打印接口耗时 执行

```sh
npx @nestjs/cli g itc request
```

此时，项目的 src 目录下就出现一个名为 `request` 的新目录，里面有一个新的文件 `request.interceptor.ts`该文件的原始内容是这样的:

```ts
import { CallHandler, ExecutionContext, Injectable, NestInterceptor } from '@nestjs/common';
import { Observable } from 'rxjs';

@Injectable()
export class RequestInterceptor implements NestInterceptor {
  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    return next.handle();
  }
}
```

此时只要把 intercept 函数的内容修改为:

```ts
intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const start = Date.now();
    return next.handle().pipe(tap(() => console.log('耗时:' + (Date.now() - start) + '毫秒')));
  }
```

然后再修改 `app.module.ts` 里的 `providers` 的内容：

```ts
@Module({
  imports: [],
  controllers: [AppController],
  providers: [
    {
      provide: APP_INTERCEPTOR,
      useClass: RequestInterceptor,
    },
    AppService],
})
export class AppModule {}
```

这样 interceptor 就会被加载了 刷新浏览器进行测试，可以看到终端有 log 打印出来

```log
耗时:1毫秒
```

这就是 interceptor 的方便之处 接下来，再实现接口请求和响应数据的打印 修改 interceptor 的代码变成如下:

```ts
intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const start = Date.now();
    const http = context.switchToHttp();
        const req = http.getRequest();
        const urlObj = new URL(req.url, `http://${req.headers.host}`);
        const url = urlObj.pathname;
        let args = '';
        if (Object.keys(req.body).length) {
            args += JSON.stringify(req.body);
        }
        if (Object.keys(req.query).length) {
            args += JSON.stringify(req.query);
        }
        if (Object.keys(req.params).length) {
            args += JSON.stringify(req.params);
        }
        console.log(`<<< 请求 >>> route:${url}, 参数:${args}`);

        return next
            .handle()
            .pipe(
                tap((value) =>
                    console.log(`<<< 响应 >>> route:${url}, 参数:${args}，结果:${JSON.stringify(value)}，耗时:${Date.now() - start}毫秒`),
                ),
            );
  }
```

这样接口的请求和响应数据都有了 最后来测试验证，在浏览器发起请求 `http://localhost:3000/?areu=ok`可以看到终端的日志

```log
[01:21:54] File change detected. Starting incremental compilation...

[01:21:54] Found 0 errors. Watching for file changes.

[Nest] 29096  - 2023/08/18 01:21:55     LOG [NestFactory] Starting Nest application...
[Nest] 29096  - 2023/08/18 01:21:55     LOG [InstanceLoader] AppModule dependencies initialized +9ms
[Nest] 29096  - 2023/08/18 01:21:55     LOG [RoutesResolver] AppController {/}: +21ms
[Nest] 29096  - 2023/08/18 01:21:55     LOG [RouterExplorer] Mapped {/, GET} route +2ms
[Nest] 29096  - 2023/08/18 01:21:55     LOG [NestApplication] Nest application successfully started +2ms
<<< 请求 >>> route:/, 参数:{"areu":"ok"}
<<< 响应 >>> route:/, 参数:{"areu":"ok"}，结果:"Hello World!"，耗时:7毫秒
```

大功告成！