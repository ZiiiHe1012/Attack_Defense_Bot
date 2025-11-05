// 会话与状态
let conversations = [];
let currentConversationId = null;
let conversationCounter = 1;

let isSidebarCollapsed = false;
let isRequestPending = false;
let currentAbortController = null;

// 工具函数
function getCurrentConversation() {
    return conversations.find(c => c.id === currentConversationId) || null;
}

// 新建对话
function createNewConversation() {
    const id = Date.now();
    const conv = {
        id,
        title: `新对话 ${conversationCounter++}`,
        messages: []
    };
    conversations.unshift(conv);
    currentConversationId = id;
    renderChatList();
    renderConversation(conv);

    fetch('/clear_history', { method: 'POST' }).catch(() => {});
}

// 删除对话
function deleteConversation(id) {
    const idx = conversations.findIndex(c => c.id === id);
    if (idx === -1) return;

    const removeCurrent = conversations[idx].id === currentConversationId;
    conversations.splice(idx, 1);

    if (removeCurrent) {
        if (conversations.length > 0) {
            currentConversationId = conversations[0].id;
            renderConversation(conversations[0]);
        } else {
            currentConversationId = null;
            clearMessagesDom();
        }
        fetch('/clear_history', { method: 'POST' }).catch(() => {});
    }
    renderChatList();
}

// 根据首条用户消息重命名
function setConversationTitleFromFirstUserMessage(conv) {
    const firstUser = conv.messages.find(m => m.type === 'user');
    if (firstUser) {
        conv.title = firstUser.content.slice(0, 20) || conv.title;
        renderChatList();
    }
}

// 渲染侧边栏列表
// 渲染侧边栏列表（支持重命名）
function renderChatList() {
    const list = document.getElementById('chatList');
    if (!list) return;
    list.innerHTML = '';

    conversations.forEach(conv => {
        const item = document.createElement('div');
        item.className = 'chat-item' + (conv.id === currentConversationId ? ' active' : '');
        item.dataset.id = conv.id;

        item.innerHTML = `
            <div class="chat-item-icon"></div>
            <div class="chat-item-title">${conv.title}</div>
            <button class="chat-item-delete" title="删除对话">×</button>
        `;

        // 点击切换对话
        item.addEventListener('click', () => switchConversation(conv.id));

        // 删除
        const delBtn = item.querySelector('.chat-item-delete');
        delBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            deleteConversation(conv.id);
        });

        // 双击重命名
        const titleEl = item.querySelector('.chat-item-title');
        titleEl.addEventListener('dblclick', (e) => {
            e.stopPropagation();
            const input = document.createElement('input');
            input.value = conv.title;
            input.className = 'chat-rename-input';
            titleEl.replaceWith(input);
            input.focus();

            const save = () => {
                conv.title = input.value.trim() || conv.title;
                renderChatList();
            };

            input.addEventListener('blur', save);
            input.addEventListener('keydown', (ev) => {
                if (ev.key === 'Enter') input.blur();
                if (ev.key === 'Escape') renderChatList();
            });
        });

        list.appendChild(item);
    });
}


// 切换会话
function switchConversation(id) {
    if (id === currentConversationId) return;
    const conv = conversations.find(c => c.id === id);
    if (!conv) return;

    currentConversationId = id;
    renderChatList();
    renderConversation(conv);
}

// 对话区域渲染
function clearMessagesDom() {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;
    chatMessages.innerHTML = `
        <div class="welcome-message">
            <div class="welcome-title">正在准备着</div>
            <div class="welcome-text">
                可以在下方输入框中提出安全相关问题，例如：<br>
                “什么是SQL注入？” “如何防御XSS攻击？”
            </div>
        </div>
    `;
}

function renderConversation(conv) {
    clearMessagesDom();
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;

    if (conv.messages.length > 0) {
        const welcomeMsg = chatMessages.querySelector('.welcome-message');
        if (welcomeMsg) welcomeMsg.remove();
    }

    conv.messages.forEach(m => renderMessageDom(m.content, m.type));
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function renderMessageDom(content, type = 'bot') {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;

    const welcomeMsg = chatMessages.querySelector('.welcome-message');
    if (welcomeMsg) welcomeMsg.remove();

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;

    const headerLabel = type === 'user' ? '你' : 'AI';
    const formattedContent = type === 'bot' ? formatMarkdown(content) : content;

    messageDiv.innerHTML = `
        <div class="message-header">
            <div class="message-icon">${headerLabel}</div>
        </div>
        <div class="message-content">${formattedContent}</div>
    `;

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function appendMessageToCurrent(content, type) {
    const conv = getCurrentConversation();
    if (!conv) return;

    conv.messages.push({ type, content });
    renderMessageDom(content, type);

    if (type === 'user' && conv.messages.length === 1) {
        setConversationTitleFromFirstUserMessage(conv);
    }
}

function addErrorMessage(content) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = 'message error-message';
    messageDiv.innerHTML = `
        <div class="message-header">
            <div class="message-icon">!</div>
        </div>
        <div class="message-content">${content}</div>
    `;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 加载状态 + 按钮形态
function setLoading(isLoading) {
    const sendBtn = document.getElementById('sendBtn');
    const chatMessages = document.getElementById('chatMessages');
    if (!sendBtn || !chatMessages) return;

    isRequestPending = isLoading;

    if (isLoading) {
        // --- 开始加载 ---
        sendBtn.classList.add('loading');
        sendBtn.title = '停止生成';

        const loadingDiv = document.createElement('div');
        loadingDiv.id = 'loadingIndicator';
        loadingDiv.className = 'message bot-message loading-message';

        loadingDiv.innerHTML = `
            <div class="message-header">
                <div class="message-icon">AI</div>
            </div>
            <div class="loading-dots">
                <span></span><span></span><span></span>
            </div>
        `;

        chatMessages.appendChild(loadingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;



    } else {
        // --- 结束加载 ---
        sendBtn.classList.remove('loading');
        sendBtn.title = '发送';

        // 4. 从聊天窗口中移除加载元素
        const loadingIndicator = document.getElementById('loadingIndicator');
        if (loadingIndicator) {
            loadingIndicator.remove();
        }
    }
}

// 发送消息
async function sendMessage() {
    const input = document.getElementById('userInput');
    if (!input) return;

    const text = input.value.trim();
    if (!text || isRequestPending) return;

    if (!getCurrentConversation()) {
        createNewConversation();
    }

    appendMessageToCurrent(text, 'user');
    input.value = '';
    autoResizeTextarea();
    setLoading(true);

    currentAbortController = new AbortController();

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text }),
            signal: currentAbortController.signal
        });

        const data = await response.json();
        setLoading(false);

        if (data.success) {
            appendMessageToCurrent(data.answer, 'bot');
        } else {
            addErrorMessage(data.error || '发生未知错误');
        }
    } catch (error) {
        // 主动中止不报错
        if (error.name === 'AbortError') {
            console.log('请求已取消');
            return;
        }
        setLoading(false);
        addErrorMessage('网络错误，请稍后重试');
        console.error(error);
    }
}

// 停止当前请求
function stopCurrentRequest() {
    if (currentAbortController) {
        currentAbortController.abort();
        currentAbortController = null;
    }
    setLoading(false);
}

// 清空当前会话
function clearChat() {
    const conv = getCurrentConversation();
    if (!conv) return;

    conv.messages = [];
    renderConversation(conv);
    fetch('/clear_history', { method: 'POST' }).catch(() => {});
}

// 输入框相关 enter发送
function handleKeyPress(event) {
    if (event.key === 'Enter' ) {
        event.preventDefault();
        if (isRequestPending) {
            stopCurrentRequest();
        } else {
            sendMessage();
        }
    }
}

function autoResizeTextarea() {
    const textarea = document.getElementById('userInput');
    if (!textarea) return;
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
}

// 侧边栏开关
function updateSidebarState() {
    const sidebar = document.getElementById('sidebar');
    const headerLogoBtn = document.getElementById('headerLogoBtn');
    if (!sidebar || !headerLogoBtn) return;

    if (isSidebarCollapsed) {
        // 折叠：侧边栏收起，右上角按钮显示（带 .collapsed，用于 hover 切图标）
        sidebar.classList.add('collapsed');
        headerLogoBtn.classList.add('collapsed');
        headerLogoBtn.style.display = 'flex';
        headerLogoBtn.title = '打开边栏';
    } else {
        // 展开：侧边栏展开，右上角按钮隐藏，只保留左上角侧边栏里的 openai logo
        sidebar.classList.remove('collapsed');
        headerLogoBtn.classList.remove('collapsed');
        headerLogoBtn.style.display = 'none';
        headerLogoBtn.title = '收起边栏';
    }
}

function toggleSidebar() {
    isSidebarCollapsed = !isSidebarCollapsed;
    updateSidebarState();
}

function collapseSidebar() {
    isSidebarCollapsed = true;
    updateSidebarState();
}

// Markdown 简单处理
function formatMarkdown(text) {
    let html = text
        .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/#### ([^\n]+)/g, '<h4>$1</h4>')
        .replace(/### ([^\n]+)/g, '<h3>$1</h3>')
        .replace(/## ([^\n]+)/g, '<h2>$1</h2>')
        .replace(/# ([^\n]+)/g, '<h1>$1</h1>')
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        .replace(/\*([^*]+)\*/g, '<em>$1</em>')
        .replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img alt="$1" src="$2">')
        .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')
        .replace(/\n/g, '<br>');
    return html;
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    const sendBtn = document.getElementById('sendBtn');
    const clearBtn = document.getElementById('clearBtn');
    const userInput = document.getElementById('userInput');
    const headerLogoBtn = document.getElementById('headerLogoBtn');
    const sidebarCollapseBtn = document.getElementById('sidebarCollapseBtn');
    const newChatBtn = document.getElementById('newChatBtn');
    const sidebarLogo = document.getElementById('sidebarLogo');

    if (sendBtn) {
        sendBtn.addEventListener('click', () => {
            if (isRequestPending) {
                stopCurrentRequest();
            } else {
                sendMessage();
            }
        });
    }

    if (clearBtn) clearBtn.addEventListener('click', clearChat);

    if (userInput) {
        userInput.addEventListener('keydown', handleKeyPress);
        userInput.addEventListener('input', autoResizeTextarea);
        autoResizeTextarea();
    }

    if (headerLogoBtn) headerLogoBtn.addEventListener('click', toggleSidebar);
    if (sidebarCollapseBtn) sidebarCollapseBtn.addEventListener('click', collapseSidebar);
    if (newChatBtn) newChatBtn.addEventListener('click', createNewConversation);

    if (sidebarLogo) {
        sidebarLogo.addEventListener('click', createNewConversation);
    }
    // 默认创建一个对话
    createNewConversation();
});
