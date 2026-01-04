using System.ComponentModel.Design;
using System.Threading.Tasks;
using Community.VisualStudio.Toolkit;
using Microsoft.VisualStudio.Shell;

namespace CodexChatExtension.Commands
{
    [Command(PackageIds.OpenChatWindowCommand)]
    internal sealed class OpenChatWindowCommand : BaseCommand<OpenChatWindowCommand>
    {
        protected override async Task ExecuteAsync(OleMenuCmdEventArgs e)
        {
            await ToolWindow.ShowAsync<ToolWindows.CodexChatWindow>();
        }
    }
}
