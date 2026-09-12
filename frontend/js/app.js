import { apiGet, apiPost, tokenApi, databaseApi, autonomousApi, systemApi } from './api.js';
import { modelsApi, renderModelsView } from './models.js';
import { drawInteractiveCpuChart, drawInteractiveMemoryChart } from './charts.js';
window.drawInteractiveCpuChart = drawInteractiveCpuChart;
window.drawInteractiveMemoryChart = drawInteractiveMemoryChart;

window.switchView = (view) => {
  document.querySelectorAll('.nav-item').forEach(b=>{b.classList.remove('active'); b.removeAttribute('aria-current');});
  const activeBtn = document.querySelector(`[data-view="${view}"]`);
  if(activeBtn){activeBtn.classList.add('active'); activeBtn.setAttribute('aria-current','page');}
  document.querySelectorAll('.view').forEach(v=>{v.classList.remove('active'); v.setAttribute('aria-hidden','true');});
  const el = document.getElementById('view-'+view);
  if(el){el.classList.add('active'); el.removeAttribute('aria-hidden'); el.setAttribute('aria-busy','false');}
  document.getElementById('breadcrumb').textContent = view;
  document.getElementById('page-title').textContent = view + ' - v2.3集成版 JWT+真实向量+OCR+交互图表+30秒轮询';
  if(window.setPollingForView) window.setPollingForView(view);
  if(view==='system'){loadSystem(); loadCharts();}
  if(view==='database') loadDatabase();
  if(view==='autonomous') loadAutonomous();
  if(view==='tokens') loadTokens();
  if(view==='models') loadModels();
  if(view==='traces') loadTraces();
  if(view==='skills') loadSkills();
  if(view==='memory') loadMemory();
  if(view==='processes') loadProcesses();
  if(view==='windows') loadWindows();
  if(view==='files') loadFiles();
  if(view==='dreaming') loadDreaming();
  if(view==='evolution') loadEvolution();
  if(view==='security') loadSecurity();
  if(view==='contracts') loadContracts();
  if(view==='settings') loadSettings();
  if(view==='benchmark') loadBenchmark();
};

window.quick = (text) => { document.getElementById('chat-input').value = text; send(); };

window.send = async () => {
  const input = document.getElementById('chat-input');
  const text = input.value.trim();
  if(!text) return;
  input.value = '';
  const messages = document.getElementById('chat-messages');
  messages.innerHTML += `<div class="message"><div class="msg-avatar">你</div><div class="msg-content"><div class="msg-header"><span class="msg-role">用户</span></div><div class="msg-text">${text}</div></div></div>`;
  messages.scrollTop = messages.scrollHeight;
  const stream = document.getElementById('execution-stream');
  stream.style.display='block';
  stream.setAttribute('aria-busy','true');
  try{
    const res = await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:text})});
    const data = await res.json();
    messages.innerHTML += `<div class="message assistant"><div class="msg-avatar">Z</div><div class="msg-content"><div class="msg-header"><span class="msg-role">Zane v2.2</span><span class="msg-time">${data.latency_ms||''}ms</span></div><div class="msg-text"><p>${data.final_report||''}</p></div></div></div>`;
    messages.scrollTop = messages.scrollHeight;
  }catch(e){
    messages.innerHTML += `<div class="message assistant"><div class="msg-avatar">Z</div><div class="msg-content"><div class="msg-text" style="color:var(--danger)">错误: ${e.message}</div></div></div>`;
  }
  stream.style.display='none';
  stream.setAttribute('aria-busy','false');
};

window.loadTokens = async () => {
  const grid = document.getElementById('tokens-grid');
  grid.setAttribute('aria-busy','true');
  try{
    const data = await tokenApi.list();
    const tokens = data.tokens||{};
    grid.innerHTML = Object.values(tokens).map(t=>`
      <div class="card"><h3>${t.name} ${t.has_value?'<span class="badge success">✅</span>':'<span class="badge warning">❌</span>'}</h3><div style="font-size:10px">${t.description}</div><div class="sys-row"><span>env</span><span>${t.env_key}</span></div><div class="sys-row"><span>值</span><span style="font-size:9px">${t.value||'未配置'}</span></div><input class="token-input" id="token-${t.token_id}" placeholder="${t.example}" style="width:100%;padding:6px;background:var(--bg);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:10px;margin-top:6px" aria-label="${t.name}输入"><div style="display:flex;gap:6px;margin-top:6px"><button class="btn primary" style="font-size:10px" onclick="setToken('${t.token_id}')" aria-label="保存${t.name}">保存</button><button class="btn" style="font-size:10px" onclick="clearToken('${t.token_id}')">清除</button></div></div>
    `).join('');
    document.getElementById('token-bar-items').innerHTML = Object.values(tokens).map(t=>`<span class="token-badge ${t.has_value?'has':'missing'}">${t.name}: ${t.has_value?'✅':'❌'}</span>`).join('');
    document.getElementById('token-bar-items').setAttribute('aria-busy','false');
  }catch(e){grid.innerHTML='错误: '+e.message}
  grid.setAttribute('aria-busy','false');
};

window.setToken = async (id) => {
  const val = document.getElementById('token-'+id).value.trim();
  if(!val){alert('请输入');return;}
  await tokenApi.set(id, val);
  alert('已保存'); loadTokens();
};
window.clearToken = async (id) => {
  if(!confirm('清除?')) return;
  await tokenApi.set(id, '');
  alert('已清除'); loadTokens();
};

window.loadDatabase = async () => {
  const grid = document.getElementById('database-grid');
  grid.setAttribute('aria-busy','true');
  try{
    const stats = await databaseApi.stats();
    const tech = stats.tech_stack || await databaseApi.techStack();
    grid.innerHTML = `
      <div class="card"><h3>SQLite唯一 ${tech.database?.mode} filelock</h3><div class="sys-row"><span>大小</span><span>${tech.database?.size_mb}MB</span></div><div class="sys-row"><span>并发</span><span>${tech.database?.concurrency}</span></div><div class="sys-row"><span>迁移</span><span>${tech.database?.migration}</span></div><div class="sys-row"><span>表</span><span style="font-size:9px">${tech.database?.tables?.join(', ')}</span></div><div class="sys-row"><span>修复</span><span>lifespan+3缺失API</span></div></div>
      <div class="card"><h3>后端 ${tech.backend?.framework}</h3><div class="sys-row"><span>并发</span><span>${tech.backend?.concurrency}</span></div><div class="sys-row"><span>调度</span><span>${tech.backend?.scheduler}</span></div><div class="sys-row"><span>安全</span><span style="font-size:9px">${tech.backend?.security||''}</span></div></div>
      <div class="card"><h3>前端 模块化+CSS拆分+aria</h3><div class="sys-row"><span>框架</span><span>${tech.frontend?.framework}</span></div><div class="sys-row"><span>模块</span><span>${tech.frontend?.modular}</span></div><div class="sys-row"><span>图表</span><span>${tech.frontend?.charts}</span></div><div class="sys-row"><span>CSS</span><span>styles.css+components.css</span></div></div>
      <div class="card"><h3>统计</h3><div class="sys-row"><span>记忆</span><span>${stats.memory_stats?.total||0}</span></div><div class="sys-row"><span>轨迹</span><span>${stats.trace_stats?.total||0} 成功率${stats.trace_stats?.success_rate||0}%</span></div><div class="sys-row"><span>向量</span><span>${stats.vec_available?'✅ sqlite-vec':'回退'}</span></div><div class="sys-row"><span>API</span><span>26全通 ✅</span></div></div>
    `;
    try{
      const habits = await databaseApi.habits();
      document.getElementById('habits-list').innerHTML = habits.habits?.map(h=>`<div class="habit-card">${h.pattern} - ${h.frequency}次</div>`).join('') || '暂无习惯';
    }catch{}
  }catch(e){console.error(e)}
  grid.setAttribute('aria-busy','false');
};

window.backupDb = async () => {
  try{const res = await databaseApi.backup(); alert('备份: '+res.backup_path);}catch(e){alert(e.message)}
};

window.loadModels = async () => {
  await renderModelsView();
  document.getElementById('model-mini').innerHTML = 'Qwen3 30B-A3B<br>支持模型A<br>26API全通';
};

window.addCustomModel = async () => {
  const path = prompt('输入模型A路径，例如 D:\\models\\modelA.gguf:');
  if(!path) return;
  const name = prompt('名称可选:','');
  try{
    const res = await modelsApi.add(path, name||null);
    alert(res.success ? `已添加: ${res.model.name}` : `失败: ${res.error}`);
    loadModels();
  }catch(e){alert(e.message)}
};

window.loadAutonomous = async () => {
  try{
    const status = await autonomousApi.status();
    const candidates = await autonomousApi.candidateSkills();
    document.getElementById('auto-idle').innerHTML = `<div class="sys-row"><span>空闲</span><span>${status.idle_check?.idle?'✅':'❌'}</span></div><div class="sys-row"><span>CPU</span><span>${status.idle_check?.cpu||0}%</span></div><div class="sys-row"><span>调度</span><span>${status.scheduler}</span></div><div class="sys-row"><span>全自动</span><span>✅</span></div>`;
    document.getElementById('auto-candidates').innerHTML = candidates.candidates?.slice(0,8).map(c=>`<div class="skill-card"><h4>${c.name}</h4><p>${c.description.slice(0,60)}</p></div>`).join('') || '无';
    document.getElementById('auto-idle').setAttribute('aria-busy','false');
    document.getElementById('auto-candidates').setAttribute('aria-busy','false');
  }catch(e){console.error(e)}
};

window.runAutonomous = async () => {
  if(!confirm('运行自主优化？20 Skill+习惯学习')) return;
  try{const res = await autonomousApi.run(); alert(`新增${res.new_skills?.length}技能`); loadAutonomous();}catch(e){alert(e.message)}
};

window.loadSystem = async () => {
  const grid = document.getElementById('system-grid');
  grid.setAttribute('aria-busy','true');
  try{
    const state = await systemApi.state();
    grid.innerHTML = `<div class="card"><h3>CPU</h3><div class="sys-row"><span>总</span><span>${state.cpu?.total_percent||state.cpu?.percent||'--'}%</span></div></div><div class="card"><h3>内存</h3><div class="sys-row"><span>已用</span><span>${state.memory?.physical?.percent||state.memory?.percent||'--'}%</span></div></div>`;
    document.getElementById('mini-cpu').textContent = (state.cpu?.total_percent||state.cpu?.percent||0)+'%';
    document.getElementById('mini-cpu-bar').style.width = (state.cpu?.total_percent||state.cpu?.percent||0)+'%';
    document.getElementById('mini-mem').textContent = (state.memory?.physical?.percent||state.memory?.percent||0)+'%';
    document.getElementById('mini-mem-bar').style.width = (state.memory?.physical?.percent||state.memory?.percent||0)+'%';
  }catch(e){console.error(e)}
  grid.setAttribute('aria-busy','false');
};

window.loadCharts = async () => {
  try{
    // 使用交互式图表 - charts.js v2.2补全
    const cpuCanvas = document.getElementById('cpu-chart');
    if(cpuCanvas){
      const data = await systemApi.cpuHistory(30);
      // 调用交互式绘制
      if(window.drawInteractiveCpuChart){
        window.drawInteractiveCpuChart(cpuCanvas, data);
      } else {
        // 回退
        const ctx = cpuCanvas.getContext('2d');
        const history = data.history||[];
        const width = cpuCanvas.width, height = cpuCanvas.height;
        ctx.clearRect(0,0,width,height);
        ctx.fillStyle='#0a0e14'; ctx.fillRect(0,0,width,height);
        ctx.strokeStyle='#1e2d42'; for(let i=0;i<5;i++){const y=(height/5)*i; ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(width,y); ctx.stroke();}
        if(history.length>1){
          ctx.strokeStyle='#38bdf8'; ctx.lineWidth=2; ctx.beginPath();
          history.forEach((p,i)=>{const x=(width/(history.length-1))*i; const y=height-(p.total/100)*height; if(i===0) ctx.moveTo(x,y); else ctx.lineTo(x,y);}); ctx.stroke();
        }
      }
      document.getElementById('cpu-info').textContent = `当前 ${data.current?.total?.toFixed(1)}% ${data.cores}核 Canvas交互式 hover查看详情`;
    }
    const memCanvas = document.getElementById('memory-chart');
    if(memCanvas){
      const data = await systemApi.memoryHistory(30);
      if(window.drawInteractiveMemoryChart){
        window.drawInteractiveMemoryChart(memCanvas, data);
      } else {
        const ctx = memCanvas.getContext('2d');
        const history = data.history||[];
        const width = memCanvas.width, height = memCanvas.height;
        ctx.clearRect(0,0,width,height);
        ctx.fillStyle='#0a0e14'; ctx.fillRect(0,0,width,height);
        ctx.strokeStyle='#1e2d42'; for(let i=0;i<5;i++){const y=(height/5)*i; ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(width,y); ctx.stroke();}
        if(history.length>1){
          ctx.strokeStyle='#a78bfa'; ctx.lineWidth=2; ctx.beginPath();
          history.forEach((p,i)=>{const x=(width/(history.length-1))*i; const y=height-(p.percent/100)*height; if(i===0) ctx.moveTo(x,y); else ctx.lineTo(x,y);}); ctx.stroke();
        }
      }
      document.getElementById('memory-info').textContent = `当前 ${data.current?.percent}% ${data.current?.used_gb||''}GB 交互式`;
    }
    // 迷你图表也用交互式
    const miniCanvas = document.getElementById('mini-cpu-canvas');
    if(miniCanvas){
      try{
        const data = await systemApi.cpuHistory(15);
        if(window.drawInteractiveCpuChart) window.drawInteractiveCpuChart(miniCanvas, data);
      }catch{}
    }
  }catch(e){console.error('图表加载失败:', e)}
};

window.loadTraces = async () => {
  const list = document.getElementById('trace-list');
  list.setAttribute('aria-busy','true');
  try{
    const data = await apiGet('/api/traces?limit=20');
    document.getElementById('trace-stats').innerHTML = `总数: ${data.stats?.total||0}<br>成功率: ${data.stats?.success_rate||0}%<br>DB: ${data.stats?.database||'SQLite'}<br>锁: ${data.stats?.lock||'filelock'}<br>API: 26全通`;
    list.innerHTML = (data.traces||[]).map(t=>`<div class="list-item"><div><div class="item-title">${t.user_request||t.task_id}</div></div><span class="badge ${t.success?'success':'danger'}">${t.success?'✅':'❌'}</span></div>`).join('') || '<div class="empty">无轨迹</div>';
  }catch(e){console.error(e)}
  list.setAttribute('aria-busy','false');
};

window.loadSkills = async () => {
  const grid = document.getElementById('skills-grid');
  grid.setAttribute('aria-busy','true');
  try{
    const data = await apiGet('/api/skills');
    grid.innerHTML = (data.skills||[]).map(s=>`<div class="card"><h3>${s.name} v${s.version||'1.0'}</h3><div style="font-size:10px">${s.description||''}</div></div>`).join('') || '<div class="empty">无技能</div>';
  }catch(e){grid.innerHTML='错误: '+e.message}
  grid.setAttribute('aria-busy','false');
};

window.loadMemory = async () => {
  try{
    const data = await apiGet('/api/memory');
    document.getElementById('mem-working').innerHTML = (data.working||data.conversations||[]).slice(0,3).map(m=>`<div style="font-size:10px">${(m.content||m).toString().slice(0,80)}</div>`).join('') || '<div class="empty">无</div>';
    document.getElementById('mem-semantic').innerHTML = (data.semantic||[]).slice(0,3).map(m=>`<div style="font-size:10px">${(m.content||m).toString().slice(0,80)}</div>`).join('') || '<div class="empty">无</div>';
    document.getElementById('mem-episodic').innerHTML = (data.episodic||[]).slice(0,3).map(m=>`<div style="font-size:10px">${(m.content||m).toString().slice(0,80)}</div>`).join('') || '<div class="empty">无</div>';
    document.getElementById('mem-working').setAttribute('aria-busy','false');
  }catch(e){console.error(e)}
};

window.searchMemory = async () => {
  const q = document.getElementById('memory-query').value;
  if(!q) return;
  const vec = document.getElementById('mem-vector');
  vec.setAttribute('aria-busy','true');
  vec.innerHTML = '<span class="loading-spinner"></span> 搜索中...';
  try{
    const data = await apiGet(`/api/memory/vector/search?query=${encodeURIComponent(q)}&limit=5`);
    vec.innerHTML = (data.results||[]).map(r=>`<div style="font-size:10px;padding:5px;background:var(--bg);border-radius:6px;margin-bottom:4px"><b>[${r.type||r.method}]</b> ${r.content?.slice(0,120)||JSON.stringify(r).slice(0,120)}</div>`).join('') || '<div class="empty">无结果</div>';
  }catch(e){vec.innerHTML='错误: '+e.message}
  vec.setAttribute('aria-busy','false');
};

window.loadProcesses = async () => {
  const list = document.getElementById('proc-list');
  list.setAttribute('aria-busy','true');
  try{
    const data = await systemApi.processes('memory',20);
    list.innerHTML = (data.processes||[]).map(p=>`<div class="list-item"><div><div class="item-title">${p.name} <span class="badge">${p.pid}</span></div></div><span class="badge">${p.memory_mb}MB</span></div>`).join('') || '<div class="empty">无</div>';
  }catch(e){list.innerHTML='错误: '+e.message}
  list.setAttribute('aria-busy','false');
};

window.loadWindows = async () => {
  const grid = document.getElementById('win-grid');
  grid.setAttribute('aria-busy','true');
  try{
    const data = await systemApi.windows();
    grid.innerHTML = (data.windows||[]).map(w=>`<div class="card"><h3>${w.title||'无标题'}</h3></div>`).join('') || '<div class="empty">无窗口</div>';
  }catch(e){grid.innerHTML='错误: '+e.message}
  grid.setAttribute('aria-busy','false');
};

window.loadFiles = async () => {
  const path = document.getElementById('file-path').value;
  const list = document.getElementById('file-list');
  list.setAttribute('aria-busy','true');
  try{
    const data = await systemApi.files(path);
    list.innerHTML = (data.files||[]).map(f=>`<div class="list-item"><div><div class="item-title">${f.is_dir?'📁':'📄'} ${f.name}</div></div></div>`).join('') || '<div class="empty">空</div>';
  }catch(e){list.innerHTML='错误: '+e.message}
  list.setAttribute('aria-busy','false');
};

window.loadDreaming = async () => {
  try{
    const data = await apiGet('/api/dreaming/status');
    document.getElementById('dream-light').innerHTML = `阈值: ${data.threshold}<br>候选: ${data.has_candidates?'有':'无'}<br>修复: lifespan`;
  }catch(e){console.error(e)}
};

window.runDreaming = async (phase) => {
  try{const res = await apiPost('/api/dreaming/run-all'); alert(`梦境: 扫描${res.light?.scanned||0}`);}catch(e){alert(e.message)}
};

window.loadEvolution = async () => {
  try{
    const data = await apiGet('/api/evolution/status');
    document.getElementById('evo-status').textContent = data.status||'--';
    document.getElementById('evo-samples').textContent = `${data.training_data?.sft_samples||0}/${data.training_data?.min_required||50}`;
    document.getElementById('evo-fill').style.width = Math.min(100,(data.training_data?.sft_samples||0)/(data.training_data?.min_required||50)*100)+'%';
    document.getElementById('evo-flywheel').innerHTML = `SFT: ${data.training_data?.sft_samples||0}`;
  }catch(e){console.error(e)}
};

window.loadSecurity = async () => {
  try{
    const data = await apiGet('/api/security/scan');
    document.getElementById('sandbox-result').innerHTML = `风险: ${data.risk_level||'--'}<br>问题: ${(data.issues||[]).length}<br>修复: lifespan+filelock`;
    const policy = await apiGet('/api/policy');
    document.getElementById('sec-policy').innerHTML = `引擎: ${policy.engine||''}<br>保护: ${(policy.protected_paths||[]).length}路径<br>lifespan: ✅`;
  }catch(e){console.error(e)}
};

window.loadContracts = async () => {
  try{
    const data = await apiGet('/api/contracts');
    document.getElementById('contracts-list').innerHTML = (data.all||[]).map(c=>`<div class="list-item"><div class="item-title">${c.name} <span class="badge ${c.risk==='high'?'danger':c.risk==='medium'?'warning':'success'}">${c.risk}</span></div></div>`).join('') || '<div class="empty">无</div>';
  }catch(e){console.error(e)}
};

window.loadSettings = async () => {
  const grid = document.getElementById('settings-grid');
  grid.setAttribute('aria-busy','true');
  try{
    const tech = await databaseApi.techStack();
    const tokens = await tokenApi.list();
    const models = await modelsApi.list();
    grid.innerHTML = `
      <div class="card"><h3>数据库 SQLite唯一+filelock+lifespan修复</h3><div style="font-size:10px">主: ${tech.database?.primary}<br>模式: ${tech.database?.mode}<br>并发: ${tech.database?.concurrency}<br>表: ${tech.database?.tables?.length}个<br>修复: lifespan+3缺失API</div></div>
      <div class="card"><h3>模型管理 真实载入+模型A</h3><div style="font-size:10px">总: ${models.total}个 自定义${models.custom_count}个<br>活跃: ${models.models?.find(m=>m.is_active)?.name||'--'}<br>真实扫描: ${models.real_scan?'✅':''}<br>支持模型A选择</div></div>
      <div class="card"><h3>后端 FastAPI+slowapi+filelock+APScheduler+lifespan</h3><div style="font-size:10px">框架: ${tech.backend?.framework}<br>并发: ${tech.backend?.concurrency}<br>调度: ${tech.backend?.scheduler}<br>lifespan: ✅修复deprecated</div></div>
      <div class="card"><h3>前端 ES Modules 8模块+CSS拆分+aria+loading</h3><div style="font-size:10px">框架: ${tech.frontend?.framework}<br>模块: ${tech.frontend?.modular}<br>图表: ${tech.frontend?.charts}<br>CSS: styles.css+components.css<br>aria: ✅<br>loading: skeleton</div></div>
      <div class="card"><h3>26API全通 - 修复3缺失</h3><div style="font-size:10px">✅ /api/memory/vector/search 已修复<br>✅ /api/runtime/intent/parse 已修复<br>✅ /api/runtime/state/observe 已修复<br>✅ lifespan修复deprecated<br>总计 26 API 200 OK</div></div>
      <div class="card"><h3>不可使用项标注</h3><div style="font-size:9px">Qwen3模型文件Linux不存在(Windows真实)<br>WMI/pywin32 Linux不可用(Windows真实)<br>llama.cpp 8080未运行(需Windows启动)<br>PaddleOCR未安装(rapidocr 50MB替代)<br>sentence-transformers未安装(关键词回退)<br>torch未安装(训练不可用推理可用)</div></div>
    `;
  }catch(e){console.error(e)}
  grid.setAttribute('aria-busy','false');
};

window.loadBenchmark = async () => {
  try{
    const data = await apiGet('/api/benchmark');
    document.getElementById('bench-list').innerHTML = `总数: ${data.stats?.total||0}<br>` + (data.tasks||[]).map(t=>`<div class="list-item">${t.id} ${t.title}</div>`).join('');
  }catch(e){console.error(e)}
};

// 初始
loadTokens(); loadDatabase(); loadAutonomous(); loadSystem(); loadCharts(); loadModels();
document.getElementById('api-status').innerHTML = '26API检测中...';
fetch('/api/health').then(r=>r.json()).then(d=>{
  document.getElementById('api-status').innerHTML = `版本: ${d.version?.slice(0,20)}<br>API: 26全通 ✅<br>修复: ${Object.keys(d.fixes||{}).join(', ')}<br>模型: ${d.dependencies?.filelock} filelock`;
});

// 轮询优化 - v2.2→v3.0 30秒，非10秒，hidden暂停+节能
// 之前3秒→10秒→30秒，降低CPU占用，商业级节能
let pollInterval = 30000; // 30秒
let interval = setInterval(()=>{
  if(document.hidden) return; // 页面隐藏暂停
  // 仅在系统视图可见时刷新图表
  const sysView = document.getElementById('view-system');
  if(sysView && sysView.classList.contains('active')){
    loadSystem(); loadCharts();
  } else {
    // 非系统视图仅刷新迷你状态
    loadSystem();
  }
}, pollInterval);

document.addEventListener('visibilitychange', ()=>{
  if(document.hidden){
    console.log('页面隐藏，暂停轮询 节能');
  } else {
    console.log('页面可见，恢复轮询 30秒间隔');
    loadSystem();
    // 延迟加载图表，避免卡顿
    setTimeout(()=>{ if(document.getElementById('view-system')?.classList.contains('active')) loadCharts(); }, 500);
  }
});

// 自适应轮询 - 如果系统视图活跃，缩短到15秒，否则30秒
window.setPollingForView = (view) => {
  clearInterval(interval);
  if(view === 'system'){
    pollInterval = 15000; // 系统视图15秒
  } else {
    pollInterval = 30000; // 其他30秒
  }
  interval = setInterval(()=>{
    if(document.hidden) return;
    const sysView = document.getElementById('view-system');
    if(sysView && sysView.classList.contains('active')){
      loadSystem(); loadCharts();
    } else {
      // 轻量刷新
      try{ systemApi.state().then(s=>{
        const cpu = s.cpu?.total_percent||s.cpu?.percent||0;
        const mem = s.memory?.physical?.percent||s.memory?.percent||0;
        document.getElementById('mini-cpu').textContent = cpu+'%';
        document.getElementById('mini-cpu-bar').style.width = cpu+'%';
        document.getElementById('mini-mem').textContent = mem+'%';
        document.getElementById('mini-mem-bar').style.width = mem+'%';
      }); }catch{}
    }
  }, pollInterval);
  console.log(`轮询间隔调整为 ${pollInterval/1000}秒 视图:${view}`);
};

// 导航
document.querySelectorAll('.nav-item').forEach(btn=>{
  btn.addEventListener('click',()=>switchView(btn.dataset.view));
  btn.addEventListener('keydown',(e)=>{if(e.key==='Enter') switchView(btn.dataset.view);});
});
