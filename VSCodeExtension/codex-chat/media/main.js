'use strict';

(function () {
    const vscode = acquireVsCodeApi();

    const statusEl = document.getElementById('status');
    const spinnerEl = document.getElementById('spinner');
    const chatLog = document.getElementById('chatLog');
    const debugList = document.getElementById('debugList');
    const debugSection = document.getElementById('debugSection');
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    const toggleDebugButton = document.getElementById('toggleDebug');
    const listToolsButton = document.getElementById('listTools');
    const newSessionButton = document.getElementById('newSession');
    const reconnectButton = document.getElementById('reconnect');

    sendButton.addEventListener('click', onSend);
    messageInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            onSend();
        }
    });
    toggleDebugButton.addEventListener('click', () => vscode.postMessage({ type: 'toggleDebug' }));
    listToolsButton.addEventListener('click', () => vscode.postMessage({ type: 'listTools' }));
    newSessionButton.addEventListener('click', () => vscode.postMessage({ type: 'newSession' }));
    reconnectButton.addEventListener('click', () => vscode.postMessage({ type: 'reconnect' }));

    function onSend() {
        const text = messageInput.value.trim();
        if (!text) {
            return;
        }
        appendEntry('user', text);
        showSpinner(true);
        vscode.postMessage({ type: 'send', content: text });
        messageInput.value = '';
        messageInput.focus();
    }

    function showSpinner(show) {
        if (spinnerEl) {
            spinnerEl.style.display = show ? '' : 'none';
        }
    }

    function appendEntry(kind, text) {
        const entry = document.createElement('div');
        entry.className = `chat-entry ${kind}`;
        entry.textContent = `${labelForKind(kind)} ${text}`;
        chatLog.appendChild(entry);
        chatLog.scrollTop = chatLog.scrollHeight;
    }

    function labelForKind(kind) {
        switch (kind) {
            case 'user':
                return 'You:';
            case 'assistant':
                return 'Assistant:';
            case 'system':
                return '[System]';
            case 'error':
                return '[Error]';
            default:
                return '';
        }
    }

    function addDebugLines(lines) {
        lines.forEach((line) => {
            const item = document.createElement('li');
            item.textContent = line;
            debugList.appendChild(item);
        });
        debugList.parentElement.scrollTop = debugList.parentElement.scrollHeight;
    }

    function setStatus(level, message) {
        statusEl.textContent = message;
        statusEl.className = `status status-${level}`;
        appendEntry(level === 'error' ? 'error' : 'system', message);
    }

    function setControlsEnabled(enabled) {
        [sendButton, toggleDebugButton, listToolsButton, newSessionButton].forEach((button) => {
            button.disabled = !enabled;
        });
        messageInput.disabled = !enabled;
        if (enabled) {
            messageInput.focus();
        }
    }

    function setDebugVisibility(visible) {
        if (!debugSection) {
            return;
        }
        if (visible) {
            debugSection.style.display = '';
            debugSection.removeAttribute('aria-hidden');
            chatLog.style.borderRight = '';
        } else {
            debugSection.style.display = 'none';
            debugSection.setAttribute('aria-hidden', 'true');
            chatLog.style.borderRight = 'none';
        }
    }

    setDebugVisibility(false);

    window.addEventListener('message', (event) => {
        const message = event.data;
        if (!message || !message.type) {
            return;
        }
        switch (message.type) {
            case 'assistant':
                appendEntry('assistant', message.message || '');
                showSpinner(false);
                break;
            case 'system':
                appendEntry('system', message.message || '');
                showSpinner(false);
                break;
            case 'status':
                setStatus(message.level || 'info', message.message || '');
                break;
            case 'debug-lines':
                if (Array.isArray(message.lines)) {
                    addDebugLines(message.lines);
                }
                break;
            case 'controls':
                setControlsEnabled(!!message.enabled);
                break;
            case 'debug-visibility':
                setDebugVisibility(!!message.visible);
                break;
            case 'spinner':
                showSpinner(!!message.show);
                break;
            default:
                break;
        }
    });
})();
