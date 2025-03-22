import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from etl import *
import mysql.connector  # 添加mysql.connector导入
from etl.load import get_conn, load_logger

"""
etl/load/py_mysql.py - MySQL数据库操作模块

主要函数:
- init_database(): 分步初始化数据库
- create_table(table_name): 根据表名创建对应的表结构
- process_file(file_path): 处理指定的JSON文件并返回数据字典
- export_wechat_to_mysql(n): 将微信文章数据导出到MySQL数据库
- query_table(table_name, limit): 查询指定表中的数据
- delete_table(table_name): 删除指定的表
- insert_record(table_name, data): 向指定表中插入单条记录
- update_record(table_name, record_id, data): 更新指定表中的记录
- delete_record(table_name, record_id): 删除指定表中的记录
- get_record_by_id(table_name, record_id): 根据ID获取指定表中的记录
- query_records(table_name, conditions, order_by, limit, offset): 按条件查询表中记录
- count_records(table_name, conditions): 计算符合条件的记录数量
- batch_insert(table_name, records, batch_size): 批量插入记录
- execute_custom_query(query, params, fetch): 执行自定义SQL查询
- upsert_record(table_name, data, unique_fields): 更新或插入记录
- get_all_tables(): 获取数据库中所有表
- get_table_structure(table_name): 获取表结构
- get_nkuwiki_tables(): 获取nkuwiki数据库中的所有表
- transfer_table_from_mysql_to_nkuwiki(table_name): 将表从MySQL迁移到nkuwiki数据库
- import_json_dir_to_table(dir_path, table_name, platform, tag, batch_size): 将目录中的JSON文件导入到指定表
- execute_raw_query(query, params=None): 执行原生SQL查询，返回查询结果
"""

def init_database():
    """分步初始化数据库
    
    步骤：
    1. 检查nkuwiki数据库连接是否正常
    2. 执行所有SQL文件创建表结构
    
    Raises:
        Exception: 任一阶段失败时抛出异常
    """
    try:
        # 第一步：连接到nkuwiki数据库，检查连接是否正常
        conn = get_conn(use_database=True)
        load_logger.info("成功连接到nkuwiki数据库")
        conn.close()
    except mysql.connector.Error as err:
        load_logger.error(f"连接nkuwiki数据库失败: {err}")
        sys.exit(1)
        
    # 获取mysql_tables目录
    sql_dir = Path(__file__).parent / "mysql_tables"
    if not sql_dir.exists():
        load_logger.error(f"SQL文件目录不存在: {sql_dir}")
        sys.exit(1)
    
    # 获取目录下所有SQL文件
    sql_files = list(sql_dir.glob("*.sql"))
    if not sql_files:
        load_logger.warning("未找到任何SQL文件")
        return
    
    # 尝试创建所有表
    success_count = 0
    failed_tables = []
    
    for sql_file in sql_files:
        table_name = sql_file.stem  # 获取文件名（不含扩展名）
        try:
            create_table(table_name)
            success_count += 1
            load_logger.info(f"表 {table_name} 已创建或已存在")
        except Exception as e:
            load_logger.error(f"创建表 {table_name} 失败: {e}")
            failed_tables.append(table_name)
    
    # 报告创建结果
    if failed_tables:
        load_logger.warning(f"共{len(sql_files)}个表，成功创建{success_count}个，失败{len(failed_tables)}个")
        load_logger.warning(f"创建失败的表: {', '.join(failed_tables)}")
    else:
        load_logger.info(f"所有表({success_count}个)均已成功创建或已存在")

def create_table(table_name: str) -> bool:
    """根据表名执行对应的SQL文件创建表结构
    
    Args:
        table_name: 要创建的表名称（对应.sql文件名）
        
    Returns:
        bool: 表是否创建成功
        
    Raises:
        FileNotFoundError: 当SQL文件不存在时抛出
        ValueError: 表名不合法时抛出
    """
    try:
        # 验证表名合法性（防止路径遍历）
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
            raise ValueError(f"非法表名: {table_name}")
            
        # 修改SQL文件查找路径，指向正确的mysql_tables目录
        sql_dir = Path(__file__).parent / "mysql_tables"
        sql_file = sql_dir / f"{table_name}.sql"
        
        if not sql_file.exists():
            raise FileNotFoundError(f"SQL文件不存在: {sql_file}")

        with get_conn() as conn:
            with conn.cursor() as cur:
                # 读取并执行SQL文件
                sql_content = sql_file.read_text(encoding='utf-8')
                for statement in sql_content.split(';'):
                    statement = statement.strip()
                    if statement:
                        try:
                            cur.execute(statement)
                        except mysql.connector.Error as err:
                            load_logger.error(f"执行SQL失败: {err}\n{statement}")
                            conn.rollback()
                            return False
                conn.commit()
                load_logger.debug(f"表 {table_name} 在nkuwiki数据库中创建成功，使用SQL文件: {sql_file.name}")
                return True

    except (FileNotFoundError, ValueError) as e:
        load_logger.error(str(e))
        return False
    except mysql.connector.Error as err:
        load_logger.error(f"数据库错误: {err}")
        return False
    except Exception as e:
        load_logger.exception("表结构创建失败")
        return False

def process_file(file_path: str, platform: str = "wechat") -> Dict:
    """处理单个JSON文件并返回清洗后的数据
    
    Args:
        file_path: JSON文件路径
        platform: 平台名称，默认为wechat
        
    Returns:
        dict: 清洗后的结构化数据
        
    Raises:
        ValueError: 缺少必要字段时抛出
        JSONDecodeError: JSON解析失败时抛出
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 修改必要字段验证
        required_fields = ['scrape_time', 'publish_time', 'title', 'author', 'original_url']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"缺少必要字段: {field}")

        # 数据清洗
        processed_data = {
            "platform": platform,
            "scrape_time": data["scrape_time"].replace(" ", "T"),
            "publish_time": data["publish_time"],
            "title": str(data.get("title", "")).strip(),
            "author": str(data.get("author", "")).strip(),
            "original_url": data["original_url"]
        }
        
        # 添加内容字段处理
        if "content" in data:
            processed_data["content"] = str(data["content"])
        else:
            # 尝试从其他可能的字段获取内容
            content_fields = ["text", "article_content", "body", "html"]
            for field in content_fields:
                if field in data and data[field]:
                    processed_data["content"] = str(data[field])
                    break
            
            # 如果仍然没有找到内容，设置为摘要信息
            if "content" not in processed_data:
                processed_data["content"] = f"未找到内容。标题: {processed_data['title']}"
        
        # 处理可能的内容类型字段
        if "content_type" in data:
            processed_data["content_type"] = data["content_type"]
        
        return processed_data
    except json.JSONDecodeError as e:
        load_logger.error(f"文件 {file_path} 不是有效的JSON: {str(e)}")
        raise

def export_wechat_to_mysql(n: int):
    """将微信JSON数据导入MySQL数据库
    
    Args:
        n: 最大导入数量限制
        
    流程：
    1. 初始化数据库连接
    2. 加载元数据文件
    3. 批量插入数据（支持断点续传）
    4. 使用upsert方式更新重复记录
    """
    
    # 初始化数据库连接
    init_database()

    # 读取所有匹配的元数据文件
    metadata_dir = RAW_PATH / "processed"
    
    # 修改后：使用正则表达式匹配带日期的元数据文件
    metadata_files = [
        f for f in metadata_dir.glob("*.json") 
        if re.match(r"^wechat_metadata_\d{8}\.json$", f.name)
    ]
    
    if not metadata_files:
        load_logger.error("未找到符合格式的元数据文件，文件名应为：wechat_metadata_YYYYMMDD.json")
        return

    # 合并多个元数据文件
    metadata = []
    for file in metadata_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                metadata.extend(json.load(f))
                load_logger.debug(f"已加载元数据文件：{file.name}（{len(metadata)}条记录）")
        except Exception as e:
            load_logger.error(f"加载元数据文件失败 {file}: {str(e)}")
            continue

    total_items = len(metadata)
    process_data = metadata[:n]

    with get_conn() as conn:
        conn.autocommit = False
        
        load_logger.info(f"开始处理 {len(process_data)}/{total_items} 条数据（配置限制 import_limit={n}）")

        batch_size = 100
        data_batch = []
        
        with conn.cursor() as cursor:
            for i, data in enumerate(process_data, 1):
                try:
                    # 修改后：添加content_type字段
                    data_batch.append((
                        data["publish_time"],
                        str(data.get("title", "")).strip(),
                        str(data.get("author", "")).strip(),
                        data["original_url"],
                        data["platform"],
                        data.get("content_type")  # 新增content_type字段
                    ))

                    if i % batch_size == 0 or i == len(process_data):
                        cursor.executemany("""
                            INSERT INTO wechat_nku_articles 
                            (publish_time, title, author, original_url, platform, content_type)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE 
                                title=VALUES(title),
                                publish_time=VALUES(publish_time),
                                author=VALUES(author),
                                platform=VALUES(platform),
                                content_type=VALUES(content_type)  # 新增更新字段
                        """, data_batch)
                        conn.commit()
                        data_batch = []
                        load_logger.info(f"已提交 {i}/{len(process_data)} ({i/len(process_data):.1%})")

                except Exception as e:
                    load_logger.error(f"数据记录处理失败: {str(e)}\n{json.dumps(data, ensure_ascii=False)}")
                    continue

        load_logger.info("数据导入完成")

def query_table(table_name: str, limit: int = None) -> list:
    """查询指定表内容
    
    Args:
        table_name: 要查询的表名
        limit: 返回结果最大条数，默认None表示不限制
        
    Returns:
        list: 查询结果列表，元素为字典形式的记录
    """
    try:
        with get_conn() as conn:
            with conn.cursor(dictionary=True) as cursor:
                if limit:
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT %s", (limit,))
                else:
                    cursor.execute(f"SELECT * FROM {table_name}")
                result = cursor.fetchall()
                load_logger.info(f"查询表 {table_name} 成功，获取 {len(result)} 条记录")
                return result
    except Exception as e:
        load_logger.error(f"查询表 {table_name} 失败: {str(e)}")
        return []

def delete_table(table_name: str) -> bool:
    """删除指定数据库表
    
    Args:
        table_name: 要删除的表名
        
    Returns:
        bool: 删除是否成功
        
    Raises:
        mysql.connector.Error: 数据库操作失败时抛出
    """
    try:
        # 验证表名格式（防止SQL注入）
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
            raise ValueError(f"非法表名: {table_name}")
            
        with get_conn() as conn:
            with conn.cursor() as cursor:
                # 使用字符串格式化（需先验证表名）
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
                conn.commit()
                load_logger.warning(f"成功删除表: {table_name}")
                return True
    except mysql.connector.Error as e:
        load_logger.error(f"删除表 {table_name} 失败: {str(e)}")
        raise
    except ValueError as e:
        load_logger.error(f"表名验证失败: {str(e)}")
        return False
    except Exception as e:
        load_logger.error(f"发生未知错误: {str(e)}")
        return False

def insert_record(table_name: str, data: Dict[str, Any]) -> int:
    """向指定表插入单条记录
    
    Args:
        table_name: 表名
        data: 字段和值的字典
        
    Returns:
        int: 插入记录的ID，失败返回-1
    """
    try:
        # 验证表名
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
            raise ValueError(f"非法表名: {table_name}")
            
        fields = list(data.keys())
        values = list(data.values())
        placeholders = ', '.join(['%s'] * len(fields))
        
        with get_conn() as conn:
            with conn.cursor() as cursor:
                query = f"INSERT INTO {table_name} ({', '.join(fields)}) VALUES ({placeholders})"
                cursor.execute(query, values)
                conn.commit()
                last_id = cursor.lastrowid
                load_logger.debug(f"向表 {table_name} 插入记录成功，ID: {last_id}")
                return last_id
    except mysql.connector.Error as e:
        load_logger.error(f"插入记录失败: {str(e)}")
        return -1

def update_record(table_name: str, record_id: int, data: Dict[str, Any]) -> bool:
    """更新表中指定ID的记录
    
    Args:
        table_name: 表名
        record_id: 记录ID
        data: 要更新的字段和值的字典
        
    Returns:
        bool: 更新是否成功
    """
    try:
        # 验证表名
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
            raise ValueError(f"非法表名: {table_name}")
            
        if not data:
            load_logger.warning("没有提供更新数据")
            return False
            
        set_clause = ", ".join([f"{key} = %s" for key in data.keys()])
        values = list(data.values())
        
        with get_conn() as conn:
            with conn.cursor() as cursor:
                query = f"UPDATE {table_name} SET {set_clause} WHERE id = %s"
                cursor.execute(query, [*values, record_id])
                conn.commit()
                affected_rows = cursor.rowcount
                # load_logger.debug(f"更新表 {table_name} 记录成功，ID: {record_id}, 影响行数: {affected_rows}")
                return affected_rows > 0
    except mysql.connector.Error as e:
        load_logger.error(f"更新记录失败: {str(e)}")
        return False

def delete_record(table_name: str, record_id: int) -> bool:
    """删除表中指定ID的记录
    
    Args:
        table_name: 表名
        record_id: 记录ID
        
    Returns:
        bool: 删除是否成功
    """
    try:
        # 验证表名
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
            raise ValueError(f"非法表名: {table_name}")
            
        with get_conn() as conn:
            with conn.cursor() as cursor:
                query = f"DELETE FROM {table_name} WHERE id = %s"
                cursor.execute(query, (record_id,))
                conn.commit()
                affected_rows = cursor.rowcount
                load_logger.debug(f"删除表 {table_name} 记录成功，ID: {record_id}, 影响行数: {affected_rows}")
                return affected_rows > 0
    except mysql.connector.Error as e:
        load_logger.error(f"删除记录失败: {str(e)}")
        return False

def get_record_by_id(table_name: str, record_id: int) -> Optional[Dict[str, Any]]:
    """根据ID获取单条记录
    
    Args:
        table_name: 表名
        record_id: 记录ID
        
    Returns:
        Optional[Dict]: 记录字典，未找到返回None
    """
    try:
        # 验证表名
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
            raise ValueError(f"非法表名: {table_name}")
            
        with get_conn() as conn:
            with conn.cursor(dictionary=True) as cursor:
                query = f"SELECT * FROM {table_name} WHERE id = %s"
                cursor.execute(query, (record_id,))
                result = cursor.fetchone()
                if result:
                    # 直接返回字典结果，因为我们使用了dictionary=True
                    load_logger.debug(f"查询表 {table_name} 记录成功，ID: {record_id}")
                    return result
                return None
    except mysql.connector.Error as e:
        load_logger.error(f"查询记录失败: {str(e)}")
        return None

def query_records(table_name: str, conditions: Dict[str, Any] = None, order_by: str = None, 
                limit: int = 1000, offset: int = 0) -> List[Dict[str, Any]]:
    """条件查询记录
    
    Args:
        table_name: 表名
        conditions: 条件字典，格式为 {字段名: 值}
        order_by: 排序字段，格式为 "字段名 ASC/DESC"
        limit: 返回结果最大条数
        offset: 分页起始位置
        
    Returns:
        List[Dict]: 查询结果列表
    """
    try:
        # 验证表名
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
            raise ValueError(f"非法表名: {table_name}")
            
        where_clause = ""
        values = []
        
        if conditions:
            where_parts = []
            for key, value in conditions.items():
                where_parts.append(f"{key} = %s")
                values.append(value)
            where_clause = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""
        
        order_clause = f"ORDER BY {order_by}" if order_by else ""
        limit_clause = f"LIMIT {limit} OFFSET {offset}"
        
        with get_conn() as conn:
            with conn.cursor(dictionary=True) as cursor:
                query = f"SELECT * FROM {table_name} {where_clause} {order_clause} {limit_clause}"
                cursor.execute(query, values)
                
                # 获取结果集
                result = cursor.fetchall()
                load_logger.debug(f"条件查询表 {table_name} 成功，获取 {len(result)} 条记录")
                return result
    except mysql.connector.Error as e:
        load_logger.error(f"条件查询失败: {str(e)}")
        return []

def count_records(table_name: str, conditions: Dict[str, Any] = None) -> int:
    """统计记录数量
    
    Args:
        table_name: 表名
        conditions: 条件字典，格式为 {字段名: 值}
        
    Returns:
        int: 记录数量，失败返回-1
    """
    try:
        # 验证表名
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
            raise ValueError(f"非法表名: {table_name}")
            
        where_clause = ""
        values = []
        
        if conditions:
            where_parts = []
            for key, value in conditions.items():
                where_parts.append(f"{key} = %s")
                values.append(value)
            where_clause = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""
        
        with get_conn() as conn:
            with conn.cursor() as cursor:
                query = f"SELECT COUNT(*) FROM {table_name} {where_clause}"
                cursor.execute(query, values)
                count = cursor.fetchone()[0]
                load_logger.debug(f"统计表 {table_name} 记录数: {count}")
                return count
    except mysql.connector.Error as e:
        load_logger.error(f"统计记录数失败: {str(e)}")
        return -1

def batch_insert(table_name: str, records: List[Dict[str, Any]], batch_size: int = 100) -> int:
    """批量插入记录
    
    Args:
        table_name: 表名
        records: 记录字典列表
        batch_size: 每批次提交的记录数
        
    Returns:
        int: 成功插入的记录数
    """
    if not records:
        load_logger.warning("没有提供记录数据")
        return 0
        
    try:
        # 验证表名
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
            raise ValueError(f"非法表名: {table_name}")
            
        # 使用第一条记录的键作为字段
        fields = list(records[0].keys())
        placeholders = ', '.join(['%s'] * len(fields))
        
        success_count = 0
        with get_conn() as conn:
            conn.autocommit = False
            with conn.cursor() as cursor:
                query = f"INSERT INTO {table_name} ({', '.join(fields)}) VALUES ({placeholders})"
                # 批量处理数据
                for i in range(0, len(records), batch_size):
                    batch = records[i:i+batch_size]
                    values = [[record.get(field) for field in fields] for record in batch]
                    try:
                        cursor.executemany(query, values)
                        conn.commit()
                        success_count += cursor.rowcount
                        load_logger.debug(f"批量插入进度: {i+len(batch)}/{len(records)} ({(i+len(batch))/len(records):.1%})")
                    except mysql.connector.Error as e:
                        conn.rollback()
                        load_logger.error(f"批量插入批次 {i//batch_size + 1} 失败: {str(e)}")
                
        load_logger.debug(f"批量插入完成，成功: {success_count}/{len(records)}")
        return success_count
    except mysql.connector.Error as e:
        load_logger.error(f"批量插入失败: {str(e)}")
        return 0

def execute_custom_query(query: str, params: Union[List[Any], Tuple[Any, ...], None] = None, fetch: bool = True) -> Union[List[Dict[str, Any]], None]:
    """执行自定义SQL查询
    
    Args:
        query: SQL查询语句，支持 ? 和 %s 两种占位符
        params: 查询参数，支持列表或元组
        fetch: 是否获取结果
        
    Returns:
        查询结果列表，每个结果是一个字典
    """
    with get_conn() as conn:
        with conn.cursor(dictionary=True) as cursor:
            try:
                # 增加超时时间到30秒
                cursor.execute("SET SESSION MAX_EXECUTION_TIME=30000")
                
                # 设置更大的缓冲区
                cursor.execute("SET SESSION group_concat_max_len = 1000000")
                cursor.execute("SET SESSION sql_buffer_result = 1")
                
                # 检查并处理参数
                if params is not None:
                    # 计算SQL中的占位符数量
                    placeholder_count = query.count('?') + query.count('%s')
                    param_count = len(params) if isinstance(params, (list, tuple)) else 0
                    
                    # 检查参数数量是否匹配
                    if placeholder_count != param_count:
                        raise ValueError(f"参数数量不匹配：SQL需要{placeholder_count}个参数，但提供了{param_count}个")
                    
                    # 将 ? 替换为 %s
                    if '?' in query:
                        query = query.replace('?', '%s')
                
                # 执行查询，如果params是列表则转换为元组
                cursor.execute(query, tuple(params) if isinstance(params, list) else params)
                if fetch:
                    return cursor.fetchall()
                return None
            except Exception as e:
                load_logger.error(f"自定义查询执行失败: {str(e)}")
                raise

def upsert_record(table_name: str, data: Dict[str, Any], unique_fields: List[str]) -> bool:
    """插入或更新记录（ON DUPLICATE KEY UPDATE）
    
    Args:
        table_name: 表名
        data: 字段和值的字典
        unique_fields: 用于识别唯一性的字段列表
        
    Returns:
        bool: 操作是否成功
    """
    try:
        # 验证表名
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
            raise ValueError(f"非法表名: {table_name}")
            
        fields = list(data.keys())
        values = list(data.values())
        placeholders = ', '.join(['%s'] * len(fields))
        
        # 构建ON DUPLICATE KEY UPDATE子句
        update_parts = [f"{field} = VALUES({field})" for field in fields if field not in unique_fields]
        update_clause = ', '.join(update_parts)
        
        with get_conn() as conn:
            with conn.cursor() as cursor:
                query = f"""
                    INSERT INTO {table_name} ({', '.join(fields)}) 
                    VALUES ({placeholders})
                    ON DUPLICATE KEY UPDATE {update_clause}
                """
                cursor.execute(query, values)
                conn.commit()
                affected_rows = cursor.rowcount
                load_logger.debug(f"Upsert操作成功，表: {table_name}, 影响行数: {affected_rows}")
                return True
    except mysql.connector.Error as e:
        load_logger.error(f"Upsert操作失败: {str(e)}")
        return False

def get_all_tables() -> List[str]:
    """获取nkuwiki数据库中所有表名
    
    Returns:
        List[str]: nkuwiki数据库中的表名列表
    """
    try:
        # 使用information_schema查询，获取nkuwiki数据库的表
        with get_conn(use_database=True) as conn:
            with conn.cursor() as cursor:
                # 使用information_schema.tables查询nkuwiki数据库中的表
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'nkuwiki'
                    ORDER BY table_name
                """)
                tables = [table[0] for table in cursor.fetchall()]
                load_logger.debug(f"获取nkuwiki数据库中的表成功，共 {len(tables)} 个表")
                return tables
    except mysql.connector.Error as e:
        load_logger.error(f"获取表列表失败: {str(e)}")
        return []

def get_table_structure(table_name: str) -> List[Dict[str, Any]]:
    """获取表结构信息
    
    Args:
        table_name: 表名
        
    Returns:
        List[Dict]: 表结构信息列表
    """
    try:
        # 验证表名
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
            raise ValueError(f"非法表名: {table_name}")
            
        with get_conn() as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(f"DESCRIBE {table_name}")
                result = cursor.fetchall()
                load_logger.debug(f"获取表 {table_name} 结构成功")
                return result
    except mysql.connector.Error as e:
        load_logger.error(f"获取表结构失败: {str(e)}")
        return []

def get_nkuwiki_tables() -> List[str]:
    """获取nkuwiki数据库中所有表名
    
    Returns:
        List[str]: nkuwiki数据库中的表名列表
    """
    try:
        with get_conn(use_database=True) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                tables = [table[0] for table in cursor.fetchall()]
                load_logger.debug(f"获取nkuwiki数据库中的表成功，共 {len(tables)} 个表")
                return tables
    except mysql.connector.Error as e:
        load_logger.error(f"获取nkuwiki表列表失败: {str(e)}")
        return []

def transfer_table_from_mysql_to_nkuwiki(table_name: str) -> bool:
    """将表从mysql数据库转移到nkuwiki数据库
    
    Args:
        table_name: 要转移的表名
        
    Returns:
        bool: 转移是否成功
    """
    load_logger.info(f"开始将表 {table_name} 从mysql数据库转移到nkuwiki数据库")
    
    try:
        # 1. 查询mysql数据库中表的结构
        mysql_conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user='nkuwiki',  # 使用nkuwiki用户
            password=DB_PASSWORD,
            database="mysql"
        )
        
        # 检查表是否存在
        with mysql_conn.cursor() as cursor:
            cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
            if not cursor.fetchone():
                load_logger.error(f"表 {table_name} 在mysql数据库中不存在")
                return False
        
        # 获取表结构
        with mysql_conn.cursor(dictionary=True) as cursor:
            cursor.execute(f"SHOW CREATE TABLE {table_name}")
            result = cursor.fetchone()
            if not result:
                load_logger.error(f"无法获取表 {table_name} 的结构")
                return False
            
            create_table_sql = result["Create Table"]
            # 修改SQL以在nkuwiki数据库中创建表
            create_table_sql = create_table_sql.replace(f"CREATE TABLE `{table_name}`", 
                                                       f"CREATE TABLE IF NOT EXISTS `{table_name}`")
            
        # 2. 从mysql获取所有数据
        with mysql_conn.cursor(dictionary=True) as cursor:
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            load_logger.info(f"从mysql数据库中获取了 {len(rows)} 条记录")
        
        # 关闭mysql连接
        mysql_conn.close()
        
        # 3. 在nkuwiki中创建表并导入数据
        nkuwiki_conn = get_conn(use_database=True)  # 连接到nkuwiki数据库
        
        # 创建表
        with nkuwiki_conn.cursor() as cursor:
            cursor.execute(create_table_sql)
            load_logger.info(f"在nkuwiki数据库中创建表 {table_name} 成功")
        
        # 如果有数据，则导入
        if rows:
            # 使用批量插入函数导入数据
            success_count = batch_insert(table_name, rows, batch_size=100)
            load_logger.info(f"成功将 {success_count}/{len(rows)} 条记录导入到nkuwiki数据库")
            
            if success_count != len(rows):
                load_logger.warning(f"有 {len(rows) - success_count} 条记录导入失败")
        
        nkuwiki_conn.close()
        load_logger.info(f"表 {table_name} 从mysql数据库转移到nkuwiki数据库完成")
        return True
        
    except Exception as e:
        load_logger.error(f"转移表 {table_name} 失败: {str(e)}")
        return False

def import_json_dir_to_table(dir_path: str = None, table_name: str = None, platform: str = None, tag: str = "nku", batch_size: int = 100) -> Dict[str, Any]:
    """将指定目录下的JSON文件导入到指定表（递归处理所有子目录）
    
    Args:
        dir_path: JSON文件所在目录路径，默认为RAW_PATH / platform / tag
        table_name: 要导入的表名（可选，如果不提供则使用platform和tag构建）
        platform: 平台名称（如wechat、web等）
        tag: 标签，默认为nku
        batch_size: 批量插入的大小，默认100
        
    Returns:
        Dict[str, Any]: 包含导入结果的字典，包括成功数量、失败数量和失败文件列表
    """
    
    # 如果没有提供表名但提供了platform，则构建表名
    if table_name is None and platform is not None:
        table_name = f"{platform}_{tag}"
    
    if table_name is None:
        load_logger.error("必须提供table_name参数或platform参数")
        return {"success": 0, "failed": 0, "failed_files": []}
    
    # 如果没有提供dir_path但提供了platform，则构建目录路径
    if dir_path is None:
        if platform is None:
            load_logger.error("必须提供dir_path参数或platform参数")
            return {"success": 0, "failed": 0, "failed_files": []}
        dir_path = RAW_PATH / platform / tag
    
    load_logger.info(f"开始将目录 {dir_path} 及其子目录下的JSON文件导入到表 {table_name}")
    
    # 确保目录存在
    if not os.path.isdir(dir_path):
        load_logger.error(f"目录 {dir_path} 不存在")
        return {"success": 0, "failed": 0, "failed_files": []}
    
    # 确保表存在
    tables = get_all_tables()
    if table_name not in tables:
        load_logger.debug(f"表 {table_name} 不存在，尝试创建")
        if not create_table(table_name):
            load_logger.error(f"创建表 {table_name} 失败")
            return {"success": 0, "failed": 0, "failed_files": []}
    
    # 用于收集所有JSON文件路径的列表
    json_files = []
    
    # 递归查找所有JSON文件
    for root, _, files in os.walk(dir_path):
        for file in files:
            if file.lower().endswith('.json'):
                json_files.append(os.path.join(root, file))
    
    total_files = len(json_files)
    load_logger.debug(f"递归发现 {total_files} 个JSON文件")
    
    # 调试输出前5个文件路径，而不是10个
    if total_files > 0:
        load_logger.debug("示例文件路径:")
        for i, path in enumerate(json_files[:5]):  # 减少为5个
            load_logger.debug(f"  {i+1}. {path}")
    
    success_count = 0
    failed_count = 0
    failed_files = []
    
    # 用于批量插入的记录列表
    records_batch = []
    
    # 调试预览计数器
    preview_count = 0
    max_previews = 3  # 最多只显示3个文件的内容预览
    
    # 处理每个JSON文件
    for file_path in tqdm(json_files, desc="处理JSON文件", unit="文件"):
        try:
            # 尝试读取并解析JSON文件
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read().strip()
                if not file_content:
                    raise ValueError("文件内容为空")
                
                # 只对前几个文件输出内容预览
                if preview_count < max_previews:
                    load_logger.debug(f"文件内容预览 ({os.path.basename(file_path)}): {file_content[:50]}...")
                    preview_count += 1
            
            # 处理文件
            data = process_file(file_path, platform)
            if data:
                # 确保数据中包含内容字段
                if "content" not in data or not data["content"]:
                    load_logger.warning(f"文件 {file_path} 处理后没有内容字段")
                    # 尝试从文件名或路径中获取一些信息作为内容
                    parent_dir = os.path.basename(os.path.dirname(file_path))
                    data["content"] = f"从文件路径提取的信息：{parent_dir}"
                
                records_batch.append(data)
                
                # 当记录数达到批量大小时进行插入
                if len(records_batch) >= batch_size:
                    inserted = batch_insert(table_name, records_batch, batch_size)
                    success_count += inserted
                    records_batch = []
            else:
                load_logger.warning(f"文件 {file_path} 处理后无数据")
                failed_count += 1
                failed_files.append(file_path)
        except Exception as e:
            load_logger.error(f"处理文件 {file_path} 失败: {str(e)}")
            failed_count += 1
            failed_files.append(file_path)
    
    # 处理剩余的记录
    if records_batch:
        inserted = batch_insert(table_name, records_batch, batch_size)
        success_count += inserted
    
    result = {
        "success": success_count,
        "failed": failed_count,
        "failed_files": failed_files
    }
    
    # 显示导入结果的进度条总结
    total_processed = success_count + failed_count
    success_rate = success_count / total_files * 100 if total_files > 0 else 0
    
    # 输出一个进度条样式的总结
    progress_bar = "=" * int(success_rate / 2)
    load_logger.info(f"导入完成 [{progress_bar}{' ' * (50 - len(progress_bar))}] {success_rate:.1f}%")
    load_logger.info(f"总计: {total_files} 文件, 成功: {success_count}, 失败: {failed_count}")
    
    # 如果有失败的文件，输出前5个以供排查
    if failed_files:
        load_logger.warning("部分文件处理失败，前5个失败文件：")
        for i, f in enumerate(failed_files[:5]):
            load_logger.warning(f"  {i+1}. {f}")
    
    return result

def execute_raw_query(query, params=None):
    """
    执行原生SQL查询，返回查询结果
    
    Args:
        query (str): SQL查询语句
        params (tuple, optional): 查询参数
    
    Returns:
        list: 包含查询结果的字典列表
    """
    try:
        # 获取数据库连接
        connection = get_conn()
        cursor = connection.cursor(dictionary=True)
        
        # 执行查询
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # 获取结果
            result = cursor.fetchall()
            load_logger.debug(f"执行原生SQL查询成功，返回 {len(result)} 条记录")
            return result
        finally:
            cursor.close()
    except Exception as e:
        load_logger.error(f"执行原生SQL查询失败: {str(e)}")
        load_logger.error(f"查询语句: {query}")
        if params:
            load_logger.error(f"查询参数: {params}")
        # 返回空列表而不是抛出异常
        return []

if __name__ == "__main__":
    # delete_table("wechat_nku")  # 注释掉删除表的操作
    delete_table("wxapp_comments")
    delete_table("wxapp_posts")
    delete_table("wxapp_users")
    delete_table("wxapp_feedback")
    delete_table("wxapp_notifications")
    init_database()  # 初始化数据库
    # get_table_structure("wxapp_posts")
    # query_table("wxapp_posts")
    # import_json_dir_to_table(platform="wechat", tag="nku")  # 导入数据
    
    