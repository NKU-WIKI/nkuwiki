<!--
 * @Date: 2019-08-31 18:21:07
 * @LastEditors: Aliver
 * @LastEditTime: 2019-08-31 19:25:34
 -->
# 项目说明

## 目录结构

```bash
.
├── B-Tree
│   ├── BTree.h
│   ├── BTree.hpp
│   ├── B-Tree.vcxproj
│   ├── B-Tree.vcxproj.filters
│   ├── B-Tree.vcxproj.user
│   └── main.cpp
├── B-Tree.sln
├── btree-test
│   ├── 1750817-btree-input-1.dat
│   ├── 1750817-btree-input-2.dat
│   ├── 1750817-btree-input-3.dat
│   ├── 1750817-btree-output-1.dat
│   ├── 1750817-btree-output-2.dat
│   └── 1750817-btree-output-3.dat
├── makedat
│   └── makedat.cpp
└── README.md
```

## 命令参数

1. B-tree 命令
> --input \*.\*, 其中 "\*.\*" 为数据文件

2. makedat 命令
> --help, 用法帮助
> --order [m], 指定为 m 阶b树
> --output [filename], 指定输出的数据文件名

## 输出说明

输出 B树 结构如下：

```txt
(2:40 73) 
(1:32)-(2:49 52)-(1:124)
```

- (2:40 73) 表示该结点有两个关键字，分别为 40、73
- (1:32)-(2:49 52) 表示该两个结点为兄弟结点
- 总体结构表示根结点有三个孩子