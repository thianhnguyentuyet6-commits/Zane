// database.js - SQLite唯一 + filelock + 技术栈 + 习惯学习 - A+C夯实
import { databaseApi } from './api.js';

export async function renderDatabaseView() {
    const container = document.getElementById('database-view');
    if (!container) return;
    try {
        const stats = await databaseApi.stats();
        const tech = stats.tech_stack || await databaseApi.techStack();
        
        let html = `
        <div class="db-stats">
            <div class="stat-card"><h4>SQLite主</h4><p>${tech.database?.primary} ${tech.database?.mode}</p><p>${tech.database?.size_mb} MB</p></div>
            <div class="stat-card"><h4>并发</h4><p>${tech.database?.concurrency}</p><p>filelock + WAL</p></div>
            <div class="stat-card"><h4>向量</h4><p>${tech.database?.vector}</p><p>${stats.vec_available ? '✅可用' : '⚠️回退'}</p></div>
            <div class="stat-card"><h4>表</h4><p>${tech.database?.tables?.length || 6}个</p><p>${tech.database?.tables?.join(', ')}</p></div>
            <div class="stat-card"><h4>记忆</h4><p>总数 ${stats.memory_stats?.total || 0}</p><p>${JSON.stringify(stats.memory_stats?.by_type || {})}</p></div>
            <div class="stat-card"><h4>轨迹</h4><p>总数 ${stats.trace_stats?.total || 0} 成功率 ${stats.trace_stats?.success_rate || 0}%</p></div>
        </div>
        
        <div class="tech-stack">
            <h3>技术栈 - A夯实 SQLite唯一</h3>
            <div class="stack-grid">
                <div><b>数据库:</b> ${tech.database?.primary} ${tech.database?.mode} | ${tech.database?.migration} | ${tech.database?.why}</div>
                <div><b>后端:</b> ${tech.backend?.framework} | ${tech.backend?.concurrency} | ${tech.backend?.scheduler} | ${tech.backend?.security}</div>
                <div><b>前端:</b> ${tech.frontend?.framework} | ${tech.frontend?.modular} | ${tech.frontend?.charts}</div>
                <div><b>部署:</b> ${tech.deployment?.port} | ${tech.deployment?.command}</div>
            </div>
        </div>
        
        <div class="db-actions">
            <button onclick="window.backupDb()" class="btn">备份数据库</button>
            <button onclick="window.searchMemories()" class="btn">搜索记忆</button>
            <button onclick="window.loadHabits()" class="btn">习惯学习</button>
        </div>
        
        <div id="habits-list"></div>
        `;
        
        container.innerHTML = html;
        
        // 习惯学习
        try {
            const habits = await databaseApi.habits();
            if (habits.habits?.length) {
                document.getElementById('habits-list').innerHTML = `
                <h3>习惯学习 (C扩展)</h3>
                <div>${habits.habits.map(h => `<div class="habit-card">${h.pattern} - 频率${h.frequency} - ${h.suggested_skill}</div>`).join('')}</div>`;
            }
        } catch {}
        
    } catch (e) {
        container.innerHTML = `加载失败: ${e.message}`;
    }
}

window.backupDb = async () => {
    try {
        const res = await databaseApi.backup();
        alert(`备份成功: ${res.backup_path}`);
    } catch (e) {
        alert(`备份失败: ${e.message}`);
    }
};

window.searchMemories = async () => {
    const query = prompt('搜索记忆关键词:');
    if (!query) return;
    try {
        const res = await databaseApi.searchMemories(query);
        alert(`找到${res.count}条: ${JSON.stringify(res.results.map(r=>r.content.slice(0,50)), null, 2)}`);
    } catch (e) {
        alert(`搜索失败: ${e.message}`);
    }
};

window.loadHabits = async () => {
    try {
        const res = await databaseApi.habits();
        alert(`习惯${res.count}条: ${JSON.stringify(res.habits, null, 2)}`);
    } catch (e) {
        alert(`加载失败: ${e.message}`);
    }
};
