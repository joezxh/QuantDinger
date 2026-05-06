"""
多存储引擎架构部署和初始化脚本
"""
import subprocess
import sys
import os
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def run_command(cmd, description):
    """运行命令并显示结果"""
    print(f"\n{'='*60}")
    print(f"执行: {description}")
    print(f"命令: {cmd}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✓ {description} 成功")
        if result.stdout:
            print(result.stdout)
        return True
    else:
        print(f"✗ {description} 失败")
        print(result.stderr)
        return False


def deploy_elasticsearch():
    """部署 Elasticsearch 和 Kibana"""
    print("\n📦 步骤 1: 部署 Elasticsearch 集群")
    
    # 检查 Docker 是否运行
    result = subprocess.run("docker info", shell=True, capture_output=True)
    if result.returncode != 0:
        print("✗ Docker 未运行，请先启动 Docker Desktop")
        return False
    
    # 创建 Docker 网络
    subprocess.run("docker network create quantdinger-network", shell=True, capture_output=True)
    
    # 启动 Elasticsearch
    cmd = "docker-compose -f docker-compose.elasticsearch.yml up -d"
    if not run_command(cmd, "启动 Elasticsearch + Kibana"):
        return False
    
    # 等待 Elasticsearch 就绪
    print("\n⏳ 等待 Elasticsearch 启动...")
    for i in range(30):
        time.sleep(2)
        result = subprocess.run(
            "curl -s http://localhost:9200/_cluster/health",
            shell=True,
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and '"status":"green"' in result.stdout:
            print("✓ Elasticsearch 已就绪")
            return True
    
    print("✗ Elasticsearch 启动超时")
    return False


def init_database():
    """初始化数据库表"""
    print("\n📦 步骤 2: 初始化数据库表")
    
    # 运行 Alembic 迁移
    cmd = "cd backend && alembic upgrade head"
    return run_command(cmd, "执行数据库迁移")


def init_es_indices():
    """初始化 Elasticsearch 索引"""
    print("\n📦 步骤 3: 初始化 Elasticsearch 索引")
    
    # 运行索引初始化脚本
    cmd = "python scripts/init_es_indices.py"
    return run_command(cmd, "创建 ES 索引")


def install_dependencies():
    """安装 Elasticsearch Python 客户端"""
    print("\n📦 步骤 0: 安装依赖")
    
    cmd = "pip install elasticsearch"
    return run_command(cmd, "安装 Elasticsearch 客户端")


def main():
    """主部署流程"""
    print("\n" + "="*60)
    print("多存储引擎架构部署工具")
    print("="*60)
    
    steps = [
        ("安装依赖", install_dependencies),
        ("部署 Elasticsearch", deploy_elasticsearch),
        ("初始化数据库", init_database),
        ("初始化 ES 索引", init_es_indices),
    ]
    
    success_count = 0
    for name, func in steps:
        try:
            if func():
                success_count += 1
        except Exception as e:
            print(f"✗ {name} 异常: {e}")
    
    print("\n" + "="*60)
    print(f"部署完成: {success_count}/{len(steps)} 步骤成功")
    print("="*60)
    
    if success_count == len(steps):
        print("\n✅ 所有部署步骤成功！")
        print("\n访问地址:")
        print("  - Elasticsearch: http://localhost:9200")
        print("  - Kibana: http://localhost:5601")
        print("\n下一步:")
        print("  1. 配置 .env 文件: ELASTICSEARCH_HOSTS=http://localhost:9200")
        print("  2. 启动 Flask 应用: flask run")
        print("  3. 测试搜索 API: POST http://localhost:5000/api/v1/search/fulltext")
    else:
        print("\n❌ 部分部署步骤失败，请检查错误信息")
        sys.exit(1)


if __name__ == '__main__':
    main()
