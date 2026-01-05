'use strict';

(function () {
    const vscode = acquireVsCodeApi();

    const statusEl = document.getElementById('status');
    const spinnerEl = document.getElementById('spinner');
    const chatLog = document.getElementById('chatLog');
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

    function setSendEnabled(enabled) {
        sendButton.disabled = !enabled;
        messageInput.disabled = !enabled;
    }

    function onSend() {
        const text = messageInput.value.trim();
        if (!text) {
            return;
        }
        appendEntry('user', text);
        showSpinner(true);
        setSendEnabled(false);
        vscode.postMessage({ type: 'send', content: text });
        messageInput.value = '';
    }

    function showSpinner(show) {
        if (spinnerEl) {
            spinnerEl.style.display = show ? '' : 'none';
        }
    }

    function escapeHtml(str) {
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function escapeAttribute(str) {
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function formatInline(text) {
        let escaped = escapeHtml(text);
        escaped = escaped.replace(/`([^`]+)`/g, (_, code) => `<code>${code}</code>`);
        escaped = escaped.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        escaped = escaped.replace(/__(.+?)__/g, '<strong>$1</strong>');
        escaped = escaped.replace(/\*(.+?)\*/g, '<em>$1</em>');
        escaped = escaped.replace(/_(.+?)_/g, '<em>$1</em>');
        escaped = escaped.replace(/\[([^\]]+)]\(([^)]+)\)/g, (_, label, url) => `<a href="${escapeAttribute(url)}" target="_blank" rel="noreferrer noopener">${label}</a>`);
        return escaped;
    }

    function renderMarkdown(text) {
        const lines = text.replace(/\r/g, '').split('\n');
        const html = [];
        let inCodeBlock = false;
        let codeLines = [];
        let listType;

        const closeList = () => {
            if (listType) {
                html.push(`</${listType}>`);
                listType = undefined;
            }
        };

        lines.forEach((line) => {
            if (line.trim().startsWith('```')) {
                if (!inCodeBlock) {
                    inCodeBlock = true;
                    codeLines = [];
                } else {
                    html.push(`<pre><code>${escapeHtml(codeLines.join('\n'))}</code></pre>`);
                    inCodeBlock = false;
                }
                return;
            }

            if (inCodeBlock) {
                codeLines.push(line);
                return;
            }

            const trimmed = line.trim();

            if (!trimmed) {
                closeList();
                html.push('<br>');
                return;
            }

            if (trimmed === '---') {
                closeList();
                html.push('<hr>');
                return;
            }

            const headingMatch = trimmed.match(/^(#{1,6})\s+(.*)$/);
            if (headingMatch) {
                closeList();
                const level = headingMatch[1].length;
                html.push(`<h${level}>${formatInline(headingMatch[2])}</h${level}>`);
                return;
            }

            const unorderedMatch = trimmed.match(/^[-*]\s+(.*)$/);
            if (unorderedMatch) {
                if (listType !== 'ul') {
                    closeList();
                    listType = 'ul';
                    html.push('<ul>');
                }
                html.push(`<li>${formatInline(unorderedMatch[1])}</li>`);
                return;
            }

            const orderedMatch = trimmed.match(/^\d+\.\s+(.*)$/);
            if (orderedMatch) {
                if (listType !== 'ol') {
                    closeList();
                    listType = 'ol';
                    html.push('<ol>');
                }
                html.push(`<li>${formatInline(orderedMatch[1])}</li>`);
                return;
            }

            closeList();
            html.push(`<p>${formatInline(trimmed)}</p>`);
        });

        if (inCodeBlock) {
            html.push(`<pre><code>${escapeHtml(codeLines.join('\n'))}</code></pre>`);
        }
        closeList();
        return html.join('');
    }

    function appendEntry(kind, text) {
        const entry = document.createElement('div');
        entry.className = `chat-entry ${kind}`;
        let html;
        if (kind === 'assistant' || kind === 'system') {
            html = `<span class="chat-label">${labelForKind(kind)}</span> ${renderMarkdown(text || '')}`;
        } else {
            html = `<span class="chat-label">${labelForKind(kind)}</span> ${formatInline(text || '').replace(/\n/g, '<br>')}`;
        }
        entry.innerHTML = html;
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


    window.addEventListener('message', (event) => {
        const message = event.data;
        if (!message || !message.type) {
            return;
        }
        switch (message.type) {
            case 'assistant':
                appendEntry('assistant', message.message || '');
                showSpinner(false);
                setSendEnabled(true);
                break;
            case 'system':
                appendEntry('system', message.message || '');
                showSpinner(false);
                setSendEnabled(true);
                break;
            case 'status':
                setStatus(message.level || 'info', message.message || '');
                break;
            case 'spinner':
                showSpinner(!!message.show);
                break;
            case 'controls':
                setControlsEnabled(!!message.enabled);
                break;
            default:
                break;
        }
    });
})();
