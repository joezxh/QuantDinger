"""Replace raw SQL in trading_executor.py with ORM calls."""
with open('app/services/trading_executor.py', 'r', encoding='utf-8') as f:
    content = f.read()

replacements = 0

# 0. Replace import
old_import = 'from app.utils.db import get_db_connection'
new_import = 'from app.database.session import get_session\nfrom app.database.repositories.strategy_repository import StrategyRepository'
if old_import in content and new_import not in content:
    content = content.replace(old_import, new_import, 1)
    print('[OK] Import replaced')
    replacements += 1
else:
    print('[INFO] Import already updated or not found')

# 1. _ensure_db_columns: Simplify - columns already in model, but keep for runtime safety
# Replace the whole function body DB access
old_ensure = '''with get_db_connection() as db:
                cursor = db.cursor()
                col_names = set()

                # PostgreSQL: 使用 information_schema 查询列
                try:
                    cursor.execute("""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = 'qd_strategy_positions'
                    """)
                    cols = cursor.fetchall() or []
                    col_names = {c.get('column_name') or c.get('COLUMN_NAME') for c in cols if isinstance(c, dict)}
                except Exception:
                    col_names = set()

                if 'highest_price' not in col_names:
                    logger.info("Adding highest_price column to qd_strategy_positions...")
                    cursor.execute("ALTER TABLE qd_strategy_positions ADD COLUMN IF NOT EXISTS highest_price DOUBLE PRECISION DEFAULT 0")
                    db.commit()
                    logger.info("highest_price column added")

                if 'lowest_price' not in col_names:
                    logger.info("Adding lowest_price column to qd_strategy_positions...")
                    cursor.execute("ALTER TABLE qd_strategy_positions ADD COLUMN IF NOT EXISTS lowest_price DOUBLE PRECISION DEFAULT 0")
                    db.commit()
                    logger.info("lowest_price column added")

                cursor.close()'''

new_ensure = '''# Columns highest_price and lowest_price are defined in the model;
                # runtime schema checks are delegated to Alembic migrations.
                # Skipping dynamic ALTER TABLE for production safety.
                pass'''

if old_ensure in content:
    content = content.replace(old_ensure, new_ensure)
    print('[OK] _ensure_db_columns replaced')
    replacements += 1
else:
    print('[FAIL] _ensure_db_columns not found')

# 2. stop_strategy - UPDATE qd_strategies_trading SET status = 'stopped'
old_stop = '''with get_db_connection() as db:
                    cursor = db.cursor()
                    cursor.execute(
                        "UPDATE qd_strategies_trading SET status = 'stopped' WHERE id = %s",
                        (strategy_id,)
                    )
                    db.commit()
                    cursor.close()'''

new_stop = '''with get_session() as session:
                    repo = StrategyRepository(session)
                    repo.set_status(strategy_id, 'stopped')'''

if old_stop in content:
    content = content.replace(old_stop, new_stop)
    print('[OK] stop_strategy replaced')
    replacements += 1
else:
    print('[FAIL] stop_strategy not found')

# 3. _persist_script_runtime_state - SELECT + UPDATE trading_config
old_persist = '''with get_db_connection() as db:
                cur = db.cursor()
                cur.execute("SELECT trading_config FROM qd_strategies_trading WHERE id = %s", (strategy_id,))
                row = cur.fetchone()
                if not row:
                    cur.close()
                    return
                tc = row.get('trading_config')
                if isinstance(tc, str) and tc.strip():
                    try:
                        tc = json.loads(tc)
                    except Exception:
                        tc = {}
                elif not isinstance(tc, dict):
                    tc = {}
                tc['script_runtime_state'] = state
                cur.execute(
                    "UPDATE qd_strategies_trading SET trading_config = %s WHERE id = %s",
                    (json.dumps(tc, ensure_ascii=False), strategy_id),
                )
                db.commit()
                cur.close()'''

new_persist = '''with get_session() as session:
                repo = StrategyRepository(session)
                tc = repo.get_trading_config(strategy_id) or {}
                tc['script_runtime_state'] = state
                repo.update_trading_config(strategy_id, tc)'''

if old_persist in content:
    content = content.replace(old_persist, new_persist)
    print('[OK] _persist_script_runtime_state replaced')
    replacements += 1
else:
    print('[FAIL] _persist_script_runtime_state not found')

# 4. _load_strategy - SELECT from qd_strategies_trading
old_load = '''with get_db_connection() as db:
                cursor = db.cursor()
                query = """
                    SELECT 
                        id, strategy_name, strategy_type, status,
                        initial_capital, leverage, decide_interval,
                        execution_mode, notification_config,
                        indicator_config, exchange_config, trading_config, ai_model_config,
                        market_category, strategy_mode, strategy_code
                    FROM qd_strategies_trading
                    WHERE id = %s
                """
                cursor.execute(query, (strategy_id,))
                strategy = cursor.fetchone()
                cursor.close()
            
            if strategy:
                # 解析JSON字段
                for field in ['indicator_config', 'trading_config', 'notification_config', 'ai_model_config']:
                    if isinstance(strategy.get(field), str):
                        try:
                            strategy[field] = json.loads(strategy[field])
                        except:
                            strategy[field] = {}
                
                # exchange_config: local deployment stores plaintext JSON
                exchange_config_str = strategy.get('exchange_config', '{}')
                if isinstance(exchange_config_str, str) and exchange_config_str:
                    try:
                        strategy['exchange_config'] = json.loads(exchange_config_str)
                    except Exception as e:
                        logger.error(f"Strategy {strategy_id} failed to parse exchange_config: {str(e)}")
                        # 尝试直接解析 JSON（向后兼容）
                        try:
                            strategy['exchange_config'] = json.loads(exchange_config_str)
                        except:
                            strategy['exchange_config'] = {}
                else:
                    strategy['exchange_config'] = {}
            
            return strategy'''

new_load = '''with get_session() as session:
                repo = StrategyRepository(session)
                strategy = repo.load_strategy_config(strategy_id)
            
            return strategy'''

if old_load in content:
    content = content.replace(old_load, new_load)
    print('[OK] _load_strategy replaced')
    replacements += 1
else:
    print('[FAIL] _load_strategy not found')

# 5. _is_strategy_running - first SELECT
old_running_1 = '''with get_db_connection() as db:
                cursor = db.cursor()
                cursor.execute(
                    "SELECT status FROM qd_strategies_trading WHERE id = %s",
                    (strategy_id,)
                )
                result = cursor.fetchone()
                cursor.close()
                db_status = result and result.get('status') == 'running' '''

new_running_1 = '''with get_session() as session:
                repo = StrategyRepository(session)
                db_status = repo.get_status(strategy_id) == 'running' '''

if old_running_1 in content:
    content = content.replace(old_running_1, new_running_1)
    print('[OK] _is_strategy_running SELECT replaced')
    replacements += 1
else:
    print('[FAIL] _is_strategy_running SELECT not found')

# 6. _is_strategy_running - second UPDATE
old_running_2 = '''with get_db_connection() as db:
                        cursor = db.cursor()
                        cursor.execute(
                            "UPDATE qd_strategies_trading SET status = 'stopped' WHERE id = %s",
                            (strategy_id,)
                        )
                        db.commit()
                        cursor.close()'''

new_running_2 = '''with get_session() as session:
                        repo = StrategyRepository(session)
                        repo.set_status(strategy_id, 'stopped')'''

if old_running_2 in content:
    content = content.replace(old_running_2, new_running_2)
    print('[OK] _is_strategy_running UPDATE replaced')
    replacements += 1
else:
    print('[FAIL] _is_strategy_running UPDATE not found')

# Write back
with open('app/services/trading_executor.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f'\nTotal replacements: {replacements}')
