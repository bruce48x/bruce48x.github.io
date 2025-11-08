---
title: Sign in with Apple
date: '2023-04-03T17:46:34+08:00'
slug: sign-in-with-apple-guide
draft: false
author: bruce
---

# 概述

我在实现 Sign in with Apple 时查看了很多文档，越看疑问越多

- 为什么苹果设备上实现的流程和 WEB 端如此不同
- 服务端验证时为什么除了 id token，还有一个 auth code，到底是干嘛用的
- 什么是 nonce ，如何验证 nonce
- 为什么要获取 refresh token 和 access token，我似乎用不到它们

直到我知道了 Apple ID 背后的原理，这些疑团就逐步解开了，

简单的说：***Sign in with Apple 是基于 OpenID Connect 协议的，简称 OIDC 协议，弄懂了 OIDC 就弄懂了 Sign in with Apple***

接下来就先弄清楚：什么是 OIDC 协议

# 原理部分

## OpenID Connect 协议

OIDC 协议是基于 Oauth2.0 协议的，额外提供了身份认证的功能。

所以要弄清楚 OIDC 协议，又要先了解 Oauth2.0 协议（套娃了属于是）。

Oauth2.0 协议提供了“授权”的功能，给第三方开发者一个`访问令牌`，在有限的范围内，访问用户的数据，给用户提供服务又不过度索取用户信息

举例：

你开发了一个照片编辑网站，可以美化用户的照片，而照片源数据在用户的QQ相册里，

这时 QQ相册提供了授权功能，你就可以接入这个系统，获取用户的授权，给用户提供照片美化服务。

这时候有人可能就问了，为什么搞这么麻烦，让用户把账号密码给我不就好了吗？

没错，这样是很方便，但是这种方式极度不安全

如果你是用户，你敢把账号密码交给别人吗，APP开发者的节操是不可靠的，网络的角落里还有无数黑客在盯着这些宝贵的数据。

在这种背景下，Oauth2.0 提供了非常好的方案来解决授权的问题。

那 Oauth2.0 解决了授权的问题，为什么还要有 OIDC 协议，

是因为 Oauth2.0 只解决了“授权”的问题，现实世界中，第三方还需要身份信息，而令牌并不提供身份信息，所以用起来还是不够方便

Oauth2.0 是授权 (authentication)

OIDC 是认证（authorization)

因此 OIDC 协议提供了“认证”的功能，提供了`身份令牌`，让第三方可以获取用户的ID，以此标记用户的身份。

关于 OIDC 协议的详细的规范，在官方的文档里写得很清楚了，我只列出流程让你更有具体的感受：

1. 你的网站中加入一个“使用QQ登录”的按钮
2. 用户点击，跳转到QQ的授权页面
3. 用户输入账号密码，确认授权，
4. 跳转回你的网站，并附带认证需要的参数
5. 你将上一步得到的参数发送给网站后端，进一步验证并获取`身份令牌`和`访问令牌`
6. 使用`身份令牌`中的用户ID为用户创建一个账号
7. 使用`访问令牌`访问用户的照片，为用户提供照片编辑服务

# 实现部分

这个部分我就不写了（真的很懒），已经有足够多优秀的文章教你如何实现

在验证的这一步，如果用不到 access token，可以不验证 auth code 的

# 参考

- OIDC 官方：[OpenID Connect core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
- OAuth 官方：[OAuth](https://oauth.net/2/)
- 苹果官方文档：[Sign in with Apple](https://developer.apple.com/documentation/sign_in_with_apple)
- 教程，来自 okta：[what the heck is sign in with apple](https://developer.okta.com/blog/2019/06/04/what-the-heck-is-sign-in-with-apple)
- 教程，来自阮一峰：[OAuth 2.0 的一个简单解释](https://www.ruanyifeng.com/blog/2019/04/oauth_design.html)
- 图解 OpenID Connect：[OIDC(OpenId Connect)身份认证(核心部分)](https://linianhui.github.io/authentication-and-authorization/04-openid-connect-core/)
- 教程，来自简书：[Sign in with Apple（苹果授权登陆）服务端验证](https://www.jianshu.com/p/655972b0e7da)
- 教程，来自简书：[Sign in with Apple 登录详解](https://www.jianshu.com/p/8190f25eaa14)
- 教程来自 sarunw.com：[sign in with apple](https://sarunw.com/posts/sign-in-with-apple-4/)
- google文档：[SIWA服务端验证](https://drive.google.com/file/d/1G7r8W_gX_eEGVadsORLmCW1yH-3BoWE3/view)[](https://www.ruanyifeng.com/blog/2019/04/oauth_design.html)
- Auth0的文档: [Add Sign In with Apple to Native iOS Apps](https://auth0.com/docs/authenticate/identity-providers/social-identity-providers/apple-native)
- 又一篇优秀的文章：[Sign in with Apple 的设计准则和功能实现](https://steppark.net/15676959360699.html)[](https://linianhui.github.io/authentication-and-authorization/04-openid-connect-core/)