// -*- coding: utf-8 -*-
// 平台状态条 - Zane v0913
// 解决缺点五：前端无真实/演示区分，演示时应该有视觉区分
// 功能：顶部平台状态条显示平台/Provider/不可用工具+demo_mode视觉区分

class PlatformStatusBar {
    constructor() {
        this.status = null;
        this.bar = null;
        this.init();
    }

    init() {
        // 创建状态条DOM
        this.createBar();
        // 加载状态
        this.loadStatus();
        // 定时刷新 30秒
        setInterval(() => this.loadStatus(), 30000);
    }

    createBar() {
        // 在topbar下方插入平台状态条
        const topbar = document.querySelector('.topbar');
        if (!topbar) return;

        const bar = document.createElement('div');
        bar.id = 'platform-status-bar';
        bar.className = 'platform-status-bar';
        bar.innerHTML = `
            <div class="platform-status-left">
                <span class="platform-badge" id="platform-provider">检测中...</span>
                <span class="platform-badge" id="platform-mode">检测中...</span>
                <span class="platform-badge" id="platform-runtime">Runtime检测中...</span>
                <span class="platform-badge" id="platform-llm">LLM检测中...</span>
            </div>
            <div class="platform-status-center">
                <span id="platform-tools-info">工具加载中...</span>
            </div>
            <div class="platform-status-right">
                <span class="platform-env" id="platform-env">环境变量加载中...</span>
            </div>
        `;
        
        // 插入到topbar后面
        topbar.parentNode.insertBefore(bar, topbar.nextSibling);
        this.bar = bar;

        // 添加样式
        this.injectStyles();
    }

    injectStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .platform-status-bar {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 6px 16px;
                background: linear-gradient(90deg, var(--card) 0%, var(--bg) 100%);
                border-bottom: 1px solid var(--border);
                font-size: 10px;
                font-family: monospace;
                gap: 12px;
                flex-wrap: wrap;
            }
            .platform-status-left, .platform-status-center, .platform-status-right {
                display: flex;
                gap: 8px;
                align-items: center;
                flex-wrap: wrap;
            }
            .platform-badge {
                padding: 3px 8px;
                border-radius: 10px;
                font-weight: 700;
                font-size: 10px;
            }
            .platform-badge.real {
                background: #10b981;
                color: white;
            }
            .platform-badge.demo {
                background: #f59e0b;
                color: white;
                animation: pulse-demo 2s infinite;
            }
            .platform-badge.windows {
                background: #0078d4;
                color: white;
            }
            .platform-badge.linux {
                background: #333;
                color: white;
            }
            .platform-badge.unknown {
                background: #6b7280;
                color: white;
            }
            @keyframes pulse-demo {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.7; }
            }
            .platform-env {
                color: var(--text-secondary);
                font-size: 9px;
            }
            .platform-tools-demo {
                color: #f59e0b;
                font-weight: 700;
            }
            .platform-tools-real {
                color: #10b981;
                font-weight: 700;
            }
            /* demo_mode视觉区分 - 整个应用 */
            body.demo-mode {
                border-top: 3px solid #f59e0b;
            }
            body.demo-mode::before {
                content: "演示模式 - 工具为模拟，非真实控制";
                position: fixed;
                top: 0;
                left: 50%;
                transform: translateX(-50%);
                background: #f59e0b;
                color: white;
                padding: 2px 12px;
                border-radius: 0 0 8px 8px;
                font-size: 10px;
                font-weight: 700;
                z-index: 9999;
            }
            /* 工具卡片demo_mode区分 */
            .tool-card.demo-mode {
                border: 1px dashed #f59e0b;
                background: rgba(245, 158, 11, 0.05);
            }
            .tool-card.demo-mode::after {
                content: "演示";
                position: absolute;
                top: 4px;
                right: 4px;
                background: #f59e0b;
                color: white;
                font-size: 8px;
                padding: 1px 4px;
                border-radius: 4px;
            }
            .tool-card.real-mode {
                border: 1px solid #10b981;
            }
            .tool-card.real-mode::after {
                content: "真实";
                position: absolute;
                top: 4px;
                right: 4px;
                background: #10b981;
                color: white;
                font-size: 8px;
                padding: 1px 4px;
                border-radius: 4px;
            }
        `;
        document.head.appendChild(style);
    }

    async loadStatus() {
        try {
            const res = await fetch('/api/platform/status');
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            this.status = data;
            this.render(data);
        } catch (e) {
            console.warn('平台状态加载失败', e);
            this.renderError(e);
        }
    }

    render(data) {
        const platform = data.platform || {};
        const isDemo = platform.is_demo;
        
        // Provider
        const providerEl = document.getElementById('platform-provider');
        if (providerEl) {
            providerEl.textContent = `Provider: ${platform.provider || 'unknown'}`;
            providerEl.className = `platform-badge ${this.getProviderClass(platform.provider)}`;
        }

        // Mode 真实/演示
        const modeEl = document.getElementById('platform-mode');
        if (modeEl) {
            modeEl.textContent = platform.mode || (isDemo ? '演示' : '真实');
            modeEl.className = `platform-badge ${isDemo ? 'demo' : 'real'}`;
        }

        // Runtime版本
        const runtimeEl = document.getElementById('platform-runtime');
        if (runtimeEl) {
            runtimeEl.textContent = `Runtime: ${data.runtime_version || 'v3'}`;
            runtimeEl.className = 'platform-badge real';
        }

        // LLM Provider
        const llmEl = document.getElementById('platform-llm');
        if (llmEl) {
            llmEl.textContent = `LLM: ${data.llm_provider || 'local'}`;
            llmEl.className = 'platform-badge windows';
        }

        // 工具信息
        const toolsEl = document.getElementById('platform-tools-info');
        if (toolsEl) {
            const realCount = data.real_count || 0;
            const demoCount = data.demo_count || 0;
            const total = data.total || 0;
            
            if (isDemo) {
                toolsEl.innerHTML = `<span class="platform-tools-demo">⚠️ 演示模式 ${demoCount}/${total} 工具为模拟</span> | 真实 ${realCount} | 演示 ${demoCount}`;
            } else {
                toolsEl.innerHTML = `<span class="platform-tools-real">✅ 真实模式 ${realCount}/${total} 工具真实控制</span> | 真实 ${realCount} | 演示 ${demoCount}`;
            }
            
            // 如果有不可用工具，显示
            const unavailable = (data.tools || []).filter(t => !t.available);
            if (unavailable.length > 0) {
                toolsEl.innerHTML += ` | 不可用: ${unavailable.map(t => t.name).join(',')}`;
            }
        }

        // 环境变量
        const envEl = document.getElementById('platform-env');
        if (envEl) {
            const env = data.env || {};
            envEl.textContent = `ZANE_RUNTIME=${env.ZANE_RUNTIME || 'v3'} ZANE_PLATFORM=${env.ZANE_PLATFORM || 'auto'} ZANE_DEMO=${env.ZANE_DEMO || 'auto'}`;
        }

        // body class demo_mode视觉区分
        if (isDemo) {
            document.body.classList.add('demo-mode');
            document.body.classList.remove('real-mode');
        } else {
            document.body.classList.add('real-mode');
            document.body.classList.remove('demo-mode');
        }

        // 更新工具卡片的demo_mode区分
        this.updateToolCards(isDemo);
    }

    updateToolCards(isDemo) {
        // 如果有工具列表，添加demo/real类
        document.querySelectorAll('.tool-card, .tool-item, [data-tool]').forEach(el => {
            if (isDemo) {
                el.classList.add('demo-mode');
                el.classList.remove('real-mode');
            } else {
                el.classList.add('real-mode');
                el.classList.remove('demo-mode');
            }
        });
    }

    getProviderClass(provider) {
        if (!provider) return 'unknown';
        const p = provider.toLowerCase();
        if (p.includes('windows')) return 'windows';
        if (p.includes('linux')) return 'linux';
        if (p.includes('psutil')) return 'demo';
        return 'unknown';
    }

    renderError(e) {
        const providerEl = document.getElementById('platform-provider');
        if (providerEl) {
            providerEl.textContent = `Provider: 错误 ${e.message}`;
            providerEl.className = 'platform-badge unknown';
        }
    }
}

// 自动初始化
if (typeof window !== 'undefined') {
    window.platformStatusBar = new PlatformStatusBar();
    console.log('✅ 平台状态条已加载 - 真实/演示视觉区分');
}

// 导出
if (typeof module !== 'undefined') {
    module.exports = PlatformStatusBar;
}
