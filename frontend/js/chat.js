// chat.js - A夯实 聊天模块拆分
import { chatApi } from './api.js';

export let chatHistory = [];

export async function sendMessage(message) {
    if (!message.trim()) return;
    chatHistory.push({role: 'user', content: message});
    renderChat();
    
    try {
        const res = await chatApi.send(message, chatHistory);
        chatHistory.push({role: 'assistant', content: res.final_report || JSON.stringify(res)});
        renderChat();
        return res;
    } catch (e) {
        chatHistory.push({role: 'assistant', content: `错误: ${e.message}`});
        renderChat();
    }
}

export function renderChat() {
    const container = document.getElementById('chat-messages');
    if (!container) return;
    container.innerHTML = chatHistory.map(m => `
        <div class="message ${m.role}">
            <div class="role">${m.role === 'user' ? '你' : 'Zane'}</div>
            <div class="content">${m.content}</div>
        </div>
    `).join('');
    container.scrollTop = container.scrollHeight;
}

export function clearChat() {
    chatHistory = [];
    renderChat();
}
