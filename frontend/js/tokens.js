// tokens.js - Token可替换管理模块 - A夯实
import { tokenApi } from './api.js';

export async function renderTokenBar() {
    const bar = document.getElementById('token-bar');
    if (!bar) return;
    try {
        const data = await tokenApi.list();
        const tokens = data.tokens || {};
        bar.innerHTML = Object.values(tokens).map(t => {
            const status = t.has_value ? '✅' : '⚠️';
            const cls = t.has_value ? 'has' : 'missing';
            return `<span class="token-badge ${cls}" title="${t.name}: ${t.has_value ? t.value : '未配置'}">${status} ${t.name}</span>`;
        }).join(' ') + ` <span class="real-search-badge">🔍 ${data.real_search_config?.overall?.current || '演示'}</span>`;
    } catch (e) {
        bar.innerHTML = 'Token栏加载失败';
    }
}

export async function renderTokensView() {
    const container = document.getElementById('tokens-view');
    if (!container) return;
    try {
        const data = await tokenApi.list();
        const tokens = data.tokens || {};
        const config = data.real_search_config || {};
        
        let html = '<div class="tokens-grid">';
        for (const [id, t] of Object.entries(tokens)) {
            html += `
            <div class="token-card">
                <div class="token-header">
                    <h3>${t.name}</h3>
                    <span class="badge ${t.has_value ? 'has' : 'missing'}">${t.has_value ? '已配置' : '未配置'}</span>
                </div>
                <p class="token-desc">${t.description}</p>
                <div class="token-meta">env: ${t.env_key} | 示例: ${t.example}</div>
                <div class="token-value">当前: ${t.value || '(空)'}</div>
                ${t.get_key_url ? `<a href="${t.get_key_url}" target="_blank" class="token-link">获取Key</a>` : ''}
                <div class="token-actions">
                    <input type="password" id="input-${id}" placeholder="输入新Token" class="token-input">
                    <button onclick="window.saveToken('${id}')" class="btn-save">保存</button>
                    <button onclick="window.clearToken('${id}')" class="btn-clear">清除</button>
                </div>
            </div>`;
        }
        html += '</div>';
        
        html += `
        <div class="real-search-config">
            <h3>真实搜索配置</h3>
            <div>Bing: ${config.bing?.configured ? '✅' : '❌'} ${config.bing?.source}</div>
            <div>GitHub: ${config.github?.configured ? '✅' : '❌'} ${config.github?.source}</div>
            <div>DuckDuckGo: ✅ ${config.duckduckgo?.source}</div>
            <div>当前优选: <b>${config.overall?.current}</b> | 真实搜索: ${config.overall?.has_real_search ? '✅可用' : '❌演示'}</div>
        </div>`;
        
        container.innerHTML = html;
    } catch (e) {
        container.innerHTML = `加载失败: ${e.message}`;
    }
}

window.saveToken = async (id) => {
    const input = document.getElementById(`input-${id}`);
    const value = input.value.trim();
    if (!value) { alert('请输入Token'); return; }
    try {
        await tokenApi.set(id, value);
        alert(`已保存 ${id}`);
        renderTokenBar();
        renderTokensView();
    } catch (e) {
        alert(`保存失败: ${e.message}`);
    }
};

window.clearToken = async (id) => {
    if (!confirm(`清除 ${id} ?`)) return;
    try {
        await tokenApi.set(id, '');
        alert(`已清除 ${id}`);
        renderTokenBar();
        renderTokensView();
    } catch (e) {
        alert(`清除失败: ${e.message}`);
    }
};
