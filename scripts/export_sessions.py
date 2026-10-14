"""Export the Claude Code session history for this project as readable Markdown.

    python scripts/export_sessions.py ai-sessions

Reads ~/.claude/projects/<this repo>/. Every prompt typed into a main session is included verbatim;
nothing is selected out. Subagent hand-backs and system notifications are not prompts, so they
are skipped, and tool output is collapsed to one line per call. Keys are redacted.
"""
import glob, json, os, re, sys
from collections import Counter, OrderedDict
from datetime import datetime, timezone, timedelta

HOME = os.path.expanduser("~")
P = HOME + "/.claude/projects/-Users-calebmadgwick-Developer-keyhook-tech-test"
OUT = sys.argv[1]
NZ = timezone(timedelta(hours=11))  # AEDT, where the work was done

TITLES = OrderedDict([
    ("56b8ed84-1e49-4e05-9cc7-20c88e7e161f", "Architecture, build, evaluation harness and prompt iterations"),
    ("38c48381-ca01-41bf-93eb-6abe5acc8177", "Generating the 349-message edge-case suite"),
    ("1e42d28e-9e7f-430c-ac50-4703f0e91edc", "README, ChatGPT blind test set and label review"),
    ("391452a6-e583-4578-b081-e8205410ba67", "Prompt changelog tracking across sessions"),
    ("b745f0e2-44a9-4e6a-85fd-f3456b4b7570", "Claude skills, code review and security review"),
    ("c65dee81-209b-468f-9108-9c554f809e35", "Git repository setup"),
    ("702faedb-6417-4b21-8fc1-6d9a85685f12", "Security review"),
    ("c5579d94-ae56-4f72-9870-051dd7c2eb6a", "High-effort code review"),
    ("b0cf7e7f-71e2-4ea1-ab4e-17edb98d39ae", "Pricing and prompt-caching check against the Claude API docs"),
    ("d4e0b768-9fa3-4858-88b2-6b6458586401", "Status check, final fixes, label review and README rewrite"),
    ("37305a26-8c08-4d0c-b9eb-7246aa3440d6", "Simplify pass over the whole project"),
    ("a9090878-7bc0-40e5-95da-e9bb74a0c148", "Mock Keyhook review, fixes, live model runs and this export"),
    ("376ab0ed-5fa0-412c-bf89-d46c091437fd", "Final pre-submission review, report fixes and two-page README"),
])

def clean(t: str) -> str:
    t = re.sub(r"<system-reminder>.*?</system-reminder>", "", t, flags=re.S)
    t = re.sub(r"<ide_opened_file>.*?</ide_opened_file>", "", t, flags=re.S)
    t = re.sub(r"<ide_selection>.*?</ide_selection>", "", t, flags=re.S)
    t = re.sub(r"Claude Code attached this context automatically.*", "", t, flags=re.S)
    t = t.replace(HOME, "~")
    t = re.sub(r"sk-(or|ant)-v?\d?-?[A-Za-z0-9_\-]{12,}", "[redacted key]", t)
    return t.strip()


def command_text(t: str):
    m = re.search(r"<command-name>(/[^<]+)</command-name>", t)
    if not m:
        return None
    a = re.search(r"<command-args>(.*?)</command-args>", t, re.S)
    args = (a.group(1).strip() if a else "")
    return (m.group(1).strip() + (" " + args if args else "")).strip()


def pasted(t: str) -> str:
    def repl(m):
        body = m.group(1)
        ids = re.findall(r'"id":\s*"(blind_\d+)"', body)
        if ids:
            return f"*[Pasted JSON from ChatGPT: {len(ids)} blind-set messages, {ids[0]} to {ids[-1]}]*"
        lines = body.strip().splitlines()
        return "\n```text\n" + "\n".join(lines[:15]) + ("\n…" if len(lines) > 15 else "") + "\n```\n"
    return re.sub(r"<pasted_content[^>]*>(.*?)</pasted_content[^>]*>", repl, t, flags=re.S)


def user_prompt(r):
    if r.get("type") != "user" or r.get("isMeta"):
        return None
    c = (r.get("message") or {}).get("content")
    if isinstance(c, list):
        if any(isinstance(b, dict) and b.get("type") == "tool_result" for b in c):
            return None
        c = "\n".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")
    if not isinstance(c, str):
        return None
    if c.lstrip().startswith(("<task-notification", "<local-command", "<command-stdout", "[Request interrupted",
                              "<agent-message", "Another Claude session sent a message", "Caveat:")):
        return None
    cmd = command_text(c)
    if cmd:
        return cmd
    if "<command-message>" in c:
        return None
    t = clean(c)
    return pasted(t) if t else None


def tool_line(b):
    i = b.get("input") or {}
    n = b.get("name", "")
    if n == "Agent":
        return f"Delegated to a subagent: *{i.get('description', '')}*" + (f" ({i.get('model')})" if i.get("model") else "")
    d = i.get("description")
    if d:
        return f"{n}: {clean(d)}"
    for k in ("file_path", "pattern", "query", "skill", "url", "action"):
        if i.get(k):
            v = clean(str(i[k]))
            return f"{n}: `{v}`"
    return n


def ts(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(NZ)
    except Exception:
        return None


def fmt(dt, with_date=False):
    return dt.strftime("%a %d %b, %H:%M" if with_date else "%H:%M") if dt else ""


def load(f):
    return [json.loads(l) for l in open(f) if l.strip()]


def render_session(sid, rows, subagent_index):
    out, tools, prompts = [], [], []
    pending_text = []

    def flush_tools():
        if tools:
            cnt = Counter(t.split(":")[0] for t in tools)
            summ = ", ".join(f"{k} ×{v}" if v > 1 else k for k, v in cnt.most_common())
            out.append(f"<details><summary>{len(tools)} tool call{'s' if len(tools) > 1 else ''} ({summ})</summary>\n")
            out.extend(f"- {t}" for t in tools)
            out.append("\n</details>\n")
            tools.clear()

    for r in rows:
        if r.get("isSidechain"):
            continue
        p = user_prompt(r)
        if p is not None:
            flush_tools()
            t = ts(r.get("timestamp", ""))
            prompts.append((t, p))
            out.append(f"\n### {fmt(t)} · Prompt\n")
            out.append("\n".join("> " + l if l.strip() else ">" for l in p.splitlines()) + "\n")
            continue
        if r.get("type") == "assistant":
            c = (r.get("message") or {}).get("content")
            if not isinstance(c, list):
                continue
            for b in c:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "text" and b.get("text", "").strip():
                    flush_tools()
                    out.append(clean(b["text"]) + "\n")
                elif b.get("type") == "tool_use":
                    tools.append(tool_line(b))
    flush_tools()
    return out, prompts


def first_prompt(rows):
    for r in rows:
        if r.get("type") == "user":
            c = (r.get("message") or {}).get("content")
            if isinstance(c, list):
                c = "\n".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")
            if isinstance(c, str) and c.strip():
                return clean(c)
    return ""


def last_text(rows):
    for r in reversed(rows):
        if r.get("type") == "assistant":
            c = (r.get("message") or {}).get("content")
            if isinstance(c, list):
                txt = "\n".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text").strip()
                if txt:
                    return clean(txt)
    return ""


os.makedirs(OUT + "/transcripts", exist_ok=True)
all_prompts, index_rows, sub_rows = [], [], []
total_prompts = kept_prompts = 0  # equal now nothing is omitted
for n, (sid, title) in enumerate(TITLES.items(), 1):
    rows = load(f"{P}/{sid}.jsonl")
    times = [ts(r["timestamp"]) for r in rows if r.get("timestamp")]
    start, end = min(times), max(times)
    subs = []
    for mf in sorted(glob.glob(f"{P}/{sid}/subagents/*.meta.json")):
        meta = json.load(open(mf))
        jf = mf.replace(".meta.json", ".jsonl")
        srows = load(jf) if os.path.exists(jf) else []
        st = [ts(r["timestamp"]) for r in srows if r.get("timestamp")]
        model = next(((r.get("message") or {}).get("model") for r in srows if r.get("type") == "assistant"), "")
        subs.append({"desc": meta.get("description") or "Subagent (no description)", "type": meta.get("agentType", ""), "start": min(st) if st else None,
                     "model": model or "", "prompt": first_prompt(srows), "report": last_text(srows)})
    subs.sort(key=lambda s: s["start"] or start)
    body, prompts = render_session(sid, rows, subs)
    # count all real prompts for the transparency note
    for r in rows:
        p = user_prompt(r)
        if p is not None and not r.get("isSidechain"):
            total_prompts += 1
    kept_prompts += len(prompts)
    slug = f"{n:02d}-" + re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60]
    with open(f"{OUT}/transcripts/{slug}.md", "w") as f:
        f.write(f"# {n}. {title}\n\n")
        f.write(f"Claude Code session, {fmt(start, True)} to {fmt(end)} AEDT. "
                f"{len(prompts)} prompt{'s' if len(prompts) != 1 else ''}, {len(subs)} subagent{'s' if len(subs) != 1 else ''}.\n\n")
        f.write("Prompts are quoted verbatim. Claude's replies are shown in full; tool calls are collapsed to one line each and tool output is left out.\n")
        f.write("\n".join(body))
        if subs:
            f.write("\n\n---\n\n## Subagents delegated in this session\n\n")
            f.write("Each subagent's full brief and final report.\n\n")
            for s in subs:
                f.write(f"### {s['desc']}\n\n*{s['type']}*" + (f" · `{s['model']}`" if s['model'] else "") + f" · started {fmt(s['start'])}\n\n")
                f.write("<details><summary>Brief</summary>\n\n```text\n" + s["prompt"].replace("```", "ˋˋˋ") + "\n```\n\n</details>\n\n")
                if s["report"]:
                    f.write("<details><summary>Report</summary>\n\n" + s["report"] + "\n\n</details>\n\n")
    index_rows.append((n, title, slug, start, end, len(prompts), len(subs)))
    all_prompts += [(t, n, title, slug, p) for t, p in prompts]
    sub_rows += [(n, s) for s in subs]

with open(f"{OUT}/prompts.md", "w") as f:
    f.write("# Prompts\n\n")
    f.write("The prompts I gave Claude Code while building this project, quoted verbatim and grouped by session, in the order the sessions started. "
            "Several sessions ran in parallel, so times overlap between sections. Times are AEDT. Large pasted data is summarised in place.\n")
    cur = None
    for t, n, title, slug, p in all_prompts:
        if n != cur:
            f.write(f"\n## {n}. [{title}](transcripts/{slug}.md)\n")
            cur = n
        f.write(f"\n**{fmt(t, True)}**\n\n" + "\n".join("> " + l if l.strip() else ">" for l in p.splitlines()) + "\n")

print(json.dumps({"total_prompts": total_prompts, "kept_prompts": kept_prompts, "subagents": len(sub_rows)}))
