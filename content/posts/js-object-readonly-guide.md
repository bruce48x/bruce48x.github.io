---
title: 将 js 对象设置为只读
date: '2022-11-12T15:34:57+08:00'
slug: js-object-readonly-guide
draft: false
author: bruce
---

在日常开发中，经常遇到一种情况，就是读配置

然而有时可能不小心会在业务逻辑中把配置给改了，导致之后的读取出现异常

## 使用 Proxy

要避免这类问题，使用 js 的 Proxy 将配置设置为只读是一个很好的办法

话不多说，上代码

```js
const handler = {
    get: function (target, key) {
        if (
            typeof target[key] === 'object' &&
            target[key] != null
        ) {
            return new Proxy(target[key], handler);
        } else {
            return Reflect.get(target, key);
        }
    },
    set: function (target, key, value) {
        return true;
    },
    defineProperty: function (target, key, desc) {
        return true;
    },
    deleteProperty: function (target, key) {
        return false;
    },
};
// 原始配置
const configData = { a: 'aaa', b: 'bbb' };
// 设置为只读的配置
const cnf = new Proxy(configData, handler);
// 尝试修改 cnf 对象
cnf.c = 'ccc';
console.log(cnf); // { a: 'aaa', b: 'bbb' }
```

使用这个定制 handler 后，怎么改 cnf 的值，它都不会变了

原因就在于 handler 中的 set 和 defineProperty 方法

不进行任何赋值，自然就不会修改原始数据了

另外一个需要注意的点，在 get 方法中

在判断子属性是对象时，需要再包裹一层 proxy，因为 proxy 只对对象的最上层属性产生作用

因而多层的对象，需要每一层都设置 proxy

## 还有要考虑的问题

上面这个 handler 的例子，在设置时并不做任何提示，有些使用场合下，可能抛出异常会更好，读者请自己判断这一点

## 别的方法可以吗

当然别的思路也能达到同样的目的，那就是深拷贝

例如

```js
const cnf = JSON.parse(JSON.stringify(configData));
```

通过 json 序列化和反序列化的方式拷贝数据

但是这么做会有大量的内存拷贝的调用发生，性能消耗大概是 proxy 的几十倍

不建议使用这种方式