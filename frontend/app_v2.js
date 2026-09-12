/* Zane AGI v2.0 - 前端逻辑 - 商业级 + 自我进化 */
const API_BASE = window.location.origin;
let currentView = 'chat';
let chatHistory = [];

document.addEventListener('DOMContentLoaded', () => {
  initNav();
  initChatInput();
  loadTools();
  loadTasks();
  loadSystemState();
  loadPolicy();
  loadEvolution();
  loadModels();
  setInterval(updateMiniResources, 3000);
  setInterval(loadEvolution, 10000);
  updateMiniResources();
});

function initNav(){
  document.querySelectorAll('.nav-item').forEach(btn=>{
    btn.addEventListener('click', ()=>{
      const view = btn.dataset.view;
      switchView(view);
    });
  });
}

function switchView(view){
  currentView = view;
  document.querySelectorAll('.nav-item').forEach(b=>b.classList.remove('active'));
  document.querySelector(`[data-view="${view}"]`)?.classList.add('active');
  document.querySelectorAll('.view').forEach(v=>v.classList.remove('active'));
  document.getElementById(`view-${view}`)?.classList.add('active');
  
  const titles = {
    chat:'对话 / Zane AGI',
    evolution:'自我进化 / 从Qwen3到你的模型',
    tasks:'任务 / 撤销栈',
    system:'电脑状态 / WMI真实数据',
    models:'模型管理 / Qwen3-30B-A3B',
    files:'文件 / 真实文件系统',
    processes:'进程 / 真实进程树',
    windows:'窗口 / HWND真实',
    vision:'视觉 / 真实截图',
    memory:'记忆 / 长期记忆',
    skills:'技能 / 可复用',
    experience:'经验 / 学习管道',
    settings:'设置 / Zane AGI v2.0'
  };
  document.getElementById('breadcrumb').textContent = titles[view] || view;
  document.getElementById('page-title').textContent = {
    chat:'Zane AGI - 你的专属模型正在进化',
    evolution:'自我进化 - 从 Qwen3 到你的模型',
    tasks:'任务历史 + 撤销栈',
    system:'WMI真实系统状态 - Windows深度控制',
    models:'模型管理 - Qwen3-30B-A3B MoE',
    files:'文件浏览器 - 真实',
    processes:'进程管理器 - 真实树',
    windows:'窗口管理器 - 真实HWND',
    vision:'视觉感知 - 真实截图',
    memory:'记忆层',
    skills:'技能库',
    experience:'经验学习',
    settings:'系统设置 - Zane AGI v2.0'
  }[view] || view;

  if(view==='files') loadFiles();
  if(view==='processes') loadProcesses();
  if(view==='windows') loadWindows();
  if(view==='memory') loadMemory('semantic');
  if(view==='skills') loadSkills();
  if(view==='experience') loadExperiences();
  if(view==='system') loadSystemState();
  if(view==='evolution') loadEvolution();
  if(view==='models') loadModels();
}

function initChatInput(){
  const input = document.getElementById('chat-input');
  input.addEventListener('keydown', (e)=>{
    if(e.key==='Enter' && !e.shiftKey){
      e.preventDefault();
      sendMessage();
    }
  });
}

function quickInput(text){
  document.getElementById('chat-input').value = text;
  sendMessage();
}

async function sendMessage(){
  const input = document.getElementById('chat-input');
  const text = input.value.trim();
  if(!text) return;
  
  input.value = '';
  addMessage('user', text);
  chatHistory.push({role:'user', content:text});
  
  const stream = document.getElementById('execution-stream');
  const stepsContainer = document.getElementById('stream-steps');
  stream.style.display = 'block';
  stepsContainer.innerHTML = '<div class="step-card"><div class="step-header"><span class="step-type reasoning">推理中</span><span class="step-title">Zane 正在理解任务并检索记忆...</span><span class="pulse"></span></div></div>';
  
  const messagesEl = document.getElementById('chat-messages');
  messagesEl.scrollTop = messagesEl.scrollHeight;
  
  try{
    const res = await fetch(`${API_BASE}/api/chat`, {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({message:text, history:chatHistory.slice(-6)})
    });
    const data = await res.json();
    
    if(data.steps){
      renderExecutionSteps(data.steps);
      if(data.relevant_memories){
        renderRelevantMemories(data.relevant_memories);
      }
    }
    
    addMessage('assistant', data.final_report || '任务完成', data.steps);
    chatHistory.push({role:'assistant', content:data.final_report});
    
    loadTasks();
    loadPolicy();
    loadEvolution();
    
  }catch(e){
    addMessage('assistant', `执行失败: ${e.message}\n\n（本地模型离线时仍可演示完整流程）`);
    stepsContainer.innerHTML += `<div class="step-card"><div class="step-header"><span class="step-type error">错误</span><span class="step-title">${e.message}</span></div></div>`;
  }
}

function addMessage(role, content, steps=null){
  const container = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = `message ${role}`;
  
  let stepsHtml = '';
  if(steps && steps.length){
    stepsHtml = `<div class="execution-stream" style="margin-top:12px"><div class="stream-header"><div class="stream-title">执行轨迹 · ${steps.length} 步 · Zane AGI</div><div class="stream-path">感知(WMI)→推理(Qwen3)→规划(DAG)→工具(真实)→验证→记忆→进化</div></div><div class="stream-steps">` +
      steps.map(s=>`
        <div class="step-card">
          <div class="step-header">
            <span class="step-type ${s.type}">${typeLabel(s.type)}</span>
            <span class="step-title">${s.title}</span>
            <span class="step-status">${s.status}</span>
          </div>
          <div class="step-content">${escapeHtml(s.content).slice(0,800)}</div>
        </div>
      `).join('') + `</div></div>`;
  }
  
  div.innerHTML = `
    <div class="msg-avatar">${role==='user'?'你':'Z'}</div>
    <div class="msg-content">
      <div class="msg-header">
        <span class="msg-role">${role==='user'?'你':'Zane AGI'}</span>
        <span class="msg-time">${new Date().toLocaleTimeString()} · ${role==='user'?'':'Qwen3-30B-A3B · 私有进化'}</span>
      </div>
      <div class="msg-text">${formatMessage(content)}${stepsHtml}</div>
    </div>
  `;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function formatMessage(text){
  if(!text) return '';
  return text
    .replace(/\n/g,'<br>')
    .replace(/`([^`]+)`/g,'<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>')
    .replace(/•/g,'<br>•');
}

function typeLabel(type){
  const map = {reasoning:'推理', tool_call:'工具调用', tool_result:'工具结果', verification:'验证', error:'错误', final:'完成'};
  return map[type] || type;
}

function renderExecutionSteps(steps){
  const container = document.getElementById('stream-steps');
  container.innerHTML = steps.map(s=>`
    <div class="step-card">
      <div class="step-header">
        <span class="step-type ${s.type}">${typeLabel(s.type)}</span>
        <span class="step-title">${escapeHtml(s.title)}</span>
        <span class="step-status">${s.status}${s.need_confirm?' · 需确认':''}</span>
      </div>
      <div class="step-content">${escapeHtml(s.content).slice(0,1200)}</div>
    </div>
  `).join('');
}

function renderRelevantMemories(mem){
  const container = document.getElementById('model-mini');
  if(!container) return;
  let html = '';
  if(mem.skills && mem.skills.length){
    html += `<div style="margin-bottom:8px"><strong>相关技能：</strong><br>` + mem.skills.map(s=>`• ${s.name}`).join('<br>') + `</div>`;
  }
  if(mem.experiences && mem.experiences.length){
    html += `<div><strong>相关经验：</strong><br>` + mem.experiences.map(e=>`• ${e.task_type}`).join('<br>') + `</div>`;
  }
  if(!html) html = 'Qwen3-30B-A3B<br>IQ4_XS · 18.5GB<br>30B total / 3B active';
  container.innerHTML = html;
}

async function loadTools(){
  try{
    const res = await fetch(`${API_BASE}/api/tools`);
    const data = await res.json();
    const container = document.getElementById('evolution-mini');
    if(container){
      container.innerHTML = `工具: ${data.total} 个<br>类别: ${Object.keys(data.by_category).length} 个<br>真实: ✅`;
    }
  }catch(e){}
}

async function loadTasks(){
  try{
    const res = await fetch(`${API_BASE}/api/tasks`);
    const data = await res.json();
    const tasks = data.tasks || [];
    const el = document.getElementById('task-count');
    if(el) el.textContent = tasks.length;
    const totalEl = document.getElementById('stat-total');
    if(totalEl) totalEl.textContent = tasks.length;
    
    const container = document.getElementById('task-list');
    if(container){
      container.innerHTML = tasks.map(t=>`
        <div class="task-card">
          <div class="task-info">
            <h3>${escapeHtml(t.title)}</h3>
            <p>${escapeHtml(t.description)}</p>
            <div class="task-meta">
              <span class="task-tag">${t.status}</span>
              <span class="task-tag">${t.duration}</span>
              <span class="task-tag">${t.steps} 步</span>
              ${(t.tools||[]).map(tool=>`<span class="task-tag">${tool}</span>`).join('')}
            </div>
          </div>
          <div><span class="badge warning">${new Date(t.created_at*1000).toLocaleTimeString()}</span></div>
        </div>
      `).join('');
    }
    
    const undoEl = document.getElementById('undo-mini');
    if(undoEl){
      const undo = data.undo_stack || [];
      undoEl.innerHTML = undo.slice(0,3).map(u=>`<div style="font-size:11px;padding:4px 0">${u.description}</div>`).join('') || '暂无可撤销';
    }
    
  }catch(e){ console.error(e); }
}

async function loadSystemState(){
  try{
    const res = await fetch(`${API_BASE}/api/system/state`);
    const data = await res.json();
    const container = document.getElementById('system-grid');
    if(!container) return;
    
    // 兼容新旧格式
    const cpu = data.cpu || {};
    const memory = data.memory || data.physical || {};
    const disks = data.disks || [];
    const topProcs = data.top_processes || [];
    
    // WMI 真实数据
    const isReal = cpu.real || data.real || false;
    const cpuName = cpu.name || 'CPU';
    const perCore = cpu.per_core || [];
    const gpus = cpu.gpus || [];
    
    container.innerHTML = `
      <div class="system-card">
        <h3>🧠 CPU ${isReal?'· 真实WMI':''}</h3>
        <div style="font-size:11px;color:var(--text3);margin-bottom:8px">${escapeHtml(cpuName).slice(0,60)}</div>
        <div class="sys-row"><span>总使用率</span><span>${cpu.total_percent||cpu.percent||0}%</span></div>
        <div class="progress"><div class="progress-fill" style="width:${cpu.total_percent||cpu.percent||0}%"></div></div>
        ${perCore.length?`<div style="margin-top:8px"><div style="font-size:11px;color:var(--text2)">每核心:</div><div style="display:grid;grid-template-columns:repeat(4,1fr);gap:4px;margin-top:4px">${perCore.slice(0,8).map(c=>`<div style="background:var(--bg3);padding:2px 4px;border-radius:4px;font-size:10px;text-align:center">${c.core}: ${Math.round(c.percent)}%</div>`).join('')}</div></div>`:''}
        ${gpus.length?`<div style="margin-top:8px"><div style="font-size:11px;color:var(--text2)">GPU:</div>${gpus.map(g=>`<div style="font-size:11px">${escapeHtml(g.name).slice(0,40)}</div>`).join('')}</div>`:''}
        <div class="sys-row" style="margin-top:8px"><span>物理核心</span><span>${cpu.physical_cores||0}</span></div>
        <div class="sys-row"><span>逻辑核心</span><span>${cpu.logical_cores||0}</span></div>
      </div>
      <div class="system-card">
        <h3>💾 内存 ${isReal?'· 真实WMI':''}</h3>
        <div class="sys-row"><span>使用率</span><span>${memory.percent||0}%</span></div>
        <div class="progress"><div class="progress-fill" style="width:${memory.percent||0}%;background:var(--purple)"></div></div>
        <div class="sys-row"><span>总量</span><span>${memory.total_gb||memory.physical?.total_gb||0} GB</span></div>
        <div class="sys-row"><span>已用</span><span>${memory.used_gb||memory.physical?.used_gb||0} GB</span></div>
        <div class="sys-row"><span>可用</span><span>${memory.available_gb||memory.physical?.available_gb||0} GB</span></div>
        ${memory.sticks?`<div style="margin-top:8px;font-size:11px">${memory.sticks.map(s=>`<div>${s.manufacturer} ${s.capacity_gb}GB ${s.speed}MHz</div>`).join('')}</div>`:''}
      </div>
      <div class="system-card">
        <h3>💿 磁盘</h3>
        ${(disks.length?disks:[{device:'C:', total_gb: data.disk?.total_gb||0, free_gb: data.disk?.free_gb||0, percent: data.disk?.percent||0}]).map(d=>`
          <div style="margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid rgba(255,255,255,0.05)">
            <div class="sys-row"><span>${d.device||d.mountpoint||'磁盘'}</span><span>${d.type||''}</span></div>
            <div class="sys-row"><span>使用率</span><span>${d.percent||0}%</span></div>
            <div class="progress"><div class="progress-fill" style="width:${d.percent||0}%;background:var(--success)"></div></div>
            <div class="sys-row"><span>总量</span><span>${d.total_gb||0} GB</span></div>
            <div class="sys-row"><span>可用</span><span>${d.free_gb||0} GB</span></div>
          </div>
        `).join('')}
      </div>
      <div class="system-card">
        <h3>🌐 系统 ${isReal?'· 真实WMI':''}</h3>
        <div class="sys-row"><span>平台</span><span>${data.platform?.system||''} ${data.platform?.release||''}</span></div>
        <div class="sys-row"><span>真实</span><span>${isReal?'✅ WMI':'❌ 演示'}</span></div>
        ${data.startup_items?`<div style="margin-top:12px"><h4 style="font-size:12px">🚀 启动项 (${data.startup_items.length})</h4>${data.startup_items.slice(0,3).map(s=>`<div style="font-size:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${escapeHtml(s.name)}: ${escapeHtml(s.path).slice(0,30)}</div>`).join('')}</div>`:''}
        <h4 style="margin-top:16px;font-size:13px">🔥 占用前5进程</h4>
        ${(topProcs||[]).map(p=>`<div class="sys-row"><span>${escapeHtml(p.name).slice(0,20)}</span><span>${p.memory_mb} MB</span></div>`).join('')}
      </div>
    `;
    
    const miniCpu = document.getElementById('mini-cpu');
    const miniCpuBar = document.getElementById('mini-cpu-bar');
    const miniMem = document.getElementById('mini-mem');
    const miniMemBar = document.getElementById('mini-mem-bar');
    if(miniCpu) miniCpu.textContent = Math.round(cpu.total_percent||cpu.percent||0)+'%';
    if(miniCpuBar) miniCpuBar.style.width = (cpu.total_percent||cpu.percent||0)+'%';
    if(miniMem) miniMem.textContent = Math.round(memory.percent||0)+'%';
    if(miniMemBar) miniMemBar.style.width = (memory.percent||0)+'%';
    
  }catch(e){
    const container = document.getElementById('system-grid');
    if(container) container.innerHTML = `<div class="empty">加载失败: ${e.message}</div>`;
  }
}

async function loadFiles(){
  const path = document.getElementById('file-path').value;
  const container = document.getElementById('file-list');
  if(!container) return;
  container.innerHTML = '<div class="empty">加载中...</div>';
  try{
    const res = await fetch(`${API_BASE}/api/system/files?path=${encodeURIComponent(path)}&detail=true`);
    const data = await res.json();
    if(data.error){
      container.innerHTML = `<div class="empty">错误: ${data.error}</div>`;
      return;
    }
    container.innerHTML = `
      <div style="padding:12px 16px;background:rgba(0,0,0,0.2);font-size:12px;color:var(--text2)">路径: ${data.path} | 总计: ${data.total} 项 (${data.total_dirs} 文件夹, ${data.total_files} 文件) ${data.truncated?'· 已截断':''} ${data.real?'· 真实':''}</div>
      ${(data.files||[]).map(f=>`
        <div class="file-item">
          <div class="file-icon">${f.is_dir?'📁':'📄'}</div>
          <div style="flex:1">
            <div class="file-name">${escapeHtml(f.name)}</div>
            <div class="file-meta">${f.is_dir?'文件夹':'文件'} ${f.size_readable?`· ${f.size_readable}`:''} ${f.modified?`· ${f.modified}`:''}</div>
          </div>
          <div><span class="task-tag">${f.is_dir?'目录':'文件'}</span></div>
        </div>
      `).join('')}
    `;
  }catch(e){
    container.innerHTML = `<div class="empty">加载失败: ${e.message}</div>`;
  }
}

async function loadProcesses(){
  const sortEl = document.getElementById('process-sort');
  const sort = sortEl ? sortEl.value : 'memory';
  const container = document.getElementById('process-list');
  if(!container) return;
  container.innerHTML = '<div class="empty">加载真实进程树中...</div>';
  try{
    const res = await fetch(`${API_BASE}/api/system/processes?sort_by=${sort}&limit=20`);
    const data = await res.json();
    if(data.error){
      container.innerHTML = `<div class="empty">${data.error}</div>`;
      return;
    }
    container.innerHTML = `
      <div class="process-header"><span>PID</span><span>名称</span><span>内存</span><span>CPU</span><span>状态</span></div>
      ${(data.processes||[]).map(p=>`
        <div class="process-row">
          <span style="font-family:monospace">${p.pid}</span>
          <span style="font-weight:500">${escapeHtml(p.name)}<br><span style="font-size:10px;color:var(--text3)">${escapeHtml(p.parent_name||'')}</span></span>
          <span>${p.memory_mb} MB</span>
          <span>${p.cpu_percent}%</span>
          <span><span class="task-tag">${p.status}</span></span>
        </div>
      `).join('')}
      <div style="padding:12px;font-size:11px;color:var(--text3)">共 ${data.total} 个进程 · ${data.real?'真实WMI进程树':'演示'} · 含父进程、命令行、线程数</div>
    `;
  }catch(e){
    container.innerHTML = `<div class="empty">失败: ${e.message}</div>`;
  }
}

async function loadWindows(){
  const container = document.getElementById('window-grid');
  if(!container) return;
  container.innerHTML = '<div class="empty">枚举真实HWND中...</div>';
  try{
    const res = await fetch(`${API_BASE}/api/system/windows`);
    const data = await res.json();
    container.innerHTML = (data.windows||[]).map(w=>`
      <div class="window-card">
        <div class="window-title">${escapeHtml(w.title)}</div>
        <div class="window-meta">HWND: ${w.hwnd} · 类: ${w.class||w.process||''} · ${w.rect?`${w.rect.width}x${w.rect.height}`:''} ${w.visible?'· 可见':''} ${w.is_topmost?'· 置顶':''} ${w.is_minimized?'· 最小化':''}</div>
        <div class="window-meta">进程: ${w.process||''} PID:${w.pid||''} Z:${w.z_order||0} DPI:${w.dpi||96} ${w.real?'· 真实':''}</div>
        <div class="window-actions">
          <button class="btn secondary" style="font-size:11px;padding:4px 8px" onclick="focusWindow('${w.title.replace(/'/g,"\\'")}')">聚焦</button>
          <button class="btn secondary" style="font-size:11px;padding:4px 8px" onclick="quickInput('把 ${w.title.slice(0,10)} 窗口切到前台')">AI切换</button>
        </div>
      </div>
    `).join('') + `<div style="grid-column:1/-1;padding:12px;font-size:11px;color:var(--text3)">共 ${data.total} 个窗口 · ${data.real?'真实Win32 API':'演示'} · 含Z序、DPI、置顶状态</div>`;
  }catch(e){
    container.innerHTML = `<div class="empty">失败: ${e.message}</div>`;
  }
}

async function focusWindow(keyword){
  try{
    const res = await fetch(`${API_BASE}/api/tools/call`, {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({tool_name:'focus_window', parameters:{title_keyword:keyword}, auto_confirm:true})
    });
    const data = await res.json();
    alert(data.result?.message || JSON.stringify(data.result));
  }catch(e){ alert('失败:'+e.message); }
}

async function takeScreenshot(){
  const preview = document.getElementById('vision-preview');
  if(!preview) return;
  preview.innerHTML = '<div class="empty">截图中... 真实WMI/DWM</div>';
  try{
    const res = await fetch(`${API_BASE}/api/system/screenshot?mode=full`);
    const data = await res.json();
    if(data.success){
      preview.innerHTML = `
        <div>
          <div style="background:var(--bg3);padding:12px;border-radius:8px;margin-bottom:12px;font-size:12px">
            ✅ 截图成功 · ${data.width}x${data.height} · ${data.size_kb||0}KB ${data.demo?'(演示占位，Windows真实桌面)':''}
          </div>
          <div style="width:100%;height:300px;background:linear-gradient(135deg,#1e293b,#334155);border-radius:8px;display:flex;align-items:center;justify-content:center;color:var(--text2);border:1px dashed var(--border)">
            <div style="text-align:center"><div style="font-size:48px">🖥️</div><div>截图已保存</div><div style="font-size:11px;margin-top:8px">Windows真实环境显示真实桌面</div></div>
          </div>
        </div>
      `;
    }else{
      preview.innerHTML = `<div class="empty">截图失败: ${data.error}</div>`;
    }
  }catch(e){
    preview.innerHTML = `<div class="empty">失败: ${e.message}</div>`;
  }
}

async function doOCR(){
  const result = document.getElementById('vision-result');
  if(!result) return;
  result.innerHTML = '<div class="empty">OCR识别中...</div>';
  try{
    const res = await fetch(`${API_BASE}/api/tools/call`, {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({tool_name:'ocr_screenshot', parameters:{lang:'chi_sim+eng'}, auto_confirm:true})
    });
    const data = await res.json();
    const ocr = data.result;
    result.innerHTML = `
      <h4>🔍 OCR结果</h4>
      <div style="background:var(--bg);padding:12px;border-radius:8px;white-space:pre-wrap;font-size:12px;margin:12px 0">${escapeHtml(ocr.text)}</div>
      <p style="font-size:11px;color:var(--text3)">${ocr.note}</p>
    `;
  }catch(e){
    result.innerHTML = `<div class="empty">OCR失败: ${e.message}</div>`;
  }
}

async function loadMemory(tab='semantic'){
  const container = document.getElementById('memory-content');
  if(!container) return;
  container.innerHTML = '<div class="empty">加载记忆中...</div>';
  try{
    const res = await fetch(`${API_BASE}/api/memory`);
    const data = await res.json();
    let items = [];
    if(tab==='semantic') items = data.semantic || [];
    else if(tab==='episodic') items = data.episodic || [];
    else items = data.conversations || [];
    
    if(tab==='conv'){
      container.innerHTML = items.slice(-20).map(c=>`
        <div class="memory-card">
          <h4>${c.role==='user'?'你':'助手'} · ${new Date(c.timestamp*1000).toLocaleString()}</h4>
          <p>${escapeHtml(c.content).slice(0,200)}</p>
        </div>
      `).join('') || '<div class="empty">暂无会话记忆</div>';
    }else{
      container.innerHTML = items.map(m=>`
        <div class="memory-card">
          <h4>${escapeHtml(m.topic||m.task||'记忆')} <span style="font-size:10px;color:var(--text3)">${new Date((m.timestamp||0)*1000).toLocaleString()}</span></h4>
          <p>${escapeHtml(m.fact||m.result||m.context||'')}${m.confidence?` · 置信度 ${(m.confidence*100).toFixed(0)}%`:''}</p>
          <div class="skill-tags">${(m.tags||[]).map(t=>`<span class="skill-tag">${t}</span>`).join('')}</div>
        </div>
      `).join('') || '<div class="empty">暂无记忆</div>';
    }
  }catch(e){
    container.innerHTML = `<div class="empty">失败: ${e.message}</div>`;
  }
}

function switchMemoryTab(tab){
  loadMemory(tab);
  document.querySelectorAll('.memory-tabs .tab').forEach((t,i)=>{
    t.classList.remove('active');
    if((tab==='semantic'&&i===0)||(tab==='episodic'&&i===1)||(tab==='conv'&&i===2)) t.classList.add('active');
  });
}

async function loadSkills(){
  const container = document.getElementById('skills-grid');
  if(!container) return;
  container.innerHTML = '<div class="empty">加载技能中...</div>';
  try{
    const res = await fetch(`${API_BASE}/api/skills`);
    const data = await res.json();
    container.innerHTML = (data.skills||[]).map(s=>`
      <div class="skill-card">
        <div class="skill-header">
          <div class="skill-name">${escapeHtml(s.name)}</div>
          <div class="skill-rate high">${(s.success_rate*100).toFixed(0)}% · ${s.usage_count}次</div>
        </div>
        <div class="skill-desc">${escapeHtml(s.description)}</div>
        <div class="skill-steps">
          ${(s.steps||[]).map((st,i)=>`<div class="skill-step"><span style="color:var(--accent)">${i+1}.</span><span>${st.tool||st.desc} - ${escapeHtml(st.desc||st.tool)}</span></div>`).join('')}
        </div>
        <div class="skill-tags">${(s.tags||[]).map(t=>`<span class="skill-tag">${t}</span>`).join('')}</div>
      </div>
    `).join('') || '<div class="empty">暂无技能</div>';
  }catch(e){
    container.innerHTML = `<div class="empty">失败: ${e.message}</div>`;
  }
}

async function loadExperiences(){
  const container = document.getElementById('experience-list');
  if(!container) return;
  container.innerHTML = '<div class="empty">加载经验中...</div>';
  try{
    const res = await fetch(`${API_BASE}/api/experiences`);
    const data = await res.json();
    container.innerHTML = (data.experiences||[]).map(exp=>`
      <div class="exp-card">
        <h4>${escapeHtml(exp.task_type)} <span style="font-size:11px;color:var(--text3)">${new Date(exp.created_at*1000).toLocaleDateString()} · ${exp.tools_used?.join(' → ')||''}</span></h4>
        <div style="margin:8px 0"><strong>问题：</strong>${escapeHtml(exp.problem)}</div>
        <div style="margin:8px 0"><strong>解法：</strong>${escapeHtml(exp.solution)}</div>
        <div style="margin:8px 0;font-size:12px;color:var(--text2)"><strong>验证：</strong>${escapeHtml(exp.verification)}</div>
        <div style="margin-top:8px"><span class="badge warning">可复用: ${exp.reusable?'是':'否'}</span></div>
      </div>
    `).join('') || '<div class="empty">暂无经验</div>';
  }catch(e){
    container.innerHTML = `<div class="empty">失败: ${e.message}</div>`;
  }
}

async function loadPolicy(){
  try{
    const res = await fetch(`${API_BASE}/api/policy`);
    const data = await res.json();
    const el = document.getElementById('policy-list');
    if(el){
      el.innerHTML = `
        <div class="sys-row"><span>自动放行</span><span>${data.auto_allow?.length||0} 个</span></div>
        <div style="font-size:11px;color:var(--text2);margin:8px 0;max-height:60px;overflow-y:auto">${(data.auto_allow||[]).slice(0,5).join(', ')}...</div>
        <div class="sys-row"><span>保护路径</span><span>${data.protected_paths?.length||0} 条</span></div>
        <div class="sys-row"><span>撤销栈</span><span>${data.undo_history?.length||0} 条</span></div>
        <h4 style="margin-top:12px;font-size:12px">最近审计</h4>
        ${(data.audit_logs||[]).slice(0,3).map(l=>`<div class="sys-row"><span>${l.tool}</span><span>${l.exec_ms}ms</span></div>`).join('')}
      `;
    }
  }catch(e){}
}

async function updateMiniResources(){
  try{
    const res = await fetch(`${API_BASE}/api/system/state`);
    const data = await res.json();
    const cpu = data.cpu || {};
    const mem = data.memory || {};
    const miniCpu = document.getElementById('mini-cpu');
    const miniCpuBar = document.getElementById('mini-cpu-bar');
    const miniMem = document.getElementById('mini-mem');
    const miniMemBar = document.getElementById('mini-mem-bar');
    if(miniCpu) miniCpu.textContent = Math.round(cpu.total_percent||cpu.percent||0)+'%';
    if(miniCpuBar) miniCpuBar.style.width = (cpu.total_percent||cpu.percent||0)+'%';
    if(miniMem) miniMem.textContent = Math.round(mem.percent||mem.physical?.percent||0)+'%';
    if(miniMemBar) miniMemBar.style.width = (mem.percent||mem.physical?.percent||0)+'%';
  }catch(e){}
}

function escapeHtml(str){
  if(!str) return '';
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// v2 额外
async function loadEvolution(){
  try{
    const res = await fetch(`${API_BASE}/api/evolution/status`);
    const data = await res.json();
    const evoStatus = document.getElementById('evo-status');
    const evoSamples = document.getElementById('evo-samples');
    const evoLora = document.getElementById('evo-lora');
    const evoProgress = document.getElementById('evo-progress');
    if(evoStatus) evoStatus.textContent = data.status;
    if(evoSamples) evoSamples.textContent = data.training_data.sft_samples;
    if(evoLora) evoLora.textContent = data.current_lora;
    if(evoProgress) evoProgress.style.width = Math.min(100, data.training_data.sft_samples/50*100)+'%';
  }catch(e){}
}

async function loadModels(){
  try{
    const res = await fetch(`${API_BASE}/api/models`);
    const data = await res.json();
    const el = document.getElementById('model-status-text');
    if(el && data.current) el.textContent = data.current.split('\\').pop().slice(0,20);
    const topModel = document.getElementById('top-model-name');
    if(topModel && data.current) topModel.textContent = data.current.split('\\').pop().slice(0,25);
  }catch(e){}
}

async function startEvolution(){
  const res = await fetch(`${API_BASE}/api/evolution/start?manual=true`, {method:'POST'});
  const data = await res.json();
  alert(data.message);
}
async function startDreaming(){
  const res = await fetch(`${API_BASE}/api/evolution/dreaming`, {method:'POST'});
  const data = await res.json();
  alert(data.message);
}
function toggleNotifications(){
  const el = document.getElementById('notification-center');
  if(el) el.style.display = el.style.display==='none'?'block':'none';
}
async function undoLast(){
  const res = await fetch(`${API_BASE}/api/tasks/undo`, {method:'POST'});
  const data = await res.json();
  alert(data.message || '已撤销');
}
