#!/usr/bin/env python3
"""查看 SQLite 数据库表结构和数据"""

import sqlite3

def view_database():
    conn = sqlite3.connect('sync_server.db')
    cursor = conn.cursor()

    print('=== 数据库表列表 ===')
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for table in tables:
        print(f'  - {table[0]}')

    print('\n=== 各表结构 ===')
    for table in tables:
        table_name = table[0]
        print(f'\n【{table_name}】表:')
        cursor.execute(f'PRAGMA table_info({table_name});')
        columns = cursor.fetchall()
        for col in columns:
            cid, name, dtype, notnull, default, pk = col
            pk_mark = 'PK' if pk else ''
            null_mark = 'NOT NULL' if notnull else 'NULL'
            default_val = f'DEFAULT {default}' if default else ''
            print(f'  {name:20} {dtype:15} {null_mark:10} {pk_mark:5} {default_val}')

    print('\n=== 数据预览 ===')
    for table in tables:
        table_name = table[0]
        print(f'\n【{table_name}】表数据:')
        cursor.execute(f'SELECT * FROM {table_name}')
        rows = cursor.fetchall()
        if rows:
            # 获取列名
            cursor.execute(f'PRAGMA table_info({table_name});')
            columns = cursor.fetchall()
            col_names = [col[1] for col in columns]
            print('  ' + ' | '.join(col_names))
            print('  ' + '-' * 80)
            for row in rows[:5]:  # 只显示前5行
                print('  ' + ' | '.join(str(v) for v in row))
            if len(rows) > 5:
                print(f'  ... 还有 {len(rows) - 5} 行数据')
        else:
            print('  (空表)')

    conn.close()

if __name__ == '__main__':
    view_database()
