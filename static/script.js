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

    // 对于 bot 消息，使用 Markdown 渲染
    let messageContent;
    if (type === 'bot') {
        // 配置 marked 选项
        marked.setOptions({
            breaks: true,  // 支持换行
            gfm: true,     // 支持 GitHub Flavored Markdown
            highlight: function(code, lang) {
                // 代码高亮
                if (lang && hljs.getLanguage(lang)) {
                    try {
                        return hljs.highlight(code, { language: lang }).value;
                    } catch (err) {}
                }
                return hljs.highlightAuto(code).value;
            }
        });
        messageContent = marked.parse(content);
    } else {
        // 用户消息保持纯文本，但转义 HTML
        messageContent = content.replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>');
    }

    messageDiv.innerHTML = `
        <div class="message-header">
            <span class="message-icon ${iconClass}">${iconText}</span>
            <span>${headerText}</span>
        </div>
        <div class="message-content markdown-body">${messageContent}</div>
    `;

    chatMessages.appendChild(messageDiv);
    
    // 高亮所有代码块
    messageDiv.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block);
    });
    
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
    const userInput = document.getElementById('userInput');
    
    loadingIndicator.style.display = isLoading ? 'block' : 'none';
    sendBtn.disabled = isLoading;
    userInput.disabled = isLoading;
    
    if (isLoading) {
        sendBtn.textContent = '发送中...';
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.scrollTop = chatMessages.scrollHeight;
    } else {
        sendBtn.textContent = '发送';
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
    input.style.height = 'auto';  // 重置高度

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
            // 读取 data.answer
            addMessage(data.answer, 'bot');
        } else {
            addErrorMessage(data.error || '发生未知错误');
        }
    } catch (error) {
        setLoading(false);
        addErrorMessage('网络错误,请检查连接后重试');
        console.error('Error:', error);
    } finally {
        // 发送后自动聚焦回输入框
        const userInput = document.getElementById('userInput');
        userInput.focus();
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

// Enter 直接发送，Shift+Enter 换行
function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
    // Shift+Enter 允许换行（不做处理，使用默认行为）
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
    
    // 页面加载后自动聚焦
    userInput.focus();
});