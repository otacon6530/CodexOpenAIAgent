using System;
using System.Runtime.InteropServices;
using System.Threading;
using System.Threading.Tasks;
using Community.VisualStudio.Toolkit;
using Microsoft.VisualStudio.Shell;
using Task = System.Threading.Tasks.Task;

namespace CodexChatExtension
{
    [PackageRegistration(UseManagedResourcesOnly = true, AllowsBackgroundLoading = true)]
    [InstalledProductRegistration("Codex Chat Extension", "Chat with the Codex agent.", "1.0")]
    [ProvideMenuResource("Menus.ctmenu", 1)]
    [ProvideToolWindow(typeof(ToolWindows.CodexChatWindow))]
    [Guid(PackageGuidString)]
    public sealed class CodexChatExtensionPackage : AsyncPackage
    {
        public const string PackageGuidString = "2DD48F86-5C2F-4E56-8F6E-5F0C0E82F1BE";

        protected override async Task InitializeAsync(CancellationToken cancellationToken, IProgress<ServiceProgressData> progress)
        {
            await this.RegisterCommandsAsync();
        }
    }
}
