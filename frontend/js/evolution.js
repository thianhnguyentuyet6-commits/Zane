// evolution.js - 进化+梦境+向量模块 - A夯实
import { apiGet, apiPost } from './api.js';

export async function renderEvolutionView() {
    const container = document.getElementById('evolution-view');
    if (!container) return;
    try {
        const status = await apiGet('/api/evolution/status');
        const data = await apiGet('/api/evolution/data');
        const dreaming = await apiGet('/api/dreaming/status');
        
        container.innerHTML = `
        <div class="evolution-status">
            <h3>自我进化 - QLoRA + 梦境三阶段 + 数据飞轮</h3>
            <div>状态: ${status.status}</div>
            <div>梦境阈值: ${dreaming.threshold} | 权重: ${JSON.stringify(dreaming.weights)}</div>
            <div>训练数据: SFT ${data.stats?.sft || 0} DPO ${data.stats?.dpo || 0}</div>
        </div>
        <div class="actions">
            <button onclick="window.runDreaming()" class="btn">梦境整理</button>
            <button onclick="window.startEvolution()" class="btn">开始进化</button>
        </div>
        <pre>${JSON.stringify(data.recent?.slice(0,3), null, 2)}</pre>
        `;
    } catch (e) {
        container.innerHTML = `加载失败: ${e.message}`;
    }
}

window.runDreaming = async () => {
    try {
        const res = await apiPost('/api/dreaming/run-all?days=7');
        alert(`梦境完成: 扫描${res.light?.scanned} 晋升${res.deep?.new_memories}`);
        renderEvolutionView();
    } catch (e) {
        alert(`失败: ${e.message}`);
    }
};

window.startEvolution = async () => {
    try {
        const res = await apiPost('/api/evolution/start?manual=true');
        alert(`进化: ${JSON.stringify(res)}`);
    } catch (e) {
        alert(`失败: ${e.message}`);
    }
};
