title LoopCLI - content-generator
cd /d "D:\loopcli\content-generator"
set IS_SANDBOX=1
type "D:\loopcli\content-generator\_debug_prompt.txt" | "C:\Users\Administrator\AppData\Roaming\npm\claude.cmd" --print --dangerously-skip-permissions
pause
