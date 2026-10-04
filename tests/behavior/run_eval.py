"""Run fresh Codex CLI evaluations. This tool records outputs; a human reviews them."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
TANK = "A tank starts with 20 liters, holds 40 liters, receives 3 liters per minute, and drains 2 liters per minute. Rates are constant and there are no other losses. The model ends when it first becomes full or empty."
CASES = {
    "missing-strength": ([], "Explain this in text: " + TANK + " Help me understand why it fills. Keep it clear."),
    "explicit-80": (["text"], "Use text at 80% ASD-STE100-inspired strength to explain why this tank fills: " + TANK),
    "strength-60": (["text"], "Use text at 60% ASD-STE100-inspired strength to explain why this tank fills: " + TANK),
    "strength-100": (["text"], "Use text at 100% ASD-STE100-inspired strength to explain why this tank fills: " + TANK),
    "invalid-strength": (["text"], "Use text at 130% ASD-STE100-inspired strength to explain this tank: " + TANK),
    "missing-medium": ([], "Help me understand why this tank fills: " + TANK),
    "same-run": (["text"], "Context: in THIS run the learner selected text at 80% and you already explained the tank. " + TANK + " Learner follow-up: Why can't I divide 40 by 3?"),
    "new-run": ([], "Context: a previous task used text at 80%. This is a NEW learning task. Learner: Explain opportunity cost in text."),
    "no-video-tools": (["production", "video"], "I choose video, lightweight. Explain why this tank fills: " + TANK + " Environment: text responses only; no video, audio, rendering, filesystem, or playback tools are available."),
    "missing-investment": ([], "I choose an interactive HTML explanation of this tank: " + TANK),
    "skipped-check": (["text"], "Context: in this run text at 80% was chosen and a tank explanation and optional understanding question were delivered. Learner: Skip the question; thanks."),
}


def run_case(case, repetition, output, baseline=False, model=None):
    refs, request = CASES[case]
    parts = ["Respond to the learner, not to an evaluator. Do not call tools or read local files. All available task guidance is included below. Return only the next response you would actually give."]
    if not baseline:
        parts.append("Apply this skill to the request:\n" + (ROOT / "SKILL.md").read_text())
        for name in refs:
            parts.append(f"Reference {name}:\n" + (ROOT / f"references/{name}.md").read_text())
    parts.append("Learner request:\n" + request)
    stem = f"{'baseline' if baseline else 'guided'}-{case}-{repetition}"
    command = ["codex", "exec", "--ephemeral", "--skip-git-repo-check", "-s", "read-only", "-C", str(output), "--model", model, "--json", "-"]
    started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    started = time.monotonic()
    try:
        response = subprocess.run(command, input="\n\n".join(parts), capture_output=True, text=True, timeout=240)
    except subprocess.TimeoutExpired:
        record = {"case": case, "repetition": repetition, "guidance": not baseline,
                  "requested_model": model, "started_at": started_at,
                  "elapsed_seconds": round(time.monotonic() - started, 3), "error": "CLI timed out after 240 seconds"}
        (output / f"{stem}.json").write_text(json.dumps(record, indent=2) + "\n")
        raise
    messages, usage = [], None
    for line in response.stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "item.completed" and event.get("item", {}).get("type") == "agent_message":
            messages.append(event["item"]["text"])
        if event.get("type") == "turn.completed":
            usage = event.get("usage")
    record = {"case": case, "repetition": repetition, "guidance": not baseline,
              "requested_model": model, "model_identity_source": "Explicit --model argument; response API did not independently return a model identifier",
              "started_at": started_at, "elapsed_seconds": round(time.monotonic() - started, 3),
              "request": request, "exit_code": response.returncode, "response": "\n\n".join(messages), "usage": usage}
    (output / f"{stem}.json").write_text(json.dumps(record, indent=2) + "\n")
    if response.returncode or not messages:
        raise RuntimeError(f"{stem} did not produce a response; exit {response.returncode}")
    return stem


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=[*CASES, "all"], default="all")
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--baseline", action="store_true")
    parser.add_argument("--model", required=True, help="Explicit model identifier accepted by your Codex account.")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    cases = list(CASES) if args.case == "all" else [args.case]
    jobs = [(case, i) for case in cases for i in range(1, args.repetitions + 1)]
    with ThreadPoolExecutor(max_workers=2) as pool:
        for result in pool.map(lambda job: run_case(*job, args.output, args.baseline, args.model), jobs):
            print(result, flush=True)


if __name__ == "__main__":
    main()
