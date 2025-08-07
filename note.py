#!/usr/bin/env python3
import json
import os
import sys
import tempfile
import subprocess
from pathlib import Path
import time

NOTES_FILE = Path.home() / ".terminal_notes" / "notes.json"
NOTES_PROGRAM_FILE = os.path.dirname(os.path.abspath(__file__))
NOTES_FILE.parent.mkdir(parents=True, exist_ok=True)

if not NOTES_FILE.exists():
    with open(NOTES_FILE, "w") as f:
        json.dump([], f)

# tools

def load_notes():
    with open(NOTES_FILE, "r") as f:
        return json.load(f)

def save_notes(notes):
    for index, note in enumerate(notes):
        note["id"] = index
    with open(NOTES_FILE, "w") as f:
        json.dump(notes, f, indent=2)

def add_note(body, tags):
    notes = load_notes()
    note = {"body": body, "tags": tags, "date": time.strftime("%Y-%m-%d"), "id": len(notes)}
    notes.append(note)
    save_notes(notes)
    return note

def run_note(notes, index=0):
    script = notes[int(index)]["body"]
    shell_attempts = [
            ["powershell", "-Command", script],
            ["cmd", "/c", script],
            ["bash", "-c", script],
            ["sh", "-c", script],
        ]
    
    for shell_cmd in shell_attempts:
        try:
            result = subprocess.run(shell_cmd)
            if result.returncode == 0:
                return
            else:
                print(f"⚠️ Shell {' '.join(shell_cmd[:1])} failed with code {result.returncode}")
        except FileNotFoundError:
            print(f"❌ Shell not found: {shell_cmd[0]}")

    print("❌ All shells failed. Could not execute the script.")


def edit_note(query, new_body):
    notes = load_notes()
    try:
        if query.isdigit():
            index = query
            notes[int(index)]["body"] = new_body
            notes[int(index)]["date"] = time.strftime("%Y-%m-%d")
        else:
            index = list_by_tag(query)[0]["id"]
            notes[int(index)]["body"] = new_body
            notes[int(index)]["date"] = time.strftime("%Y-%m-%d")
        save_notes(notes)
    except (IndexError, ValueError):
        print("Invalid note.")

def search_notes(query):
    notes = load_notes()
    found = [n for n in notes if query.lower() in n["body"].lower() or query.lower() in " ".join(n["tags"]).lower()]
    if found:
        return found
    else:
        print("⚠️ No notes found. future implementation will fuzzy search using gpt")

def list_by_tag(tag):
    notes = load_notes()
    filtered = [n for n in notes if tag in n["tags"]]
    for i, note in enumerate(filtered):
        print_note(note)
    return filtered

def remove_note(index):
    notes = load_notes()
    try:
        removed = notes.pop(int(index))
        save_notes(notes)
        print(f"❌ Removed note at index {index}")
    except (IndexError, ValueError):
        print("⚠️ Invalid index.")

def execute_note(identifier):
    notes = load_notes()
    try:
        script = None
        if (identifier.isdigit()):
            script = notes[int(identifier)]["body"]
        else:
            script = list_by_tag(identifier)[0]["body"]


        shell_attempts = [
            ["powershell", "-Command", script],
            ["cmd", "/c", script],
            ["bash", "-c", script],
            ["sh", "-c", script],
        ]

        for shell_cmd in shell_attempts:
            try:
                result = subprocess.run(shell_cmd)
                if result.returncode == 0:
                    return
                else:
                    print(f"⚠️ Shell {' '.join(shell_cmd[:1])} failed with code {result.returncode}")
            except FileNotFoundError:
                print(f"❌ Shell not found: {shell_cmd[0]}")

        print("❌ All shells failed. Could not execute the script.")

    except (IndexError, ValueError):
        print("⚠️ Invalid note index.")


def tag_note(identifier, tag):
    notes = load_notes()
    try:
        if (identifier.isdigit()):
            if ('untagged' in notes[int(identifier)]["tags"]):
                notes[int(identifier)]["tags"].remove('untagged')
            if (tag not in notes[int(identifier)]["tags"]):
                notes[int(identifier)]["tags"].append(tag)
        else:
            if ('untagged' in list_by_tag(identifier)[0]["tags"]):
                list_by_tag(identifier)[0]["tags"].remove('untagged')
            if (tag not in list_by_tag(identifier)[0]["tags"]):
                list_by_tag(identifier)[0]["tags"].append(tag)
        save_notes(notes)
    except (IndexError, ValueError):
        print("⚠️ Invalid note index.")

def remove_tag(identifier, tag):
    notes = load_notes()
    try:
        if (identifier.isdigit()):
            notes[int(identifier)]["tags"].remove(tag)
        else:
            list_by_tag(identifier)[0]["tags"].remove(tag)
        save_notes(notes)
    except (IndexError, ValueError):
        print("⚠️ Invalid note index.")


def upload_notes():
    for repo_dir in [NOTES_PROGRAM_FILE, os.path.dirname(NOTES_FILE)]:
        try:
            subprocess.run(["git", "add", "--all"], cwd=repo_dir, check=True)

            if has_changes_to_commit(repo_dir):
                subprocess.run(["git", "commit", "-m", "changed notes"], cwd=repo_dir, check=True)
                subprocess.run(["git", "push", "origin", "main"], cwd=repo_dir, check=True)
            else:
                print(f"No changes to commit in {repo_dir}")

        except subprocess.CalledProcessError as e:
            print(f"Git command failed in {repo_dir}:", e)

def download_notes():
    for repo_dir in [NOTES_PROGRAM_FILE, os.path.dirname(NOTES_FILE)]:
        subprocess.run(["git", "pull", "origin", "main"], cwd=repo_dir, check=True)

def has_changes_to_commit(repo_dir):
    unstaged = subprocess.run(["git", "diff", "--quiet"], cwd=repo_dir)
    staged = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=repo_dir)
    return unstaged.returncode != 0 or staged.returncode != 0

# user experience

def print_note_search(query):
    notes = search_notes(query)
    for i, note in enumerate(notes):
            print(f"{i}: [tags: {', '.join(note['tags'])}]\n{note['body']}\n")


def print_note(note):
    print(f"{note["id"]}: ({note['date']}) {note["body"]} [tags: {', '.join(note['tags'])}]")

def list_notes():
    notes = load_notes()
    for i, note in enumerate(notes):
        print(f"{i}: {note['date']} {note["body"]} [tags: {', '.join(note['tags'])}]")

def print_add_note(body, tags):
    add_note(body, tags)
    notes = load_notes()
    print(f"{len(notes) - 1}: {body} [tags: {', '.join(tags)}]")


def print_usage():
    print("""Usage:
  notes.py add "body text" tag1,tag2
  notes.py edit index "new body text"
  notes.py list [optional_tag]
  notes.py query "search text"
  notes.py remove index
  notes.py run index
  notes.py ask "question"
  notes.py pull - pull notes from repo
  notes.py save - push notes to repo
    """)


def main():
    print(sys.argv)
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
        return
    cmd = sys.argv[1]
    if cmd == "add":
        if len(sys.argv) > 2:
            tags = []
            if len(sys.argv) == 3:
                tags = ['untagged']
            for i in range(3, len(sys.argv)):
                tags.append(sys.argv[i])
            note = add_note(sys.argv[2], tags)
            print_note(note)
        return
    elif cmd == 'edit':
        if len(sys.argv) == 2:
            subprocess.run(["powershell", "-Command", f"code {NOTES_FILE}"])
        elif len(sys.argv) == 4:
            edit_note(sys.argv[2], sys.argv[3])
        return
    elif cmd == 'list':
        if len(sys.argv) == 2:
            list_notes()
        else:
            list_by_tag(sys.argv[2])
        return
    elif cmd == 'remove':
        if len(sys.argv) == 3:
            remove_note(sys.argv[2])
        return
    elif cmd == 'run':
        if len(sys.argv) == 3:
            execute_note(sys.argv[2])
        return
    elif cmd == 'tag':
        if len(sys.argv) > 3:
            tag_note(sys.argv[2], sys.argv[3])
        return
    elif cmd == 'remove_tag':
        if len(sys.argv) == 3:
            remove_tag(sys.argv[2], sys.argv[3])
        return
    elif cmd == 'save':
        upload_notes()
        return
    elif cmd == 'pull':
        download_notes()
        return
    elif len(sys.argv) == 2:
        execute_note(sys.argv[1])
        return
    elif len(sys.argv) > 2:
        tags = []

        for i in range(2, len(sys.argv)):
            tags.append(sys.argv[i])
        note = add_note(sys.argv[1], tags)
        print_note(note)
        return

if __name__ == "__main__":
    main()


# if cmd.isdigit():
#     notes = load_notes()
#     run_note(notes, cmd)

# if len(sys.argv) == 2:
#     notes = list_by_tag(sys.argv[1])
#     run_note(notes)

# if len(sys.argv) == 3:
#     notes = search_notes(sys.argv[1])
#     run_note(notes, sys.argv[2])


# if cmd == "add" and len(sys.argv) == 4:
#     print_add_note(sys.argv[2], sys.argv[3].split(","))
# elif cmd == "edit" and len(sys.argv) == 4:
#     edit_note(sys.argv[2], sys.argv[3])
# elif cmd == "list":
#     if len(sys.argv) == 3:
#         list_by_tag(sys.argv[2])
#     else:
#         list_notes()
# elif cmd == "query" and len(sys.argv) == 3:
#     print_note_search(sys.argv[2])
# elif cmd == "remove" and len(sys.argv) == 3:
#     remove_note(sys.argv[2])
# elif cmd == "run" and len(sys.argv) == 3:
#     execute_note(sys.argv[2])
# elif cmd == "ask" and len(sys.argv) == 3:
#     subprocess.run(["sgpt", sys.argv[2]])
# elif len(sys.argv) == 2:
#     execute_note(sys.argv[1])
# else:
#     print_usage()