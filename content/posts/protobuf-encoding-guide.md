---
title: protobuf 编码
date: '2024-03-02T21:49:35+08:00'
slug: protobuf-encoding-guide
draft: false
author: bruce
---

# 引言

假设有如下的消息定义

```protobuf
message Person {
    string name = 1;
    uint32 age = 2;
    uint32 height = 3;
    uint32 weight = 4;
}
```

有如下数据:

```js
const person = { 
    name: 'kobe',
    age: 18,
    height: 198,
    weight: 120,
}
```

序列化后得到的数据是 `0a056272756365102118ac012041`，跟 json 字符串相比明显长度变短了

这背后的原理是什么呢，请往下看

## 消息结构

protobuf 把数据分为了以下几类：

表格1:

|---|
|-----|
|  | 0 |  | VARIANT |  | int32, int64, uint32, uint64, sint32, sint64, bool, enum |  |
|  | 1 |  | I64 |  | fixed64, sfixed64, double |  |
|  | 2 |  | LEN |  | string, bytes, embedded messages, packed repeated fields |  |
|  | 3 |  | SGROUP |  | 废弃 |  |
|  | 4 |  | EGROUP |  | 废弃 |  |
|  | 5 |  | I32 |  | fixed32, sfixed32, float |  |

类型0 的是可变长度的数字类型，在数据中有大量小数字的情况下可以达到极高的压缩效率

类型1 和 类型5 分别是 64 位和 32 位的数字

类型2 的是靠长度值 (LEN) 来确定数据长度的类型

## 编码规则

接下来逐一看看各种类型是如何编码的

### 1 数字类型

先看看最基本的类型

#### 1.1 可变长度的数字类型

可变长度的数字类型就是 类型0，包括了 32位整数、64位整数和布尔型、枚举型

可变长度的好处就是在数字较小的时候，编码占用的数据也小

用一个例子来说明

有结构如下

```protobuf
message MsgInt {
  int32 field1 = 1;
}
```

数据如下

```js
const payload = {
    field1: 12
};
```

编码后数据

```txt
080c
```

用二进制表示就是

```txt
08 = 0000 1000 
0c = 0000 1100
```

其中第一个字节是 TAG，分为前后两段，前5位是消息编号，后3位是类型

在这个例子里，消息编号是1，类型是0

第二个字节的 0000 1100 转成10进制就是12

由此可见，protobuf 编码后使用消息编号和ID来区分数据，消息的KEY是不会编码进去的

#### 1.2 固定长度的数字类型

固定长度就是 类型1 和 类型5，包括 float、double、fixed32、fixed64 等等

// todo

### 2 按长度划分的类型

### 2.1 字符串

// todo

### 2.2 字节数组

// todo

### 2.3 内嵌 message

举例：有结构如下

```protobuf
message MsgEmbeddedMsg {
  message Msg1 {
    string field1 = 1;
  }
  Msg1 field1 = 1;
}
```

有数据：

```js
const payload = {
    field1: {
        field1: 'abc'
    }
};
```

编码后数据：

```txt
0a050a03616263
```

同样，转成二进制，来分析 TAG

```txt
0a = 00001 010 = 编号1，类型2 
05 = 长度：5
0a = 00001 010 = 编号1，类型2
03 = 长度：3
61 = 数据：a
62 = 数据：b
63 = 数据：c
```

### 3 数组

数组可以包含基本类型，也可以是 message

### 3.1 数组元素是基本类型

有结构如下

```protobuf
message MsgRepeatedInt {
  repeated int32 field1 = 1;
}
```

数据如下

```js
const payload = {
    field1: [1, 2, 3]
};
```

编码结果

```txt
0a03010203
```

同样，把 TAG 转成二进制来分析

```txt
0a = 00001 010 = 编号1 和 类型2
03 = 长度：3
01 = 数据：1
02 = 数据：2
03 = 数据：3
```

#### 3.2 数组元素是 message

结构是

```protobuf
message MsgRepeatedMsg {
  message Msg1 {
    string key = 1;
    uint32 value = 2;
  }
  repeated Msg1 field1 = 1;
}
```

数据是

```js
const payload = {
    field1: [
        { key: 'a', value: 1 },
        { key: 'b', value: 2 },
        { key: 'c', value: 3 }
    ]
};
```

编码后的数据是

```txt
0a050a016110010a050a016210020a050a01631003
```

分析一下编码：

```txt
第一段数据
0a = 00001 010 = 编号1 和 类型2
05 = 长度：5
0a = 00001 010 = 编号1 和 类型2
01 = 长度：1
61 = 数据：a
10 = 00010 000 = 编号2 和 类型0
01 = 数据：1

第二段数据
0a = 00001 010 = 编号1 和 类型2
05 = 长度：5
0a = 00001 010 = 编号1 和 类型2
01 = 长度：1
62 = 数据：a
10 = 00010 000 = 编号2 和 类型0
02 = 数据：2

第三段数据
0a = 00001 010 = 编号1 和 类型2
05 = 长度：5
0a = 00001 010 = 编号1 和 类型2
01 = 长度：1
63 = 数据：a
10 = 00010 000 = 编号2 和 类型0
03 = 数据：3
```

可以看出 message 数组的编码不像 uint32 数组是有一个 总长度 值，

如果这两种数组混合编码会是什么样呢，往下看

#### 3.3 多数组

结构是

```protobuf
message MsgMultipleArray {
  message Msg1 {
    string key = 1;
    uint32 value = 2;
  }
  repeated uint32 arr1 = 1;
  repeated Msg1 arr2 = 2;
  repeated uint32 arr3 = 3;
}
```

数据是

```js
const payload = {
    arr1: [1,2,3],
    arr2: [
        { key: 'a', value: 1 },
        { key: 'b', value: 2 },
        { key: 'c', value: 3 }
    ],
    arr3: [1,2,3],
};
```

编码后的数据是

```txt
0a0301020312050a0161100112050a0162100212050a016310031a03010203
```

分析一下编码：

```txt
第 1 段数据
0a = 00001 010 = 编号1 和 类型2
03 = 长度：3
01 = 数据：1
02 = 数据：2
03 = 数据：3

第 2.1 段数据
12 = 00010 010 = 编号2 和 类型2
05 = 长度：5
0a = 00001 010 = 编号1 和 类型2
01 = 长度：1
61 = 数据：a
10 = 00010 000 = 编号2 和 类型0
01 = 数据：1

第 2.2 段数据
12 = 00010 010 = 编号2 和 类型2
05 = 长度：5
0a = 00001 010 = 编号1 和 类型2
01 = 长度：1
62 = 数据：b
10 = 00010 000 = 编号2 和 类型0
02 = 数据：2

第 2.3 段数据
12 = 00010 010 = 编号2 和 类型2
05 = 长度：5
0a = 00001 010 = 编号1 和 类型2
01 = 长度：1
63 = 数据：c
10 = 00010 000 = 编号2 和 类型0
03 = 数据：3

第 3 段数据
1a = 00011 010 = 编号3 和 类型2
03 = 长度：3
01 = 数据：1
02 = 数据：2
03 = 数据：3
```

如果再复杂一些，是嵌套多层得数组呢？继续往下看

#### 3.4 嵌套数组

结构是：

```protobuf
message MsgNestedArray {
  message Msg1 {
    string key = 1;
    uint32 value = 2;
    repeated uint32 arr1 = 3;
  }
  repeated uint32 arr1 = 1;
  repeated Msg1 arr2 = 2;
  repeated uint32 arr3 = 3;
}
```

相比例子 3.3，其中 Msg1 多了第3个字段：名为 arr1 的 uint32 数组

数据是:

```js
const payload = {
    arr1: [1,2,3],
    arr2: [
        { key: 'a', value: 1, arr1: [3,2,1] },
        { key: 'b', value: 2, arr1: [3,2,1] },
        { key: 'c', value: 3, arr1: [3,2,1] }
    ],
    arr3: [1,2,3],
};
```

编码后的数据是

```txt
0a03010203120a0a016110011a03030201120a0a016210021a03030201120a0a016310031a030302011a03010203
```

分析一下编码：

```txt
第 1 段数据
0a = 00001 010 = 编号1 和 类型2
03 = 长度：3
01 = 数据：1
02 = 数据：2
03 = 数据：3

第 2.1 段数据
12 = 00010 010 = 编号2 和 类型2
0a = 长度：10
0a = 00001 010 = 编号1 和 类型2
01 = 长度：1
61 = 数据：a
10 = 00010 000 = 编号2 和 类型0
01 = 数据：1
1a = 00011 010 = 编号3 和 类型2
03 = 长度：3
03 = 数据：3
02 = 数据：2
01 = 数据：1

第 2.2 段数据（与2.1类似）
12
0a
0a
01
62
10
02
1a
03
03
02
01

第 2.3 段数据（与2.1类似）
12
0a
0a
01
63
10
03
1a
03
03
02
01

第 3 段数据
1a = 00011 010 = 编号3 和 类型2
03 = 长度：3
01 = 数据：1
02 = 数据：2
03 = 数据：3
```

### 4 字典

#### 4.1 字典值是基础类型

结构是

```protobuf
message MsgMapStringInt {
  map<string, int32> field1 = 1;
}
```

数据是

```js
const payload = {
    field1: {
        'a': 1,
        'b': 2,
        'c': 3
    }
};
```

编码后的数据是

```txt
0a050a016110010a050a016210020a050a01631003
```

有趣的事情来了

编码的结果跟之前例子 3.2 的 message 数组是一样的

protobuf 把 map 里的每一对 key-value 当作数组的元素来处理。

#### 4.2 字典值是 message

结构：

```protobuf
message MsgMap {
  message Msg1 {
    string key = 1;
    uint32 value = 2;
  }
  map<string, Msg1> field1 = 1;
}
```

数据：

```js
const payload = {
    field1: {
        'a': { key: 'x', value: 1 },
        'b': { key: 'y', value: 2 },
        'c': { key: 'z', value: 3 }
    }
};
```

编码后数据：

```txt
0a0a0a016112050a017810010a0a0a016212050a017910020a0a0a016312050a017a1003
```

转二进制进行分析：

```txt
0a = 00001 010 = 编号1 和 类型2
0a
0a
01
61
12
05
0a
01
78
10
01
0a
0a
0a
01
62
12
05
0a
01
79
10
02
0a
0a
0a
01
63
12
05
0a
01
7a
10
03
```

## 最后

看到这儿，你可以分析出本文最初的例子的编码为什么是 `0a056272756365102118ac012041` 了吗，留这个作业给读者自己动动手。