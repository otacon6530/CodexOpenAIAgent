using System.Collections.Generic;

namespace CodexChatExtension.Models
{
    internal class ChatResponse
    {
        public string Type { get; set; } = string.Empty;
        public string? Content { get; set; }
        public IReadOnlyList<string> Debug { get; set; } = System.Array.Empty<string>();
        public IReadOnlyList<string> Extras { get; set; } = System.Array.Empty<string>();
        public bool? DebugEnabled { get; set; }
    }
}
