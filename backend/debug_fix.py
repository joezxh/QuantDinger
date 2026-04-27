with open('app/services/trading_executor.py', 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find('# 1. 检查数据库状态')
snippet = content[idx:idx+400]
print('Full snippet ending:', repr(snippet[300:]))

# Find db_status line
db_idx = snippet.find("db_status = result")
db_end = snippet[db_idx:db_idx+60]
print('db_status line:', repr(db_end))

# Now do exact replacement
old = '''# 1. 检查数据库状态
            with get_db_connection() as db:
                cursor = db.cursor()
                cursor.execute(
                    "SELECT status FROM qd_strategies_trading WHERE id = %s",
                    (strategy_id,)
                )
                result = cursor.fetchone()
                cursor.close()
                db_status = result and result.get('status') == 'running' '''

# Try with exact content from the file
old_from_file = snippet[:snippet.find("db_status = result") + len("db_status = result and result.get('status') == 'running'")]
print('old_from_file:', repr(old_from_file[-50:]))

# Construct the exact old string from actual content
# Find \n after the db_status line  
start = content.find('# 1. 检查数据库状态')
end = content.find('\n', content.find("db_status = result and result.get('status') == 'running'", start))
exact_old = content[start:end]
print('exact_old ending:', repr(exact_old[-60:]))

new = '''# 1. 检查数据库状态
            with get_session() as session:
                repo = StrategyRepository(session)
                db_status = repo.get_status(strategy_id) == 'running\''''

if exact_old in content:
    content = content.replace(exact_old, new)
    print('[OK] Replaced using exact match')
elif old in content:
    content = content.replace(old, new)
    print('[OK] Replaced using old')
else:
    print('[FAIL]')
    # Force replacement using exact_old
    print(f'exact_old length: {len(exact_old)}')
    print(f'new length: {len(new)}')

with open('app/services/trading_executor.py', 'w', encoding='utf-8') as f:
    f.write(content)
