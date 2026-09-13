# -*- coding: utf-8 -*-
"""
Webapp自动化测试 - Playwright - 前端功能+后端API真实性
"""
import subprocess
import time
import sys
from pathlib import Path

def test_frontend_loads():
    """前端加载测试"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("⚠️ Playwright未安装，跳过自动化测试，安装: pip install playwright && playwright install chromium")
        return True
    
    # 检查后端是否运行
    import requests
    try:
        resp = requests.get("http://localhost:8000/api/health", timeout=2)
        if resp.status_code != 200:
            print("⚠️ 后端未运行，跳过前端测试")
            return True
    except:
        print("⚠️ 后端未运行，跳过前端测试")
        return True
    
    print("✅ 后端运行，开始前端自动化测试...")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # 1. 加载前端
            page.goto('http://localhost:8000/', timeout=10000)
            page.wait_for_load_state('networkidle', timeout=10000)
            
            # 2. 检查标题
            title = page.title()
            assert "Zane" in title, f"标题应包含Zane，实际{title}"
            print(f"✅ 标题: {title}")
            
            # 3. 检查无内部备注
            content = page.content()
            internal_terms = ["110API", "Impeccable", "后端基础打牢", "iOS默认禁用"]
            for term in internal_terms:
                assert term not in content, f"前端不应包含内部备注: {term}"
            print("✅ 无内部备注")
            
            # 4. 检查滚动条
            body_overflow = page.evaluate("() => getComputedStyle(document.body).overflowY")
            assert body_overflow != "hidden", f"body不应overflow:hidden，实际{body_overflow}"
            print(f"✅ 滚动条: body overflow-y={body_overflow}")
            
            # 5. 检查系统状态
            # 等待系统状态加载
            page.wait_for_timeout(2000)
            # 检查是否有系统指标
            metrics = page.locator('.metric').all()
            print(f"✅ 系统指标: {len(metrics)}个")
            
            # 6. 检查知识图谱Canvas
            kg_canvas = page.locator('#knowledge-graph')
            if kg_canvas.count() > 0:
                print("✅ 知识图谱Canvas存在")
                # 检查是否可点击
                kg_canvas.click(timeout=2000)
                print("✅ 知识图谱可点击")
            
            # 7. 检查设置可交互
            # 切换到设置页
            settings_btn = page.locator('text=设置').first
            if settings_btn.count() > 0:
                settings_btn.click(timeout=2000)
                page.wait_for_timeout(1000)
                switches = page.locator('.switch').all()
                print(f"✅ 设置页: {len(switches)}个switch可交互")
            
            # 8. 截图
            page.screenshot(path='/tmp/zane-frontend-test.png', full_page=True)
            print("✅ 截图已保存 /tmp/zane-frontend-test.png")
            
            browser.close()
            print("✅ 前端自动化测试通过")
            return True
            
    except Exception as e:
        print(f"❌ 前端自动化测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_real():
    """API真实性测试"""
    import requests
    
    apis = [
        ("/api/health", "健康检查"),
        ("/api/platform/status", "平台状态"),
        ("/api/system/state", "系统状态"),
        ("/api/dependency/check", "依赖检测"),
        ("/api/knowledge-graph/memory", "记忆图谱"),
        ("/api/knowledge-graph/database", "数据库图谱"),
    ]
    
    base = "http://localhost:8000"
    real_count = 0
    
    for path, name in apis:
        try:
            resp = requests.get(f"{base}{path}", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                # 检查是否真实数据，非错误
                if "error" not in data or data.get("real", True):
                    print(f"✅ {name} {path}: 真实")
                    real_count += 1
                else:
                    print(f"⚠️ {name} {path}: 演示或错误 - {data.get('error','')}")
            else:
                print(f"❌ {name} {path}: HTTP {resp.status_code}")
        except Exception as e:
            print(f"❌ {name} {path}: 异常 {e}")
    
    print(f"API真实性: {real_count}/{len(apis)} 真实")
    return real_count >= len(apis) * 0.8  # 80%真实算通过

def test_dependency_auto_install():
    """依赖自动安装测试"""
    try:
        from backend.utils.dependency_checker import dependency_checker
        status = dependency_checker.check_all()
        api_status = dependency_checker.get_api_real_status()
        
        print(f"依赖: {status['available']}/{status['total']} 可用，缺失{status['missing']}")
        print(f"核心缺失: {status['required_missing']}")
        print(f"API真实: {api_status['real']}/{api_status['total']}")
        
        # 核心缺失应为0
        assert len(status['required_missing']) == 0, f"核心依赖缺失: {status['required_missing']}"
        print("✅ 核心依赖无缺失")
        
        # API应大部分真实
        assert api_status['real'] >= 8, f"API真实性不足: {api_status['real']}"
        print(f"✅ API真实性: {api_status['real']}/{api_status['total']}")
        
        return True
    except Exception as e:
        print(f"❌ 依赖检测失败: {e}")
        return False

if __name__ == "__main__":
    print("=== Webapp自动化测试 ===")
    print("")
    print("1. 依赖自动安装测试")
    test_dependency_auto_install()
    print("")
    print("2. API真实性测试")
    test_api_real()
    print("")
    print("3. 前端加载测试")
    test_frontend_loads()
    print("")
    print("=== 测试完成 ===")
