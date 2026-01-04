using System;
using System.Threading.Tasks;
using Microsoft.VisualStudio.Threading;

namespace CodexChatExtension.Services
{
    internal static class JoinableTaskExtensions
    {
        public static void FireAndForget(this JoinableTask task, Action<Exception>? onError = null)
        {
            task.Task.ContinueWith(t => onError?.Invoke(t.Exception!), TaskContinuationOptions.OnlyOnFaulted | TaskContinuationOptions.ExecuteSynchronously);
        }
    }
}
