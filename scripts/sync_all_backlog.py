import subprocess
import json
import time
import sys

REPO = "Shashankb30/Hostel-Management-System"
SPRINT_1_TITLE = "Sprint-1 [19th Oct to 23rd Oct]"
SPRINT_2_TITLE = "Sprint-2 [26th Oct to 30th Oct]"

def get_story_points(issue):
    title = issue['title'].lower()
    labels = [l['name'].lower() for l in issue.get('labels', [])]
    
    if '[epic]' in title:
        if 'setup' in title or 'qa' in title or 'foundation' in title:
            return 8
        return 5
    if 'spike' in title or 'framework' in title or 'relational schema' in title:
        return 5
    if 'automate' in title or 'regression' in title or 'ci pipeline' in title:
        return 5
    if 'story' in labels or '[fr-' in title:
        return 3
    if 'test' in labels or 'qa' in labels or '[qa.' in title:
        return 3
    if 'docs' in labels or '[doc.' in title:
        return 2
    if 'nfr' in labels or '[nfr.' in title:
        return 2
    if 'task' in labels or '[setup.' in title:
        return 2
    return 2

def main():
    print("Fetching all issues from GitHub...")
    cmd = ['gh', 'issue', 'list', '--repo', REPO, '--limit', '300', '--state', 'all', '--json', 'number,title,labels,milestone,assignees']
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("Error fetching issues:", res.stderr)
        sys.exit(1)
        
    issues = json.loads(res.stdout)
    issues.sort(key=lambda x: x['number'])
    print(f"Total issues fetched: {len(issues)}")
    
    team = ['Shashankb30', 'abhijeetcyalgi']
    
    s1_count = 0
    s2_count = 0
    s1_pts = {'Shashankb30': 0, 'abhijeetcyalgi': 0}
    s2_pts = {'Shashankb30': 0, 'abhijeetcyalgi': 0}
    
    for idx, iss in enumerate(issues):
        num = iss['number']
        pts = get_story_points(iss)
        sp_label = f"SP: {pts}"
        
        # Sprint assignment: 1..84 is Sprint 1, 85..180 is Sprint 2
        if num <= 84:
            milestone = SPRINT_1_TITLE
            s1_count += 1
        else:
            milestone = SPRINT_2_TITLE
            s2_count += 1
            
        assignee = team[idx % 2]
        if num <= 84:
            s1_pts[assignee] += pts
        else:
            s2_pts[assignee] += pts
            
        # Check current state
        current_m = iss.get('milestone', {})
        current_m_title = current_m.get('title') if current_m else None
        current_assignees = [a['login'] for a in iss.get('assignees', [])]
        current_labels = [l['name'] for l in iss.get('labels', [])]
        
        needs_update = False
        if current_m_title != milestone:
            needs_update = True
        if assignee not in current_assignees:
            needs_update = True
        if sp_label not in current_labels:
            needs_update = True
            
        if needs_update:
            print(f"Updating #{num:3d}: {iss['title'][:40]:40s} -> [{milestone}] [Assignee: {assignee}] [{sp_label}]")
            edit_cmd = [
                'gh', 'issue', 'edit', str(num),
                '--repo', REPO,
                '--milestone', milestone,
                '--add-label', sp_label,
                '--add-assignee', assignee
            ]
            r = subprocess.run(edit_cmd, capture_output=True, text=True)
            if r.returncode != 0:
                print(f"  Error updating #{num}: {r.stderr.strip()}")
            time.sleep(0.3)
        else:
            print(f"Skipping #{num:3d} (already up to date)")

    print("\n=== SUMMARY ===")
    print(f"Sprint 1 Issues: {s1_count}, Story Points: {s1_pts}")
    print(f"Sprint 2 Issues: {s2_count}, Story Points: {s2_pts}")

if __name__ == '__main__':
    main()
