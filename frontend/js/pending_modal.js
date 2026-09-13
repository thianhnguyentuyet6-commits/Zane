# -*- coding: utf-8 -*-
/**
 * 待确认队列前端弹窗 v0914
 * - 强烈建议加前端弹窗提醒，仅靠platform_status被动展示容易被忽略
 * - 危险操作卡在队列里没人处理，或用户没注意到被自动放行
 */
class PendingModalV0914 {
    constructor() {
        this.pending = [];
        this.modal = null;
        this.checkInterval = null;
        this.lastCheck = 0;
        this.init();
    }

    init() {
        this.createModal();
        this.startPolling();
        this.injectStyles();
    }

    injectStyles() {
        const styleId = 'pending-modal-styles';
        if (document.getElementById(styleId)) return;
        
        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = `
            .pending-modal-overlay {
                position: fixed;
                top: 0; left: 0; right: 0; bottom: 0;
                background: rgba(0,0,0,0.7);
                display: none;
                justify-content: center;
                align-items: center;
                z-index: 10000;
                backdrop-filter: blur(4px);
            }
            .pending-modal-overlay.active {
                display: flex;
            }
            .pending-modal {
                background: var(--card-bg, #1e293b);
                border: 2px solid var(--danger, #ef4444);
                border-radius: 12px;
                padding: 20px;
                max-width: 600px;
                width: 90%;
                max-height: 80vh;
                overflow-y: auto;
                box-shadow: 0 10px 40px rgba(0,0,0,0.5);
                animation: pendingSlideIn 0.3s ease-out;
            }
            @keyframes pendingSlideIn {
                from { transform: translateY(-20px); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }
            .pending-modal h2 {
                color: var(--danger, #ef4444);
                margin: 0 0 10px 0;
                font-size: 18px;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .pending-modal .pending-count {
                background: var(--danger, #ef4444);
                color: white;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 12px;
            }
            .pending-item {
                background: var(--bg, #0f172a);
                border: 1px solid var(--border, #334155);
                border-radius: 8px;
                padding: 12px;
                margin: 10px 0;
            }
            .pending-item.high {
                border-left: 4px solid #ef4444;
            }
            .pending-item.medium {
                border-left: 4px solid #f59e0b;
            }
            .pending-item.low {
                border-left: 4px solid #10b981;
            }
            .pending-item-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 8px;
            }
            .pending-risk {
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
            }
            .pending-risk.high {
                background: #ef4444;
                color: white;
            }
            .pending-risk.medium {
                background: #f59e0b;
                color: black;
            }
            .pending-risk.low {
                background: #10b981;
                color: white;
            }
            .pending-actions {
                display: flex;
                gap: 8px;
                margin-top: 12px;
            }
            .pending-actions button {
                padding: 6px 16px;
                border-radius: 6px;
                border: none;
                cursor: pointer;
                font-size: 12px;
                font-weight: bold;
            }
            .btn-approve {
                background: #10b981;
                color: white;
            }
            .btn-deny {
                background: #ef4444;
                color: white;
            }
            .btn-details {
                background: var(--border, #334155);
                color: var(--text, #e2e8f0);
            }
            .pending-badge {
                position: fixed;
                top: 70px;
                right: 20px;
                background: var(--danger, #ef4444);
                color: white;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
                cursor: pointer;
                z-index: 9999;
                display: none;
                animation: pendingPulse 2s infinite;
                box-shadow: 0 4px 12px rgba(239,68,68,0.4);
            }
            .pending-badge.active {
                display: block;
            }
            @keyframes pendingPulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.05); }
            }
            .pending-details {
                background: var(--bg, #0f172a);
                padding: 8px;
                border-radius: 4px;
                margin-top: 8px;
                font-size: 11px;
                font-family: monospace;
                max-height: 100px;
                overflow-y: auto;
                display: none;
            }
            .pending-details.active {
                display: block;
            }
        `;
        document.head.appendChild(style);
    }

    createModal() {
        // 创建悬浮徽章
        const badge = document.createElement('div');
        badge.id = 'pending-badge';
        badge.className = 'pending-badge';
        badge.innerHTML = '🛡️ <span id="pending-count">0</span> 待确认';
        badge.onclick = () => this.showModal();
        document.body.appendChild(badge);

        // 创建弹窗
        const overlay = document.createElement('div');
        overlay.id = 'pending-modal-overlay';
        overlay.className = 'pending-modal-overlay';
        overlay.innerHTML = `
            <div class="pending-modal">
                <h2>🛡️ 待确认操作 <span class="pending-count" id="modal-pending-count">0</span></h2>
                <p style="font-size:12px;color:var(--text-muted);margin-bottom:12px;">
                    检测到危险操作需要确认，仅靠状态条被动展示容易忽略，弹窗主动提醒避免卡队列或自动放行
                </p>
                <div id="pending-list"></div>
                <div style="display:flex;gap:8px;margin-top:16px;justify-content:flex-end;">
                    <button class="btn-details" onclick="pendingModal.hideModal()">关闭</button>
                    <button class="btn-details" onclick="pendingModal.refresh()">刷新</button>
                </div>
            </div>
        `;
        overlay.onclick = (e) => {
            if (e.target === overlay) this.hideModal();
        };
        document.body.appendChild(overlay);
        this.modal = overlay;
    }

    async fetchPending() {
        try {
            const res = await fetch('/api/security/pending');
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            return data.pending || data.items || [];
        } catch (e) {
            console.warn('获取待确认队列失败:', e);
            return [];
        }
    }

    async refresh() {
        const pending = await this.fetchPending();
        this.pending = pending;
        this.updateBadge();
        this.renderList();
        
        // 如果有待确认且弹窗未显示，自动弹出（首次）
        if (pending.length > 0 && !this.modal.classList.contains('active')) {
            const lastAutoShow = localStorage.getItem('pending_last_autoshow');
            const now = Date.now();
            // 5分钟内只自动弹出一次，避免骚扰
            if (!lastAutoShow || now - parseInt(lastAutoShow) > 5*60*1000) {
                this.showModal();
                localStorage.setItem('pending_last_autoshow', now.toString());
            }
        }
    }

    updateBadge() {
        const badge = document.getElementById('pending-badge');
        const countEl = document.getElementById('pending-count');
        const modalCountEl = document.getElementById('modal-pending-count');
        
        if (this.pending.length > 0) {
            badge.classList.add('active');
            if (countEl) countEl.textContent = this.pending.length;
            if (modalCountEl) modalCountEl.textContent = this.pending.length;
        } else {
            badge.classList.remove('active');
            this.hideModal();
        }
    }

    renderList() {
        const listEl = document.getElementById('pending-list');
        if (!listEl) return;

        if (this.pending.length === 0) {
            listEl.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-muted);">✅ 暂无待确认操作</div>';
            return;
        }

        listEl.innerHTML = this.pending.map((item, idx) => {
            const risk = item.risk_level || item.risk || 'medium';
            const id = item.confirm_id || item.id || `pending_${idx}`;
            const tool = item.tool || item.operation || '未知操作';
            const reason = item.reason || item.description || '危险操作需确认';
            const timestamp = item.timestamp || item.created_at || Date.now()/1000;
            const timeStr = new Date(timestamp*1000).toLocaleString();
            
            return `
                <div class="pending-item ${risk}">
                    <div class="pending-item-header">
                        <strong>${tool}</strong>
                        <span class="pending-risk ${risk}">${risk.toUpperCase()}</span>
                    </div>
                    <div style="font-size:12px;margin:4px 0;">${reason}</div>
                    <div style="font-size:11px;color:var(--text-muted);">ID: ${id} | 时间: ${timeStr}</div>
                    <div style="font-size:11px;color:var(--text-muted);">参数: ${JSON.stringify(item.params || item.args || {}).slice(0,100)}</div>
                    <div class="pending-details" id="details-${id}">
                        <pre>${JSON.stringify(item, null, 2).slice(0,500)}</pre>
                    </div>
                    <div class="pending-actions">
                        <button class="btn-approve" onclick="pendingModal.approve('${id}')">✅ 批准</button>
                        <button class="btn-deny" onclick="pendingModal.deny('${id}')">❌ 拒绝</button>
                        <button class="btn-details" onclick="pendingModal.toggleDetails('${id}')">详情</button>
                    </div>
                </div>
            `;
        }).join('');
    }

    showModal() {
        if (this.modal) {
            this.modal.classList.add('active');
            this.renderList();
        }
    }

    hideModal() {
        if (this.modal) {
            this.modal.classList.remove('active');
        }
    }

    toggleDetails(id) {
        const details = document.getElementById(`details-${id}`);
        if (details) {
            details.classList.toggle('active');
        }
    }

    async approve(confirmId) {
        if (!confirm(`确定批准操作 ${confirmId}？\n危险操作需谨慎确认`)) return;
        
        try {
            const res = await fetch('/api/security/confirm', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({confirm_id: confirmId, approved: true})
            });
            const data = await res.json();
            
            if (data.success) {
                alert(`✅ 已批准: ${confirmId}`);
                this.refresh();
            } else {
                alert(`❌ 批准失败: ${data.error || '未知错误'}`);
            }
        } catch (e) {
            alert(`❌ 请求失败: ${e.message}`);
        }
    }

    async deny(confirmId) {
        if (!confirm(`确定拒绝操作 ${confirmId}？`)) return;
        
        try {
            const res = await fetch('/api/security/confirm', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({confirm_id: confirmId, approved: false})
            });
            const data = await res.json();
            
            if (data.success) {
                alert(`✅ 已拒绝: ${confirmId}`);
                this.refresh();
            } else {
                alert(`❌ 拒绝失败: ${data.error || '未知错误'}`);
            }
        } catch (e) {
            alert(`❌ 请求失败: ${e.message}`);
        }
    }

    startPolling() {
        // 立即检查一次
        this.refresh();
        
        // 每10秒轮询待确认队列
        this.checkInterval = setInterval(() => {
            if (document.hidden) return; // 页面隐藏暂停
            this.refresh();
        }, 10000);
        
        console.log('✅ 待确认队列弹窗已启动，每10秒轮询，弹窗主动提醒');
    }

    stopPolling() {
        if (this.checkInterval) {
            clearInterval(this.checkInterval);
            this.checkInterval = null;
        }
    }
}

// 全局单例
window.pendingModal = new PendingModalV0914();
console.log('✅ 待确认队列前端弹窗v0914已加载 - 主动提醒避免忽略');
