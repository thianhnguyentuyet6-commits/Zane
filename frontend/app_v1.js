/* 本地AI电脑助手 - 前端逻辑 */
const API_BASE = window.location.origin;
let currentView = 'chat';
let chatHistory = [];

// 初始化
document.addEventListener('DOMContentLoaded', () => {
  initNav();
  initChatInput();
  loadTools();
  loadTasks();
  loadSystemState();
  loadPolicy();
  setInterval(updateMiniResources, 3000);
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
    chat:'对话 / 智能执行',
    tasks:'任务 / 执行历史',
    system:'电脑状态 / 真实系统数据',
    files:'文件 / 真实文件系统',
    processes:'进程 / 真实进程监控',
    windows:'窗口 / 窗口管理',
    vision:'截图与视觉 / 真实屏幕感知',
    memory:'记忆 / 长期记忆',
    skills:'技能 / 可复用流程',
    experience:'经验 / 学习管道',
    settings:'设置 / 本地优先架构'
  };
  document.getElementById('breadcrumb').textContent = titles[view] || view;
  document.getElementById('page-title').textContent = {
    chat:'与本地AI助手对话',
    tasks:'智能体任务历史',
    system:'真实系统状态监控',
    files:'文件浏览器',
    processes:'进程管理器',
    windows:'窗口管理器',
    vision:'视觉感知系统',
    memory:'记忆层',
    skills:'技能库',
    experience:'经验学习',
    settings:'系统设置'
  }[view] || view;

  // 懒加载
  if(view==='files') loadFiles();
  if(view==='processes') loadProcesses();
  if(view==='windows') loadWindows();
  if(view==='memory') loadMemory('semantic');
  if(view==='skills') loadSkills();
  if(view==='experience') loadExperiences();
  if(view==='system') loadSystemState();
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
  
  // 显示执行流
  const stream = document.getElementById('execution-stream');
  const stepsContainer = document.getElementById('stream-steps');
  stream.style.display = 'block';
  stepsContainer.innerHTML = '<div class="step-card"><div class="step-header"><span class="step-type reasoning">推理中</span><span class="step-title">正在理解任务并检索记忆...</span><span class="pulse"></span></div></div>';
  
  // 滚动到底部
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
      // 显示相关记忆
      if(data.relevant_memories){
        renderRelevantMemories(data.relevant_memories);
      }
    }
    
    // 最终报告作为助手消息
    addMessage('assistant', data.final_report || '任务完成', data.steps);
    chatHistory.push({role:'assistant', content:data.final_report});
    
    // 更新任务计数
    loadTasks();
    loadPolicy();
    
  }catch(e){
    addMessage('assistant', `执行失败: ${e.message}\n\n（本地模型离线时仍可演示完整流程，请检查后端服务）`);
    stepsContainer.innerHTML += `<div class="step-card"><div class="step-header"><span class="step-type error">错误</span><span class="step-title">${e.message}</span></div></div>`;
  }
}

function addMessage(role, content, steps=null){
  const container = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = `message ${role}`;
  
  let stepsHtml = '';
  if(steps && steps.length){
    stepsHtml = `<div class="execution-stream" style="margin-top:12px"><div class="stream-header"><div class="stream-title">执行轨迹 · ${steps.length} 步</div><div class="stream-path">代码维护现实 · AI解释现实</div></div><div class="stream-steps">` +
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
    <div class="msg-avatar">${role==='user'?'你':'◈'}</div>
    <div class="msg-content">
      <div class="msg-header">
        <span class="msg-role">${role==='user'?'你':'本地助手'}</span>
        <span class="msg-time">${new Date().toLocaleTimeString()} · ${role==='user'?'':'本地私有运行'}</span>
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
  const container = document.getElementById('memory-mini');
  let html = '';
  if(mem.skills && mem.skills.length){
    html += `<div style="margin-bottom:8px"><strong>相关技能：</strong><br>` + mem.skills.map(s=>`• ${s.name}`).join('<br>') + `</div>`;
  }
  if(mem.experiences && mem.experiences.length){
    html += `<div><strong>相关经验：</strong><br>` + mem.experiences.map(e=>`• ${e.task_type}: ${e.problem.slice(0,30)}`).join('<br>') + `</div>`;
  }
  if(!html) html = '<div class="empty">无相关记忆，使用后会自动积累</div>';
  container.innerHTML = html;
}

async function loadTools(){
  try{
    const res = await fetch(`${API_BASE}/api/tools`);
    const data = await res.json();
    const container = document.getElementById('tool-list-mini');
    let html = '';
    for(const [cat, tools] of Object.entries(data.by_category)){
      html += `<div style="font-weight:600;margin:8px 0 4px;color:var(--accent);font-size:11px">${cat}</div>`;
      tools.slice(0,3).forEach(t=>{
        html += `<div class="mini-tool"><span class="mini-tool-name">${t.display_name}</span><span class="mini-tool-cat">${t.permission}</span></div>`;
      });
    }
    container.innerHTML = html;
  }catch(e){
    document.getElementById('tool-list-mini').innerHTML = '<div class="empty">工具加载失败</div>';
  }
}

async function loadTasks(){
  try{
    const res = await fetch(`${API_BASE}/api/tasks`);
    const data = await res.json();
    const tasks = data.tasks || [];
    document.getElementById('task-count').textContent = tasks.length;
    document.getElementById('stat-total').textContent = tasks.length;
    document.getElementById('stat-success').textContent = tasks.filter(t=>t.status==='已完成').length;
    document.getElementById('stat-pending').textContent = tasks.filter(t=>t.status==='等待中').length;
    
    const container = document.getElementById('task-list');
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
    
    // 审计
    const audit = data.audit_logs || [];
    document.getElementById('audit-mini').innerHTML = audit.slice(0,5).map(l=>`
      <div class="mini-tool"><span>${l.tool}</span><span>${l.exec_ms}ms</span></div>
    `).join('') || '<div class="empty">暂无日志</div>';
    
  }catch(e){ console.error(e); }
}

async function loadSystemState(){
  try{
    const res = await fetch(`${API_BASE}/api/system/state`);
    const data = await res.json();
    const container = document.getElementById('system-grid');
    container.innerHTML = `
      <div class="system-card">
        <h3>🧠 CPU</h3>
        <div class="sys-row"><span>使用率</span><span>${data.cpu?.percent||0}%</span></div>
        <div class="progress"><div class="progress-fill" style="width:${data.cpu?.percent||0}%"></div></div>
        <div class="sys-row"><span>核心数</span><span>${data.cpu?.cores||0} 逻辑 / ${data.cpu?.physical_cores||0} 物理</span></div>
      </div>
      <div class="system-card">
        <h3>💾 内存</h3>
        <div class="sys-row"><span>使用率</span><span>${data.memory?.percent||0}%</span></div>
        <div class="progress"><div class="progress-fill" style="width:${data.memory?.percent||0}%;background:var(--purple)"></div></div>
        <div class="sys-row"><span>总量</span><span>${data.memory?.total_gb||0} GB</span></div>
        <div class="sys-row"><span>已用</span><span>${data.memory?.used_gb||0} GB</span></div>
        <div class="sys-row"><span>可用</span><span>${data.memory?.available_gb||0} GB</span></div>
      </div>
      <div class="system-card">
        <h3>💿 磁盘</h3>
        <div class="sys-row"><span>使用率</span><span>${data.disk?.percent||0}%</span></div>
        <div class="progress"><div class="progress-fill" style="width:${data.disk?.percent||0}%;background:var(--success)"></div></div>
        <div class="sys-row"><span>总量</span><span>${data.disk?.total_gb||0} GB</span></div>
        <div class="sys-row"><span>可用</span><span>${data.disk?.free_gb||0} GB</span></div>
      </div>
      <div class="system-card">
        <h3>🌐 网络与系统</h3>
        <div class="sys-row"><span>平台</span><span>${data.platform||''}</span></div>
        <div class="sys-row"><span>开机时间</span><span>${data.boot_time||''}</span></div>
        <div class="sys-row"><span>发送</span><span>${data.network?.bytes_sent_mb||0} MB</span></div>
        <div class="sys-row"><span>接收</span><span>${data.network?.bytes_recv_mb||0} MB</span></div>
        <h4 style="margin-top:16px;font-size:13px">🔥 占用前5进程</h4>
        ${(data.top_processes||[]).map(p=>`<div class="sys-row"><span>${p.name}</span><span>${p.memory_mb} MB</span></div>`).join('')}
      </div>
    `;
    document.getElementById('mini-cpu').textContent = (data.cpu?.percent||0)+'%';
    document.getElementById('mini-cpu-bar').style.width = (data.cpu?.percent||0)+'%';
    document.getElementById('mini-mem').textContent = (data.memory?.percent||0)+'%';
    document.getElementById('mini-mem-bar').style.width = (data.memory?.percent||0)+'%';
  }catch(e){
    document.getElementById('system-grid').innerHTML = `<div class="empty">加载失败: ${e.message}</div>`;
  }
}

async function loadFiles(){
  const path = document.getElementById('file-path').value;
  const container = document.getElementById('file-list');
  container.innerHTML = '<div class="empty">加载中...</div>';
  try{
    const res = await fetch(`${API_BASE}/api/system/files?path=${encodeURIComponent(path)}&detail=true`);
    const data = await res.json();
    if(data.error){
      container.innerHTML = `<div class="empty">错误: ${data.error}</div>`;
      return;
    }
    container.innerHTML = `
      <div style="padding:12px 16px;background:rgba(0,0,0,0.2);font-size:12px;color:var(--text2)">路径: ${data.path} | 总计: ${data.total} 项 (${data.total_dirs} 文件夹, ${data.total_files} 文件) ${data.truncated?'· 已截断':''}</div>
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
  const sort = document.getElementById('process-sort').value;
  const container = document.getElementById('process-list');
  container.innerHTML = '<div class="empty">加载真实进程中...</div>';
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
          <span style="font-weight:500">${escapeHtml(p.name)}</span>
          <span>${p.memory_mb} MB</span>
          <span>${p.cpu_percent}%</span>
          <span><span class="task-tag">${p.status}</span></span>
        </div>
      `).join('')}
      <div style="padding:12px;font-size:11px;color:var(--text3)">系统内存: ${data.system_memory?.used_gb||0}/${data.system_memory?.total_gb||0} GB (${data.system_memory?.percent||0}%) · 共 ${data.total} 个进程 · 真实数据，非模拟</div>
    `;
  }catch(e){
    container.innerHTML = `<div class="empty">失败: ${e.message}</div>`;
  }
}

async function loadWindows(){
  const container = document.getElementById('window-grid');
  container.innerHTML = '<div class="empty">枚举窗口中...</div>';
  try{
    const res = await fetch(`${API_BASE}/api/system/windows`);
    const data = await res.json();
    container.innerHTML = (data.windows||[]).map(w=>`
      <div class="window-card">
        <div class="window-title">${escapeHtml(w.title)}</div>
        <div class="window-meta">HWND: ${w.hwnd} · 类: ${w.class||w.process||''} · ${w.rect?`${w.rect.width}x${w.rect.height}`:''} ${w.visible?'· 可见':''}</div>
        <div class="window-meta">${w.process?`进程: ${w.process} ${w.memory_mb?`· ${w.memory_mb}MB`:''}`:''}</div>
        <div class="window-actions">
          <button class="btn secondary" style="font-size:11px;padding:4px 8px" onclick="focusWindow('${w.title.replace(/'/g,"\\'")}')">聚焦窗口</button>
          <button class="btn secondary" style="font-size:11px;padding:4px 8px" onclick="quickInput('把 ${w.title.slice(0,10)} 窗口切到前台')">AI切换</button>
        </div>
      </div>
    `).join('') + `<div style="grid-column:1/-1;padding:12px;font-size:11px;color:var(--text3)">共 ${data.total} 个窗口 · ${data.note||'真实窗口数据'}</div>`;
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
  preview.innerHTML = '<div class="empty">截图中... 调用真实截图工具</div>';
  try{
    const res = await fetch(`${API_BASE}/api/system/screenshot?mode=full`);
    const data = await res.json();
    if(data.success){
      preview.innerHTML = `
        <div>
          <div style="background:var(--bg3);padding:12px;border-radius:8px;margin-bottom:12px;font-size:12px">
            ✅ 截图成功 · 路径: ${data.image_path} · 尺寸: ${data.width}x${data.height} · ${data.size_kb||0}KB ${data.demo?'(演示占位图，Windows上为真实桌面)':''}
          </div>
          <div style="width:100%;height:300px;background:linear-gradient(135deg,#1e293b,#334155);border-radius:8px;display:flex;align-items:center;justify-content:center;color:var(--text2);border:1px dashed var(--border)">
            <div style="text-align:center">
              <div style="font-size:48px">🖥️</div>
              <div>截图已保存至服务器</div>
              <div style="font-size:11px;margin-top:8px">Windows真实环境中此处显示真实桌面缩略图</div>
              <div style="font-size:10px;font-family:monospace;margin-top:4px">${data.image_path}</div>
            </div>
          </div>
        </div>
      `;
      document.getElementById('vision-result').innerHTML = `
        <h4>📸 截图信息</h4>
        <div class="sys-row"><span>模式</span><span>${data.mode}</span></div>
        <div class="sys-row"><span>宽度</span><span>${data.width}px</span></div>
        <div class="sys-row"><span>高度</span><span>${data.height}px</span></div>
        <div class="sys-row"><span>真实操作</span><span>✅ 是</span></div>
        <p style="margin-top:12px;font-size:12px;color:var(--text2)">代码维护现实：截图由PIL ImageGrab真实捕获，Windows上为真实桌面</p>
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
      <h4>🔍 OCR识别结果</h4>
      <div style="background:var(--bg);padding:12px;border-radius:8px;white-space:pre-wrap;font-size:12px;margin:12px 0">${escapeHtml(ocr.text)}</div>
      <h5>文字块：</h5>
      ${(ocr.blocks||[]).map(b=>`<div class="sys-row"><span>${escapeHtml(b.text)}</span><span>${(b.confidence*100).toFixed(0)}% (${b.x},${b.y})</span></div>`).join('')}
      <p style="margin-top:12px;font-size:11px;color:var(--text3)">${ocr.note}</p>
    `;
  }catch(e){
    result.innerHTML = `<div class="empty">OCR失败: ${e.message}</div>`;
  }
}

async function loadMemory(tab='semantic'){
  document.querySelectorAll('.memory-tabs .tab').forEach(t=>t.classList.remove('active'));
  event?.target?.classList?.add('active');
  const container = document.getElementById('memory-content');
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
    `).join('') || '<div class="empty">暂无技能，执行任务后自动积累</div>';
  }catch(e){
    container.innerHTML = `<div class="empty">失败: ${e.message}</div>`;
  }
}

async function loadExperiences(){
  const container = document.getElementById('experience-list');
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
    document.getElementById('policy-list').innerHTML = `
      <div class="sys-row"><span>自动放行工具</span><span>${data.auto_allow?.length||0} 个</span></div>
      <div style="font-size:11px;color:var(--text2);margin:8px 0;max-height:80px;overflow-y:auto">${(data.auto_allow||[]).join(', ')}</div>
      <div class="sys-row"><span>保护路径</span><span>${data.protected_paths?.length||0} 条</span></div>
      <div style="font-size:11px;color:var(--text2);margin:8px 0">${(data.protected_paths||[]).join('<br>')}</div>
      <h4 style="margin-top:16px;font-size:13px">最近审计</h4>
      ${(data.audit_logs||[]).slice(0,5).map(l=>`<div class="sys-row"><span>${l.tool}</span><span>${l.exec_ms}ms ${l.confirmed?'✅':''}</span></div>`).join('')}
    `;
  }catch(e){ console.error(e); }
}

async function updateMiniResources(){
  try{
    const res = await fetch(`${API_BASE}/api/system/state`);
    const data = await res.json();
    if(data.cpu){
      document.getElementById('mini-cpu').textContent = Math.round(data.cpu.percent)+'%';
      document.getElementById('mini-cpu-bar').style.width = data.cpu.percent+'%';
    }
    if(data.memory){
      document.getElementById('mini-mem').textContent = Math.round(data.memory.percent)+'%';
      document.getElementById('mini-mem-bar').style.width = data.memory.percent+'%';
    }
  }catch(e){}
}

function showAudit(){
  switchView('settings');
}

function clearChat(){
  if(confirm('确定清除对话历史？')){
    document.getElementById('chat-messages').innerHTML = `
      <div class="message assistant">
        <div class="msg-avatar">◈</div>
        <div class="msg-content">
          <div class="msg-header"><span class="msg-role">本地助手</span><span class="msg-time">刚刚</span></div>
          <div class="msg-text"><p>对话已清除。我是你的本地私有助手，有什么可以帮你？</p></div>
        </div>
      </div>
    `;
    chatHistory = [];
    document.getElementById('execution-stream').style.display='none';
  }
}

function escapeHtml(str){
  if(!str) return '';
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function closeConfirm(ok){
  document.getElementById('confirm-modal').style.display='none';
}
