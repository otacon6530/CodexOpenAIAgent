using System;

namespace CodexChatExtension.Models
{
    internal sealed class ChatResponseEventArgs : EventArgs
    {
        public ChatResponseEventArgs(ChatResponse response)
        {
            Response = response;
        }

        public ChatResponse Response { get; }
    }
}
