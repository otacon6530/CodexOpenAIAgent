using System;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using CodexChatExtension.Models;

namespace CodexChatExtension.Services
{
    internal sealed class PythonChatClient : IDisposable
    {
        private readonly SemaphoreSlim _writeLock = new(1, 1);
        private Process? _process;
        private CancellationTokenSource? _readerCts;
        private Task? _readerTask;
        private StreamWriter? _stdin;

        public event EventHandler<ChatResponseEventArgs>? ResponseReceived;
        public event EventHandler<string>? ErrorReceived;

        public bool IsConnected => _process != null && !_process.HasExited;

        public async Task StartAsync(string workspacePath, string pythonExecutable, CancellationToken cancellationToken = default)
        {
            if (IsConnected)
            {
                return;
            }

            if (string.IsNullOrWhiteSpace(workspacePath))
            {
                throw new ArgumentException("Workspace path is required.", nameof(workspacePath));
            }

            if (!Directory.Exists(workspacePath))
            {
                throw new DirectoryNotFoundException($"Workspace path '{workspacePath}' does not exist.");
            }

            pythonExecutable = string.IsNullOrWhiteSpace(pythonExecutable) ? "python" : pythonExecutable;

            var startInfo = new ProcessStartInfo
            {
                FileName = pythonExecutable,
                Arguments = "-u -m core.chat_process",
                WorkingDirectory = workspacePath,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                RedirectStandardInput = true,
                UseShellExecute = false,
                CreateNoWindow = true,
                StandardOutputEncoding = Encoding.UTF8,
                StandardErrorEncoding = Encoding.UTF8
            };

            _process = new Process { StartInfo = startInfo, EnableRaisingEvents = true };

            try
            {
                _process.Start();
            }
            catch (Exception ex)
            {
                _process?.Dispose();
                _process = null;
                throw new InvalidOperationException("Failed to start Python chat process.", ex);
            }

            _stdin = _process.StandardInput;
            _stdin.AutoFlush = true;

            _process.ErrorDataReceived += (_, args) =>
            {
                if (!string.IsNullOrEmpty(args.Data))
                {
                    ErrorReceived?.Invoke(this, args.Data);
                }
            };
            _process.BeginErrorReadLine();

            _readerCts = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
            _readerTask = Task.Run(() => ReadLoopAsync(_readerCts.Token), _readerCts.Token);
        }

        private async Task ReadLoopAsync(CancellationToken cancellationToken)
        {
            if (_process == null)
            {
                return;
            }

            while (!cancellationToken.IsCancellationRequested && !_process.HasExited)
            {
                var line = await _process.StandardOutput.ReadLineAsync().ConfigureAwait(false);
                if (line == null)
                {
                    break;
                }
                line = line.Trim();
                if (line.Length == 0)
                {
                    continue;
                }
                try
                {
                    var response = ParseResponse(line);
                    ResponseReceived?.Invoke(this, new ChatResponseEventArgs(response));
                }
                catch (Exception ex)
                {
                    ErrorReceived?.Invoke(this, $"Failed to parse response: {ex.Message}");
                }
            }
        }

        private static ChatResponse ParseResponse(string json)
        {
            using var document = JsonDocument.Parse(json);
            var root = document.RootElement;
            var response = new ChatResponse
            {
                Type = root.GetProperty("type").GetString() ?? string.Empty,
                Content = root.TryGetProperty("content", out var content) ? content.GetString() : null,
            };

            if (root.TryGetProperty("debug", out var debugElement))
            {
                switch (debugElement.ValueKind)
                {
                    case JsonValueKind.Array:
                        response.Debug = DeserializeStringArray(debugElement);
                        break;
                    case JsonValueKind.True:
                        response.DebugEnabled = true;
                        break;
                    case JsonValueKind.False:
                        response.DebugEnabled = false;
                        break;
                }
            }

            if (root.TryGetProperty("extras", out var extrasElement) && extrasElement.ValueKind == JsonValueKind.Array)
            {
                response.Extras = DeserializeStringArray(extrasElement);
            }

            return response;
        }

        private static string[] DeserializeStringArray(JsonElement element)
        {
            var result = new string[element.GetArrayLength()];
            var index = 0;
            foreach (var item in element.EnumerateArray())
            {
                result[index++] = item.GetString() ?? string.Empty;
            }
            return result;
        }

        public async Task SendAsync(object payload, CancellationToken cancellationToken = default)
        {
            if (_stdin == null)
            {
                throw new InvalidOperationException("Python process is not running.");
            }

            var json = JsonSerializer.Serialize(payload);
            await _writeLock.WaitAsync(cancellationToken).ConfigureAwait(false);
            try
            {
                await _stdin.WriteLineAsync(json).ConfigureAwait(false);
            }
            finally
            {
                _writeLock.Release();
            }
        }

        public async Task StopAsync(CancellationToken cancellationToken = default)
        {
            if (!IsConnected)
            {
                return;
            }

            try
            {
                await SendAsync(new { type = "shutdown" }, cancellationToken).ConfigureAwait(false);
            }
            catch
            {
            }

            if (_readerCts != null)
            {
                _readerCts.Cancel();
            }

            if (_readerTask != null)
            {
                try
                {
                    await Task.WhenAny(_readerTask, Task.Delay(1000, cancellationToken)).ConfigureAwait(false);
                }
                catch
                {
                }
            }

            if (_stdin != null)
            {
                await _stdin.DisposeAsync().ConfigureAwait(false);
                _stdin = null;
            }

            if (_process != null && !_process.HasExited)
            {
                _process.Kill(entireProcessTree: true);
            }
            _process?.Dispose();
            _process = null;
        }

        public void Dispose()
        {
            _readerCts?.Cancel();
            _readerTask?.Wait(250);
            _stdin?.Dispose();
            _process?.Dispose();
            _writeLock.Dispose();
        }
    }
}
