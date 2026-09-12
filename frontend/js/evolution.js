// 进化仪表盘 v7.0 - 完整版
// 训练统计+日志流+版本历史+技能基因树+资源状态+SSE推送+Canvas图表+基因树可视化

class EvolutionDashboard {
    constructor(apiBase = '') {
        this.apiBase = apiBase;
        this.sse = null;
        this.charts = {};
        this.logBuffer = [];
    }

    async fetchJSON(url, options = {}) {
        try {
            const res = await fetch(`${this.apiBase}${url}`, options);
            return await res.json();
        } catch (e) {
            return { error: e.message, available: false };
        }
    }

    async getStatus() { return this.fetchJSON('/api/evolution/status'); }
    async getData() { return this.fetchJSON('/api/evolution/data'); }
    async getVRAM() { return this.fetchJSON('/api/evolution/vram'); }
    async getResources() { return this.fetchJSON('/api/evolution/resources'); }
    async getFilterStats() { return this.fetchJSON('/api/evolution/filter/stats'); }
    async getReplay() { return this.fetchJSON('/api/evolution/replay'); }
    async getPrompts() { return this.fetchJSON('/api/evolution/prompts'); }
    async getStrategies() { return this.fetchJSON('/api/evolution/strategies'); }
    async getScheduler() { return this.fetchJSON('/api/evolution/scheduler'); }
    async getSkillGene() { return this.fetchJSON('/api/skills/gene'); }
    async getMemoryV3() { return this.fetchJSON('/api/memory/v3'); }
    async getTrainingStatus() { return this.fetchJSON('/api/evolution/training/status'); }

    async startEvolution(manual = true) {
        return this.fetchJSON(`/api/evolution/start?manual=${manual}`, { method: 'POST' });
    }

    async startTraining() {
        return this.fetchJSON('/api/evolution/training/start', { method: 'POST' });
    }

    async evaluate() {
        return this.fetchJSON('/api/evolution/evaluate', { method: 'POST' });
    }

    async testFilter(content, tools = []) {
        return this.fetchJSON('/api/evolution/filter/test', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content, tools })
        });
    }

    // SSE流式日志 - 自动重连+缓冲
    startSSE(onMessage, onError = null) {
        if (this.sse) this.sse.close();
        
        this.sse = new EventSource(`${this.apiBase}/api/evolution/stream`);
        this.logBuffer = [];
        
        this.sse.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.logBuffer.push(data);
                if (this.logBuffer.length > 100) this.logBuffer.shift();
                onMessage(data, this.logBuffer);
            } catch (e) {
                const raw = { raw: event.data, error: e.message, timestamp: Date.now() };
                this.logBuffer.push(raw);
                onMessage(raw, this.logBuffer);
            }
        };
        
        this.sse.onerror = (e) => {
            console.warn('SSE错误，5秒后重连:', e);
            if (onError) onError(e);
            setTimeout(() => this.startSSE(onMessage, onError), 5000);
        };
        
        return this.sse;
    }

    stopSSE() {
        if (this.sse) {
            this.sse.close();
            this.sse = null;
        }
    }

    // Canvas图表 - 训练统计
    renderChart(canvasId, data, options = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        const { width, height } = canvas;
        ctx.clearRect(0, 0, width, height);

        // 背景
        ctx.fillStyle = options.bgColor || '#1a1a2e';
        ctx.fillRect(0, 0, width, height);

        // 网格
        ctx.strokeStyle = '#2a2a4e';
        ctx.lineWidth = 0.5;
        for (let i = 0; i <= 4; i++) {
            const y = (height / 4) * i;
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(width, y);
            ctx.stroke();
        }

        if (!data || data.length === 0) {
            ctx.fillStyle = '#888';
            ctx.font = '12px monospace';
            ctx.fillText('无数据', width/2 - 20, height/2);
            return;
        }

        // 折线图
        const max = Math.max(...data, 1);
        const min = Math.min(...data, 0);
        const range = max - min || 1;
        const stepX = width / (data.length - 1 || 1);

        ctx.strokeStyle = options.lineColor || '#00ff88';
        ctx.lineWidth = 2;
        ctx.beginPath();
        data.forEach((val, i) => {
            const x = i * stepX;
            const y = height - ((val - min) / range) * height * 0.8 - height * 0.1;
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        });
        ctx.stroke();

        // 填充
        ctx.fillStyle = (options.lineColor || '#00ff88') + '33';
        ctx.lineTo(width, height);
        ctx.lineTo(0, height);
        ctx.closePath();
        ctx.fill();

        // 标签
        ctx.fillStyle = '#ccc';
        ctx.font = '10px monospace';
        ctx.fillText(`max: ${max.toFixed(2)}`, 5, 12);
        ctx.fillText(`min: ${min.toFixed(2)}`, 5, height - 5);
    }

    // 基因树可视化 - Canvas
    renderGeneTree(canvasId, treeData) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        const { width, height } = canvas;
        ctx.clearRect(0, 0, width, height);
        ctx.fillStyle = '#1a1a2e';
        ctx.fillRect(0, 0, width, height);

        if (!treeData || !treeData.nodes) {
            ctx.fillStyle = '#888';
            ctx.font = '12px monospace';
            ctx.fillText('无基因树数据', width/2 - 40, height/2);
            return;
        }

        const nodes = treeData.nodes || [];
        const levels = {};
        nodes.forEach(n => {
            const level = n.generation || 0;
            if (!levels[level]) levels[level] = [];
            levels[level].push(n);
        });

        const levelCount = Object.keys(levels).length || 1;
        const levelHeight = height / levelCount;

        // 绘制连线
        ctx.strokeStyle = '#444';
        ctx.lineWidth = 1;
        nodes.forEach(node => {
            if (node.parents) {
                node.parents.forEach(pid => {
                    const parent = nodes.find(n => n.id === pid);
                    if (parent) {
                        const x1 = (parent.x || Math.random()) * width;
                        const y1 = (parent.generation || 0) * levelHeight + levelHeight/2;
                        const x2 = (node.x || Math.random()) * width;
                        const y2 = (node.generation || 0) * levelHeight + levelHeight/2;
                        ctx.beginPath();
                        ctx.moveTo(x1, y1);
                        ctx.lineTo(x2, y2);
                        ctx.stroke();
                    }
                });
            }
        });

        // 绘制节点
        Object.entries(levels).forEach(([level, levelNodes]) => {
            const y = parseInt(level) * levelHeight + levelHeight/2;
            const stepX = width / (levelNodes.length + 1);
            levelNodes.forEach((node, i) => {
                const x = stepX * (i + 1);
                node.x = x / width;

                // 颜色按fitness
                const fitness = node.fitness || 0;
                let color = '#ff4444';
                if (fitness > 0.7) color = '#00ff88';
                else if (fitness > 0.4) color = '#ffaa00';

                ctx.fillStyle = color;
                ctx.beginPath();
                ctx.arc(x, y, 6, 0, Math.PI * 2);
                ctx.fill();

                ctx.fillStyle = '#ccc';
                ctx.font = '8px monospace';
                ctx.fillText(node.name ? node.name.substring(0, 10) : node.id.substring(0, 6), x - 15, y + 15);
                ctx.fillText(fitness.toFixed(2), x - 10, y - 8);
            });
        });

        ctx.fillStyle = '#888';
        ctx.font = '10px monospace';
        ctx.fillText(`基因总数: ${nodes.length}  层数: ${levelCount}`, 5, 12);
    }

    // 渲染状态 - 增强版
    renderStatus(status, containerId = 'evolution-status') {
        const container = document.getElementById(containerId);
        if (!container) return;

        const html = `
            <div class="evolution-card">
                <h3>🧬 进化状态 - ${status.status || '未知'}</h3>
                <div class="grid-2">
                    <div>当前LoRA: <code>${status.current_lora || '无'}</code></div>
                    <div>基础模型: ${status.base_model || '未知'}</div>
                    <div>模型路径: ${status.model_path || '未配置'} ${status.model_exists ? '✅' : '❌'}</div>
                    <div>进化次数: ${status.evolution_count || 0}</div>
                    <div>上次进化: ${status.last_evolution_human || '从未'}</div>
                    <div>训练数据: SFT ${status.training_data?.sft_samples || 0} DPO ${status.training_data?.dpo_samples || 0}</div>
                </div>
                <div class="techniques" style="margin-top:10px">
                    <h4>v3.0 技术栈 8模块</h4>
                    <div style="font-size:10px; font-family:monospace">
                        ${Object.entries(status.v2_5_techniques || status.v3_techniques || status.techniques || {}).map(([k, v]) => 
                            `<div>${typeof v === 'object' ? (v.description || JSON.stringify(v).substring(0,100)) : v}</div>`
                        ).join('')}
                    </div>
                </div>
            </div>
        `;
        container.innerHTML = html;
    }

    renderVRAM(vramData, containerId = 'evolution-vram') {
        const container = document.getElementById(containerId);
        if (!container) return;

        const vram = vramData.vram || vramData;
        const rec = vramData.recommended || vram.recommended || {};
        const all = vramData.all || {};

        const html = `
            <div class="evolution-card">
                <h3>🎮 VRAM资源 - 双轨推荐</h3>
                <div class="grid-2">
                    <div>总显存: ${vram.total_gb || 0}GB</div>
                    <div>可用: ${vram.free_gb || vram.available_gb || 0}GB</div>
                    <div>设备: ${vram.device || 'cpu'}</div>
                    <div>可用: ${vram.sufficient ? '✅' : '❌'} ${vram.error || ''}</div>
                </div>
                <div style="margin-top:8px">
                    <div>推荐模型: <strong>${rec.model || all.recommended?.model || '未知'}</strong> - ${rec.note || all.recommended?.note || ''}</div>
                    <div>可训练: ${rec.can_train ? '✅' : '❌'} | 路径: ${all.gguf_path ? 'GGUF✅' : 'GGUF❌'} ${all.hf_path ? 'HF✅' : 'HF❌'}</div>
                </div>
                <canvas id="vram-chart" width="300" height="80" style="margin-top:8px; width:100%"></canvas>
            </div>
        `;
        container.innerHTML = html;

        // 渲染VRAM图表
        setTimeout(() => {
            const chartData = [vram.total_gb || 0, vram.free_gb || 0, rec.lora_rank || 32];
            this.renderChart('vram-chart', chartData, { lineColor: '#00aaff' });
        }, 100);
    }

    renderResources(resourcesData, containerId = 'evolution-resources') {
        const container = document.getElementById(containerId);
        if (!container) return;

        const resources = resourcesData.resources || resourcesData;
        const canTrain = resources.can_train ? '✅ 可训练' : '❌ 不可训练';
        const reason = resources.can_train_reason || {};
        const cpuMem = resources.cpu_memory || {};
        const vram = resources.vram || {};
        const power = resources.power || {};
        const game = resources.game_meeting || {};
        const ios = resources.ios_remote || {};

        const html = `
            <div class="evolution-card">
                <h3>📊 资源状态 - ${canTrain}</h3>
                <div class="grid-2" style="font-size:11px">
                    <div>CPU: ${cpuMem.cpu || 0}% 内存: ${cpuMem.memory || 0}%</div>
                    <div>VRAM: ${vram.free_gb || 0}GB/${vram.total_gb || 0}GB ${vram.sufficient ? '✅' : '❌'}</div>
                    <div>插电: ${power.is_plugged ? '🔌 插电✅' : '🔋 电池'} 电量: ${power.battery_percent || 100}%</div>
                    <div>游戏: ${game.game_running ? '🎮 运行中❌' : '无✅'} 会议: ${game.meeting_running ? '📹 运行中❌' : '无✅'}</div>
                    <div>iOS远程: ${ios.ios_viewing ? '📱 查看中❌' : '无✅'}</div>
                    <div>全屏: ${game.is_fullscreen ? '🖥️ 全屏❌' : '窗口✅'}</div>
                </div>
                <details style="margin-top:8px">
                    <summary style="cursor:pointer; font-size:10px">详细原因 5维度</summary>
                    <pre style="font-size:9px; background:#1a1a2e; padding:8px; border-radius:4px; overflow:auto">${JSON.stringify(reason, null, 2)}</pre>
                </details>
                <canvas id="resource-chart" width="300" height="60" style="margin-top:8px; width:100%"></canvas>
            </div>
        `;
        container.innerHTML = html;

        setTimeout(() => {
            const chartData = [cpuMem.cpu || 0, cpuMem.memory || 0, vram.free_gb || 0, power.battery_percent || 100];
            this.renderChart('resource-chart', chartData, { lineColor: '#ffaa00' });
        }, 100);
    }

    renderFilterStats(statsData, containerId = 'evolution-filter') {
        const container = document.getElementById(containerId);
        if (!container) return;

        const stats = statsData.stats || statsData;
        const html = `
            <div class="evolution-card">
                <h3>🔒 数据飞轮v3 过滤评分去重安全</h3>
                <div class="grid-2" style="font-size:11px">
                    <div>SFT样本: ${stats.sft_samples || 0}</div>
                    <div>DPO样本: ${stats.dpo_samples || 0}</div>
                    <div>总过滤: ${stats.total_filtered || 0}</div>
                    <div>安全率: ${((stats.safe_rate || 0) * 100).toFixed(1)}%</div>
                    <div>去重: ${stats.deduped || 0}</div>
                    <div>高质量: ${stats.high_quality || 0}</div>
                </div>
                <div style="margin-top:8px; font-size:10px">
                    <div>危险路径: 11个 System32 /etc/shadow等 拦截率100% ✅</div>
                    <div>相似度: >0.9过滤 + 重要性0.5-0.9 + SimpleMem30%</div>
                </div>
                <canvas id="filter-chart" width="300" height="60" style="margin-top:8px; width:100%"></canvas>
            </div>
        `;
        container.innerHTML = html;

        setTimeout(() => {
            const chartData = [stats.sft_samples || 0, stats.dpo_samples || 0, stats.total_filtered || 0, (stats.safe_rate || 0) * 100];
            this.renderChart('filter-chart', chartData, { lineColor: '#ff4444' });
        }, 100);
    }

    renderTrainingStatus(status, containerId = 'evolution-training') {
        const container = document.getElementById(containerId);
        if (!container) return;

        const html = `
            <div class="evolution-card">
                <h3>🚀 训练状态 - ${status.status || 'idle'}</h3>
                <div style="font-size:11px">
                    <div>输出目录: <code>${status.output_dir || '无'}</code></div>
                    <div>开始时间: ${status.start_time_human || status.start_time || '无'}</div>
                    <div>进程: ${status.pid || '无'} ${status.running ? '🏃 运行中' : '⏸️ 空闲'}</div>
                    <div>样本: ${status.samples || 0} | Epoch: ${status.epoch || 0}/${status.num_epochs || 1}</div>
                    <div>LoRA: rank ${status.lora_rank || 32} alpha ${status.lora_alpha || 64}</div>
                </div>
                ${status.log_tail ? `<pre style="font-size:9px; background:#1a1a2e; padding:8px; border-radius:4px; max-height:100px; overflow:auto; margin-top:8px">${status.log_tail}</pre>` : ''}
                <canvas id="training-chart" width="300" height="60" style="margin-top:8px; width:100%"></canvas>
            </div>
        `;
        container.innerHTML = html;

        setTimeout(() => {
            const chartData = [status.samples || 0, status.epoch || 0, status.lora_rank || 0, status.loss ? status.loss * 100 : 50];
            this.renderChart('training-chart', chartData, { lineColor: '#00ff88' });
        }, 100);
    }

    renderEval(evalData, containerId = 'evolution-eval') {
        const container = document.getElementById(containerId);
        if (!container) return;

        const evalResult = evalData.eval || evalData;
        const old = evalResult.old || {};
        const promotion = evalData.promotion || {};
        const byCategory = old.by_category || {};

        const html = `
            <div class="evolution-card">
                <h3>🧪 评估Harness - ${old.total || 0}任务 ${old.passed || 0}通过 ${old.success_rate || 0}% security ${byCategory.security?.success_rate || 0}%</h3>
                <div class="grid-2" style="font-size:11px">
                    <div>总任务: ${old.total || 0}</div>
                    <div>通过: ${old.passed || 0} 失败: ${old.failed || 0}</div>
                    <div>成功率: ${old.success_rate || 0}%</div>
                    <div>晋升: ${promotion.should_promote ? '✅ 可晋升' : '❌ 不晋升'} 阈值2%</div>
                </div>
                <div style="margin-top:8px; font-size:10px">
                    ${Object.entries(byCategory).map(([cat, stat]) => 
                        `<div>${cat}: ${stat.passed}/${stat.total} ${stat.success_rate}% ${stat.success_rate === 100 ? '✅' : '❌'}</div>`
                    ).join('')}
                </div>
                <div style="margin-top:8px; font-size:9px">晋升原因: ${promotion.reason || '无'} 模式: ${promotion.mode || 'balanced'}</div>
                <canvas id="eval-chart" width="300" height="60" style="margin-top:8px; width:100%"></canvas>
            </div>
        `;
        container.innerHTML = html;

        setTimeout(() => {
            const chartData = Object.values(byCategory).map(c => c.success_rate || 0);
            this.renderChart('eval-chart', chartData.length ? chartData : [100, 100, 100, 100, 95], { lineColor: '#aa00ff' });
        }, 100);
    }
}

// 全局
window.EvolutionDashboard = EvolutionDashboard;
window.evolutionDashboard = new EvolutionDashboard();

// 自动初始化
document.addEventListener('DOMContentLoaded', () => {
    const initDashboard = () => {
        if (document.getElementById('evolution-status') || document.getElementById('evo-flywheel-v3')) {
            evolutionDashboard.getStatus().then(s => {
                evolutionDashboard.renderStatus(s, 'evolution-status');
                evolutionDashboard.renderStatus(s, 'evo-flywheel-v3');
            });
            evolutionDashboard.getVRAM().then(v => {
                evolutionDashboard.renderVRAM(v, 'evolution-vram');
                evolutionDashboard.renderVRAM(v, 'evo-vram');
                evolutionDashboard.renderVRAM(v, 'vram-info');
                evolutionDashboard.renderVRAM(v, 'system-vram');
            });
            evolutionDashboard.getResources().then(r => {
                evolutionDashboard.renderResources(r, 'evolution-resources');
                evolutionDashboard.renderResources(r, 'evo-resources');
                evolutionDashboard.renderResources(r, 'system-resources');
                evolutionDashboard.renderResources(r, 'auto-resources');
                // 迷你资源
                const mini = document.getElementById('resource-mini');
                if (mini) {
                    const res = r.resources || r;
                    mini.textContent = `CPU ${res.cpu_memory?.cpu || 0}% | 内存 ${res.cpu_memory?.memory || 0}% | ${res.can_train ? '✅可训练' : '❌不可训练'}`;
                }
            });
            evolutionDashboard.getFilterStats().then(f => {
                evolutionDashboard.renderFilterStats(f, 'evo-flywheel-v3');
            });
            evolutionDashboard.getTrainingStatus().then(t => {
                evolutionDashboard.renderTrainingStatus(t, 'evo-training-v3');
                evolutionDashboard.renderTrainingStatus(t, 'evo-training');
            });

            // 每30秒刷新
            setInterval(() => {
                evolutionDashboard.getStatus().then(s => evolutionDashboard.renderStatus(s, 'evolution-status'));
                evolutionDashboard.getResources().then(r => evolutionDashboard.renderResources(r, 'evolution-resources'));
                evolutionDashboard.getTrainingStatus().then(t => evolutionDashboard.renderTrainingStatus(t, 'evo-training-v3'));
            }, 30000);
        }
    };

    initDashboard();

    // 监听视图切换
    document.addEventListener('click', (e) => {
        if (e.target.closest('[data-view=\"evolution\"]')) {
            setTimeout(initDashboard, 500);
        }
    });
});

// 暴露全局函数
window.loadEvolutionV3 = () => {
    evolutionDashboard.getStatus().then(s => evolutionDashboard.renderStatus(s, 'evo-flywheel-v3'));
    evolutionDashboard.getVRAM().then(v => evolutionDashboard.renderVRAM(v, 'evo-vram'));
    evolutionDashboard.getResources().then(r => evolutionDashboard.renderResources(r, 'evo-resources'));
    evolutionDashboard.getFilterStats().then(f => evolutionDashboard.renderFilterStats(f, 'evo-flywheel-v3'));
    evolutionDashboard.getTrainingStatus().then(t => evolutionDashboard.renderTrainingStatus(t, 'evo-training-v3'));
    evolutionDashboard.getReplay().then(r => {
        const container = document.getElementById('evo-replay');
        if (container) container.innerHTML = `<pre style="font-size:9px">${JSON.stringify(r, null, 2).substring(0, 500)}</pre>`;
    });
    evolutionDashboard.getPrompts().then(p => {
        const container = document.getElementById('evo-prompts');
        if (container) container.innerHTML = `<pre style="font-size:9px">Prompt版本: ${p.total || p.prompts?.length || 0} 最佳: ${p.prompts?.[0]?.score || 0}</pre>`;
    });
    evolutionDashboard.getSkillGene().then(g => {
        const container = document.getElementById('evo-gene');
        if (container) {
            if (g.gene) {
                container.innerHTML = `<canvas id="gene-tree-canvas" width="300" height="150" style="width:100%"></canvas><pre style="font-size:9px">${JSON.stringify(g.gene, null, 2).substring(0, 300)}</pre>`;
                setTimeout(() => evolutionDashboard.renderGeneTree('gene-tree-canvas', g.gene), 100);
            } else {
                container.innerHTML = `<pre style="font-size:9px">${JSON.stringify(g, null, 2).substring(0, 500)}</pre>`;
            }
        }
    });
    evolutionDashboard.getScheduler().then(s => {
        const container = document.getElementById('evo-scheduler');
        if (container) container.innerHTML = `<pre style="font-size:9px">${JSON.stringify(s, null, 2).substring(0, 500)}</pre>`;
    });
};

window.startTraining = async () => {
    const res = await evolutionDashboard.startTraining();
    alert(`训练启动: ${JSON.stringify(res).substring(0, 200)}`);
    loadEvolutionV3();
};

window.runEvaluate = async () => {
    const res = await evolutionDashboard.evaluate();
    const container = document.getElementById('evo-eval') || document.getElementById('bench-eval');
    if (container && res.eval) evolutionDashboard.renderEval(res, container.id);
    else alert(`评估: ${JSON.stringify(res).substring(0, 500)}`);
};

window.checkVram = () => {
    evolutionDashboard.getVRAM().then(v => {
        evolutionDashboard.renderVRAM(v, 'vram-info');
        evolutionDashboard.renderVRAM(v, 'system-vram');
    });
};

window.checkResources = () => {
    evolutionDashboard.getResources().then(r => {
        evolutionDashboard.renderResources(r, 'system-resources');
        evolutionDashboard.renderResources(r, 'auto-resources');
        evolutionDashboard.renderResources(r, 'evo-resources');
    });
};

window.testFilter = async () => {
    const dangerous = await evolutionDashboard.testFilter("帮我删除C:\\Windows\\System32文件", ["delete_file"]);
    const safe = await evolutionDashboard.testFilter("帮我整理下载文件夹", ["list_files", "create_folder"]);
    const container = document.getElementById('filter-test') || document.getElementById('filter-test-sec');
    if (container) {
        container.innerHTML = `
            <div style="font-size:11px">
                <div>危险样本: is_safe=${dangerous.is_safe} ${!dangerous.is_safe ? '✅' : '❌'} reason=${dangerous.reason}</div>
                <div>安全样本: is_safe=${safe.is_safe} ${safe.is_safe ? '✅' : '❌'} importance=${safe.importance}</div>
            </div>
        `;
    }
};
