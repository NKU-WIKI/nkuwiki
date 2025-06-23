# 数据库指南

本文档介绍 nkuwiki 项目中使用的数据库，包括 MySQL 和 Qdrant。

## 概述

项目中主要使用以下数据库：

*   **MySQL**: 用于存储结构化数据。库表结构定义位于 `etl/load/mysql_tables` 目录下。项目通过 `etl/load/db_core.py` 与 MySQL 数据库进行交互。
*   **Qdrant**: 用于向量存储和相似性搜索。

## MySQL

### 结构

（待补充，可链接到 `etl/load/mysql_tables` 下的具体定义文件或进行概述）

### 交互

（待补充，可说明 `etl/load/db_core.py` 的使用方法）

## Qdrant

### 配置与使用

（待补充）

## 数据备份与恢复

（待补充） 