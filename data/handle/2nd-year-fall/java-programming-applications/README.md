# java-programming-applications

## intro

南开大学Java语言与应用（24fall），授课老师：辛运帏。

`./labs` 目录下是实验代码，包括九个实验：

1. 第2章作业练习5(1),练习8(3)。
2. 第3章作业练习14(3),第4章练习9(4),练习10(5)
3. 第8章作业
4. 第8章作业(Playable)
5. gomoku-console
6. CDstore
7. caculator
8. painter
9. gomoku(大作业)

以及实验报告latex模板。

`./Textbook(with Code)`目录下是教材(*Thinking in Java 4th Edition* )和配套代码。

## experience

作业量确实大，但可以借鉴已有的项目做出优化和改进（在LLM时代更加容易零知识入门一个领域）。

平时基本没去上课。

- [ ] 给分待定。

## gomoku(大作业)简介

### 实验报告(`./labs/lab9(gomoku)/report/在线五子棋游戏实验报告.pdf`)摘要

本文介绍了一款基于 Java 语言的五子棋游戏程序设计，具备网络通信功能。该程序的图形用户界面（GUI）采用 Java Swing 开发。程序架构严格遵循 MVC设计模式，实现了 Controller 层、Mapper 层和 Viewer 层的分离。网络通信部分基于 UDP 协议，支持即时的网络对战和文字聊天。程序还实现了悔棋、认输、保存对战记录、复盘、输赢判断等功能，以及本地对战和其他装饰性功能，如计时器和背景音乐等。此外，本程序实现了游戏大厅功能，支持任意数量的客户端开设不同数量的游戏房间，并可自由选择加入游戏对战。游戏大厅主从节点通信、一对一对战通信等方面采用了创新性的通信方式设计。在设计过程中，本程序综合利用了 Java 语言的面向对象等特性，展现了创新性、综合性和独创性等特点。

关键词： **Java Swing；UDP 协议；MCV 设计模式；五子棋**

### GUI

#### 游戏大厅

![游戏大厅界面](./Labs/lab9(gomoku)/img/4.jpg)

#### 对战面板

![网络对战面板](./Labs/lab9(gomoku)/img/9.jpg)






