// 添加消息到聊天区域
function addMessage(content, type = 'bot') {
    const chatMessages = document.getElementById('chatMessages');
    
    // 移除欢迎消息
    const welcomeMsg = chatMessages.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;

    const iconClass = type === 'user' ? 'user-icon' : 'bot-icon';
    const iconText = type === 'user' ? '👤' : '🤖';
    const headerText = type === 'user' ? '您' : 'AI助手';

    messageDiv.innerHTML = `
        <div class="message-header">
            <span class="message-icon ${iconClass}">${iconText}</span>
            <span>${headerText}</span>
        </div>
        <div class="message-content">${content}</div>
    `;

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 添加错误消息
function addErrorMessage(content) {
    const chatMessages = document.getElementById('chatMessages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message error-message';

    messageDiv.innerHTML = `
        <div class="message-header">
            <span class="message-icon" style="background: #ff4d4f;">⚠️</span>
            <span>系统提示</span>
        </div>
        <div class="message-content">${content}</div>
    `;

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 显示/隐藏加载状态
function setLoading(isLoading) {
    const loadingIndicator = document.getElementById('loadingIndicator');
    const sendBtn = document.getElementById('sendBtn');
    
    loadingIndicator.style.display = isLoading ? 'block' : 'none';
    sendBtn.disabled = isLoading;
    
    if (isLoading) {
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

// 发送消息
async function sendMessage() {
    const input = document.getElementById('userInput');
    const message = input.value.trim();

    if (!message) {
        return;
    }

    // 显示用户消息
    addMessage(message, 'user');
    input.value = '';

    // 显示加载状态
    setLoading(true);

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });

        const data = await response.json();

        // 隐藏加载状态
        setLoading(false);

        if (data.success) {
            addMessage(data.response, 'bot');
        } else {
            addErrorMessage(data.error || '发生未知错误');
        }
    } catch (error) {
        setLoading(false);
        addErrorMessage('网络错误,请检查连接后重试');
        console.error('Error:', error);
    }
}

// 清空对话
function clearChat() {
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.innerHTML = `
        <div class="welcome-message">
            <div class="welcome-icon">💬</div>
            <div class="welcome-title">对话窗口</div>
            <div class="welcome-text">
                您可以在下方输入框中提出安全相关的问题<br>
                例如: 什么是SQL注入? 如何防御XSS攻击?
            </div>
        </div>
    `;
}

// 处理回车键
function handleKeyPress(event) {
    // Ctrl+Enter 或 Cmd+Enter 发送消息
    if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
        event.preventDefault();
        sendMessage();
    }
}

// 自动调整输入框高度
function autoResizeTextarea() {
    const textarea = document.getElementById('userInput');
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 绑定发送按钮
    document.getElementById('sendBtn').addEventListener('click', sendMessage);
    
    // 绑定清空按钮
    document.getElementById('clearBtn').addEventListener('click', clearChat);
    
    // 绑定输入框事件
    const userInput = document.getElementById('userInput');
    userInput.addEventListener('keydown', handleKeyPress);
    userInput.addEventListener('input', autoResizeTextarea);
});