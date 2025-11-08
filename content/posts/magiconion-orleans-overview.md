---
title: MagicOnion 结合 Orleans
date: '2024-07-23T11:36:04+08:00'
slug: magiconion-orleans-overview
draft: false
author: bruce
---

书接上回，上一篇文章介绍了怎么利用 MagicOnion 搭建实时通信程序，这一篇将扩展服务端，结合 Orleans 创建一个分布式的系统，突破单台机器的上限，可服务海量用户。

Orleans 项目分为几个部分：`Grain Interface` / `Grain` / `Silo` / `Client`

- `Grain Interface` : 定义接口，用于 Silo 和 Client 之间共享代码。
- `Grain` : Interface 的具体实现
- `Silo` : 服务端
- `Client` : 客户端

# 创建项目

执行以下命令创建项目

```shell
cd magiconion-sample-server
dotnet new classlib -n GrainInterfaces --framework net8.0
dotnet new classlib -n Grains --framework net8.0
dotnet new console -n Silo --framework net8.0
dotnet sln magiconion-sample-server.sln add GrainInterfaces/GrainInterfaces.csproj
dotnet sln magiconion-sample-server.sln add Grains/Grains.csproj
dotnet sln magiconion-sample-server.sln add Silo/Silo.csproj
```

这里为什么没有创建 Client，因为 MagicOnion 的 Server 就作为 Orleans 的 Client

删除无用的文件

- GrainInterfaces/Class1.cs
- Grains/Class1.cs

## GrainInterface 添加依赖

修改 GrainInterfaces/GrainInterfaces.csproj

```xml
<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="Microsoft.Orleans.Sdk" Version="8.2.0" />
  </ItemGroup>

</Project>
```

## Grains 添加依赖

修改 Grains/Grains.csproj 将 GrainInterfaces.csproj 加入其中，

并且加入 `Microsoft.Orleans.Sdk` 和 `Microsoft.Extensions.Logging.Abstractions`

```xml
<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>

  <ItemGroup>
    <ProjectReference Include="../GrainInterfaces/GrainInterfaces.csproj" />
    <PackageReference Include="Microsoft.Orleans.Sdk" Version="8.2.0" />
    <PackageReference Include="Microsoft.Extensions.Logging.Abstractions" Version="8.0.1" />
  </ItemGroup>

</Project>
```

## Silo 添加依赖

修改 Silo.csproj

```xml
<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net8.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>

  <ItemGroup>
    <ProjectReference Include="../Grains/Grains.csproj" />
    <PackageReference Include="Microsoft.Orleans.Server" Version="8.2.0" />
    <PackageReference Include="Microsoft.Extensions.Logging.Console" Version="8.0.0" />
    <PackageReference Include="Microsoft.Extensions.Hosting" Version="8.0.0" />
  </ItemGroup>

</Project>
```

## Server 添加依赖

修改 Server.csproj

```xml
<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net8.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="MagicOnion.Server" Version="6.0.0" />
    <ProjectReference Include="../Shared/Shared.csproj" />
    <ProjectReference Include="../GrainInterfaces/GrainInterfaces.csproj" />
    <PackageReference Include="Microsoft.Orleans.Client" Version="8.2.0" />
    <PackageReference Include="Microsoft.Extensions.Logging.Console" Version="8.0.0" />
    <PackageReference Include="Microsoft.Extensions.Hosting" Version="8.0.0" />
  </ItemGroup>

</Project>
```

此时项目的文件结构是这样

```txt
.
├── GrainInterfaces
│   ├── GrainInterfaces.csproj
├── Grains
│   ├── Grains.csproj
├── magiconion-sample-server.sln
├── README.md
├── Server
│   ├── bin
│   ├── obj
│   ├── Program.cs
│   ├── Server.csproj
│   ├── Services
│   └── StreamingHub
├── Shared
│   ├── bin
│   ├── Interfaces
│   ├── obj
│   ├── package.json
│   ├── Shared.asmdef
│   └── Shared.csproj
└── Silo
    ├── bin
    ├── obj
    ├── Program.cs
    └── Silo.csproj
```

# 创建一个 Grain 接口

在 GrainInterfaces 项目中，创建 IHello.cs 文件

```csharp
namespace GrainInterfaces;

public interface IHello : IGrainWithIntegerKey
{
    ValueTask<string> SayHello(string greeting);
}
```

# 创建一个 Grain 类

在 Grains 项目中，创建 HelloGrain.cs 文件

```csharp
using GrainInterfaces;
using Microsoft.Extensions.Logging;

namespace Grains;

public class HelloGrain : Grain, IHello
{
    private readonly ILogger _logger;

    public HelloGrain(ILogger<HelloGrain> logger) => _logger = logger;

    ValueTask<string> IHello.SayHello(string greeting)
    {
        _logger.LogInformation("""
            SayHello message received: greeting = "{Greeting}"
            """,
            greeting);

        return ValueTask.FromResult($"""

            Client said: "{greeting}", so HelloGrain says: Hello!
            """);
    }
}
```

# 创建 Silo

修改 Silo/Program.cs 如下

```csharp
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

IHostBuilder builder = Host.CreateDefaultBuilder(args)
    .UseOrleans(silo =>
    {
        silo.UseLocalhostClustering()
            .ConfigureLogging(logging => logging.AddConsole());
    })
    .UseConsoleLifetime();

using IHost host = builder.Build();

await host.RunAsync();
```

# 创建 Orleans 的 Client

修改 Server/Program.cs

```csharp
using System.Net;
using System.Security.Cryptography.X509Certificates;
using GrainInterfaces;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Server.Kestrel.Core;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Orleans.Serialization.WireProtocol;

using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.DependencyInjection;
using GrainInterfaces;

namespace Server;

internal static class Program
{
    public static async Task Main(string[] args)
    {
        // Orleans
        IHostBuilder builder1 = Host.CreateDefaultBuilder(args).UseOrleansClient(client =>
        {
            client.UseLocalhostClustering();
        })
        .ConfigureLogging(logging => logging.AddConsole())
        .UseConsoleLifetime();

        using IHost host = builder1.Build();
        await host.StartAsync();

        IClusterClient client = host.Services.GetRequiredService<IClusterClient>();

        //IHello friend = client.GetGrain<IHello>(0);
        //string response = await friend.SayHello("Hi friend!");

        // MagicOnion
        var builder = WebApplication.CreateBuilder(args);

        builder.WebHost.UseKestrel(options =>
        {
            options.ConfigureEndpointDefaults(endpointOptions =>
            {
                endpointOptions.Protocols = HttpProtocols.Http2;
            });

            options.Listen(IPAddress.Parse("0.0.0.0"), 5000, listenOptions =>
            {
                listenOptions.Protocols = HttpProtocols.Http1;
            });

            options.Listen(IPAddress.Parse("0.0.0.0"), 5001, listenOptions =>
            {
                if (args.Any(arg => arg == "--load-cert=true"))
                {
                    Console.WriteLine("load certificate");
                    listenOptions.UseHttps(new X509Certificate2("certificate/certificate.pfx", "test"));
                }
            });
        });

        builder.Services.AddGrpc();
        builder.Services.AddMagicOnion();

        var app = builder.Build();

        app.MapGet("/", () => "Hello World!");

        app.MapMagicOnionService();

        app.Run();
    }
}
```

# 运行项目

右键点击\[解决方案\] ![](/wp-content/uploads/2024/07/QQ20240723-111325.png)设置顺序 ![](/wp-content/uploads/2024/07/QQ20240723-111431.png)点击启动 ![](/wp-content/uploads/2024/07/QQ20240723-111505.png)