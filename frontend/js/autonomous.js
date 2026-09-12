// autonomous.js - 20 Skill + APScheduler + 习惯学习 - C扩展全自动
import { autonomousApi } from './api.js';

export async function renderAutonomousView() {
    const container = document.getElementById('autonomous-view');
    if (!container) return;
    try {
        const status = await autonomousApi.status();
        const candidates = await autonomousApi.candidateSkills();
        
        let html = `
        <div class="autonomous-status">
            <h3>自主优化状态 - C扩展全自动</h3>
            <div>空闲: ${status.idle_check?.idle ? '✅' : '❌'} ${status.idle_check?.reason}</div>
            <div>候选Skill: ${status.total_candidates || status.candidate_skills}个 (原7+新增13=20)</div>
            <div>报告: ${status.reports}个</div>
            <div>习惯: ${status.habits_count}个 (C扩展)</div>
            <div>技能总数: ${status.skills_total}</div>
            <div>调度器: ${status.scheduler} | 运行中: ${status.scheduler_running ? '✅' : '❌'}</div>
            <div>全自动: ${status.full_auto ? '✅默认开启' : '❌'}</div>
        </div>
        
        <div class="autonomous-actions">
            <button onclick="window.runAutonomous()" class="btn-primary">运行自主优化</button>
            <button onclick="window.learnHabits()" class="btn">习惯学习</button>
            <button onclick="window.startScheduler()" class="btn">启动定时(凌晨2点)</button>
            <button onclick="window.stopScheduler()" class="btn">停止定时</button>
            <button onclick="window.queryOpenSource()" class="btn">查询开源</button>
        </div>
        
        <div class="candidate-skills">
            <h3>20候选Skill (A+C扩展)</h3>
            <div class="skills-grid">
                ${candidates.candidates?.map(c => `
                <div class="skill-card">
                    <h4>${c.name}</h4>
                    <p>${c.description}</p>
                    <div class="meta">来源:${c.source} | 分类:${c.category} | 优先级:${c.priority}</div>
                    <div>触发: ${c.trigger?.join(', ')}</div>
                </div>`).join('') || '加载中...'}
            </div>
        </div>
        
        <div class="habits-section">
            <h3>习惯学习 (C扩展默认开启)</h3>
            <div>${status.habits?.map(h => `<div class="habit-card">${h.pattern} - 频率${h.frequency} - ${h.suggested_skill} - ${new Date(h.last_seen*1000).toLocaleString()}</div>`).join('') || '暂无习惯'}</div>
        </div>
        
        <div class="latest-report">
            <h3>最新报告</h3>
            <pre>${JSON.stringify(status.latest_report, null, 2) || '无'}</pre>
        </div>
        `;
        
        container.innerHTML = html;
    } catch (e) {
        container.innerHTML = `加载失败: ${e.message}`;
    }
}

window.runAutonomous = async () => {
    if (!confirm('运行自主优化？将查询开源+分析失败+习惯学习+生成Skill+梦境')) return;
    try {
        const btn = event.target;
        btn.textContent = '运行中...';
        btn.disabled = true;
        const res = await autonomousApi.run();
        alert(`完成: 新增${res.new_skills?.length}技能，习惯${res.habits?.length}个，耗时${res.duration}s`);
        renderAutonomousView();
    } catch (e) {
        alert(`失败: ${e.message}`);
    }
};

window.learnHabits = async () => {
    try {
        const res = await autonomousApi.learnHabits();
        alert(`习惯学习: 发现${res.count}个模式，个性化Skill: ${res.personalized_skills?.join(', ')}`);
        renderAutonomousView();
    } catch (e) {
        alert(`失败: ${e.message}`);
    }
};

window.startScheduler = async () => {
    try {
        const res = await autonomousApi.startScheduler();
        alert(res.success ? '调度器已启动：凌晨2点+每30分钟' : `失败: ${res.error}`);
        renderAutonomousView();
    } catch (e) {
        alert(`失败: ${e.message}`);
    }
};

window.stopScheduler = async () => {
    try {
        const res = await autonomousApi.stopScheduler();
        alert(res.success ? '调度器已停止' : `失败: ${res.error}`);
        renderAutonomousView();
    } catch (e) {
        alert(`失败: ${e.message}`);
    }
};

window.queryOpenSource = async () => {
    try {
        const res = await autonomousApi.queryOpenSource();
        alert(`查询完成: ${res.github_repos?.length}个仓库，${res.search_results?.length}条搜索`);
    } catch (e) {
        alert(`失败: ${e.message}`);
    }
};
