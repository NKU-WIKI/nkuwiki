#!/bin/bash
set -e

# 初始化PostgreSQL数据目录
if [ ! -s "$PGDATA/PG_VERSION" ]; then
    echo "Initializing PostgreSQL database..."
    initdb -D "$PGDATA"
    
    # 配置PostgreSQL监听所有地址
    echo "listen_addresses='*'" >> "$PGDATA/postgresql.conf"
    echo "host all all all md5" >> "$PGDATA/pg_hba.conf"
fi

# 启动PostgreSQL
if [ "$1" = 'postgres' ]; then
    if [ ! -s "$PGDATA/PG_VERSION" ]; then
        echo "Initializing PostgreSQL database..."
        su - postgres -c "initdb -D $PGDATA $POSTGRES_INITDB_ARGS"
    fi
    exec postgres
fi

exec "$@" 