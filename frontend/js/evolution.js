// 进化仪表盘 v3.0 - 前端
// 训练统计+日志流+版本历史+技能基因树+资源状态+SSE推送

class EvolutionDashboard {
    constructor(apiBase = '') {
        this.apiBase = apiBase;
        this.sse = null;
    }

    async getStatus() {
        try {
            const res = await fetch(`${this.apiBase}/api/evolution/status`);
            return await res.json();
        } catch (e) {
            return { error: e.message };
        }
    }

    async getData() {
        try {
            const res = await fetch(`${this.apiBase}/api/evolution/data`);
            return await res.json();
        } catch (e) {
            return { error: e.message };
        }
    }

    async getVRAM() {
        try {
            const res = await fetch(`${this.apiBase}/api/evolution/vram`);
            return await res.json();
        } catch (e) {
            return { error: e.message };
        }
    }

    async getResources() {
        try {
            const res = await fetch(`${this.apiBase}/api/evolution/resources`);
            return await res.json();
        } catch (e) {
            return { error: e.message };
        }
    }

    async getPrompts() {
        try {
            const res = await fetch(`${this.apiBase}/api/evolution/prompts`);
            return await res.json();
        } catch (e) {
            return { error: e.message };
        }
    }

    async getSkillGene() {
        try {
            const res = await fetch(`${this.apiBase}/api/skills/gene`);
            return await res.json();
        } catch (e) {
            return { error: e.message };
        }
    }

    async getMemoryV3() {
        try {
            const res = await fetch(`${this.apiBase}/api/memory/v3`);
            return await res.json();
        } catch (e) {
            return { error: e.message };
        }
    }

    async startEvolution(manual = true) {
        try {
            const res = await fetch(`${this.apiBase}/api/evolution/start?manual=${manual}`, { method: 'POST' });
            return await res.json();
        } catch (e) {
            return { error: e.message };
        }
    }

    async evaluate() {
        try {
            const res = await fetch(`${this.apiBase}/api/evolution/evaluate`, { method: 'POST' });
            return await res.json();
        } catch (e) {
            return { error: e.message };
        }
    }

    startSSE(onMessage) {
        if (this.sse) this.sse.close();
        
        this.sse = new EventSource(`${this.apiBase}/api/evolution/stream`);
        
        this.sse.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                onMessage(data);
            } catch (e) {
                onMessage({ raw: event.data, error: e.message });
            }
        };
        
        this.sse.onerror = (e) => {
            console.warn('SSE错误:', e);
            // 自动重连
            setTimeout(() => this.startSSE(onMessage), 5000);
        };
        
        return this.sse;
    }

    stopSSE() {
        if (this.sse) {
            this.sse.close();
            this.sse = null;
        }
    }

    renderStatus(status, containerId = 'evolution-status') {
        const container = document.getElementById(containerId);
        if (!container) return;

        const html = `
            <div class="evolution-card">
                <h3>进化状态 - ${status.status || '未知'}</h3>
                <p>当前LoRA: ${status.current_lora || '无'}</p>
                <p>基础模型: ${status.base_model || '未知'}</p>
                <p>模型路径: ${status.model_path || '未配置'} ${status.model_exists ? '✅' : '❌'}</p>
                <p>进化次数: ${status.evolution_count || 0}</p>
                <p>上次进化: ${status.last_evolution_human || '从未'}</p>
                <p>训练数据: SFT ${status.training_data?.sft_samples || 0} DPO ${status.training_data?.dpo_samples || 0}</p>
                <div class="techniques">
                    <h4>v3.0 技术</h4>
                    <ul>
                        ${Object.entries(status.v2_5_techniques || status.v3_techniques || {}).map(([k, v]) => 
                            `<li>${k}: ${typeof v === 'object' ? v.description || JSON.stringify(v) : v}</li>`
                        ).join('')}
                    </ul>
                </div>
            </div>
        `;
        container.innerHTML = html;
    }

    renderVRAM(vram, containerId = 'evolution-vram') {
        const container = document.getElementById(containerId);
        if (!container) return;

        const rec = vram.recommended || {};
        const html = `
            <div class="evolution-card">
                <h3>VRAM资源</h3>
                <p>总显存: ${vram.total_gb || 0}GB</p>
                <p>可用: ${vram.available_gb || 0}GB</p>
                <p>设备: ${vram.device || '未知'}</p>
                <p>推荐模型: ${rec.model || '未知'} - ${rec.note || ''}</p>
                <p>可训练: ${rec.can_train ? '✅' : '❌'}</p>
            </div>
        `;
        container.innerHTML = html;
    }

    renderResources(resources, containerId = 'evolution-resources') {
        const container = document.getElementById(containerId);
        if (!container) return;

        const canTrain = resources.can_train ? '✅ 可训练' : '❌ 不可训练';
        const reason = resources.can_train_reason || {};

        const html = `
            <div class="evolution-card">
                <h3>资源状态 - ${canTrain}</h3>
                <p>CPU: ${resources.cpu_memory?.cpu || 0}% 内存: ${resources.cpu_memory?.memory || 0}%</p>
                <p>VRAM: ${resources.vram?.free_gb || 0}GB/${resources.vram?.total_gb || 0}GB</p>
                <p>插电: ${resources.power?.is_plugged ? '✅' : '❌'} 电量: ${resources.power?.battery_percent || 100}%</p>
                <p>游戏: ${resources.game_meeting?.game_running ? '🎮 运行中' : '无'} 会议: ${resources.game_meeting?.meeting_running ? '📹 运行中' : '无'}</p>
                <details>
                    <summary>详细原因</summary>
                    <pre>${JSON.stringify(reason, null, 2)}</pre>
                </details>
            </div>
        `;
        container.innerHTML = html;
    }
}

// 全局
window.EvolutionDashboard = EvolutionDashboard;
window.evolutionDashboard = new EvolutionDashboard();

// 自动初始化
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('evolution-status')) {
        evolutionDashboard.getStatus().then(s => evolutionDashboard.renderStatus(s));
        evolutionDashboard.getVRAM().then(v => evolutionDashboard.renderVRAM(v));
        evolutionDashboard.getResources().then(r => evolutionDashboard.renderResources(r));
        
        // 每30秒刷新
        setInterval(() => {
            evolutionDashboard.getStatus().then(s => evolutionDashboard.renderStatus(s));
            evolutionDashboard.getResources().then(r => evolutionDashboard.renderResources(r));
        }, 30000);
    }
});
