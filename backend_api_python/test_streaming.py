"""
测试 LLM 流式和非流式输出功能

使用方法：
    python test_streaming.py
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.llm import LLMService
from app.utils.logger import get_logger

logger = get_logger(__name__)


def test_non_streaming():
    """测试非流式模式（默认）"""
    print("\n" + "="*60)
    print("测试 1: 非流式模式（默认）")
    print("="*60)
    
    llm = LLMService()
    
    try:
        result = llm.call_llm_api(
            messages=[
                {"role": "system", "content": "你是一个简洁的助手。"},
                {"role": "user", "content": "请说'你好，这是非流式测试'"}
            ],
            temperature=0.1,
            stream=False  # 显式设置为 False
        )
        
        print(f"✅ 成功！")
        print(f"响应长度: {len(result)} 字符")
        print(f"响应内容: {result[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_streaming():
    """测试流式模式"""
    print("\n" + "="*60)
    print("测试 2: 流式模式（stream=True）")
    print("="*60)
    
    llm = LLMService()
    
    try:
        result = llm.call_llm_api(
            messages=[
                {"role": "system", "content": "你是一个简洁的助手。"},
                {"role": "user", "content": "请说'你好，这是流式测试'"}
            ],
            temperature=0.1,
            stream=True  # 启用流式
        )
        
        print(f"✅ 成功！")
        print(f"响应长度: {len(result)} 字符")
        print(f"响应内容: {result[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_streaming_method():
    """测试便捷流式方法"""
    print("\n" + "="*60)
    print("测试 3: 便捷方法 call_llm_streaming()")
    print("="*60)
    
    llm = LLMService()
    
    try:
        result = llm.call_llm_streaming(
            messages=[
                {"role": "system", "content": "你是一个简洁的助手。"},
                {"role": "user", "content": "请说'你好，这是便捷流式方法测试'"}
            ],
            temperature=0.1
        )
        
        print(f"✅ 成功！")
        print(f"响应长度: {len(result)} 字符")
        print(f"响应内容: {result[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_json_mode_streaming():
    """测试 JSON 模式 + 流式"""
    print("\n" + "="*60)
    print("测试 4: JSON 模式 + 流式")
    print("="*60)
    
    llm = LLMService()
    
    try:
        result = llm.call_llm_api(
            messages=[
                {"role": "system", "content": "返回 JSON 格式"},
                {"role": "user", "content": '{"name": "test", "value": 123}'}
            ],
            temperature=0.1,
            use_json_mode=True,
            stream=True
        )
        
        print(f"✅ 成功！")
        print(f"响应长度: {len(result)} 字符")
        print(f"响应内容: {result[:150]}...")
        return True
        
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_long_text_streaming():
    """测试长文本流式生成"""
    print("\n" + "="*60)
    print("测试 5: 长文本流式生成")
    print("="*60)
    
    llm = LLMService()
    
    try:
        result = llm.call_llm_api(
            messages=[
                {"role": "user", "content": "请写一篇200字左右的短文，介绍人工智能的未来发展"}
            ],
            temperature=0.7,
            stream=True
        )
        
        print(f"✅ 成功！")
        print(f"响应长度: {len(result)} 字符")
        print(f"\n完整内容:\n{result}\n")
        return True
        
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("LLM 流式/非流式功能测试")
    print("="*60)
    
    tests = [
        ("非流式模式", test_non_streaming),
        ("流式模式", test_streaming),
        ("便捷流式方法", test_streaming_method),
        ("JSON模式+流式", test_json_mode_streaming),
        ("长文本流式", test_long_text_streaming),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ 测试 [{name}] 异常: {e}")
            results.append((name, False))
    
    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} - {name}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\n总计: {passed}/{total} 通过")
    print("="*60 + "\n")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    exit(main())
