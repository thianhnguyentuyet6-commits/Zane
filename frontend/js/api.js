// api.js - A夯实 前端拆分 - API封装模块
// 技术诚实：原生Fetch，无外部依赖，支持filelock后端

export const API_BASE = '';

export async function apiGet(path) {
    const res = await fetch(`${API_BASE}${path}`);
    if (!res.ok) throw new Error(`${path} ${res.status}`);
    return res.json();
}

export async function apiPost(path, body = {}) {
    const res = await fetch(`${API_BASE}${path}`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body)
    });
    if (!res.ok) throw new Error(`${path} ${res.status}`);
    return res.json();
}

// Token管理
export const tokenApi = {
    list: () => apiGet('/api/tokens'),
    get: (id) => apiGet(`/api/tokens/${id}`),
    set: (id, value) => apiPost(`/api/tokens/${id}?value=${encodeURIComponent(value)}`),
    realSearchConfig: () => apiGet('/api/tokens/real-search/config')
};

// 数据库
export const databaseApi = {
    stats: () => apiGet('/api/database/stats'),
    techStack: () => apiGet('/api/database/tech-stack'),
    searchMemories: (query, limit=5) => apiGet(`/api/database/memories/search?query=${encodeURIComponent(query)}&limit=${limit}`),
    habits: (limit=10) => apiGet(`/api/database/habits?limit=${limit}`),
    backup: () => apiPost('/api/database/backup')
};

// 自主优化
export const autonomousApi = {
    status: () => apiGet('/api/autonomous/status'),
    run: () => apiPost('/api/autonomous/run'),
    candidateSkills: () => apiGet('/api/autonomous/candidate-skills'),
    learnHabits: () => apiGet('/api/autonomous/habits/learn'),
    startScheduler: () => apiPost('/api/autonomous/scheduler/start'),
    stopScheduler: () => apiPost('/api/autonomous/scheduler/stop'),
    queryOpenSource: () => apiPost('/api/autonomous/query-open-source')
};

// 系统
export const systemApi = {
    state: () => apiGet('/api/system/state'),
    processes: (sort='memory', limit=20) => apiGet(`/api/system/processes?sort_by=${sort}&limit=${limit}`),
    windows: () => apiGet('/api/system/windows'),
    files: (path) => apiGet(`/api/system/files?path=${encodeURIComponent(path)}`),
    cpuHistory: (points=20) => apiGet(`/api/system/charts/cpu-history?points=${points}`),
    memoryHistory: (points=20) => apiGet(`/api/system/charts/memory-history?points=${points}`)
};

// 搜索
export const searchApi = {
    real: (query, count=5) => apiGet(`/api/search/real?query=${encodeURIComponent(query)}&count=${count}`)
};

// Chat
export const chatApi = {
    send: (message, history=[]) => apiPost('/api/chat', {message, history})
};
