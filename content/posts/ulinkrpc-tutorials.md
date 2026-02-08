+++
date = '2026-01-30T19:50:03+08:00'
draft = true
title = 'ULinkRPC 入门（搭建C#双端项目 .NET 服务端 + Unity 客户端）'
+++

# 概述

由于 [MagicOnion](https://github.com/Cysharp/MagicOnion) 依赖于 gRPC，无法灵活切换传输层，对 KCP 的支持已经胎死腹中，因此我创建了 ULinkRPC 项目来满足需求。

使用 ULinkRPC 可以搭建 Unity + .NET 双端项目，实现代码共享，使用方便的目的。

# 环境

- **.NET 10** 最新的.NET的LTS版本。
- **Unity2022 LTS**

# 示例的 Git 存储库

下面是本文介绍的示例存储库。如果文章中的解释不够充分，请参考以下项目

- [ULinkRPC-Sample-Server](https://github.com/bruce48x/ULinkRPC-Sample-Server)
- [ULinkRPC-Sample-Client](https://github.com/bruce48x/ULinkRPC-Sample-Client)

# ULinkRPC 服务器

程序大致分为 ULinkRPC Server 版和 Unity 客户端版。首先，我们来谈谈 ULinkRPC Server。

## 提前准备

- 安装.NET SDK10.0 
  - [下载 .NET 10.0（Linux、macOS、Windows）](https://dotnet.microsoft.com/zh-cn/download/dotnet/10.0)
- 更新IDE 
  - 您可能需要将 Visual Studio 或 Rider 更新到最新版本才能支持 .NET8

## 初始文件夹结构

```txt
ULinkRPC-Sample-Server
├── .git
├── .gitignore
└── README.md
```

## 创建解决方案

创建一个 .NET 解决方案和两个项目，并将这两个项目添加到该解决方案中。 这两个项目之一是 Server 项目，其中包含 ULinkRPC Server 实现。第二个是Shared项目，它在Server和Unity客户端之间共享，定义了一组Interface。在Server项目端实现该接口，在Unity客户端使用该接口。

```shell
> cd ULinkRPC-Sample-Server
> dotnet new sln -n ULinkRPC-Sample-Server
> dotnet new console -n Server -o Server --framework net10.0
> dotnet sln ULinkRPC-Sample-Server.sln add Server/Server.csproj
> dotnet new classlib -n Shared -o Shared --framework netstandard2.1
> dotnet sln ULinkRPC-Sample-Server.sln add Shared/Shared.csproj
```

服务器项目指定了最新的 .NET 10。这是当前最新的LTS版本。

`Shared`被指定为`netstandard2.1`框架，因为该项目在服务器和 Unity 客户端之间共享。

从资源管理器中双击`ULinkRPC-Sample-Server.sln`将其打开。

您应该具有如下所示的目录结构:

```txt
ULinkRPC-Sample-Server
├── .git
├── .gitignore
├── README.md
├── Server
│   ├── Program.cs
│   └── Server.csproj
├── Shared
│   ├── Class1.cs
│   └── Shared.csproj
└── ULinkRPC-Sample-Server.sln

```

另外，Shared 工程在服务器端是在 .NET 10 环境中执行的，在 Unity 客户端是在 Unity 2022.3 编译环境（最高兼容C#9.0）中执行的，所以必须用C#9.0语法来编写。

## 准备 Shared 项目

Shared 项目定义一个接口。Shared项目中定义的接口将在 Server 项目中实现，并从 Unity 客户端使用。

首先修改`Shared.csproj`为以下内容

```xml
<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <TargetFramework>netstandard2.1</TargetFramework>
    <LangVersion>9.0</LangVersion>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="ULinkRPC.Runtime" Version="0.1.3" />
  </ItemGroup>

</Project>
```

## 在Shared项目中定义接口

在Shared目录下创建一个目录`Interfaces`，并在其下添加以下内容。

IMyFirstService.cs

```csharp
using ULinkRPC.Runtime;
namespace Shared.Interfaces
{
    [RpcService(1)]
    public interface IMyFirstService
    {
        [RpcMethod(1)]
        UnaryResult<int> SumAsync(int x, int y);
    }
}
```

## Package化

接下来，在共享项目根目录中添加`package.json`，以便 Unity 将共享项目识别为包。

```json
{
  "name": "com.ulinkrpc-sample-server.shared",
  "version": "0.0.1",
  "displayName": "ulinkrpc-sample-server shared"
}
```

删除不需要的Class1.cs后，Shared下的目录结构应该如下所示。

```txt
Shared
├── Interfaces
│   └── IMyFirstService.cs
├── Shared.csproj
└── package.json
```

## 准备 Server 项目

接下来，我们将准备Server项目。 首先，添加 ULinkRPC.Runtime 0.1.3 和Shared项目。 Server.csproj

```xml
<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net10.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>

  <ItemGroup>
    <ProjectReference Include="../Shared/Shared.csproj"/>
  </ItemGroup>

</Project>

```

## 在Server项目中实现接口

目录结构如下。

```txt
Server
├── Program.cs
├── Server.csproj
└─── Services
   └── MyFirstService.cs

```

MyFistService.cs

```csharp
using ULinkRPC.Runtime;
using Shared.Interfaces;

namespace Server.Services;

// Implements RPC service in the server project.
public class MyFirstService : IMyFirstService
{
    // `UnaryResult<T>` allows the method to be treated as `async` method.
    public async UnaryResult<int> SumAsync(int x, int y)
    {
        Console.WriteLine($"Received:{x}, {y}");
        return x + y;
    }
}

```

## 生成 Service Binder

先安装代码生成器

```sh
dotnet tool install -g ULinkRPC.CodeGen
```

安装之后，该命令位于 `~/.dotnet/tools` 下，需要将该路径加入全局变量 `$PATH` 使得 shell 可以找到这个命令
```sh
echo 'export PATH="$HOME/.dotnet/tools:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

执行以下命令生成 Service Binder

```sh
ulinkrpc-codegen --contracts ../Shared
```

## 实现 Server 程序的入口点

将以下内容写入服务器程序的入口点 Program.cs

```csharp
using System.Net;
using System.Net.Sockets;
using RpcCall.Server.Generated;
using RpcCall.Server.Services;
using ULinkRPC.Runtime;

const int defaultTcpPort = 20000;
var tcpPort = defaultTcpPort;
if (args.Length > 0 && int.TryParse(args[0], out var p))
    tcpPort = p;
using var cts = new CancellationTokenSource();
Console.CancelKeyPress += (_, e) =>
{
    e.Cancel = true;
    cts.Cancel();
};

Console.WriteLine($"RpcCall Server TCP listening on 0.0.0.0:{tcpPort}. Press Ctrl+C to stop.");

var tcpTask = RunTcpListenerAsync(tcpPort, cts.Token);

try
{
    await tcpTask.ConfigureAwait(false);
}
finally
{
    Console.WriteLine("Server stopped.");
}

async Task RunTcpListenerAsync(int port, CancellationToken hostCt)
{
    var listener = new TcpListener(IPAddress.Any, port);
    listener.Start();

    try
    {
        while (!hostCt.IsCancellationRequested)
        {
            TcpClient client;
            try
            {
                client = await listener.AcceptTcpClientAsync(hostCt).ConfigureAwait(false);
            }
            catch (OperationCanceledException)
            {
                break;
            }

            var transport = new TcpServerTransport(client);
            _ = RunConnectionAsync(transport, client.Client.RemoteEndPoint?.ToString() ?? "?", hostCt);
        }
    }
    finally
    {
        listener.Stop();
    }
}

async Task RunConnectionAsync(ITransport transport, string remote, CancellationToken hostCt)
{
    RpcServer? server = null;

    try
    {
        server = new RpcServer(transport);

        AllServicesBinder.BindAll(server, new PlayerService());
        await server.StartAsync(hostCt).ConfigureAwait(false);
        await server.WaitForCompletionAsync().ConfigureAwait(false);
    }
    catch (OperationCanceledException)
    {
        // Host shutdown
    }
    catch (Exception ex)
    {
        Console.WriteLine($"[{remote}] Error: {ex}");
    }
    finally
    {
        if (server is not null)
            await server.StopAsync().ConfigureAwait(false);

        await transport.DisposeAsync().ConfigureAwait(false);
    }

    Console.WriteLine($"[{remote}] Disconnected.");
}

```

我们考虑以下几点：

- 设置端点IP0.0.0.0是为了在docker容器上启动Server时更容易从主机访问。 
  - 所以如果你想在宿主机上启动服务器127.0.0.1也是可以的。

最后，将其推送到相应的 GitHub 存储库。

```shell
git push origin main
```

# Unity客户端

## 提前准备

- 安装 C++ 编译器和 Windows SDK（如果需要） 
  - 例如，您可以启动 `Visual Studio Installer` 并选择 `Change` -> `Desktop Development with C++` 进行安装。
  - IL2CPP 构建
- 从 UnityHub 创建合适的 Unity 项目 
  - 我选择了Unity2022.3.62f3c1 & URP 3D模板。
- 添加.gitignore、.gitattribute 
  - [magiconion-样本-客户端/.gitignore](https://github.com/tou-tou/magiconion-sample-client/blob/main/.gitignore)
  - [magiconion-样本-客户端/.gitattributes](https://github.com/tou-tou/magiconion-sample-client/blob/main/.gitattributes)
- 使用以下命令创建本地 git 存储库`git init`

## 通过openupm添加所需的Unity包

在`Packages` 文件夹下的`manifest.json`文件添加以下内容`scopedRegistries`。

manfest.json

```json
"scopedRegistries": [
    {
      "name": "package.openupm.com",
      "url": "https://package.openupm.com",
      "scopes": [
        "com.github-glitchenzo.nugetforunity"
      ]
    }
  ],
```

`dependencies`添加以下内容：

```json
...
 "dependencies": {
    "com.github-glitchenzo.nugetforunity": "4.5.0",
    "com.ulinkrpc-sample-server.shared": "file:../../ulinkrpc-sample-client/ulinkrpc-sample-server/Shared/"
 }
```

添加后，它将如 [manifest.json](https://github.com/bruce48x/ULinkRPC-Sample-Client/blob/main/Packages/manifest.json) 所示

然后，将 server 项目作为子模块加入 client 中

```shell
git submodule add https://github.com/bruce48x/ULinkRPC-Sample-Server ulinkrpc-sample-server
```

关于添加的包

- 指定 `"com.ulinkrpc-sample-server.shared": "file:../../ulinkrpc-sample-client/ulinkrpc-sample-server/Shared/"`, 加载共享项目。 
  - `"file:../../ulinkrpc-sample-client/ulinkrpc-sample-server/Shared/"`我们之所以指定上面两级的父目录`../../`，是为了让 `ParrelSync` 能够正常工作。
- NuGetForUnity：Unity 的 NuGet 包管理器 
  - 使用此功能，您无需导入`.unitypacakge`文件和加载 dll。
  - 它还管理软件包版本，使更新更容易。

## 添加所需的 NuGet 包

首先，通过 NuGetForUnity添加 MemoryPack 和 KCP 依赖项。

通过在 NuGetForUnity GUI 上单击或编写以下内容来`Assets/package.config`添加上面列出的所需库。

[NuGet Gallery | MemoryPack 1.21.4](https://www.nuget.org/packages/MemoryPack#dependencies-body-tab)

packages.config

```xml
<?xml version="1.0" encoding="utf-8"?>
<packages>
  <package id="Kcp" version="2.7.0" manuallyInstalled="true" />
  <package id="MemoryPack" version="1.21.4" manuallyInstalled="true" />
  <package id="System.Text.Json" version="10.0.2" manuallyInstalled="true" />
</packages>
```

## 将 AssemblyDefinition 文件添加到Shared项目

在服务器端，使用 csproj 文件解决包依赖关系，但在 Unity 端，使用 asmdef 文件来解决包依赖关系。

从 Unity 编辑器的 Projet 窗口中打开该文件夹`Packages/ulinkrpc-sample-server shared`，然后在其下创建 `Shared.asmdef` 文件。

将 `MessagePack.Annotations` 和 `MagicOnion.Abstractions` 添加到 `Assembly Deffinition References`。

这允许您加载`Shared`项目中所需的任何 MagicOnion 或 MessagePack 依赖库。

![Shared.asmdef](/wp-content/uploads/2024/07/QQ20240718-140700.png)之后，让我们将更改推送到子模块 ulinkrpc-sample-server 项目中的远程存储库。

```shell
# path-to/ulinkrpc-sample-client 
> cd ulinkrpc-sample-server
> git status
Untracked files:
  (use "git add <file>..." to include in what will be committed)
        Shared/Shared.asmdef
> git add Shared/Shared.asmdef
> git commit -m "add asmdef"
> git push origin main

```

## 客户端实施

接下来参考MagicOnion的[README](https://github.com/Cysharp/MagicOnion?tab=readme-ov-file#streaminghub)实现Streming Hub。

在 Assets 下创建 Scripts 文件夹，然后创建 GamingHubClient.cs 脚本

GamingHubClient.cs

```csharp
using System.Collections.Generic;
using System.Threading.Tasks;
using Grpc.Core;
using MagicOnion.Client;
using Shared.Interfaces;
using UnityEngine;

namespace SampleClient
{
   public class GamingHubClient : IGamingHubReceiver
   {
       private Dictionary<string, GameObject> _players = new();

       private IGamingHub _client;

       private readonly GameObject _ownPlayer;

       public GamingHubClient(GameObject player)
       {
           _ownPlayer = player;
       }

       public async ValueTask<GameObject> ConnectAsync(ChannelBase grpcChannel, string roomName, string playerName)
       {
           _client = await StreamingHubClient.ConnectAsync<IGamingHub, IGamingHubReceiver>(grpcChannel, this);

           var roomPlayers = await _client.JoinAsync(roomName, playerName, Vector3.zero, Quaternion.identity);
           foreach (var player in roomPlayers) (this as IGamingHubReceiver).OnJoin(player);

           return _players[playerName];
       }

       // methods send to server.

       public ValueTask LeaveAsync(string playerName)
       {
           foreach (var cube in _players)
               if (cube.Value.name != playerName)
                   Object.Destroy(cube.Value);

           return _client.LeaveAsync();
       }

       public ValueTask MoveAsync(Vector3 position, Quaternion rotation)
       {
           // たまにnullになることがあるので、nullチェックを入れる
           if (_client == null) return new ValueTask();
           return _client.MoveAsync(position, rotation);
       }

       // dispose client-connection before channel.ShutDownAsync is important!
       public Task DisposeAsync()
       {
           return _client.DisposeAsync();
       }

       // You can watch connection state, use this for retry etc.
       public Task WaitForDisconnect()
       {
           return _client.WaitForDisconnect();
       }

       // Receivers of message from server.

       void IGamingHubReceiver.OnJoin(Player player)
       {
           Debug.Log("Join Player:" + player.Name);

           // 自分の場合は自分のオブジェクトを生成しない
           if (_ownPlayer.name == player.Name)
           {
               _players[player.Name] = _ownPlayer;
           }
           else
           {
               var playerObject = GameObject.CreatePrimitive(PrimitiveType.Cube);
               var LitMat = Resources.Load<Material>("LitMat");
               playerObject.GetComponent<Renderer>().material = LitMat;
               playerObject.name = player.Name;
               playerObject.transform.SetPositionAndRotation(player.Position, player.Rotation);
               _players[player.Name] = playerObject;
           }
       }

       void IGamingHubReceiver.OnLeave(Player player)
       {
           Debug.Log("Leave Player:" + player.Name);

           if (_players.TryGetValue(player.Name, out var cube)) Object.Destroy(cube);
       }

       void IGamingHubReceiver.OnMove(Player player)
       {
           Debug.Log("Move Player:" + player.Name);

           if (_players.TryGetValue(player.Name, out var cube))
           {
               if (player.Name == _ownPlayer.name) return;
               cube.transform.SetPositionAndRotation(player.Position, player.Rotation);
           }
       }
   }
}
```

## 添加Cube控制器

允许您使用键盘输入操作 Cube。

创建 Controller.cs 脚本

```csharp
using UnityEngine;

namespace SampleClient
{
    public class Controller : MonoBehaviour
    {
        public float moveSpeed = 5.0f;

        void Update()
        {
            if (Input.GetKey(KeyCode.W))
            {
                transform.Translate(Vector3.forward * (moveSpeed * Time.deltaTime));
            }
            if (Input.GetKey(KeyCode.S))
            {
                transform.Translate(Vector3.back * (moveSpeed * Time.deltaTime));
            }

            if (Input.GetKey(KeyCode.A))
            {
                transform.Translate(Vector3.left * (moveSpeed * Time.deltaTime));
            }
            if (Input.GetKey(KeyCode.D))
            {
                transform.Translate(Vector3.right * (moveSpeed * Time.deltaTime));
            }

            if (Input.GetKey(KeyCode.Q))
            {
                transform.Translate(Vector3.up * (moveSpeed * Time.deltaTime));
            }
            if (Input.GetKey(KeyCode.Z))
            {
                transform.Translate(Vector3.down * (moveSpeed * Time.deltaTime));
            }
        }
    }
}
```

如下图所示，在场景中创建一个Cube（名称为user1），并将`Controller.cs`上面的内容附加到user1上。

//todo 补一张图

## 使用 UI ToolKit 添加 UI

基于`UI ToolKit`创建简单的UI并构建高效的 UI。如果还不了解 UI ToolKit 请先看[官方文档](https://docs.unity3d.com/Manual/UIE-get-started-with-runtime-ui.html)熟悉一下。

例如，创建如下所示的 UI。 ![UI Builder](/wp-content/uploads/2024/07/QQ20240718-111819.png)

让我们链接上面 UI 的每个按钮和功能，并编写一些可以工作的代码。 （UI和功能没有分离，Dispose处理很可疑，但目前可以使用......）

SampleUIClient.cs

```csharp
using System;
using Cysharp.Net.Http;
using Grpc.Core;
using Shared.Interfaces;
using Grpc.Net.Client;
using MagicOnion;
using MagicOnion.Client;
using UnityEngine;
using UnityEngine.UIElements;

namespace SampleClient
{
    public class SampleUIClient : MonoBehaviour
    {
        [SerializeField] private GameObject playerObject;
        private GamingHubClient _hubClient;
        private ChannelBase _channel;

        private TextField nameField;
        private TextField roomField;
        private bool _isConnected = false;

        private async void Start()
        {
            _channel = GrpcChannelx.ForAddress("http://127.0.0.1:5001/");

            var serviceClient = MagicOnionClient.Create<IMyFirstService>(_channel);
            var result = await serviceClient.SumAsync(100, 200);
            Debug.Log(result);

            // UIボタンと機能の連携
            var root = GetComponent<UIDocument>().rootVisualElement;
            var button = root.Q<Button>("Connect");
            button.clicked += async () =>
            {
                Debug.Log("room Button clicked!");
                if (_isConnected) return;
                _hubClient = new GamingHubClient(playerObject);
                _ = await _hubClient.ConnectAsync(_channel, roomField.value, nameField.value);
                _isConnected = true;
                nameField.isReadOnly = true;
                nameField.isReadOnly = true;
            };

            var button2 = root.Q<Button>("Disconnect");
            button2.clicked += async () =>
            {
                Debug.Log("name Button clicked!");
                _isConnected = false;
                nameField.isReadOnly = false;
                nameField.isReadOnly = false;
                await _hubClient.LeaveAsync(playerObject.name);
                await _hubClient.DisposeAsync();
            };

            nameField = root.Q<TextField>("name");
            playerObject.name = nameField.value;
            nameField.RegisterValueChangedCallback(evt =>
            {
                Debug.Log("Entered Name: " + evt.newValue);
                if (!_isConnected) playerObject.name = evt.newValue;
            });

            roomField = root.Q<TextField>("room");
            roomField.RegisterValueChangedCallback(evt =>
            {
                Debug.Log("Entered Name: " + evt.newValue);
                if (_isConnected) roomField.isReadOnly = true;
            });
        }

        private async void Update()
        {
            if (_hubClient == null) return;
            if (_isConnected)
            {
                var position = playerObject.transform.position;
                var rotation = playerObject.transform.rotation;
                await _hubClient.MoveAsync(position, rotation);
            }
        }

        private async void OnApplicationQuit()
        {
            if (_hubClient == null) return;
            await _hubClient.LeaveAsync(playerObject.name);
            await _hubClient.DisposeAsync();
        }
    }
}
```

将上述脚本附加到场景中存在的 UI 文档所附加的游戏对象（下例中的 UIClient），并将您之前创建的 user1 分配给玩家对象。 ![](/wp-content/uploads/2024/07/7c71b3129d322ffd69e492af.jpg)

## 生成 IL2CPP 代码

IL2CPP 是一种在构建时将 Unity 脚本中的 C# 代码生成的中间语言代码转换为 C++ 代码，然后编译为本机代码以生成可执行文件的机制。

另外，在通信部分（MagicOnion）和序列化部分（MessagePack）中使用了反射函数的一部分（在本例中，是一种使用对象类型信息动态生成高效代码的机制）。在大多数情况下，IL2CPP 禁止在以下位置动态生成代码。运行时，并限制依赖于动态代码生成的反射功能。

因此，IL2CPP要求提前生成依赖动态代码生成的反射函数所需的所有代码。

为了解决上述问题，MessagePack提供了代码生成工具，MagicOnion提供了SourceGnerator，所以我们将使用它们。

### MessagePack for C# 代码生成

使用 mpc (MessagePack Codegen) 生成代码。这是作为编辑器扩展提供的，因此请使用它。请参阅MessagePack [README](https://github.com/MessagePack-CSharp/MessagePack-CSharp?tab=readme-ov-file#aot-code-generation-support-for-unityxamarin)继续操作。

首先需要生成 Shared.csproj 文件

在 External Tools 中，将 `Local packages` 勾上，点击 `Regenerate project files` ，生成 Shared.csproj ![](/wp-content/uploads/2024/07/QQ20240718-114056.png)然后，按照以下设置，生成代码 ![MessagePack CodeGen](/wp-content/uploads/2024/07/7d8019992f78b6b861015249.jpg)上面的例子将生成：`Assets/Scripts/Generated/Serializer.generated.cs`

### MagicOnion 和 Resolver 注册的代码生成

根据MagicOnion 的自述文件，它可以使用源生成器生成。

确保上面生成的代码 (`MessagePackSampleResolver.Instance`和`MagicOnionClientInitializer.Resolver`)在运行时注册在静态实例中。

在Assets/Scripts/目录下创建以下内容Initializer.cs。

Initializer.cs

```csharp
using Grpc.Net.Client;
using MagicOnion.Client;
using MagicOnion.Unity;
using MessagePack;
using MessagePack.Resolvers;
using UnityEngine;

namespace SampleClient
{
    // Shared プロジェクト のアセンブリに含まれていれば、`IMyFirstService` か `IGamingHub` のどちらの指定でもOK
    [MagicOnionClientGeneration(typeof(Shared.Interfaces.IMyFirstService))]
    internal partial class MagicOnionClientInitializer
    {
    }

    public static class Initializer
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        private static void RegisterResolvers()
        {
            // NOTE: Currently, CompositeResolver doesn't work on Unity IL2CPP build. Use StaticCompositeResolver instead of it.
            StaticCompositeResolver.Instance.Register(
                // This resolver is generated by MagicOnion's Source Generator.
                // See below for details. https://github.com/Cysharp/MagicOnion?tab=readme-ov-file#ahead-of-time-compilation-support-with-source-generator
                MagicOnionClientInitializer.Resolver,
                // This resolver is generated by MessagePack's code generator.
                MessagePackSampleResolver.Instance,
                BuiltinResolver.Instance,
                PrimitiveObjectResolver.Instance,
                MessagePack.Unity.UnityResolver.Instance,
                StandardResolver.Instance
            );

            MessagePackSerializer.DefaultOptions = MessagePackSerializer.DefaultOptions
                .WithResolver(StaticCompositeResolver.Instance);
        }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        public static void OnRuntimeInitialize()
        {
            GrpcChannelProviderHost.Initialize(
                new GrpcNetClientGrpcChannelProvider(() => new GrpcChannelOptions()
                {
                    HttpHandler = new Cysharp.Net.Http.YetAnotherHttpHandler()
                    {
                        Http2Only = true
                    }
                }));
        }
    }
}
```

## 材质设置

在目录`Assets/Rsources`中生成一个材质`LitMat`，名称如下图所示。着色器是`Universal Render Pipeline/Lit`。通过将 LitMat 拖放到 user1 来更改user1 的材质。

![](https://res.cloudinary.com/zenn/image/fetch/s--NFbeLPlp--/c_limit%2Cf_auto%2Cfl_progressive%2Cq_auto%2Cw_1200/https://storage.googleapis.com/zenn-user-upload/deployed-images/6d7ae40ef5901e5c83dda754.png%3Fsha%3Df00c9279374a899d932b7d144eaa685d9fb569b5)

GameObject.CreatePrimitive(PrimitiveType.Cube)该材质附加到生成的立方体上，如下所示。由于某种原因，使用此方法时，在构建 URP 项目时未附加预期的材料。

Scripts/GamingHubClient.cs

```csharp
var playerObject = GameObject.CreatePrimitive(PrimitiveType.Cube);
Material LitMat = Resources.Load<Material>("LitMat");
playerObject.GetComponent<Renderer>().material = LitMat;
```

## 配置 IL2CPP 构建

最后，配置 IL2CPP 构建的设置。

从 Unity 编辑器中点击 `file` -> `BuildSetting` -> `PlayerSetting` -> `player`

IL2CPP 后端脚本编写

![](https://res.cloudinary.com/zenn/image/fetch/s--HY80QzqC--/c_limit%2Cf_auto%2Cfl_progressive%2Cq_auto%2Cw_1200/https://storage.googleapis.com/zenn-user-upload/deployed-images/519fc7982ef9772ce77c6748.png%3Fsha%3Daec2a04c6ad2ae388466ceb3b0619b3a97bf56ea)

在后台运行

![](https://res.cloudinary.com/zenn/image/fetch/s--EIDhiwWw--/c_limit%2Cf_auto%2Cfl_progressive%2Cq_auto%2Cw_1200/https://storage.googleapis.com/zenn-user-upload/deployed-images/f8f973142c36f2e65a1c03ba.png%3Fsha%3D9cf491de8f9f1c8ea1392518582581796e9f0d23)

将应用程序窗口大小调整为合适的大小

![](https://res.cloudinary.com/zenn/image/fetch/s--cFwR9ivm--/c_limit%2Cf_auto%2Cfl_progressive%2Cq_auto%2Cw_1200/https://storage.googleapis.com/zenn-user-upload/deployed-images/96607a105d8dd0458558f69d.png%3Fsha%3Db91961d18b81440aa767b3801c2cf121775822a8)

从 `file` -> `BuildSetting` -> `build` 来构建应用程序。

## 移动

通过直接从 IDE 运行 ulinkrpc-sample-server 服务器项目或通过构建并运行可执行文件来启动服务器。 多次单击您之前创建的 Unity 客户端可执行文件以启动多个客户端。

我感觉是这样的。[video](https://x.com/__tou__tou/status/1743201497654173782?ref_src=twsrc%5Etfw%7Ctwcamp%5Etweetembed%7Ctwterm%5E1743201497654173782%7Ctwgr%5E%7Ctwcon%5Es1_&ref_url=https%3A%2F%2Fembed.zenn.studio%2Ftweetzenn-embedded__31fdb5898b497)

## 最后

搭建环境很困难，因为有很多令人惊讶的地方，但我很高兴客户端和服务器都可以用 C# 实现！

## 参考文章

- [C# 使用 MagicOnion + MessagePack + YetAnotherHttpHandler 进行实时通信](https://bruce48x.github.io/posts/magiconion-messagepack-realtime/)