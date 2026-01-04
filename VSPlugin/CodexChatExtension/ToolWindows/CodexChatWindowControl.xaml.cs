using System;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using CodexChatExtension.Models;
using CodexChatExtension.Services;
using Microsoft.VisualStudio.Shell;

namespace CodexChatExtension.ToolWindows
{
    public partial class CodexChatWindowControl : UserControl
    {
        private readonly PythonChatClient _client = new();
        private bool _isConnected;
        private bool _debugEnabled;
        private readonly StringBuilder _chatBuilder = new();

        public CodexChatWindowControl()
        {
            InitializeComponent();
            WorkspacePath.Text = Environment.GetEnvironmentVariable("CODEX_AGENT_ROOT") ?? string.Empty;
            PythonPath.Text = Environment.GetEnvironmentVariable("PYTHON") ?? "python";

            _client.ResponseReceived += OnResponseReceived;
            _client.ErrorReceived += OnErrorReceived;
        }

        private void ConnectButton_OnClick(object sender, RoutedEventArgs e)
        {
            ThreadHelper.JoinableTaskFactory.RunAsync(async () =>
            {
                try
                {
                    if (_isConnected)
                    {
                        await DisconnectAsync().ConfigureAwait(false);
                    }
                    else
                    {
                        await ConnectAsync().ConfigureAwait(false);
                    }
                }
                catch (Exception ex)
                {
                    await ThreadHelper.JoinableTaskFactory.SwitchToMainThreadAsync();
                    AppendError($"Unexpected error: {ex.Message}");
                }
            }).FireAndForget();
        }

        private async Task ConnectAsync()
        {
            var workspace = WorkspacePath.Text.Trim();
            var python = PythonPath.Text.Trim();

            try
            {
                await _client.StartAsync(workspace, python);
                _isConnected = true;
                AppendSystem($"Connected. Workspace: {workspace}");
                UpdateControls();
            }
            catch (Exception ex)
            {
                AppendError($"Failed to connect: {ex.Message}");
            }
        }

        private async Task DisconnectAsync()
        {
            try
            {
                await _client.StopAsync();
            }
            catch (Exception ex)
            {
                AppendError($"Failed to disconnect cleanly: {ex.Message}");
            }
            finally
            {
                _isConnected = false;
                AppendSystem("Disconnected.");
                UpdateControls();
            }
        }

        private void SendButton_OnClick(object sender, RoutedEventArgs e)
        {
            ThreadHelper.JoinableTaskFactory.RunAsync(async () =>
            {
                try
                {
                    await SendCurrentMessageAsync().ConfigureAwait(false);
                }
                catch (Exception ex)
                {
                    await ThreadHelper.JoinableTaskFactory.SwitchToMainThreadAsync();
                    AppendError($"Unexpected error: {ex.Message}");
                }
            }).FireAndForget();
        }

        private async Task SendCurrentMessageAsync()
        {
            if (!_isConnected)
            {
                AppendSystem("Not connected.");
                return;
            }

            var message = MessageInput.Text.Trim();
            if (string.IsNullOrEmpty(message))
            {
                return;
            }

            AppendUser(message);
            MessageInput.Clear();

            try
            {
                await _client.SendAsync(new { type = "message", content = message });
            }
            catch (Exception ex)
            {
                AppendError($"Failed to send message: {ex.Message}");
            }
        }

        private void DebugToggleButton_OnClick(object sender, RoutedEventArgs e)
        {
            if (!_isConnected)
            {
                return;
            }

            ThreadHelper.JoinableTaskFactory.RunAsync(async () =>
            {
                try
                {
                    await _client.SendAsync(new { type = "toggle_debug" }).ConfigureAwait(false);
                }
                catch (Exception ex)
                {
                    await ThreadHelper.JoinableTaskFactory.SwitchToMainThreadAsync();
                    AppendError($"Failed to toggle debug metrics: {ex.Message}");
                }
            }).FireAndForget();
        }

        private void ToolsButton_OnClick(object sender, RoutedEventArgs e)
        {
            if (!_isConnected)
            {
                return;
            }

            ThreadHelper.JoinableTaskFactory.RunAsync(async () =>
            {
                try
                {
                    await _client.SendAsync(new { type = "message", content = "!tools" }).ConfigureAwait(false);
                }
                catch (Exception ex)
                {
                    await ThreadHelper.JoinableTaskFactory.SwitchToMainThreadAsync();
                    AppendError($"Failed to request tools: {ex.Message}");
                }
            }).FireAndForget();
        }

        private void NewSessionButton_OnClick(object sender, RoutedEventArgs e)
        {
            if (!_isConnected)
            {
                return;
            }

            ThreadHelper.JoinableTaskFactory.RunAsync(async () =>
            {
                try
                {
                    await _client.SendAsync(new { type = "message", content = "!new" }).ConfigureAwait(false);
                }
                catch (Exception ex)
                {
                    await ThreadHelper.JoinableTaskFactory.SwitchToMainThreadAsync();
                    AppendError($"Failed to reset session: {ex.Message}");
                }
            }).FireAndForget();
        }

        private void OnResponseReceived(object? sender, ChatResponseEventArgs e)
        {
            ThreadHelper.JoinableTaskFactory.RunAsync(async () =>
            {
                await ThreadHelper.JoinableTaskFactory.SwitchToMainThreadAsync();
                HandleResponse(e.Response);
            }).FireAndForget();
        }

        private void HandleResponse(ChatResponse response)
        {
            if (response.DebugEnabled.HasValue)
            {
                _debugEnabled = response.DebugEnabled.Value;
                AppendSystem($"Debug metrics {(_debugEnabled ? "enabled" : "disabled")}." );
            }

            switch (response.Type)
            {
                case "ready":
                    if (response.DebugEnabled.HasValue)
                    {
                        _debugEnabled = response.DebugEnabled.Value;
                    }
                    AppendSystem("Backend ready.");
                    break;
                case "assistant":
                    AppendAssistant(response.Content ?? string.Empty);
                    if (response.Extras.Any())
                    {
                        foreach (var extra in response.Extras)
                        {
                            AppendSystem(extra);
                        }
                    }
                    break;
                case "notification":
                    AppendSystem(response.Content ?? string.Empty);
                    break;
                case "error":
                    AppendError(response.Content ?? string.Empty);
                    break;
                default:
                    AppendSystem(response.Content ?? string.Empty);
                    break;
            }

            if (response.Debug.Any())
            {
                foreach (var line in response.Debug)
                {
                    DebugList.Items.Add(line);
                }
                if (DebugList.Items.Count > 0)
                {
                    DebugList.ScrollIntoView(DebugList.Items[DebugList.Items.Count - 1]);
                }
            }
        }

        private void OnErrorReceived(object? sender, string e)
        {
            ThreadHelper.JoinableTaskFactory.RunAsync(async () =>
            {
                await ThreadHelper.JoinableTaskFactory.SwitchToMainThreadAsync();
                AppendError(e);
            }).FireAndForget();
        }

        private void AppendUser(string message)
        {
            _chatBuilder.AppendLine($"You: {message}");
            ChatLog.Text = _chatBuilder.ToString();
            ChatLog.ScrollToEnd();
        }

        private void AppendAssistant(string message)
        {
            _chatBuilder.AppendLine($"Assistant: {message}");
            ChatLog.Text = _chatBuilder.ToString();
            ChatLog.ScrollToEnd();
        }

        private void AppendSystem(string message)
        {
            _chatBuilder.AppendLine($"[System] {message}");
            ChatLog.Text = _chatBuilder.ToString();
            ChatLog.ScrollToEnd();
        }

        private void AppendError(string message)
        {
            _chatBuilder.AppendLine($"[Error] {message}");
            ChatLog.Text = _chatBuilder.ToString();
            ChatLog.ScrollToEnd();
        }

        private void UpdateControls()
        {
            ConnectButton.Content = _isConnected ? "Disconnect" : "Connect";
            SendButton.IsEnabled = _isConnected;
            DebugToggleButton.IsEnabled = _isConnected;
            ToolsButton.IsEnabled = _isConnected;
            NewSessionButton.IsEnabled = _isConnected;
        }

        private void CodexChatWindowControl_OnUnloaded(object sender, RoutedEventArgs e)
        {
            if (_isConnected)
            {
                Microsoft.VisualStudio.Shell.ThreadHelper.JoinableTaskFactory.Run(() => DisconnectAsync());
            }
            _client.Dispose();
        }
    }
}
