"""
微信桥接使用示例

演示如何使用微信桥接模块与 LoopCLI 集成
"""

from wechat_bridge import WeChatBridge, WeChatInboxHandler

# 示例 1: 基本使用
def basic_example():
    """基本使用示例"""

    # 创建桥接器
    bridge = WeChatBridge(
        token="your_wechat_ilink_token_here",
        allow_from="*",  # 允许所有用户（生产环境应该限制）
    )

    # 定义消息处理函数
    def handle_message(user_id: str, content: str, message_id: int, context_token: str):
        print(f"收到来自 {user_id} 的消息: {content}")
        # 这里可以添加自定义处理逻辑

    # 启动桥接
    bridge.start(handle_message)

    # 保持运行
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        bridge.stop()


# 示例 2: 与 LoopCLI inbox 集成
def inbox_integration_example():
    """与 LoopCLI inbox 集成示例"""

    from pathlib import Path

    # 创建桥接器
    bridge = WeChatBridge(token="your_token_here")

    # 创建 inbox 处理器
    handler = WeChatInboxHandler(
        bridge=bridge,
        inbox_dir="D:/loopcli/main/inbox",
        report_dir="D:/loopcli/main/report",
    )

    # 启动处理器
    handler.start()

    print("微信桥接已启动，等待消息...")
    print(f"消息将写入: {handler.inbox_dir}")
    print(f"报告将发送到微信，来源: {handler.report_dir}")

    # 保持运行
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        bridge.stop()


# 示例 3: 自定义消息处理
def custom_handler_example():
    """自定义消息处理示例"""

    bridge = WeChatBridge(token="your_token_here")

    def custom_handler(user_id: str, content: str, message_id: int, context_token: str):
        """自定义消息处理逻辑"""
        from datetime import datetime
        from pathlib import Path

        # 根据消息内容执行不同操作
        if content.startswith("/status"):
            # 状态查询
            response = "系统运行正常"
            bridge.send_message(user_id, response, context_token)

        elif content.startswith("/help"):
            # 帮助信息
            help_text = """
可用命令：
/status - 查看系统状态
/help - 显示帮助信息
其他消息将转发给 Agent 处理
            """
            bridge.send_message(user_id, help_text, context_token)

        else:
            # 默认：写入 inbox 让 Agent 处理
            inbox_dir = Path("D:/loopcli/main/inbox")
            inbox_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"wechat_{user_id.replace('@', '_')}_{timestamp}.md"
            filepath = inbox_dir / filename

            message_content = f"""# 来自微信的消息

- 类型：指令
- 来源：微信 ({user_id})
- 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 消息ID：{message_id}

## 内容

{content}

## 上下文

- Context Token: {context_token}
- User ID: {user_id}
"""

            filepath.write_text(message_content, encoding="utf-8")
            print(f"消息已写入 inbox: {filename}")

            # 确认收到
            bridge.send_message(user_id, "消息已接收，正在处理...", context_token)

    bridge.start(custom_handler)

    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        bridge.stop()


# 示例 4: 测试连接
def test_connection_example():
    """测试微信连接示例"""

    import sys

    if len(sys.argv) < 2:
        print("用法: python wechat_example.py test <TOKEN>")
        return

    token = sys.argv[2] if len(sys.argv) > 2 else input("请输入微信 token: ")

    print("正在测试微信连接...")

    try:
        bridge = WeChatBridge(token=token)

        # 尝试获取一次消息（测试连接）
        messages = bridge.get_updates()

        print(f"✓ 连接成功！")
        print(f"当前有 {len(messages)} 条待处理消息")

        bridge.stop()
    except Exception as e:
        print(f"✗ 连接失败: {e}")
        print("\n请检查：")
        print("1. Token 是否正确")
        print("2. 网络连接是否正常")
        print("3. ilink 服务是否可用")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "test":
            test_connection_example()
        elif command == "basic":
            basic_example()
        elif command == "inbox":
            inbox_integration_example()
        elif command == "custom":
            custom_handler_example()
        else:
            print(f"未知命令: {command}")
            print("可用命令: test, basic, inbox, custom")
    else:
        print("微信桥接使用示例")
        print("\n使用方法:")
        print("  python wechat_example.py <command>")
        print("\n可用命令:")
        print("  test   - 测试微信连接")
        print("  basic  - 基本使用示例")
        print("  inbox  - 与 LoopCLI inbox 集成")
        print("  custom - 自定义消息处理")
        print("\n示例:")
        print("  python wechat_example.py test YOUR_TOKEN")
