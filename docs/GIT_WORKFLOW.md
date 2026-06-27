# Git Workflow — Orkestr (Build2026)

> First hackathon? First time with Git? This is all you need. Keep it open on Saturday.
> The golden rule: **pull before you start, push when you pause, stay in your own folder.**

---

## ⚡ The cheat sheet (90% of what you'll type)

```bash
# starting work / coming back after a break
git checkout main
git pull origin main          # get everyone's latest
git checkout <your-branch>
git merge main                # fold their latest into your branch

# every 30–60 min, whenever a chunk works
git add .
git commit -m "what you did"
git push origin <your-branch>

# share your work with the team (when your piece works)
git checkout main
git pull origin main
git merge <your-branch>
git push origin main
git checkout <your-branch>    # go back to your lane
```

Your branch name = your first name: **jaydon · lucas · leeshan · nigel**

---

## The mental model (30 seconds)

GitHub is a shared folder for code, but it does **not** auto-sync — you manually
**push** (upload) and **pull** (download). To stop four people overwriting each other,
**everyone works on their own branch**, not on `main`.

- A **branch** = your private copy of the code. Break things freely; nobody else is affected.
- **`main`** = the official shared version. You merge your branch into it when your piece works.
- Because each of you owns a different folder, your changes rarely collide.

---

## Step 0 — One time only

### Jaydon (creates the repo, once)
```bash
cd orkestr
git init
git add .
git commit -m "Backend skeleton + API contract"
git branch -M main
git remote add origin https://github.com/jaydonnnk/orkestr.git
git push -u origin main
```
> Make the empty repo on github.com first. **Don't** tick "Add a README" — we already have one.

### Everyone else (Lucas, Leeshan, Nigel — once each)
```bash
git clone https://github.com/jaydonnnk/orkestr.git
cd orkestr
git checkout -b lucas          # use your own name
```
`checkout -b` = "make a new branch and switch onto it." You're now in your own lane.

> Jaydon also makes his branch: `git checkout -b jaydon`

---

## Step 1 — The loop you repeat all day

Every time a chunk of work runs (not once at 9pm — **every 30–60 min**):

```bash
git add .                              # stage everything you changed
git commit -m "added negotiation rounds"   # save a labelled snapshot
git push origin jaydon                 # upload YOUR branch
```

**add → commit → push.** Each commit is a save point you can roll back to. Commit small,
commit often — it's free, and it's your undo button.

---

## Step 2 — Get everyone else's work (the step people forget)

After anyone merges to `main`, your copy is behind. Before you keep building, sync:

```bash
git checkout main
git pull origin main          # download the latest main
git checkout jaydon           # back to your branch
git merge main                # pull main's updates into your branch
```

> **The #1 hackathon Git disaster** is coding for 8 hours without pulling, then trying to
> merge a giant pile at 8pm. Sync a few times during the day. Small and frequent wins.

---

## Step 3 — Share your work (merge into main)

When your piece works and you want the team to have it:

```bash
git checkout main
git pull origin main          # make sure main is current first
git merge jaydon              # fold your branch in
git push origin main          # upload the new main
git checkout jaydon           # return to your lane
```

That's it — no formal Pull Request needed for a hackathon. (If you *prefer* the GitHub
button flow: push your branch, then on github.com click **"Compare & pull request" → "Merge"**.
Either works. Command-line is faster.)

---

## Merge conflicts — don't panic

If two people changed the **same lines**, Git pauses and marks the clash inside the file:

```
<<<<<<< HEAD
your version of the line
=======
their version of the line
>>>>>>> main
```

Fix it in 4 steps:
1. Open the file, find the `<<<<<<<` markers.
2. Decide which version is right — keep yours, keep theirs, or combine both.
3. **Delete all three marker lines** (`<<<<<<<`, `=======`, `>>>>>>>`).
4. Save, then:
   ```bash
   git add .
   git commit -m "resolved conflict"
   ```

It looks scary the first time; it's really just "pick which line wins." Read both sides,
choose, delete the markers. If you're unsure which side is right — ask in the group chat
**before** picking.

---

## 🆘 Panic button (common rescues)

Git almost never truly loses committed work — when in doubt, **commit first, then experiment.**

| Situation | Fix |
|---|---|
| "I want to throw away my un-committed changes" | `git restore .` (wipes uncommitted edits — careful) |
| "I committed but want to undo it, keep my changes" | `git reset --soft HEAD~1` |
| "I need to switch branches but have unfinished work" | `git stash` → switch → `git stash pop` to get it back |
| "I'm scared I'll lose work" | `git add . && git commit -m "wip"` first — now it's saved |
| "git push got rejected" | someone pushed first → `git pull origin <branch>`, fix any conflict, push again |
| "I'm completely lost" | **stop typing commands**, screenshot the terminal, ask Jaydon |

> Don't use `git push --force` or `git reset --hard` unless Jaydon says so — those can delete
> teammates' work. Everything else is recoverable.

---

## The 3 rules (put these on the wall)

1. **Pull before you start, push when you pause.** Never go more than ~1 hour without syncing.
2. **Stay in your own folder.** Editing a shared file (the `data/*.json`, the README)? Say
   *"anyone in data?"* in the chat first.
3. **Commit small, commit often.** Every working chunk is a save point.

---

## Who owns what (stay in your lane)

| Person | Branch | Owns (edit freely) |
|---|---|---|
| **Jaydon** | `jaydon` | `agents/` (Convener, negotiation), `core/settlement.py` |
| **Lucas** | `lucas` | `api/`, `core/session.py`, `payments/` |
| **Leeshan** | `leeshan` | `frontend/` (her whole Next.js app) |
| **Nigel** | `nigel` | `ai/`, `data/` (seeding), demo ops |

**Shared / coordinate first:** `data/personas.json`, `data/venues.json`, `README.md`.
These are the files most likely to cause a conflict — ping the chat before editing.

---

## Already handled (don't worry about these)

`.gitignore` is set up, so `node_modules/`, `.venv/`, `__pycache__/`, and `.env` **won't**
get committed. Never force-add those — they're huge and break things. If `git status` shows
hundreds of files, something's wrong — stop and check with Jaydon.

---

### The one-line summary
Make your branch → work → `add`/`commit`/`push` often → `merge main` into your branch to stay
current → `merge` your branch into `main` to share. Stay in your folder. You've got this.
