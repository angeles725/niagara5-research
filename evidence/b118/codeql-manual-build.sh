#!/usr/bin/env bash
/home/linuxbrew/.linuxbrew/opt/openjdk@25/bin/javac -nowarn -proc:none -d /tmp/claude-1000/-home-cristian-niagara-research/4d9a109b-8d01-4d7d-acb1-4d2d675d1b66/scratchpad/b118/m5/out2 -cp "$(cat /tmp/claude-1000/-home-cristian-niagara-research/4d9a109b-8d01-4d7d-acb1-4d2d675d1b66/scratchpad/b118/m5/libs.cp)" $(find /tmp/claude-1000/-home-cristian-niagara-research/4d9a109b-8d01-4d7d-acb1-4d2d675d1b66/scratchpad/b118/m5/src2 -name '*.java')
exit 0
