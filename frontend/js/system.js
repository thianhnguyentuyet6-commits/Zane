// system.js - A夯实 系统状态+Canvas图表模块
import { systemApi } from './api.js';

export function initSystemCharts() {
    console.log('系统图表模块初始化 - Canvas原生');
}

export async function renderCpuChart(canvasId, points=20) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const data = await systemApi.cpuHistory(points);
    const history = data.history || [];
    
    // Canvas绘制
    const width = canvas.width;
    const height = canvas.height;
    ctx.clearRect(0, 0, width, height);
    
    // 背景
    ctx.fillStyle = '#0a0e14';
    ctx.fillRect(0, 0, width, height);
    
    // 网格
    ctx.strokeStyle = '#1e2d42';
    ctx.lineWidth = 1;
    for (let i=0; i<5; i++) {
        const y = (height / 5) * i;
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
    }
    
    if (history.length < 2) return;
    
    // 绘制总CPU
    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 2;
    ctx.beginPath();
    history.forEach((p, i) => {
        const x = (width / (history.length-1)) * i;
        const y = height - (p.total / 100) * height;
        if (i===0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    ctx.stroke();
    
    // 绘制每核心（半透明）
    if (history[0].per_core) {
        const coreCount = history[0].per_core.length;
        for (let core=0; core<Math.min(coreCount, 4); core++) {
            ctx.strokeStyle = `hsla(${200 + core*30}, 70%, 60%, 0.4)`;
            ctx.lineWidth = 1;
            ctx.beginPath();
            history.forEach((p, i) => {
                const x = (width / (history.length-1)) * i;
                const y = height - (p.per_core[core] / 100) * height;
                if (i===0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            });
            ctx.stroke();
        }
    }
    
    // 标题
    ctx.fillStyle = '#e2e8f0';
    ctx.font = '12px monospace';
    ctx.fillText(`CPU 总: ${data.current?.total?.toFixed(1)}% 核心:${data.cores}`, 10, 20);
}

export async function renderMemoryChart(canvasId, points=20) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const data = await systemApi.memoryHistory(points);
    const history = data.history || [];
    
    const width = canvas.width;
    const height = canvas.height;
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = '#0a0e14';
    ctx.fillRect(0, 0, width, height);
    
    ctx.strokeStyle = '#1e2d42';
    for (let i=0; i<5; i++) {
        const y = (height / 5) * i;
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
    }
    
    if (history.length < 2) return;
    
    ctx.strokeStyle = '#a78bfa';
    ctx.lineWidth = 2;
    ctx.beginPath();
    history.forEach((p, i) => {
        const x = (width / (history.length-1)) * i;
        const y = height - (p.percent / 100) * height;
        if (i===0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    ctx.stroke();
    
    ctx.fillStyle = '#e2e8f0';
    ctx.font = '12px monospace';
    ctx.fillText(`内存: ${data.current?.percent}% ${data.current?.used_gb}GB/${data.current?.total_gb}GB`, 10, 20);
}

export async function loadSystemState() {
    try {
        const state = await systemApi.state();
        return state;
    } catch (e) {
        console.error('系统状态加载失败', e);
        return null;
    }
}
