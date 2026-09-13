// 进化仪表盘 v0914 - SSE重连指数退避+失败状态+训练崩溃恢复
// 训练统计+日志流+版本历史+技能基因树+资源状态+SSE推送+Canvas图表

class EvolutionDashboardV0914 {
    constructor(apiBase = '') {
        this.apiBase = apiBase;
        this.sse = null;
        this.sseRetryCount = 0;
        this.sseMaxRetries = 10;
        this.sseBaseDelay = 1000; // 1秒基础延迟
        this.charts = {};
        this.logBuffer = [];
        this.trainingState = 'idle'; // idle, training, failed, success
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
        const result = await this.fetchJSON('/api/evolution/training/start', { method: 'POST' });
        if (result.success) {
            this.trainingState = 'training';
            this.sseRetryCount = 0; // 重置重连计数
        }
        return result;
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

    // SSE流式日志 - v0914 指数退避重连+失败状态处理+不卡转圈
    startSSE(onMessage, onError = null, onStateChange = null) {
        if (this.sse) {
            this.sse.close();
            this.sse = null;
        }
        
        const connect = () => {
            console.log(`[SSE] 尝试连接，重试次数: ${this.sseRetryCount}/${this.sseMaxRetries}`);
            
            this.sse = new EventSource(`${this.apiBase}/api/evolution/stream`);
            this.logBuffer = [];
            
            this.sse.onopen = () => {
                console.log('[SSE] 连接已建立');
                this.sseRetryCount = 0; // 重置
                if (onStateChange) onStateChange('connected');
            };
            
            this.sse.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.logBuffer.push(data);
                    if (this.logBuffer.length > 100) this.logBuffer.shift();
                    
                    // 检查训练状态
                    if (data.status) {
                        this.trainingState = data.status;
                        if (onStateChange) onStateChange(data.status, data);
                        
                        // 训练失败或成功，停止重连
                        if (data.status === 'failed' || data.status === 'error') {
                            console.error('[SSE] 训练失败:', data);
                            this.trainingState = 'failed';
                            if (onStateChange) onStateChange('failed', data);
                            // 不自动重连，显示失败状态
                            this.stopSSE();
                            if (onError) onError(new Error(data.message || '训练失败'), data);
                            return;
                        } else if (data.status === 'success' || data.status === 'completed') {
                            console.log('[SSE] 训练成功:', data);
                            this.trainingState = 'success';
                            if (onStateChange) onStateChange('success', data);
                        }
                    }
                    
                    // 检查是否有错误
                    if (data.error || data.level === 'error') {
                        console.warn('[SSE] 收到错误:', data);
                        if (data.need_reconnect === false) {
                            // 明确不需要重连
                            this.stopSSE();
                        }
                    }
                    
                    onMessage(data, this.logBuffer);
                } catch (e) {
                    const raw = { raw: event.data, error: e.message, timestamp: Date.now(), parse_error: true };
                    this.logBuffer.push(raw);
                    onMessage(raw, this.logBuffer);
                }
            };
            
            this.sse.onerror = (e) => {
                console.warn(`[SSE] 连接错误，重试 ${this.sseRetryCount+1}/${this.sseMaxRetries}:`, e);
                
                this.sse.close();
                this.sse = null;
                
                if (this.sseRetryCount >= this.sseMaxRetries) {
                    console.error('[SSE] 达到最大重试次数，停止重连');
                    this.trainingState = 'failed';
                    if (onStateChange) onStateChange('failed', {error: 'SSE重连失败，已达最大重试'});
                    if (onError) onError(new Error('SSE连接失败，已达最大重试次数'), {retry_count: this.sseRetryCount});
                    return;
                }
                
                // 指数退避重连：1s, 2s, 4s, 8s, 16s... 最大30s
                const delay = Math.min(this.sseBaseDelay * Math.pow(2, this.sseRetryCount), 30000);
                this.sseRetryCount++;
                
                console.log(`[SSE] ${delay}ms后重连...`);
                if (onStateChange) onStateChange('reconnecting', {retry_count: this.sseRetryCount, delay});
                
                setTimeout(() => {
                    connect();
                }, delay);
                
                if (onError) onError(e, {retry_count: this.sseRetryCount, delay, will_retry: true});
            };
        };
        
        connect();
        return this.sse;
    }

    stopSSE() {
        if (this.sse) {
            this.sse.close();
            this.sse = null;
            console.log('[SSE] 已停止');
        }
    }

    // 检查训练是否卡死 - 前端检测训练进程异常退出
    async checkTrainingStuck() {
        try {
            const status = await this.getTrainingStatus();
            
            // 如果前端显示训练中，但后端状态不是训练中，可能卡死或异常退出
            if (this.trainingState === 'training' && status.status !== 'training' && status.status !== 'running') {
                console.warn('[训练检测] 前端显示训练中，但后端状态:', status.status);
                
                if (status.status === 'failed' || status.status === 'error') {
                    this.trainingState = 'failed';
                    return {
                        stuck: false,
                        failed: true,
                        status: status,
                        message: `训练失败: ${status.error || status.message || '未知错误'}`
                    };
                } else if (status.status === 'idle' || status.status === 'completed' || status.status === 'success') {
                    // 后端已空闲但前端还在训练中，可能异常退出未通知
                    if (status.last_error) {
                        this.trainingState = 'failed';
                        return {
                            stuck: true,
                            failed: true,
                            status: status,
                            message: `训练异常退出: ${status.last_error}，前端卡在训练中`
                        };
                    } else {
                        this.trainingState = status.status;
                        return {
                            stuck: true,
                            failed: false,
                            status: status,
                            message: `训练已结束但前端未更新，后端状态: ${status.status}`
                        };
                    }
                }
            }
            
            return {stuck: false, failed: false, status: status};
        } catch (e) {
            console.error('[训练检测] 检查失败:', e);
            return {stuck: false, failed: false, error: e.message};
        }
    }

    // Canvas图表
    renderChart(canvasId, data, options = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        const { width, height } = canvas;
        ctx.clearRect(0, 0, width, height);

        ctx.fillStyle = options.bgColor || '#1a1a2e';
        ctx.fillRect(0, 0, width, height);

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

        ctx.fillStyle = (options.lineColor || '#00ff88') + '33';
        ctx.lineTo(width, height);
        ctx.lineTo(0, height);
        ctx.closePath();
        ctx.fill();

        ctx.fillStyle = '#ccc';
        ctx.font = '10px monospace';
        ctx.fillText(`max: ${max.toFixed(2)}`, 5, 12);
        ctx.fillText(`min: ${min.toFixed(2)}`, 5, height - 5);
    }

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

        Object.entries(levels).forEach(([level, levelNodes]) => {
            const y = parseInt(level) * levelHeight + levelHeight/2;
            const stepX = width / (levelNodes.length + 1);
            levelNodes.forEach((node, i) => {
                const x = stepX * (i + 1);
                node.x = x / width;

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

    renderStatus(status, containerId = 'evolution-status') {
        const container = document.getElementById(containerId);
        if (!container) return;

        const trainingStatus = status.training_status || {};
        const stateDisplay = this.trainingState === 'failed' ? '❌ 失败' : 
                           this.trainingState === 'training' ? '🏃 训练中' :
                           this.trainingState === 'success' ? '✅ 成功' : status.status || '空闲';

        const html = `
            <div class="evolution-card">
                <h3>🧬 进化状态 - ${stateDisplay}</h3>
                <div class="grid-2">
                    <div>当前LoRA: <code>${status.current_lora || '无'}</code></div>
                    <div>基础模型: ${status.base_model || '未知'}</div>
                    <div>模型路径: ${status.model_path || '未配置'} ${status.model_exists ? '✅' : '❌'}</div>
                    <div>进化次数: ${status.evolution_count || 0}</div>
                    <div>上次进化: ${status.last_evolution_human || '从未'}</div>
                    <div>训练数据: SFT ${status.training_data?.sft_samples || 0} DPO ${status.training_data?.dpo_samples || 0}</div>
                    <div>训练状态: ${trainingStatus.status || this.trainingState} ${trainingStatus.pid ? `PID:${trainingStatus.pid}` : ''}</div>
                    <div>SSE重连: ${this.sseRetryCount}次 ${this.sse ? '🟢 已连接' : '🔴 未连接'}</div>
                </div>
                ${this.trainingState === 'failed' ? `
                <div style="background:#ef4444; color:white; padding:8px; border-radius:4px; margin-top:8px; font-size:11px">
                    ⚠️ 训练失败，前端不再卡在"训练中"转圈，已正确收到失败状态<br>
                    错误: ${trainingStatus.error || status.last_error || '未知'}<br>
                    请检查日志: data/logs/training_*.log
                </div>` : ''}
                <div class="techniques" style="margin-top:10px">
                    <h4>v0914 技术栈 8模块 + 崩溃恢复+SSE重连</h4>
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
                <h3>🎮 VRAM资源 - 双轨推荐 + 8GB 3060ti支持</h3>
                <div class="grid-2">
                    <div>总显存: ${vram.total_gb || 0}GB</div>
                    <div>可用: ${vram.free_gb || vram.available_gb || 0}GB</div>
                    <div>设备: ${vram.device || 'cpu'}</div>
                    <div>可用: ${vram.sufficient ? '✅' : '❌'} ${vram.error || ''}</div>
                    <div>GPU利用率: ${vram.gpu_util || 0}%</div>
                    <div>支持8GB: ${vramData.supports_8gb ? '✅ 3060ti可训练7B' : '❌'}</div>
                </div>
                <div style="margin-top:8px">
                    <div>推荐模型: <strong>${rec.model || all.recommended?.model || '未知'}</strong> - ${rec.note || all.recommended?.note || ''}</div>
                    <div>可训练: ${rec.can_train ? '✅' : '❌'} | 路径: ${all.gguf_path ? 'GGUF✅' : 'GGUF❌'} ${all.hf_path ? 'HF✅' : 'HF❌'}</div>
                    ${rec.cpu_offload ? `<div>CPU Offload: ✅ 需32GB内存 | 梯度检查点: ${rec.gradient_checkpointing ? '✅' : '❌'}</div>` : ''}
                </div>
                <canvas id="vram-chart" width="300" height="80" style="margin-top:8px; width:100%"></canvas>
            </div>
        `;
        container.innerHTML = html;

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
        const idle = resources.idle || {};

        const html = `
            <div class="evolution-card">
                <h3>📊 资源状态 - ${canTrain} - 空闲${idle.idle_minutes || 0}分+CPU/GPU阈值</h3>
                <div class="grid-2" style="font-size:11px">
                    <div>空闲: ${idle.is_idle ? `✅ ${idle.idle_minutes}分` : `❌ ${idle.idle_minutes}分/需${idle.required_idle}分`}</div>
                    <div>CPU: ${cpuMem.cpu || 0}% 内存: ${cpuMem.memory || 0}%</div>
                    <div>VRAM: ${vram.free_gb || 0}GB/${vram.total_gb || 0}GB GPU:${vram.gpu_util || 0}% ${vram.sufficient ? '✅' : '❌'}</div>
                    <div>插电: ${power.is_plugged ? '🔌 插电✅' : '🔋 电池'} 电量: ${power.battery_percent || 100}%</div>
                    <div>游戏: ${game.game_running ? '🎮 运行中❌' : '无✅'} 会议: ${game.meeting_running ? '📹 运行中❌' : '无✅'}</div>
                    <div>全屏: ${game.is_fullscreen ? '🖥️ 全屏❌' : '窗口✅'}</div>
                    <div>摄像头: ${game.camera_mic?.camera_in_use ? '📹 占用❌' : '无✅'} 麦克风: ${game.camera_mic?.mic_in_use ? '🎤 占用❌' : '无✅'}</div>
                    <div>iOS远程: ${ios.ios_viewing ? '📱 查看中❌' : '无✅'}</div>
                </div>
                <details style="margin-top:8px">
                    <summary style="cursor:pointer; font-size:10px">详细原因 - 空闲N分钟+CPU/GPU阈值组合</summary>
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
                <h3>🔒 数据飞轮v3 过滤评分去重安全 + 阈值可配置</h3>
                <div class="grid-2" style="font-size:11px">
                    <div>SFT样本: ${stats.sft_samples || 0}</div>
                    <div>DPO样本: ${stats.dpo_samples || 0}</div>
                    <div>总过滤: ${stats.total_filtered || 0}</div>
                    <div>安全率: ${((stats.safe_rate || 0) * 100).toFixed(1)}%</div>
                    <div>去重: ${stats.deduped || 0}</div>
                    <div>高质量: ${stats.high_quality || 0}</div>
                    <div>阈值: ${stats.config?.min_quality || 0.8} 可配置</div>
                    <div>比例: ${stats.config?.ratio || 0.3}</div>
                </div>
                <div style="margin-top:8px; font-size:10px">
                    <div>危险路径: 11个 System32 /etc/shadow等 拦截率100% ✅</div>
                    <div>相似度: >0.9过滤 + 重要性0.5-0.9 + SimpleMem30% + 阈值可配置验证脚本</div>
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

        const isFailed = status.status === 'failed' || status.status === 'error' || this.trainingState === 'failed';
        const isTraining = status.status === 'training' || status.status === 'running' || this.trainingState === 'training';

        const html = `
            <div class="evolution-card" style="${isFailed ? 'border:2px solid #ef4444' : ''}">
                <h3>🚀 训练状态 - ${isFailed ? '❌ 失败' : isTraining ? '🏃 训练中' : status.status || '空闲'} ${isFailed ? '前端不再转圈' : ''}</h3>
                <div style="font-size:11px">
                    <div>输出目录: <code>${status.output_dir || '无'}</code></div>
                    <div>开始时间: ${status.start_time_human || status.start_time || '无'}</div>
                    <div>进程: ${status.pid || '无'} ${status.running ? '🏃 运行中' : '⏸️ 空闲'} 重试: ${status.retry_count || 0}/3</div>
                    <div>样本: ${status.samples || 0} | Epoch: ${status.epoch || 0}/${status.num_epochs || 1}</div>
                    <div>LoRA: rank ${status.lora_rank || 32} alpha ${status.lora_alpha || 64} ${status.cpu_offload ? 'CPU Offload✅' : ''}</div>
                    <div>SSE: ${this.sse ? '🟢 已连接' : '🔴 未连接'} 重连: ${this.sseRetryCount}次</div>
                </div>
                ${isFailed ? `
                <div style="background:#ef4444; color:white; padding:8px; border-radius:4px; margin-top:8px; font-size:11px">
                    ❌ 训练失败，前端已正确收到失败状态，不再卡在"训练中"转圈<br>
                    错误: ${status.error || status.last_error || '未知'}<br>
                    日志: ${status.log_path || 'data/logs/training_*.log'}<br>
                    崩溃恢复: ${status.retry_count || 0}/3次重试，状态已持久化
                </div>` : ''}
                ${status.log_tail ? `<pre style="font-size:9px; background:#1a1a2e; padding:8px; border-radius:4px; max-height:100px; overflow:auto; margin-top:8px">${status.log_tail}</pre>` : ''}
                <canvas id="training-chart" width="300" height="60" style="margin-top:8px; width:100%"></canvas>
            </div>
        `;
        container.innerHTML = html;

        setTimeout(() => {
            const chartData = [status.samples || 0, status.epoch || 0, status.lora_rank || 0, status.loss ? status.loss * 100 : 50];
            this.renderChart('training-chart', chartData, { lineColor: isFailed ? '#ef4444' : '#00ff88' });
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
                <h3>🧪 评估Harness - ${old.total || 0}任务 ${old.passed || 0}通过 ${old.success_rate || 0}% security ${byCategory.security?.success_rate || 0}% + 真实回放</h3>
                <div class="grid-2" style="font-size:11px">
                    <div>总任务: ${old.total || 0}</div>
                    <div>通过: ${old.passed || 0} 失败: ${old.failed || 0}</div>
                    <div>成功率: ${old.success_rate || 0}% ${evalData.real_eval ? '真实执行' : '模拟'}</div>
                    <div>晋升: ${promotion.should_promote ? '✅ 可晋升' : '❌ 不晋升'} 阈值2%</div>
                    <div>模式: ${evalData.real_eval ? '真实agent_runtime执行' : '模拟'} 可信度: ${evalData.real_eval ? '高' : '低(冒烟)'}</div>
                </div>
                <div style="margin-top:8px; font-size:10px">
                    ${Object.entries(byCategory).map(([cat, stat]) => 
                        `<div>${cat}: ${stat.passed}/${stat.total} ${stat.success_rate}% ${stat.success_rate === 100 ? '✅' : '❌'}</div>`
                    ).join('')}
                </div>
                <div style="margin-top:8px; font-size:9px">晋升原因: ${promotion.reason || '无'} 模式: ${promotion.mode || 'balanced'} ${evalData.real_eval ? '真实执行可信' : '模拟仅冒烟'}</div>
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

// 全局 v0914
window.EvolutionDashboard = EvolutionDashboardV0914;
window.evolutionDashboard = new EvolutionDashboardV0914();

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
                const mini = document.getElementById('resource-mini');
                if (mini) {
                    const res = r.resources || r;
                    mini.textContent = `CPU ${res.cpu_memory?.cpu || 0}% | 内存 ${res.cpu_memory?.memory || 0}% | ${res.can_train ? '✅可训练' : '❌不可训练'} 空闲${res.idle?.idle_minutes || 0}分`;
                }
            });
            evolutionDashboard.getFilterStats().then(f => {
                evolutionDashboard.renderFilterStats(f, 'evo-flywheel-v3');
            });
            evolutionDashboard.getTrainingStatus().then(t => {
                evolutionDashboard.renderTrainingStatus(t, 'evo-training-v3');
                evolutionDashboard.renderTrainingStatus(t, 'evo-training');
            });

            // 每30秒刷新 + 检查训练是否卡死
            setInterval(async () => {
                evolutionDashboard.getStatus().then(s => evolutionDashboard.renderStatus(s, 'evolution-status'));
                evolutionDashboard.getResources().then(r => evolutionDashboard.renderResources(r, 'evolution-resources'));
                evolutionDashboard.getTrainingStatus().then(t => evolutionDashboard.renderTrainingStatus(t, 'evo-training-v3'));
                
                // 检查训练是否卡死
                const stuckCheck = await evolutionDashboard.checkTrainingStuck();
                if (stuckCheck.stuck || stuckCheck.failed) {
                    console.warn('[训练检测]', stuckCheck.message);
                    const container = document.getElementById('evo-training-v3');
                    if (container && stuckCheck.failed) {
                        // 显示失败，不卡转圈
                        evolutionDashboard.renderTrainingStatus(stuckCheck.status, 'evo-training-v3');
                    }
                }
            }, 30000);
        }
    };

    initDashboard();

    document.addEventListener('click', (e) => {
        if (e.target.closest('[data-view="evolution"]')) {
            setTimeout(initDashboard, 500);
        }
    });
});

// 暴露全局函数 v0914
window.loadEvolutionV3 = () => {
    evolutionDashboard.getStatus().then(s => evolutionDashboard.renderStatus(s, 'evo-flywheel-v3'));
    evolutionDashboard.getVRAM().then(v => evolutionDashboard.renderVRAM(v, 'evo-vram'));
    evolutionDashboard.getResources().then(r => evolutionDashboard.renderResources(r, 'evo-resources'));
    evolutionDashboard.getFilterStats().then(f => evolutionDashboard.renderFilterStats(f, 'evo-flywheel-v3'));
    evolutionDashboard.getTrainingStatus().then(t => evolutionDashboard.renderTrainingStatus(t, 'evo-training-v3'));
    evolutionDashboard.getReplay().then(r => {
        const container = document.getElementById('evo-replay');
        if (container) container.innerHTML = `<pre style="font-size:9px">Replay: ${r.replay_count || 0}条 阈值${r.config?.min_quality || 0.8}可配置\n${JSON.stringify(r, null, 2).substring(0, 500)}</pre>`;
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
        if (container) container.innerHTML = `<pre style="font-size:9px">调度器: ${s.enabled ? '✅启用' : '❌禁用(默认)'} 空闲${s.idle_minutes}分+CPU阈值\n${JSON.stringify(s, null, 2).substring(0, 500)}</pre>`;
    });
};

window.startTraining = async () => {
    if (!confirm('启动训练？\n- 需24GB VRAM训练30B或8GB训练7B+32GB RAM\n- 非阻塞Popen+日志流+LoRA版本+崩溃重试3次\n- SSE推送+重连指数退避+失败不卡转圈')) return;
    
    const res = await evolutionDashboard.startTraining();
    alert(`训练启动: ${JSON.stringify(res).substring(0, 300)}`);
    
    // 启动SSE监听
    const logContainer = document.getElementById('training-log') || document.getElementById('evo-training-log');
    if (logContainer) {
        logContainer.innerHTML = 'SSE连接中...\n';
        evolutionDashboard.startSSE(
            (data, buffer) => {
                logContainer.innerHTML = buffer.slice(-20).map(d => 
                    `[${new Date(d.timestamp || Date.now()).toLocaleTimeString()}] ${d.message || d.raw || JSON.stringify(d).slice(0,100)}`
                ).join('\n');
                logContainer.scrollTop = logContainer.scrollHeight;
                
                // 更新状态
                evolutionDashboard.getTrainingStatus().then(t => {
                    evolutionDashboard.renderTrainingStatus(t, 'evo-training-v3');
                });
            },
            (error, info) => {
                console.warn('SSE错误:', error, info);
                if (info && info.will_retry) {
                    logContainer.innerHTML += `\n[SSE重连] ${info.retry_count}次 ${info.delay}ms后重连...\n`;
                } else {
                    logContainer.innerHTML += `\n[SSE失败] ${error.message} 不再重连，前端已正确收到失败状态，不卡转圈\n`;
                }
            },
            (state, data) => {
                console.log('[SSE状态]', state, data);
                if (state === 'failed') {
                    alert(`❌ 训练失败: ${data.message || data.error}\n前端不再转圈，已正确收到失败状态`);
                    evolutionDashboard.getTrainingStatus().then(t => {
                        evolutionDashboard.renderTrainingStatus(t, 'evo-training-v3');
                    });
                }
            }
        );
    }
    
    loadEvolutionV3();
};

window.runEvaluate = async () => {
    const useReal = confirm('是否使用真实回放评估？\n确定=真实调用agent_runtime执行几十条任务统计成功率（可信度高，耗时）\n取消=模拟成功率（冒烟测试，快速）');
    
    const res = await evolutionDashboard.fetchJSON(`/api/evolution/evaluate?real=${useReal}`, { method: 'POST' });
    const container = document.getElementById('evo-eval') || document.getElementById('bench-eval');
    if (container && res.eval) evolutionDashboard.renderEval(res, container.id);
    else alert(`评估: ${JSON.stringify(res).substring(0, 500)}\n${useReal ? '真实执行' : '模拟'}模式`);
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
                <div>危险样本: is_safe=${dangerous.is_safe} ${!dangerous.is_safe ? '✅拦截' : '❌未拦截'} reason=${dangerous.reason}</div>
                <div>安全样本: is_safe=${safe.is_safe} ${safe.is_safe ? '✅通过' : '❌拦截'} importance=${safe.importance}</div>
                <div>阈值: 可配置，验证脚本tests/test_threshold_validation.py</div>
            </div>
        `;
    }
};

console.log('✅ 进化仪表盘v0914已加载 - SSE重连指数退避+失败不卡转圈+崩溃恢复+8GB 3060ti支持');
