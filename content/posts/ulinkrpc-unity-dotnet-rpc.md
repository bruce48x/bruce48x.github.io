---
title: ULinkRPC - Unity + .NET 强类型 RPC 框架
date: '2026-03-04T20:00:00+08:00'
slug: ulinkrpc-unity-dotnet-rpc
draft: true
author: bruce
---

本文介绍如何使用 **ULinkRPC** 构建 Unity + .NET 双端的强类型 RPC 通信环境。ULinkRPC 是一个轻量级 RPC 框架，支持多种传输协议和序列化器，特别适合需要 IL2CPP 兼容的 Unity 项目。

## 特性

- **强类型 RPC**：基于接口定义，自动生成客户端/服务器代码
- **多传输协议**：TCP、WebSocket、KCP、Loopback（进程内测试）
- **多序列化器**：MemoryPack（高性能）、JSON（调试友好）
- **IL2CPP/HybridCLR 兼容**：支持 iOS 热更新
- **传输安全**：支持压缩和加密

## 环境

- **.NET 8** - 服务器运行环境
- **Unity 2022 LTS** - 客户端运行环境
- **ULinkRPC** - RPC 框架（NuGet 包）

## 示例项目

本文配套的示例项目：
- **服务端**：[ULinkRPC-Sample-Server](https://github.com/bruce48x/ULinkRPC-Sample-Server)
- **客户端**：[ULinkRPC-Sample-Client](https://github.com/bruce48x/ULinkRPC-Sample-Client)
- **框架源码**：[unity-rpc-starter](https://github.com/bruce48x/unity-rpc-starter)

---

## 1. 概述

ULinkRPC 的核心思想与 MagicOnion 类似：定义一组共享接口（Contracts），在服务器端实现，在客户端生成调用代理。

关键概念：
- **Contracts**：共享的接口，定义服务方法
- **Client Stub**：根据 Contracts 生成的客户端调用代码
- **Server Binder**：服务器端的服务注册器
- **Transport**：传输层抽象（TCP/WebSocket/KCP）
- **Serializer**：序列化器（MemoryPack/JSON）

---

## 2. Contracts 定义

Contracts 是客户端和服务器共享的核心代码。需要创建一个独立的 Package 或 Class Library。

### 项目结构

```
Shared/
├── Interfaces/
│   └── IMyFirstService.cs
└── Shared.csproj
```

### 定义服务接口

```csharp
using System.Threading.Tasks;
using ULinkRPC.Core;

namespace Shared.Interfaces
{
    [RpcService(1)]
    public interface IMyFirstService
    {
        [RpcMethod(1)]
        ValueTask<int> SumAsync(int x, int y);
    }
}
```

关键特性：
- `[RpcService(N)]`：服务 ID
- `[RpcMethod(N)]`：方法 ID

---

## 3. 服务器端实现

### 项目结构

```
ULinkRPC-Sample-Server/
├── Shared/                  # 共享 Contracts
│   └── Interfaces/
│       └── IMyFirstService.cs
├── ULinkRPC-Sample-Server/  # 服务端实现
│   ├── Services/
│   │   └── MyFirstService.cs
│   ├── Generated/           # 自动生成
│   └── Program.cs
└── ULinkRPC-Sample-Server.sln
```

### 创建项目

```bash
dotnet new console -n ULinkRPC-Sample-Server --framework net8.0
cd ULinkRPC-Sample-Server
dotnet add package ULinkRPC.Server
dotnet add package ULinkRPC.Transport.Tcp
dotnet add package ULinkRPC.Serializer.MemoryPack
```

### 添加 Shared 引用

在 `.csproj` 中添加：

```xml
<ItemGroup>
  <Compile Include="..\Shared\**\*.cs" />
</ItemGroup>
```

### 实现服务

```csharp
using Shared.Interfaces;

namespace Server.Services;

public class MyFirstService : IMyFirstService
{
    public ValueTask<int> SumAsync(int x, int y)
    {
        Console.WriteLine($"Received: {x}, {y}");
        return new ValueTask<int>(x + y);
    }
}
```

### 启动服务器

```csharp
using System.Net;
using System.Net.Sockets;
using Shared.Interfaces.Server.Generated;
using Server.Services;
using ULinkRPC.Core;
using ULinkRPC.Server;
using ULinkRPC.Serializer.MemoryPack;
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
        var serializer = new MemoryPackRpcSerializer();
        server = new RpcServer(transport, serializer);

        // 注册服务
        AllServicesBinder.BindAll(server, new MyFirstService());
        
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

## 4. Unity 客户端实现

### 安装 NuGet 包

在 Unity 中使用 [NuGet for Unity](https://github.com/GlitchEnzo/NuGetForUnity)（通过 OpenUPM 安装）：

安装以下包：
- `ULinkRPC.Runtime`
- `MemoryPack`

### 导入 Contracts

将 Shared 文件夹复制到 Unity 项目中，或创建为 UPM Package。

### 连接服务器

```csharp
using System.Threading;
using System.Threading.Tasks;
using Shared.Interfaces;
using Shared.Interfaces.Runtime.Generated;
using ULinkRPC.Client;
using ULinkRPC.Serializer.MemoryPack;
using ULinkRPC.Transport.Tcp;
using UnityEngine;

public class RpcCaller : MonoBehaviour
{
    public string Host = "127.0.0.1";
    public int Port = 20000;

    private RpcClient? _client;
    private CancellationTokenSource? _cts;
    private IMyFirstService? _service;

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
            
            // 创建 MemoryPack 序列化器
            var serializer = new MemoryPackRpcSerializer();
            
            // 创建 RPC 客户端
            _client = new RpcClient(transport, serializer);
            
            await _client.StartAsync(_cts.Token);
            Debug.Log("Connected!");

            // 获取服务代理
            var rpcApi = _client.CreateRpcApi();
            _service = rpcApi.Game.MyFirst;

            // 调用 RPC 方法
            int result = await _service.SumAsync(10, 20);
            Debug.Log($"Sum(10, 20) = {result}");
        }
        catch (System.Exception ex)
        {
            Debug.LogError($"RPC error: {ex}");
        }
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
```

生成的文件包括：
- `MyFirstServiceClient.cs` - 客户端调用代理
- `MyFirstServiceBinder.cs` - 服务器端注册器
- `AllServicesBinder.cs` - 批量注册

---

## 6. 切换到 JSON

如果追求更好的调试体验，可以将 MemoryPack 替换为 JSON。

### 服务器端

```bash
dotnet remove package ULinkRPC.Serializer.MemoryPack
dotnet add package ULinkRPC.Serializer.Json
```

修改代码：

```csharp
using ULinkRPC.Serializer.Json;

var serializer = new JsonRpcSerializer();
```

### Unity 客户端

安装包：
- `ULinkRPC.Serializer.Json`

修改客户端代码：

```csharp
using ULinkRPC.Serializer.Json;

var serializer = new JsonRpcSerializer();
```

---

## 7. 切换传输协议

### WebSocket

服务器端安装：
```bash
dotnet add package ULinkRPC.Transport.WebSocket
```

### KCP (UDP)

服务器端安装：
```bash
dotnet add package ULinkRPC.Transport.Kcp
```

---

## 8. 传输安全（可选）

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

## 9. 总结

ULinkRPC 提供了一个轻量、灵活的 Unity + .NET RPC 解决方案：

- **简单易用**：基于接口定义，自动生成代码
- **高性能**：支持 MemoryPack 序列化
- **多协议**：TCP、WebSocket、KCP 可选
- **安全**：支持压缩和加密
- **IL2CPP 兼容**：支持 iOS 和热更新

更多细节请参考示例项目：
- [ULinkRPC-Sample-Server](https://github.com/bruce48x/ULinkRPC-Sample-Server)
- [ULinkRPC-Sample-Client](https://github.com/bruce48x/ULinkRPC-Sample-Client)

---

## 参考

- [ULinkRPC-Sample-Server](https://github.com/bruce48x/ULinkRPC-Sample-Server) - 服务端示例
- [ULinkRPC-Sample-Client](https://github.com/bruce48x/ULinkRPC-Sample-Client) - 客户端示例
- [ULinkRPC 框架源码](https://github.com/bruce48x/unity-rpc-starter)
- [MagicOnion](https://github.com/Cysharp/MagicOnion)
- [MessagePack-CSharp](https://github.com/msgpack/msgpack-cli)
