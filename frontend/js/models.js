// models.js - 本地模型载入功能 - 真实扫描+自定义模型A
import { apiGet, apiPost } from './api.js';

export const modelsApi = {
    list: () => apiGet('/api/models'),
    status: () => apiGet('/api/models/status'),
    switch: (id) => apiPost(`/api/models/switch?model_id=${encodeURIComponent(id)}`),
    add: (path, name) => apiPost('/api/models/add', {path, name}),
    remove: (id) => fetch(`/api/models/${encodeURIComponent(id)}`, {method: 'DELETE'}).then(r=>r.json()),
    versions: () => apiGet('/api/models/versions'),
    scanDirs: () => apiGet('/api/models/scan/dirs')
};

export async function renderModelsView() {
    let container = document.getElementById('models-view') || document.getElementById('view-models') || document.getElementById('models-grid');
    if (!container) return;
    // If container is view-models, use it directly, else find inner
    if (container.id === 'view-models') {
        // Check if has inner grid
        const inner = document.getElementById('models-grid');
        if (inner) container = inner;
    }
    
    try {
        const data = await modelsApi.list();
        const status = await modelsApi.status();
        const versions = await modelsApi.versions();
        
        let html = `
        <div class="models-status">
            <h3>🦙 llama.cpp Server 状态 - 真实检测</h3>
            <div class="sys-row"><span>运行中</span><span>${status.running ? '✅ 是' : '❌ 否'} ${status.running ? `端口${status.port}监听` : '未运行'}</span></div>
            <div class="sys-row"><span>地址</span><span>${status.host}:${status.port} - ${status.api_base}</span></div>
            <div class="sys-row"><span>活跃模型</span><span>${status.active_model?.name || '无'} (${status.active_model_id||'--'})</span></div>
            <div class="sys-row"><span>总模型数</span><span>${status.total_models} (自定义${status.custom_models})</span></div>
            <div class="sys-row"><span>进程</span><span>${status.processes?.length||0}个 ${status.processes?.map(p=>p.pid).join(', ')||''}</span></div>
            <div class="sys-row"><span>真实检测</span><span>✅ 端口+进程真实检测，非演示</span></div>
        </div>
        
        <div class="models-actions" style="margin:12px 0;display:flex;gap:8px;flex-wrap:wrap">
            <button onclick="window.scanModels()" class="btn">刷新扫描</button>
            <button onclick="window.addCustomModel()" class="btn primary">添加模型A (自定义路径)</button>
            <button onclick="window.showScanDirs()" class="btn">扫描目录</button>
        </div>
        
        <div class="models-grid">
            <h3>📦 本地模型列表 - 真实扫描文件系统 GGUF + 自定义模型A (${data.total}个)</h3>
            <div class="grid grid-2">
                ${data.models?.map(m => `
                <div class="card" style="${m.is_active ? 'border-color:var(--success);background:rgba(34,197,94,0.05)' : ''}">
                    <h3>${m.name} ${m.is_active ? '<span class="badge success">活跃</span>' : ''} ${m.is_custom ? '<span class="badge accent">自定义A</span>' : ''} ${m.type==='gguf' ? '<span class="badge">GGUF</span>' : ''} ${m.type==='ollama' ? '<span class="badge">Ollama</span>' : ''}</h3>
                    <div class="sys-row"><span>ID</span><span style="font-size:9px">${m.id}</span></div>
                    <div class="sys-row"><span>路径</span><span style="font-size:8px;word-break:break-all">${m.path}</span></div>
                    <div class="sys-row"><span>大小</span><span>${m.size_gb}GB</span></div>
                    <div class="sys-row"><span>量化</span><span>${m.quantization}</span></div>
                    <div class="sys-row"><span>参数</span><span>${m.parameters}</span></div>
                    <div class="sys-row"><span>上下文</span><span>${m.context_length}</span></div>
                    <div class="sys-row"><span>存在</span><span>${m.exists ? '✅' : '❌ (Windows路径Linux演示)'} ${m.is_custom ? '| 自定义模型A' : ''}</span></div>
                    <div style="display:flex;gap:6px;margin-top:8px">
                        <button onclick="window.switchModel('${m.id}')" class="btn primary" style="font-size:10px" ${m.is_active ? 'disabled' : ''}>${m.is_active ? '当前' : '切换到此模型'}</button>
                        ${m.is_custom ? `<button onclick="window.removeModel('${m.id}')" class="btn" style="font-size:10px">移除</button>` : ''}
                    </div>
                    <div style="font-size:8px;color:var(--text3);margin-top:6px">${JSON.stringify(m.performance||{}).slice(0,100)}</div>
                </div>
                `).join('') || '<div class="empty">无模型，请添加模型A</div>'}
            </div>
        </div>
        
        <div class="card" style="margin-top:12px">
            <h3>📚 模型版本 - LoRA进化版本</h3>
            <div class="list">
                ${versions.versions?.map(v => `
                <div class="list-item">
                    <div><div class="item-title">${v.name} ${v.is_active ? '<span class="badge success">当前</span>' : ''}</div><div class="item-meta">${v.type} | ${v.created} | ${v.size_mb}MB | ${v.description||''} ${v.improvement||''}</div></div>
                    <span class="badge ${v.is_active?'success':''}">${v.id}</span>
                </div>
                `).join('') || '无版本'}
            </div>
        </div>
        
        <div class="card" style="margin-top:12px">
            <h3>💡 如何添加本地模型A</h3>
            <div style="font-size:11px;line-height:1.6">
                <p>1. 点击“添加模型A”，输入你的模型路径，例如：</p>
                <code style="display:block;padding:8px;background:var(--bg);border-radius:6px;margin:6px 0">D:\\models\\你的模型A.gguf<br>/home/user/models/modelA.gguf<br>./models/custom.gguf</code>
                <p>2. 系统会真实检查路径，GGUF文件大小、量化自动识别</p>
                <p>3. 添加后可在列表中看到，标记为“自定义A”，可切换</p>
                <p>4. 切换模型会真实重启 llama.cpp server (Windows) 或记录意图 (Linux演示)</p>
                <p>5. 支持Ollama自动检测，若Ollama运行在11434端口，会自动列出</p>
                <p><b>你的Qwen3模型：</b> D:\\llama.cpp\\Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ4_XS.gguf 已预置</p>
            </div>
        </div>
        `;
        
        container.innerHTML = html;
    } catch (e) {
        container.innerHTML = `加载失败: ${e.message}<br><pre>${e.stack||''}</pre>`;
    }
}

window.scanModels = async () => {
    await renderModelsView();
};

window.switchModel = async (id) => {
    if (!confirm(`切换到模型 ${id}？将重启 llama.cpp server`)) return;
    try {
        const btn = event.target;
        btn.textContent = '切换中...';
        btn.disabled = true;
        const res = await modelsApi.switch(id);
        alert(`${res.success ? '✅' : '❌'} ${res.message||res.error}\n步骤:\n${(res.steps||[]).join('\n')}`);
        renderModelsView();
    } catch (e) {
        alert(`切换失败: ${e.message}`);
    }
};

window.addCustomModel = async () => {
    const path = prompt('输入模型A路径，例如 D:\\models\\modelA.gguf 或 /home/user/models/model.gguf:');
    if (!path) return;
    const name = prompt('模型名称（可选，回车使用文件名）:', '');
    try {
        const res = await modelsApi.add(path, name || null);
        if (res.success) {
            alert(`✅ 已添加模型A: ${res.model.name}\n路径: ${res.model.path}\n大小: ${res.model.size_gb}GB`);
            renderModelsView();
        } else {
            alert(`❌ 失败: ${res.error}`);
        }
    } catch (e) {
        alert(`添加失败: ${e.message}`);
    }
};

window.removeModel = async (id) => {
    if (!confirm(`移除自定义模型 ${id}？`)) return;
    try {
        const res = await modelsApi.remove(id);
        alert(res.success ? '已移除' : `失败: ${res.error}`);
        renderModelsView();
    } catch (e) {
        alert(`移除失败: ${e.message}`);
    }
};

window.showScanDirs = async () => {
    try {
        const data = await modelsApi.scanDirs();
        alert(`扫描目录:\n${data.scan_dirs?.join('\n')}\n\n自定义文件: ${data.custom_file}\n\n${data.note}`);
    } catch (e) {
        alert(e.message);
    }
};
