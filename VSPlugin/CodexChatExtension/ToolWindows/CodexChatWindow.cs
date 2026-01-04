using System.Threading.Tasks;
using Community.VisualStudio.Toolkit;
using Microsoft.VisualStudio.Shell;

namespace CodexChatExtension.ToolWindows
{
    internal class CodexChatWindow : ToolkitToolWindow<CodexChatWindow>
    {
        public override string GetTitle(int toolWindowId) => "Codex Chat";

        protected override async Task InitializeAsync()
        {
            await ThreadHelper.JoinableTaskFactory.SwitchToMainThreadAsync();
            Content = new CodexChatWindowControl();
        }
    }
}
