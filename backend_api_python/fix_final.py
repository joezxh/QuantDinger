with open('app/services/trading_executor.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = '''            # 1. 检查数据库状态
            with get_db_connection() as db:
                cursor = db.cursor()
                cursor.execute(
                    "SELECT status FROM qd_strategies_trading WHERE id = %s",
                    (strategy_id,)
                )
                result = cursor.fetchone()
                cursor.close()
                db_status = result and result.get('status') == 'running' '''

new = '''            # 1. 检查数据库状态
            with get_session() as session:
                repo = StrategyRepository(session)
                db_status = repo.get_status(strategy_id) == 'running' '''

if old in content:
    content = content.replace(old, new)
    print('[OK] _is_strategy_running SELECT replaced')
else:
    print('[FAIL] not found')
    # Try to find approximate location
    idx = content.find('_is_strategy_running')
    if idx > 0:
        print(f'Found at index {idx}')
        print(repr(content[idx:idx+300]))

with open('app/services/trading_executor.py', 'w', encoding='utf-8') as f:
    f.write(content)
