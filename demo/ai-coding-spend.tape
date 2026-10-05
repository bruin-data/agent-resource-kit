# Try ai-coding-spend in 2 minutes: the ai-coding-usage template on fake data.
#
# Recorded with Bruin CLI v0.11.767 and VHS. Re-render from this folder:
#
#   python3 ../resources/coding-agent-workflows/record-terminal-demo/scripts/render_demo.py ai-coding-spend.tape
#
# Hidden setup stands in for step 1's `git clone`: it links this working tree
# into a fresh folder as agent-resource-kit, so the recording shows the sample
# data at this commit rather than whatever is on GitHub.

Output ai-coding-spend.gif

Set Shell bash
Set FontSize 18
Set Width 1280
Set Height 760
Set Margin 0
Set Padding 28
Set LineHeight 1.15
Set TypingSpeed 25ms
Set Framerate 30
Set CursorBlink false
Set Theme "GitHub Dark"

Hide
Type "export KIT=$(git rev-parse --show-toplevel)" Enter
Type "rm -rf /tmp/try-ai-coding-spend && mkdir /tmp/try-ai-coding-spend && cd /tmp/try-ai-coding-spend" Enter
Type "ln -s $KIT agent-resource-kit" Enter
Type "unset NO_COLOR && export TERM=xterm-256color CLICOLOR=1" Enter
# \[ \] mark the colour codes as zero-width, so readline wraps the long query
# line correctly.
Type `export PS1="\n\[$(tput setaf 6)\]> \[$(tput sgr0)\]"` Enter
Type "clear" Enter
Show

Type "# 1. The real ai-coding-usage template" Enter
Type "bruin init ai-coding-usage ai-coding-demo" Enter
Sleep 2s

Type "# 2. Fake Claude Code and Cursor CSVs instead of the API assets" Enter
Type "cp agent-resource-kit/resources/startup-data-kit/ai-coding-spend/sample-data/*.{asset.yml,csv} bruin/ai-coding-demo/assets/raw/" Enter
Sleep 1s
Type "clear" Enter

Type "# 3. Build every table on DuckDB, then query one" Enter
Type "cd bruin" Enter
Type "bruin run ai-coding-demo --full-refresh --workers 1 --start-date 2026-09-14 --end-date 2026-09-27" Enter
Sleep 4s
Type "clear" Enter
Type@15ms `bruin query -c duckdb-default -q "SELECT strftime(date_trunc('week', usage_date), '%Y-%m-%d') AS week, platform, CAST(SUM(total_tokens) AS BIGINT) AS tokens, ROUND(SUM(estimated_cost_usd), 2) AS est_cost_usd FROM marts.ai_coding_usage_by_user_day GROUP BY ALL ORDER BY ALL"` Enter
Sleep 6s
