# PowerShell script to send development questions to core.core --planOnly and log Q/A pairs
chcp 65001
$OutputEncoding = [System.Text.Encoding]::UTF8

$questions = @(
    "Summarize what this function/class/file does.",
    "Explain this error message and how to fix it.",
    "Refactor this code for readability/performance.",
    "Write unit tests for this function.",
    "Suggest edge cases for this logic.",
    "Generate a docstring for this function.",
    "Convert this code from Python to JavaScript (or another language).",
    "What libraries can help with X task?",
    "How do I use [library/class/function]?",
    "Find bugs or potential issues in this code.",
    "Suggest a regular expression for this pattern.",
    "What is the time/space complexity of this function?",
    "How can I optimize this loop/algorithm?",
    "What are best practices for [framework/language]?",
    "Generate a SQL query for this data need.",
    "How do I mock this dependency in tests?",
    "What’s the difference between X and Y in this context?",
    "How do I set up CI/CD for this project?",
    "What’s a good commit message for these changes?",
    "How do I fix this merge conflict?"
)

$logFile = "llm_planOnly_log.txt"
Remove-Item $logFile -ErrorAction SilentlyContinue

foreach ($q in $questions) {
    Add-Content $logFile "QUESTION: $q"
    $answer = python -m core.core --planOnly "$q" 2>&1
    Add-Content $logFile "ANSWER:`n$answer`n`n-----------------------------`n"
}

Write-Host "All questions processed. See $logFile for results."
