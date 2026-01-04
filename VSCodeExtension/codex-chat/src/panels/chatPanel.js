'use strict';

const vscode = require('vscode');
const { PythonBridge } = require('../services/pythonBridge');

class ChatPanel {
    static createOrShow(extensionUri) {
        const column = vscode.window.activeTextEditor
            ? vscode.window.activeTextEditor.viewColumn
            : vscode.ViewColumn.One;

        if (ChatPanel.currentPanel) {
            ChatPanel.currentPanel.panel.reveal(column);
            return;
        }

        const panel = vscode.window.createWebviewPanel(
            'codexChat',
            'Codex Chat',
            column || vscode.ViewColumn.One,
            {
                enableScripts: true,
                retainContextWhenHidden: true,
                localResourceRoots: [vscode.Uri.joinPath(extensionUri, 'media')],
            }
        );

        ChatPanel.currentPanel = new ChatPanel(panel, extensionUri);
    }

    static disposeAll() {
        if (ChatPanel.currentPanel) {
            ChatPanel.currentPanel.dispose();
            ChatPanel.currentPanel = undefined;
        }
    }

    constructor(panel, extensionUri) {
        this.panel = panel;
        this.extensionUri = extensionUri;
        this.bridge = undefined;
        this.disposables = [];
        this.bridgeDisposables = [];
        this.debugEnabled = false;
        this.workspacePath = undefined;
        this.pythonPath = undefined;

        this.panel.onDidDispose(() => this.dispose(), null, this.disposables);
        this.panel.webview.onDidReceiveMessage((message) => this.handleWebviewMessage(message), null, this.disposables);

        this.updateWebviewHtml();
        this.startBackend();
    }

    dispose() {
        ChatPanel.currentPanel = undefined;
        if (this.bridge) {
            this.disposeBridgeListeners();
            this.bridge.dispose();
            this.bridge = undefined;
        }
        while (this.disposables.length) {
            const disposable = this.disposables.pop();
            try {
                if (disposable) {
                    disposable.dispose();
                }
            } catch (err) {
                console.error('Failed to dispose resource', err);
            }
        }
        this.panel.dispose();
    }

    updateWebviewHtml() {
        const webview = this.panel.webview;
        const scriptUri = webview.asWebviewUri(vscode.Uri.joinPath(this.extensionUri, 'media', 'main.js'));
        const styleUri = webview.asWebviewUri(vscode.Uri.joinPath(this.extensionUri, 'media', 'styles.css'));
        const nonce = getNonce();

        webview.html = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src ${webview.cspSource} https:; script-src 'nonce-${nonce}'; style-src ${webview.cspSource};">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="${styleUri}">
    <title>Codex Chat</title>
</head>
<body>
    <div class="container">
        <header class="toolbar">
            <span id="status" class="status">Connecting…</span>
            <div class="actions">
                <button id="toggleDebug" disabled>Toggle Debug</button>
                <button id="listTools" disabled>List Tools</button>
                <button id="newSession" disabled>New Session</button>
                <button id="reconnect">Reconnect</button>
            </div>
        </header>
        <main class="content">
            <section class="chat" id="chatLog"></section>
            <section class="debug" id="debugSection">
                <h2>Debug</h2>
                <ul id="debugList"></ul>
            </section>
        </main>
        <footer class="composer">
            <input type="text" id="messageInput" placeholder="Message the Codex agent" />
            <button id="sendButton" disabled>Send</button>
        </footer>
    </div>
    <script nonce="${nonce}" src="${scriptUri}"></script>
</body>
</html>`;
    }

    async startBackend() {
        const config = vscode.workspace.getConfiguration('codexChat');
        const configuredWorkspace = (config.get('workspacePath') || '').trim();
        this.workspacePath = configuredWorkspace || this.resolveWorkspacePath();
        this.pythonPath = (config.get('pythonPath') || 'python').trim() || 'python';

        this.setControlsEnabled(false);
        this.postToWebview({ type: 'debug-visibility', visible: false });

        if (!this.workspacePath) {
            this.postToWebview({ type: 'status', level: 'error', message: 'Unable to determine workspace path. Set codexChat.workspacePath in settings.' });
            this.setControlsEnabled(false);
            return;
        }

        this.postToWebview({ type: 'status', level: 'info', message: `Starting backend in ${this.workspacePath}…` });

        if (this.bridge) {
            this.disposeBridgeListeners();
            this.bridge.dispose();
            this.bridge = undefined;
        }
        this.bridge = new PythonBridge();

        this.bridgeDisposables.push(this.bridge.onMessage((payload) => this.handleBridgeMessage(payload)));
        this.bridgeDisposables.push(this.bridge.onError((message) => this.postToWebview({ type: 'debug-lines', lines: [message] })));
        this.bridgeDisposables.push(this.bridge.onExit(({ code, signal }) => {
            this.postToWebview({ type: 'status', level: 'warning', message: `Backend exited (code: ${code ?? 'null'}, signal: ${signal ?? 'null'}).` });
            this.setControlsEnabled(false);
            this.postToWebview({ type: 'debug-visibility', visible: false });
        }));

        try {
            await this.bridge.start(this.workspacePath, this.pythonPath);
            this.postToWebview({ type: 'status', level: 'info', message: 'Backend process started. Waiting for ready event…' });
        } catch (error) {
            const message = error && error.message ? error.message : String(error);
            this.postToWebview({ type: 'status', level: 'error', message: `Failed to launch backend: ${message}` });
            this.setControlsEnabled(false);
        }
    }

    resolveWorkspacePath() {
        const folders = vscode.workspace.workspaceFolders;
        if (folders && folders.length > 0) {
            return folders[0].uri.fsPath;
        }
        const envPath = process.env.CODEX_AGENT_ROOT;
        if (envPath && envPath.trim().length > 0) {
            return envPath.trim();
        }
        return undefined;
    }

    async handleWebviewMessage(message) {
        if (!message || !message.type) {
            return;
        }

        switch (message.type) {
            case 'send':
                if (!this.bridge || !this.bridge.isRunning) {
                    this.postToWebview({ type: 'status', level: 'error', message: 'Backend is not running. Click reconnect.' });
                    return;
                }
                if (message.content && message.content.trim().length > 0) {
                    try {
                        await this.bridge.send({ type: 'message', content: message.content });
                    } catch (error) {
                        this.postToWebview({ type: 'status', level: 'error', message: `Failed to send message: ${error.message || error}` });
                    }
                }
                break;
            case 'toggleDebug':
                if (this.bridge && this.bridge.isRunning) {
                    this.bridge.send({ type: 'toggle_debug' }).catch((error) => {
                        this.postToWebview({ type: 'status', level: 'error', message: `Failed to toggle debug: ${error.message || error}` });
                    });
                }
                break;
            case 'listTools':
                if (this.bridge && this.bridge.isRunning) {
                    this.bridge.send({ type: 'message', content: '!tools' }).catch((error) => {
                        this.postToWebview({ type: 'status', level: 'error', message: `Failed to request tools: ${error.message || error}` });
                    });
                }
                break;
            case 'newSession':
                if (this.bridge && this.bridge.isRunning) {
                    this.bridge.send({ type: 'message', content: '!new' }).catch((error) => {
                        this.postToWebview({ type: 'status', level: 'error', message: `Failed to reset session: ${error.message || error}` });
                    });
                }
                break;
            case 'reconnect':
                await this.restartBackend();
                break;
            default:
                break;
        }
    }

    async restartBackend() {
        this.setControlsEnabled(false);
        this.postToWebview({ type: 'status', level: 'info', message: 'Restarting backend…' });
        if (this.bridge) {
            await this.bridge.stop().catch(() => undefined);
        }
        await this.startBackend();
    }

    handleBridgeMessage(message) {
        if (!message || !message.type) {
            return;
        }

        if (typeof message.debug === 'boolean') {
            this.debugEnabled = message.debug;
            this.postToWebview({ type: 'debug-visibility', visible: this.debugEnabled });
            this.postToWebview({ type: 'status', level: 'info', message: `Debug metrics ${this.debugEnabled ? 'enabled' : 'disabled'}.` });
        }

        if (Array.isArray(message.debug) && message.debug.length > 0) {
            this.postToWebview({ type: 'debug-lines', lines: message.debug });
        }

        if (Array.isArray(message.extras) && message.extras.length > 0) {
            message.extras.forEach((line) => {
                this.postToWebview({ type: 'system', message: line });
            });
        }

        switch (message.type) {
            case 'ready':
                this.setControlsEnabled(true);
                this.postToWebview({ type: 'status', level: 'info', message: 'Backend ready. Say hello!' });
                break;
            case 'assistant':
                this.postToWebview({ type: 'assistant', message: message.content || '' });
                break;
            case 'notification':
                this.postToWebview({ type: 'system', message: message.content || '' });
                break;
            case 'error':
                this.postToWebview({ type: 'status', level: 'error', message: message.content || 'Unknown backend error.' });
                break;
            default:
                if (message.content) {
                    this.postToWebview({ type: 'system', message: message.content });
                }
                break;
        }
    }

    postToWebview(payload) {
        try {
            this.panel.webview.postMessage(payload);
        } catch (err) {
            console.error('Failed to post message to webview', err);
        }
    }

    setControlsEnabled(enabled) {
        this.postToWebview({ type: 'controls', enabled });
    }

    disposeBridgeListeners() {
        while (this.bridgeDisposables.length) {
            const disposable = this.bridgeDisposables.pop();
            if (disposable && typeof disposable.dispose === 'function') {
                try {
                    disposable.dispose();
                } catch (err) {
                    console.error('Failed to dispose listener', err);
                }
            }
        }
    }
}

ChatPanel.currentPanel = undefined;

function getNonce() {
    const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let text = '';
    for (let i = 0; i < 32; i += 1) {
        text += possible.charAt(Math.floor(Math.random() * possible.length));
    }
    return text;
}

module.exports = {
    ChatPanel,
};
