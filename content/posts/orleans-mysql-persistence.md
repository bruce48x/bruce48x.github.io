---
title: Microsoft Orleans 使用 MySQL 持久化数据
date: '2024-10-26T23:45:39+08:00'
slug: orleans-mysql-persistence
draft: true
author: bruce
---

上一篇[文章](https://www.bruce2077.xyz/2024/07/23/magiconion-%e7%bb%93%e5%90%88-orleans/)介绍了 Microsoft Orleans 这个框架，这篇继续完善，介绍如何将数据保存到MySQL中。

# 首先，添加依赖

为 Silo 项目添加依赖

- `Microsoft.Orleans.Persistence.AdoNet` 8.2.0
- `MySql.Data` 8.0.33

添加依赖后，`Silo/Silo.csproj` 的内容变成：

```xml
<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net8.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="MySql.Data" Version="8.0.33" />
    <ProjectReference Include="../Grains/Grains.csproj" />
    <PackageReference Include="Microsoft.Orleans.Persistence.AdoNet" Version="8.2.0" />
    <PackageReference Include="Microsoft.Orleans.Server" Version="8.2.0" />
    <PackageReference Include="Microsoft.Extensions.Logging.Console" Version="8.0.0" />
    <PackageReference Include="Microsoft.Extensions.Hosting" Version="8.0.0" />
  </ItemGroup>

</Project>

```

然后，为 Grains 项目添加相同的依赖

- `Microsoft.Orleans.Persistence.AdoNet` 8.2.0
- `MySql.Data` 8.0.33

添加依赖后，`Grains/Grains.csproj` 的内容变成：

```xml
<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>

  <ItemGroup>
    <ProjectReference Include="../GrainInterfaces/GrainInterfaces.csproj" />
    <PackageReference Include="Microsoft.Orleans.Persistence.AdoNet" Version="8.2.0" />
    <PackageReference Include="Microsoft.Orleans.Sdk" Version="8.2.0" />
    <PackageReference Include="Microsoft.Extensions.Logging.Abstractions" Version="8.0.1" />
    <PackageReference Include="MySql.Data" Version="8.0.33" />
  </ItemGroup>

</Project>

```

# 创建数据库

执行以下命令，启动一个MySQL实例

```shell
docker run --name orleans-sample -d -e MYSQL_ROOT_PASSWORD=123456 -p 3306:3306 mysql:8.0
```

然后创建一个名为 `orleanssample` 的库

接下来，运行初始化脚本

[官方文档](https://learn.microsoft.com/en-us/dotnet/orleans/host/configuration-guide/adonet-configuration)中提到要先手动运行初始化脚本，Orleans 才能正常启动。 他们分别是：

- [MySQL-Main.sql](https://github.com/dotnet/orleans/blob/main/src/AdoNet/Shared/MySQL-Main.sql)
- [MySQL-Clustering.sql](https://github.com/dotnet/orleans/blob/main/src/AdoNet/Orleans.Clustering.AdoNet/MySQL-Clustering.sql)
- [MySQL-Persistence.sql](https://github.com/dotnet/orleans/blob/main/src/AdoNet/Orleans.Persistence.AdoNet/MySQL-Persistence.sql)
- [MySQL-Reminders.sql](https://github.com/dotnet/orleans/blob/main/src/AdoNet/Orleans.Reminders.AdoNet/MySQL-Reminders.sql)

依次运行以上几个脚本即完成数据库初始化，库中会创建如下几张表:

```txt
+-------------------------------+
| Tables_in_orleanssample       |
+-------------------------------+
| OrleansMembershipTable        |
| OrleansMembershipVersionTable |
| OrleansQuery                  |
| OrleansRemindersTable         |
| OrleansStorage                |
+-------------------------------+
```

# 修改代码，连接MySQL

将 Silo/Program.cs 改为如下：

```csharp
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

IHostBuilder builder = Host.CreateDefaultBuilder(args)
    .UseOrleans(silo =>
    {
        silo.UseLocalhostClustering()
            .ConfigureLogging(logging => logging.AddConsole())
            .AddAdoNetGrainStorage("MyStorage", options =>
            {
                options.Invariant = "MySql.Data.MySqlClient";
                options.ConnectionString = "Server=localhost;DataBase=orleanssample;uid=root;pwd=123456;pooling=true;port=3306;CharSet=utf8mb4;sslMode=None;";
            });
    })
    .UseConsoleLifetime();

using IHost host = builder.Build();

await host.RunAsync();
```

之后运行程序，看到如下日志代表启动成功：

```log
info: Orleans.Runtime.Silo[100452]
      Start deployment load collector took 50 milliseconds to finish
info: Orleans.Runtime.MembershipService.SystemTargetBasedMembershipTable[100631]
      Connected to membership table provider.
info: Orleans.Runtime.MembershipService.MembershipAgent[100663]
      Joining
info: Orleans.Storage.AdoNetGrainStorage[200409]
      Initialized storage provider: ServiceId=default ProviderName=OrleansStorage Invariant=MySql.Data.MySqlClient ConnectionString=<--SNIP-->.
info: Orleans.Runtime.MembershipService.MembershipAgent[100604]
      -BecomeActive
info: Orleans.Runtime.MembershipService.MembershipAgent[100605]
      -Finished BecomeActive.
info: Orleans.Hosting.SiloHostedService[0]
      Orleans Silo started.
info: Microsoft.Hosting.Lifetime[0]
      Application started. Press Ctrl+C to shut down.
info: Microsoft.Hosting.Lifetime[0]
      Hosting environment: Production
info: Microsoft.Hosting.Lifetime[0]
      Content root path: /Users/wangql/workspace/magiconion-sample-server/Silo/bin/Debug/net8.0

```

# 自定义持久化类

## 修改 GrainInterfaces 项目

创建 `IUserGrain.cs` 文件

```csharp
namespace GrainInterfaces;

public interface IUserGrain : IGrainWithIntegerKey
{
    public Task CreateUser(int userId, string userName);
    public Task<string> GetNameAsync();
    public Task SetNameAsync(string name);
}
```

创建 `UserState.cs`文件

```csharp
namespace GrainInterfaces;

public class UserState
{
    public int UserId { get; set; }
    public string UserName { get; set; }
}
```

## 修改 Grains 项目

创建 `UserGrain.cs` 文件

```csharp
using GrainInterfaces;
using Microsoft.Extensions.Logging;
using Orleans.Providers;

namespace Grains;

[StorageProvider(ProviderName ="MyStorage")]
public class UserGrain : Grain<UserState>, IUserGrain
{
    private readonly ILogger<UserGrain> _logger;

    public UserGrain(ILogger<UserGrain> logger)
    {
        _logger = logger;
    }

    public async Task CreateUser(int userId, string userName)
    {
        this.State.UserId = userId;
        this.State.UserName = userName;
        await this.WriteStateAsync();
    }

    public Task<string> GetNameAsync()
    {
        return Task.FromResult(this.State.UserName);
    }

    public async Task SetNameAsync(string name)
    {
        this.State.UserName = name;
        await this.WriteStateAsync();
    }

}
```

## 修改 Server 项目

修改 `Program.cs` 文件

在 Main 函数中增加以下代码

```csharp
app.MapGet("/createuser", async ([FromQuery] int userId, [FromQuery] string userName) =>
{
    IUserGrain userGrain = client.GetGrain<IUserGrain>((long)userId);
    await userGrain.CreateUser(userId, userName);
    await userGrain.GetNameAsync();
    int code = 0;
    return JsonSerializer.Serialize(new { code });
});

app.MapGet("/user", async ([FromQuery] int userId) =>
{
    IUserGrain userGrain = client.GetGrain<IUserGrain>((long)userId);
    string name = await userGrain.GetNameAsync();
    int code = 0;
    return JsonSerializer.Serialize(new { code, userId, name });
});
```

这些代码增加了两个 http 接口

- `/createuser` 接口创建用户
- `/user` 接口查询用户

## 测试

### 创建用户

执行命令

```
curl "http://localhost:5000/createuser?userId=1&userName=abc"
```

返回如下数据代表成功：

```txt
{"code":0}
```

查看数据库发现有写入:

```txt
mysql> select * from OrleansStorage \G
*************************** 1. row ***************************
           GrainIdHash: 1168708852
             GrainIdN0: 0
             GrainIdN1: 1
         GrainTypeHash: 631257761
       GrainTypeString: state
GrainIdExtensionString: NULL
             ServiceId: default
         PayloadBinary: 0x7B22246964223A2231222C222474797065223A22477261696E496E74657266616365732E5573657253746174652C20477261696E496E7465726661636573222C22557365724964223A312C22557365724E616D65223A22616263227D
            ModifiedOn: 2024-10-25 06:21:22
               Version: 1
```

### 查询用户

执行命令

```
curl "http://localhost:5000/user?userId=1"
```

返回如下数据：

```txt
{"code":0,"userId":1,"name":"abc"}
```