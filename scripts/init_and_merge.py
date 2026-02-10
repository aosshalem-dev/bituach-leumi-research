#!/usr/bin/env python3
import os, time, subprocess, sys

PROJECT_DIR = '/Users/zvishalem/Downloads/bituach_leumi_research'
REPORTS_DIR = os.path.join(PROJECT_DIR, 'reports')
CHAPTERS_1_3 = os.path.join(REPORTS_DIR, 'chapters_1_3.md')
CHAPTERS_4_5 = os.path.join(REPORTS_DIR, 'chapters_4_5.md')
CHAPTERS_6_7 = os.path.join(REPORTS_DIR, 'chapters_6_7.md')
FULL_PAPER = os.path.join(REPORTS_DIR, 'full_paper.md')

TITLE_PAGE = u"""# מי מבוטח בביטוח הלאומי?
## מחקר משפטי מקיף
### פברואר 2026
---

"""

def run(cmd, cwd=PROJECT_DIR):
    print(f'$ {cmd}')
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.stdout: print(result.stdout)
    if result.stderr: print(result.stderr)
    return result.returncode

def main():
    os.chdir(PROJECT_DIR)
    print('=== Step 1: Initializing git repo ===')
    rc = run('git init')
    if rc != 0:
        print('ERROR: git init failed'); sys.exit(1)

    print('\n=== Step 2: Waiting for chapters_1_3.md ===')
    found = False
    for attempt in range(1, 6):
        if os.path.exists(CHAPTERS_1_3):
            size = os.path.getsize(CHAPTERS_1_3)
            print(f'Found chapters_1_3.md ({size} bytes) on attempt {attempt}')
            found = True; break
        print(f'Attempt {attempt}/5: not found. Waiting 30s...')
        time.sleep(30)
    if not found:
        print('WARNING: chapters_1_3.md not found after 5 attempts.')

    print('\n=== Step 3: Creating full_paper.md ===')
    parts = [TITLE_PAGE]
    for path, label in [(CHAPTERS_1_3, 'ch1-3'), (CHAPTERS_4_5, 'ch4-5'), (CHAPTERS_6_7, 'ch6-7')]:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f: content = f.read()
            parts.append(content); parts.append('\n\n')
            print(f'  Added {label} ({len(content)} chars)')
        else:
            print(f'  SKIPPED {label}')
    with open(FULL_PAPER, 'w', encoding='utf-8') as f: f.write(''.join(parts))
    print(f'  Created full_paper.md ({os.path.getsize(FULL_PAPER)} bytes)')

    print('\n=== Step 5: git add ===')
    run('git add -A')

    print('\n=== Step 6: git commit ===')
    msg = 'Initial commit: NII research paper with website\n\nResearch paper on who is insured by Israel\'s National Insurance (Bituach Leumi).\nIncludes 7 chapters covering old/new law, additional legislation, practice gaps,\ncase law, and meta-legal conclusions. Static website with charts and sources.'
    run(f'git commit -m "{msg}"')

    print('\n=== Step 7: Confirmation ===')
    run('git log --oneline')
    run('git status')
    print('\nDone!')

if __name__ == '__main__': main()
