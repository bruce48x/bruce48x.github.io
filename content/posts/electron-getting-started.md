---
title: Electron 入门
date: '2024-01-07T00:35:19+08:00'
slug: electron-getting-started
draft: false
author: bruce
---

> 没想到 2024 年了，创建一个 electron 项目还是那么困难，本文记录可顺利创建 electron 项目的方法，避免后来者浪费时间。

# 创建 electron 项目

首先是使用 electron forge 创建项目

```sh
npm init electron-app@latest demo-electron -- --template=vite-typescript
```

第二，如果还没安装 `cnpm` 则执行以下命令安装

```sh
npm install cnpm -g --registry=https://registry.npmmirror.com
```

第三，安装 electron 依赖

```sh
cd demo-electron
cnpm i -D electron
```

到了这一步，electron 项目就初始化完成了，感谢 `cnpm` !

执行 `cnpm start` 可以启动项目

# 添加 react

实际开发还是需要 react 或者 vue 这类框架的，这里以 react 为例

安装 react

```sh
cnpm i -D @types/react-dom @types/react
cnpm i react react-dom
```

也许你还需要UI库，以 `antd` 为例

```sh
cnpm i antd
```

接下来，修改 `index.html`，把其中的 body 改为

```html
<html>
  <body>
    <script type="module" src="/src/renderer.tsx"></script>
    <div id="root"></div>
  </body>
</html>
```

然后把 `renderer.ts` 改名为 `renderer.tsx` 并修改其内容为

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import App from "./App";

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

然后，添加 `src/App.tsx` 文件，内容如下

```tsx
import React from "react";
import { Button } from 'antd';

function App() {
  return (
    <div>
      <h1>💖 Hello World!</h1>
      <p>Welcome to your Electron application.</p>
      <Button>Click Me</Button>
    </div>
  );
}

export default App;
```

再修改 `tsconfig.json` ，为 compilerOptions 增加以下内容

```json
{
  "compilerOptions": {
    "jsx": "react",
  }
}
```

至此，react 初始化完成

执行以下命令看效果

```sh
cnpm start
```

# 也许你喜欢的是 vue

如果你用的是 vue，不是 react，则通过以下方法来初始化

添加依赖

```sh
cnpm i vue
cnpm i -D @vitejs/plugin-vue
```

修改 index.html，将 body 的内容改为

```html
<body>
    <div id="app"></div>
    <script type="module" src="/src/renderer.ts"></script>
</body>
```

将 renderer.ts 的内容修改为

```ts
import { createApp } from 'vue';
import App from './App.vue';

createApp(App).mount('#app');
```

创建 `src/App.vue` 文件

```vue
<template>
  <h1>💖 Hello World!</h1>
  <p>Welcome to your Electron application.</p>
</template>

<script setup>
console.log('👋 This message is being logged by "App.vue", included via Vite');
</script>
```

修改配置 `vite.renderer.config.ts`

```ts
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

// https://vitejs.dev/config
export default defineConfig({
  plugins: [vue()]
});
```

至此完成VUE的安装和配置，执行 `cnpm start` 查看效果

</body></html>