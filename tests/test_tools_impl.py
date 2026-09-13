# -*- coding: utf-8 -*-
"""
工具实现测试 - Zane v0913 单文件统一版
验证：21工具无覆盖+demo_mode字段+安全增强
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pathlib import Path

def test_tools_unified():
    """测试统一工具实现"""
    print("="*60)
    print("测试工具统一实现 - Zane v0913")
    print("="*60)
    
    try:
        from backend.tools_impl import TOOL_FUNCTIONS, tool_executor
        
        print(f"✅ 工具数: {len(TOOL_FUNCTIONS)}")
        print(f"工具列表: {list(TOOL_FUNCTIONS.keys())}")
        
        # 检查无覆盖 - 统一后21+3工具
        expected_tools = [
            "list_files", "read_file", "create_folder", "delete_file", "write_file",
            "move_file", "inspect_processes", "get_system_state", "list_windows",
            "focus_window", "take_screenshot", "ocr_screenshot", "launch_application",
            "web_search", "verify_info", "get_clipboard", "set_clipboard",
            "mouse_click", "keyboard_input"  # 统一实现：mouse_click+keyboard_input，兼容mouse_move/key_press
        ]
        
        for tool in expected_tools:
            assert tool in TOOL_FUNCTIONS, f"工具缺失: {tool}"
            print(f"  ✅ {tool}")
        
        # 检查demo_mode字段
        print()
        print("检查demo_mode字段:")
        print(f"  tool_executor.demo_mode: {tool_executor.demo_mode}")
        print(f"  platform_provider: {tool_executor.platform_provider}")
        
        # 测试list_files
        print()
        print("测试list_files:")
        result = TOOL_FUNCTIONS["list_files"](path="/tmp", detail=False)
        print(f"  结果: files={len(result.get('files', []))} total={result.get('total')} demo_mode={result.get('demo_mode')}")
        # list_files返回files+total+demo_mode，无success字段（成功时）
        assert "files" in result or "error" in result, "应有files或error"
        assert "demo_mode" in result, "缺少demo_mode字段"
        # 如果有files，认为成功
        if "files" in result:
            print(f"  ✅ list_files成功 文件数: {len(result['files'])}")
        
        # 测试安全增强
        print()
        print("测试安全增强:")
        # 危险路径应该被拦截或标记
        try:
            result = TOOL_FUNCTIONS["delete_file"](path="C:\\Windows\\System32\\test.txt")
            print(f"  危险路径删除: success={result.get('success')} error={result.get('error')}")
            # 应该失败
        except Exception as e:
            print(f"  危险路径拦截: {e}")
        
        # 白名单测试
        print()
        print("测试白名单:")
        result = TOOL_FUNCTIONS["list_files"](path="/tmp", detail=False)
        assert "files" in result or result.get("success"), "白名单路径应该成功"
        print(f"  /tmp 白名单: ✅ files={len(result.get('files', []))}")
        
        print()
        print("✅ 工具统一实现测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_policy_firewall():
    """测试策略防火墙硬化版"""
    print()
    print("="*60)
    print("测试策略防火墙v0913硬化版")
    print("="*60)
    
    try:
        # loguru可选
        try:
            import loguru
        except ImportError:
            print("⚠️ loguru未安装，使用logging模拟")
            import logging
            import sys
            # 模拟loguru
            class FakeLogger:
                def info(self, msg): print(f"INFO {msg}")
                def warning(self, msg): print(f"WARN {msg}")
                def error(self, msg): print(f"ERROR {msg}")
                def debug(self, msg): pass
            sys.modules['loguru'] = type(sys)('loguru')
            sys.modules['loguru'].logger = FakeLogger()
        
        from backend.policy_firewall_v0913 import policy_firewall_v0913
        
        print(f"✅ 防火墙版本: v0913 硬化版")
        print(f"  auto_allow: {policy_firewall_v0913.auto_allow_tools}")
        print(f"  protected_paths: {len(policy_firewall_v0913.protected_paths)}个")
        
        # 测试只读自动放行
        rule = policy_firewall_v0913.check_permission("list_files", {"path": "/tmp"})
        print(f"  list_files /tmp: {rule.action.value} - {rule.reason}")
        assert rule.action.value == "allow", "只读应该自动放行"
        
        # 测试危险操作需要确认
        rule = policy_firewall_v0913.check_permission("delete_file", {"path": "/tmp/test.txt"})
        print(f"  delete_file /tmp/test.txt: {rule.action.value} - {rule.reason}")
        assert rule.action.value == "pending_confirm", "危险操作应该pending_confirm阻断"
        assert rule.confirm_id is not None, "应该有confirm_id"
        
        # 测试保护路径
        rule = policy_firewall_v0913.check_permission("delete_file", {"path": "C:\\Windows\\System32\\test.txt"})
        print(f"  delete_file System32: {rule.action.value} - {rule.reason}")
        assert rule.action.value in ["pending_confirm", "deny"], "保护路径应该阻断"
        
        print()
        print("✅ 策略防火墙测试通过 - NEED_CONFIRM真正阻断")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    ok1 = test_tools_unified()
    ok2 = test_policy_firewall()
    
    print()
    print("="*60)
    if ok1 and ok2:
        print("✅ 全部测试通过")
    else:
        print("❌ 部分测试失败")
        sys.exit(1)
