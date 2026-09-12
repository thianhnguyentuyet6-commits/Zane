// charts.js - Canvas图表交互优化 - 补全
// 无外部依赖，原生Canvas，支持hover tooltip

export function drawInteractiveCpuChart(canvas, data) {
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    const history = data.history || [];
    
    if (history.length < 2) return;
    
    // 清空
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = '#0a0e14';
    ctx.fillRect(0, 0, width, height);
    
    // 网格
    ctx.strokeStyle = '#1e2d42';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
        const y = (height / 4) * i;
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
        // Y轴标签
        ctx.fillStyle = '#5a6d8a';
        ctx.font = '9px monospace';
        ctx.fillText(`${100 - i*25}%`, 2, y - 2);
    }
    
    // 总CPU线
    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 2;
    ctx.beginPath();
    history.forEach((p, i) => {
        const x = (width / (history.length - 1)) * i;
        const y = height - (p.total / 100) * height;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    ctx.stroke();
    
    // 填充
    ctx.fillStyle = 'rgba(56, 189, 248, 0.1)';
    ctx.beginPath();
    history.forEach((p, i) => {
        const x = (width / (history.length - 1)) * i;
        const y = height - (p.total / 100) * height;
        if (i === 0) ctx.moveTo(x, height);
        ctx.lineTo(x, y);
    });
    ctx.lineTo(width, height);
    ctx.closePath();
    ctx.fill();
    
    // 每核心
    if (history[0].per_core) {
        const coreCount = history[0].per_core.length;
        for (let core = 0; core < Math.min(coreCount, 4); core++) {
            ctx.strokeStyle = `hsla(${200 + core * 30}, 70%, 60%, 0.3)`;
            ctx.lineWidth = 1;
            ctx.setLineDash([3, 3]);
            ctx.beginPath();
            history.forEach((p, i) => {
                const x = (width / (history.length - 1)) * i;
                const y = height - (p.per_core[core] / 100) * height;
                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            });
            ctx.stroke();
            ctx.setLineDash([]);
        }
    }
    
    // 标题
    ctx.fillStyle = '#e2e8f0';
    ctx.font = 'bold 11px monospace';
    ctx.fillText(`CPU 总:${data.current?.total?.toFixed(1)}% 核心:${data.cores}  Canvas原生`, 10, 16);
    
    // 交互 - hover tooltip
    canvas.onmousemove = (e) => {
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const index = Math.round((x / width) * (history.length - 1));
        if (index >= 0 && index < history.length) {
            const point = history[index];
            // 显示tooltip
            canvas.title = `时间: ${new Date(point.time * 1000).toLocaleTimeString()} 总: ${point.total.toFixed(1)}% 每核心: ${point.per_core?.map(c=>c.toFixed(1)+'%').join(' ')||''}`;
        }
    };
}

export function drawInteractiveMemoryChart(canvas, data) {
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    const history = data.history || [];
    
    if (history.length < 2) return;
    
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = '#0a0e14';
    ctx.fillRect(0, 0, width, height);
    
    ctx.strokeStyle = '#1e2d42';
    for (let i = 0; i <= 4; i++) {
        const y = (height / 4) * i;
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
        ctx.fillStyle = '#5a6d8a';
        ctx.font = '9px monospace';
        ctx.fillText(`${100 - i*25}%`, 2, y - 2);
    }
    
    // 内存线
    ctx.strokeStyle = '#a78bfa';
    ctx.lineWidth = 2;
    ctx.beginPath();
    history.forEach((p, i) => {
        const x = (width / (history.length - 1)) * i;
        const y = height - (p.percent / 100) * height;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    ctx.stroke();
    
    ctx.fillStyle = 'rgba(167, 139, 250, 0.1)';
    ctx.beginPath();
    history.forEach((p, i) => {
        const x = (width / (history.length - 1)) * i;
        const y = height - (p.percent / 100) * height;
        if (i === 0) ctx.moveTo(x, height);
        ctx.lineTo(x, y);
    });
    ctx.lineTo(width, height);
    ctx.closePath();
    ctx.fill();
    
    ctx.fillStyle = '#e2e8f0';
    ctx.font = 'bold 11px monospace';
    ctx.fillText(`内存 ${data.current?.percent}% ${data.current?.used_gb}GB/${data.current?.total_gb}GB`, 10, 16);
    
    canvas.onmousemove = (e) => {
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const index = Math.round((x / width) * (history.length - 1));
        if (index >= 0 && index < history.length) {
            const point = history[index];
            canvas.title = `时间: ${new Date(point.time * 1000).toLocaleTimeString()} 内存: ${point.percent.toFixed(1)}% ${point.used_gb}GB`;
        }
    };
}
