---
title: ULinkRPC - Unity + .NET 强类型 RPC 框架
date: '2026-03-04T20:00:00+08:00'
slug: ulinkrpc-unity-dotnet-rpc
draft: false
author: bruce
---

本文介绍如何使用 **ULinkRPC** 构建 Unity + .NET 双端的强类型 RPC 通信环境。ULinkRPC 是一个轻量级 RPC 框架，支持多种传输协议和序列化器，特别适合需要 IL2CPP 兼容的 Unity 项目。

## 特性

- **强类型 RPC**：基于接口定义，自动生成客户端/服务器代码
- **多传输协议**：TCP、WebSocket、KCP、Loopback（进程内测试）
- **多序列化器**：MemoryPack（高性能）、JSON（调试友好）
- **IL2CPP/HybridCLR 兼容**：支持 iOS 热更新
- **传输安全**：支持压缩和加密
- **双向通信**：支持 Server Push（Server → Client 推送）

## 环境

- **.NET 8** - 服务器运行环境
- **Unity 2022 LTS** - 客户端运行环境
- **ULinkRPC** - RPC 框架（NuGet 包）

## 示例项目

本文配套的示例项目位于：
- [unity-rpc-starter](https://github.com/bruce48x/unity-rpc-starter)

项目包含两个完整示例：
- `RpcCall.Json` - JSON + TCP 示例（本教程使用）
- `RpcCall.MemoryPack` - MemoryPack 示例

---

## 1. 概述

ULinkRPC 的核心思想与 MagicOnion 类似：定义一组共享接口（Contracts），在服务器端实现，在客户端生成调用代理。

关键概念：
- **Contracts**：共享的接口和 DTO，定义服务方法
- **Client Stub**：根据 Contracts 生成的客户端调用代码
- **Server Binder**：服务器端的服务注册器
- **Transport**：传输层抽象（TCP/WebSocket/KCP）
- **Serializer**：序列化器（MemoryPack/JSON）

---

## 2. Contracts 定义

Contracts 是客户端和服务器共享的核心代码。需要创建一个独立的 Package 或 Class Library。

### 项目结构

```
com.samples.contracts/
├── com.samples.contracts.asmdef
├── IPlayerService.cs
└── ExampleDtos.cs
```

### 定义服务接口

```csharp
using System.Threading.Tasks;
using ULinkRPC.Core;

namespace Game.Rpc.Contracts
{
    [RpcService(1)]
    public interface IPlayerService : IRpcService<IPlayerService, IPlayerCallback>
    {
        [RpcMethod(1)]
        ValueTask<LoginReply> LoginAsync(LoginRequest req);

        [RpcMethod(2)]
        ValueTask PingAsync();
    }

    public interface IPlayerCallback
    {
        [RpcMethod(1)]
        void OnNotify(string message);
    }
}
```

### 定义 DTO

```csharp
namespace Game.Rpc.Contracts
{
    public class LoginRequest
    {
        public string Account { get; set; } = "";
        public string Password { get; set; } = "";
    }

    public class LoginReply
    {
        public int Code { get; set; }
        public string Token { get; set; } = "";
    }
}
```

### 关键特性

- `[RpcService(N)]`：服务 ID
- `[RpcMethod(N)]`：方法 ID
- `IRpcService<TSelf, TCallback>`：支持双向通信的服务接口
- `IPlayerCallback`：Server Push 用的回调接口

---

## 3. 服务器端实现（TCP + JSON）

### 创建 Server 项目

```bash
dotnet new console -n RpcCall.Server --framework net8.0
cd RpcCall.Server
dotnet add package ULinkRPC.Server
dotnet add package ULinkRPC.Transport.Tcp
dotnet add package ULinkRPC.Serializer.Json
```

### 添加 Contracts 引用

在 `.csproj` 中添加：

```xml
<ItemGroup>
  <Compile Include="..\path\to\com.samples.contracts\**\*.cs" />
</ItemGroup>
```

### 实现服务

```csharp
using System;
using System.Threading.Tasks;
using Game.Rpc.Contracts;
using Game.Rpc.Server.Generated;
using ULinkRPC.Core;
using ULinkRPC.Server;

namespace RpcCall.Server.Services;

public class PlayerService : IPlayerService
{
    private readonly IPlayerCallback _callback;

    public PlayerService(IPlayerCallback callback)
    {
        _callback = callback;
    }

    public async ValueTask<LoginReply> LoginAsync(LoginRequest req)
    {
        _callback.OnNotify($"Welcome {req.Account}, login request accepted.");

        // 模拟登录逻辑
        return new LoginReply
        {
            Code = 0,
            Token = $"token-{req.Account}-{Guid.NewGuid():N}"
        };
    }

    public ValueTask PingAsync()
    {
        _callback.OnNotify("Ping received by server.");
        return default;
    }
}
```

### 启动 TCP 服务器

```csharp
using System.Net;
using System.Net.Sockets;
using Game.Rpc.Server.Generated;
using RpcCall.Server.Services;
using ULinkRPC.Core;
using ULinkRPC.Server;
using ULinkRPC.Serializer.Json;
using ULinkRPC.Transport.Tcp;

const int defaultTcpPort = 20000;
var tcpPort = args.Length > 0 && int.TryParse(args[0], out var p) ? p : defaultTcpPort;

using var cts = new CancellationTokenSource();
Console.CancelKeyPress += (_, e) =>
{
    e.Cancel = true;
    cts.Cancel();
};

Console.WriteLine($"Server listening on 0.0.0.0:{tcpPort}. Press Ctrl+C to stop.");

var listener = new TcpListener(IPAddress.Any, tcpPort);
listener.Start();

try
{
    while (!cts.Token.IsCancellationRequested)
    {
        var client = await listener.AcceptTcpClientAsync(cts.Token);
        var transport = new TcpServerTransport(client);
        _ = HandleConnectionAsync(transport, cts.Token);
    }
}
finally
{
    listener.Stop();
}

async Task HandleConnectionAsync(ITransport transport, CancellationToken ct)
{
    RpcServer? server = null;
    try
    {
        var serializer = new JsonRpcSerializer();
        server = new RpcServer(transport, serializer);

        // 注册服务
        PlayerServiceBinder.Bind(server, callback => new PlayerService(callback));
        
        await server.StartAsync(ct);
        await server.WaitForCompletionAsync(ct);
    }
    catch (Exception ex)
    {
        Console.WriteLine($"Error: {ex}");
    }
    finally
    {
        if (server is not null)
            await server.StopAsync();
        await transport.DisposeAsync();
    }
}
```

### 运行服务器

```bash
dotnet run
# Server listening on 0.0.0.0:20000. Press Ctrl+C to stop.
```

---

## 4. Unity 客户端实现（TCP + JSON）

### 安装 NuGet 包

在 Unity 中使用 [NuGet for Unity](https://github.com/GlitchEnzo/NuGetForUnity)（通过 OpenUPM 安装）：

```
com.ylsdev.nugetforunity
```

安装以下包：
- `ULinkRPC.Core`
- `ULinkRPC.Client`
- `ULinkRPC.Transport.Tcp`
- `ULinkRPC.Serializer.Json`

### 导入 Contracts

将 Contracts Package 导入 Unity 项目。

### 连接服务器

```csharp
using System;
using System.Threading;
using System.Threading.Tasks;
using Game.Rpc.Contracts;
using Game.Rpc.Runtime.Generated;
using ULinkRPC.Client;
using ULinkRPC.Serializer.Json;
using ULinkRPC.Transport.Tcp;
using UnityEngine;

public class RpcConnectionTester : MonoBehaviour
{
    public string Host = "127.0.0.1";
    public int Port = 20000;

    private RpcClient? _client;
    private CancellationTokenSource? _cts;
    private IPlayerService? _playerService;

    private async void Start()
    {
        await ConnectAndTestAsync();
    }

    private async Task ConnectAndTestAsync()
    {
        try
        {
            _cts = new CancellationTokenSource();
            
            // 创建 TCP 传输
            var transport = new TcpTransport(Host, Port);
            
            // 创建 JSON 序列化器
            var serializer = new JsonRpcSerializer();
            
            // 创建 RPC 客户端
            _client = new RpcClient(transport, serializer);
            
            // 注册回调（处理 Server Push）
            PlayerCallbackBinder.Bind(_client, this);
            
            await _client.StartAsync(_cts.Token);
            Debug.Log("Connected!");

            // 获取服务代理
            var rpcApi = _client.CreateRpcApi();
            _playerService = rpcApi.Game.Player;

            // 调用 RPC 方法
            var reply = await _playerService.LoginAsync(new LoginRequest
            {
                Account = "test",
                Password = "123456"
            });

            Debug.Log($"Login result: code={reply.Code}, token={reply.Token}");

            await _playerService.PingAsync();
            Debug.Log("Ping ok!");
        }
        catch (Exception ex)
        {
            Debug.LogError($"RPC error: {ex}");
        }
    }

    // Server Push 回调
    public void OnNotify(string message)
    {
        Debug.Log($"Server push: {message}");
    }

    private async void OnDestroy()
    {
        if (_client is not null)
        {
            await _client.DisposeAsync();
        }
    }
}
```

---

## 5. 代码生成

RPC 客户端 Stub 和服务器端 Binder 需要通过代码生成工具自动生成。

### 运行代码生成器

```bash
dotnet run --project src/ULinkRPC.CodeGen/ULinkRPC.CodeGen.csproj --
# 或者使用脚本
./scripts/gen.sh
# 或
./scripts/gen.ps1
```

生成的文件包括：
- `PlayerServiceClient.cs` - 客户端调用代理
- `PlayerServiceBinder.cs` - 服务器端注册器
- `PlayerCallbackProxy.cs` - 服务器端回调代理
- `PlayerCallbackBinder.cs` - 客户端回调绑定器
- `RpcApi.cs` - 统一的 API 入口

生成的代码会被放到 `Assets/Scripts/Rpc/RpcGenerated/` 目录，需要提交到版本控制。

---

## 6. 传输安全（可选）

如果需要开启压缩或加密，可以使用 `TransformingTransport`：

```csharp
var security = new TransportSecurityConfig
{
    EnableCompression = true,
    CompressionThresholdBytes = 1024,
    EnableEncryption = true,
    EncryptionKeyBase32 = "YOUR_32_BYTE_BASE32_KEY_HERE"
};

ITransport rawTransport = new TcpTransport("127.0.0.1", 20000);
ITransport secureTransport = new TransformingTransport(rawTransport, security);
```

注意：客户端和服务器必须使用相同的加密设置和密钥。

---

## 7. 测试

### 服务器端测试

使用 xUnit + 标准 .NET 测试框架。

### Unity 端测试

使用 Unity Test Framework + NUnit。

```csharp
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;
using System.Collections;

public class RpcTests
{
    [UnityTest]
    public IEnumerator TestRpcCall()
    {
        var task = RunRpcTestAsync();
        yield return new WaitUntil(() => task.IsCompleted);
        
        if (task.IsFaulted)
            throw task.Exception!;
    }

    private async Task RunRpcTestAsync()
    {
        // 测试代码
    }
}
```

---

## 8. 切换到 WebSocket

如果需要通过浏览器访问或使用 HTTP 端口，可以切换到 WebSocket 传输。

### 服务器端

安装包：
```bash
dotnet add package ULinkRPC.Transport.WebSocket
```

启动 WebSocket 服务器：

```csharp
using System.Net.WebSockets;
using Game.Rpc.Server.Generated;
using ULinkRPC.Core;
using ULinkRPC.Server;
using ULinkRPC.Serializer.Json;
using ULinkRPC.Transport.WebSocket;

const int wsPort = 20001;
var listener = new WebSocketServerTransport.WebSocketListener(IPAddress.Any, wsPort);

while (!cts.Token.IsCancellationRequested)
{
    var ws = await listener.AcceptAsync(cts.Token);
    var transport = new WebSocketServerTransport(ws);
    _ = HandleConnectionAsync(transport, cts.Token);
}
```

### Unity 客户端

安装包：
- `ULinkRPC.Transport.WebSocket`

客户端连接：

```csharp
// 注意：Unity 客户端使用 YetAnotherHttpHandler 连接 WebSocket
// 具体用法请参考项目中的 WebSocket 示例
```

---

## 9. 切换到 MemoryPack

如果追求更高性能，可以将 JSON 替换为 MemoryPack。

### 服务器端

安装包：
```bash
dotnet remove package ULinkRPC.Serializer.Json
dotnet add package ULinkRPC.Serializer.MemoryPack
```

修改代码：

```csharp
using ULinkRPC.Serializer.MemoryPack;

// JsonRpcSerializer 替换为 MemoryPackRpcSerializer
var serializer = new MemoryPackRpcSerializer();
```

### Unity 客户端

安装包：
- `ULinkRPC.Serializer.MemoryPack`

修改客户端代码：

```csharp
using ULinkRPC.Serializer.MemoryPack;

// JsonRpcSerializer 替换为 MemoryPackRpcSerializer
var serializer = new MemoryPackRpcSerializer();
```

### DTO 注意事项

使用 MemoryPack 时，DTO 需要添加 `[MemoryPackable]` 特性：

```csharp
using MessagePack;

namespace Game.Rpc.Contracts
{
    [MessagePackObject]
    public class LoginRequest
    {
        [Key(0)]
        public string Account { get; set; } = "";
        
        [Key(1)]
        public string Password { get; set; } = "";
    }

    [MessagePackObject]
    public class LoginReply
    {
        [Key(0)]
        public int Code { get; set; }
        
        [Key(1)]
        public string Token { get; set; } = "";
    }
}
```

---

## 10. 总结

ULinkRPC 提供了一个轻量、灵活的 Unity + .NET RPC 解决方案：

- **简单易用**：基于接口定义，自动生成代码
- **高性能**：支持 MemoryPack 序列化
- **多协议**：TCP、WebSocket、KCP 可选
- **安全**：支持压缩和加密
- **IL2CPP 兼容**：支持 iOS 和热更新

更多细节请参考 [unity-rpc-starter](https://github.com/bruce48x/unity-rpc-starter) 项目。

---

## 参考

- [ULinkRPC GitHub](https://github.com/bruce48x/unity-rpc-starter)
- [MagicOnion](https://github.com/Cysharp/MagicOnion)
- [MessagePack-CSharp](https://github.com/msgpack/msgpack-cli)
