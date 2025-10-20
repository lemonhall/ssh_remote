"""测试 AI 服务"""

import asyncio
from ssh_remote.services.ai_service import AIAssistant
from ssh_remote.config import settings

async def test_ai():
    print("=" * 50)
    print("AI 服务测试")
    print("=" * 50)
    
    # 检查配置
    print(f"\n配置信息:")
    print(f"  API Key: {'已设置' if settings.openai_api_key else '未设置'}")
    print(f"  Base URL: {settings.openai_base_url or '默认'}")
    print(f"  Model: {settings.openai_model}")
    
    if not settings.openai_api_key:
        print("\n❌ 错误: 未配置 OPENAI_API_KEY")
        return
    
    try:
        # 初始化 AI 助手
        print("\n正在初始化 AI 助手...")
        assistant = AIAssistant()
        print("✅ AI 助手初始化成功")
        
        # 测试命令生成
        test_queries = [
            "查看当前目录下的所有文件",
            "查找所有 Python 文件",
            "显示系统内存使用情况",
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{'=' * 50}")
            print(f"测试 {i}: {query}")
            print("=" * 50)
            
            print("正在生成命令...")
            explanation, commands = assistant.generate_command(query)
            
            print(f"\n📝 解释:\n{explanation}")
            
            if commands:
                print(f"\n📋 生成的命令:")
                for j, cmd in enumerate(commands, 1):
                    is_dangerous, warning = assistant.check_dangerous_command(cmd)
                    if is_dangerous:
                        print(f"  {j}. {cmd} ⚠️ {warning}")
                    else:
                        print(f"  {j}. {cmd}")
            else:
                print("\n（未生成命令）")
            
            print()
    
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ai())
