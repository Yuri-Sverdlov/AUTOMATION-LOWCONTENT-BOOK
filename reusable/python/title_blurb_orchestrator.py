"""Stage 2 orchestrator: generate and judge Title+Blurb pairs.

Workflow per cover title:
1) A/B/C each generate 2 pairs (product_title + blurb) => up to 6 pairs
2) Judge evaluates the 6 pairs as linked units
3) Exactly one winning pair is selected
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import os
import re
import sys
from typing import Any

# Allow direct script execution: python .\execution\stage2\title_blurb_orchestrator.py
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from execution import orchestrator as stage1


CONFIG_PATH = ROOT_DIR / "data" / "config.yaml"
GEN_PROMPTS_PATH = ROOT_DIR / "execution" / "prompts" / "title_blurb_generators.md"
JUDGE_PROMPT_PATH = ROOT_DIR / "execution" / "prompts" / "title_blurb_judge.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def log(message: str) -> None:
    stage1.log(f"[stage2] {message}")


def extract_agent_sections(markdown_text: str) -> tuple[str, dict[str, str]]:
    """Extract global prompt part and A/B/C sections."""
    first_agent = markdown_text.find("## Agent ")
    global_part = markdown_text[:first_agent].strip() if first_agent != -1 else markdown_text.strip()
    sections: dict[str, str] = {}
    pattern = re.compile(r"##\s+Agent\s+([A-Z]).*?\n(.*?)(?=\n---\n\n##\s+Agent\s+[A-Z]|\Z)", re.S)
    for m in pattern.finditer(markdown_text):
        sections[m.group(1).strip()] = m.group(2).strip()
    return global_part, sections


def extract_json_array(text: str) -> list[dict[str, Any]] | None:
    t = text.strip()
    if not t:
        return None
    try:
        parsed = json.loads(t)
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        pass

    start = t.find("[")
    end = t.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return None
    frag = t[start : end + 1]
    try:
        parsed = json.loads(frag)
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        return None
    return None


def parse_pairs_from_text(text: str) -> list[dict[str, Any]]:
    """Parse model output into a list of {product_title, blurb} objects."""
    t = text.strip()
    if not t:
        return []

    # Remove fenced code block wrappers if present.
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*\n?", "", t).strip()
        t = re.sub(r"\n?```$", "", t).strip()

    candidates: list[dict[str, Any]] = []

    def collect_from_list(items: list[Any]) -> None:
        for item in items:
            if not isinstance(item, dict):
                continue
            pt = str(item.get("product_title", "")).strip()
            bl = str(item.get("blurb", "")).strip()
            if pt and bl:
                candidates.append({"product_title": pt, "blurb": bl})

    # 1) Direct JSON parse
    try:
        parsed = json.loads(t)
        if isinstance(parsed, list):
            collect_from_list(parsed)
        elif isinstance(parsed, dict):
            if isinstance(parsed.get("pairs"), list):
                collect_from_list(parsed["pairs"])
            else:
                # Try to find first list value in dict
                for v in parsed.values():
                    if isinstance(v, list):
                        collect_from_list(v)
    except json.JSONDecodeError:
        pass

    if candidates:
        return candidates

    # 2) Fallback to array fragment
    arr = extract_json_array(t)
    if arr:
        collect_from_list(arr)

    return candidates


def build_agent_user_prompt(cover_title: str) -> str:
    return (
        f"Approved cover_title: {cover_title}\n"
        "Product context: lined notebook, 108 pages, 6x9 inches.\n"
        "Generate exactly 2 aligned pairs in JSON array format.\n"
        "Each object must contain keys: product_title, blurb.\n"
        "Do not include any extra keys or text."
    )


def build_judge_user_prompt(cover_title: str, candidates: list[dict[str, Any]]) -> str:
    payload = []
    for c in candidates:
        payload.append(
            {
                "agent_id": c["agent_id"],
                "pair_id": c["pair_id"],
                "product_title": c["product_title"],
                "blurb": c["blurb"],
            }
        )
    contract = {
        "cover_title": "string",
        "winner": {
            "agent_id": "A|B|C",
            "pair_id": "string",
            "product_title": "string",
            "blurb": "string",
            "why_selected": "1-2 sentences",
        },
        "candidates_count": 6,
    }
    return (
        f"cover_title: {cover_title}\n"
        f"candidates_json: {json.dumps(payload, ensure_ascii=False)}\n"
        "Select exactly one winner pair from candidates.\n"
        "Return JSON only following this contract:\n"
        f"{json.dumps(contract, ensure_ascii=False, indent=2)}"
    )


def resolve_runtime_models(
    cfg: dict,
) -> tuple[dict, dict, list[str], list[str], list[dict], dict[str, str | None]]:
    """Resolve model_class aliases to concrete model IDs for stage2 run."""
    timeout = int(cfg["ollama"].get("timeout", 300))
    enabled_agents = list(cfg["generation"].get("enabled_agents", ["A", "B", "C"]))
    generation_agents = dict(cfg["generation"].get("agents", {}))
    judge_cfg = dict(cfg.get("judge", {}))
    judge_provider = str(judge_cfg.get("provider", "ollama")).lower()
    judge_model = str(judge_cfg.get("model") or judge_cfg.get("model_class") or "")

    ollama_models: list[str] = []
    anthropic_models: list[str] = []
    preflight: dict[str, str | None] = {
        "ollama_model_check_error": None,
        "anthropic_model_check_error": None,
    }

    try:
        ollama_models = stage1.list_models(cfg["ollama"]["base_url"], timeout)
    except Exception as exc:  # noqa: BLE001
        ollama_models = []
        preflight["ollama_model_check_error"] = str(exc)

    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if api_key:
        try:
            anthropic_models = stage1.list_anthropic_models(api_key, timeout)
        except Exception as exc:  # noqa: BLE001
            anthropic_models = []
            preflight["anthropic_model_check_error"] = str(exc)
    else:
        preflight["anthropic_model_check_error"] = "ANTHROPIC_API_KEY is not set"

    resolved_agents, resolved_judge, resolution_log = stage1.resolve_all_models(
        generation_agents=generation_agents,
        judge_model=judge_model,
        judge_provider=judge_provider,
        enabled_agents=enabled_agents,
        anthropic_models=anthropic_models,
        ollama_models=ollama_models,
    )
    judge_cfg["model"] = resolved_judge
    cfg["generation"]["agents"] = resolved_agents
    cfg["judge"] = judge_cfg
    return cfg, resolved_agents, ollama_models, anthropic_models, resolution_log, preflight


def call_model(
    *,
    provider: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    timeout: int,
    max_tokens: int = 1200,
) -> str:
    if provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        return stage1.chat_anthropic_once(
            api_key=api_key,
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            timeout=timeout,
            temperature=0.4,
            max_tokens=max_tokens,
        )
    return stage1.chat_once(
        base_url=stage1.load_yaml(CONFIG_PATH)["ollama"]["base_url"],
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        timeout=timeout,
        temperature=0.5,
    )


def generate_pairs_for_cover_title(
    cover_title: str,
    cfg: dict,
    agents_cfg: dict,
    global_prompt: str,
    per_agent_prompt: dict[str, str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    pairs: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    raw_map: dict[str, str] = {}
    timeout = int(cfg["ollama"].get("timeout", 300))
    stage2_cfg = dict(cfg.get("stage2", {}))
    default_stage2_agent_max_tokens = int(stage2_cfg.get("agent_max_tokens", 2200))
    enabled_agents = list(cfg["generation"].get("enabled_agents", ["A", "B", "C"]))
    base_url = cfg["ollama"]["base_url"]

    for agent_id in enabled_agents:
        a_cfg = dict(agents_cfg.get(agent_id, {}))
        provider = str(a_cfg.get("provider", "ollama")).lower()
        model = str(a_cfg.get("model") or "")
        max_tokens = int(a_cfg.get("stage2_max_tokens", default_stage2_agent_max_tokens))
        agent_section = per_agent_prompt.get(agent_id, "")
        if not model or not agent_section:
            errors.append({"agent_id": agent_id, "error": "missing model or stage2 prompt section"})
            continue
        if str(a_cfg.get("_resolution_status", "unchanged")) == "not_found":
            errors.append({"agent_id": agent_id, "model": model, "error": "model resolution not found"})
            continue

        system_prompt = f"{global_prompt}\n\n## Agent {agent_id}\n{agent_section}"
        user_prompt = build_agent_user_prompt(cover_title)
        try:
            log(f"[{cover_title}] agent {agent_id} -> {provider}/{model}")
            if provider == "anthropic":
                raw = call_model(
                    provider=provider,
                    model=model,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    timeout=timeout,
                    max_tokens=max_tokens,
                )
            else:
                raw = stage1.chat_once(
                    base_url=base_url,
                    model=model,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    timeout=timeout,
                    temperature=0.6,
                )
            raw_map[agent_id] = raw
            arr = parse_pairs_from_text(raw)
            arr = arr[:2]
            if not arr:
                errors.append(
                    {
                        "agent_id": agent_id,
                        "model": model,
                        "error": "no_parseable_pairs_in_output",
                    }
                )
                continue
            for idx, item in enumerate(arr, start=1):
                p_title = str(item.get("product_title", "")).strip()
                blurb = str(item.get("blurb", "")).strip()
                if not p_title or not blurb:
                    continue
                pairs.append(
                    {
                        "agent_id": agent_id,
                        "pair_id": f"{agent_id}-{idx}",
                        "cover_title": cover_title,
                        "product_title": p_title,
                        "blurb": blurb,
                        "provider": provider,
                        "model": model,
                    }
                )
        except Exception as exc:  # noqa: BLE001
            errors.append({"agent_id": agent_id, "model": model, "error": str(exc)})

    return pairs, errors, raw_map


def choose_winner_pair(
    cover_title: str,
    candidates: list[dict[str, Any]],
    cfg: dict,
    judge_prompt: str,
) -> tuple[dict[str, Any], str, dict[str, Any] | None]:
    judge_cfg = dict(cfg.get("judge", {}))
    provider = str(judge_cfg.get("provider", "ollama")).lower()
    model = str(judge_cfg.get("model") or judge_cfg.get("model_class") or "")
    timeout = int(judge_cfg.get("timeout", cfg["ollama"].get("timeout", 300)))
    stage2_cfg = dict(cfg.get("stage2", {}))
    max_tokens = int(judge_cfg.get("stage2_max_tokens", stage2_cfg.get("judge_max_tokens", 1800)))

    if not candidates:
        return {"cover_title": cover_title, "winner": None, "candidates_count": 0}, "", None

    user_prompt = build_judge_user_prompt(cover_title, candidates)
    raw = ""
    parsed: dict[str, Any] | None = None
    try:
        log(f"[{cover_title}] judge -> {provider}/{model}")
        raw = call_model(
            provider=provider,
            model=model,
            system_prompt=judge_prompt,
            user_prompt=user_prompt,
            timeout=timeout,
            max_tokens=max_tokens,
        )
        parsed = stage1.extract_json_object(raw)
    except Exception:
        parsed = None

    if isinstance(parsed, dict) and isinstance(parsed.get("winner"), dict):
        winner = parsed["winner"]
        pair_id = str(winner.get("pair_id", "")).strip()
        chosen = next((c for c in candidates if c["pair_id"] == pair_id and c["agent_id"] == winner.get("agent_id")), None)
        if chosen is None and pair_id:
            chosen = next((c for c in candidates if c["pair_id"] == pair_id), None)
        if chosen is None:
            chosen = candidates[0]
        result = {
            "cover_title": cover_title,
            "winner": {
                "agent_id": chosen["agent_id"],
                "pair_id": chosen["pair_id"],
                "product_title": winner.get("product_title", chosen["product_title"]),
                "blurb": winner.get("blurb", chosen["blurb"]),
                "why_selected": winner.get("why_selected", ""),
            },
            "candidates_count": len(candidates),
        }
        return result, raw, parsed

    fallback = candidates[0]
    result = {
        "cover_title": cover_title,
        "winner": {
            "agent_id": fallback["agent_id"],
            "pair_id": fallback["pair_id"],
            "product_title": fallback["product_title"],
            "blurb": fallback["blurb"],
            "why_selected": "Fallback: judge JSON unavailable.",
        },
        "candidates_count": len(candidates),
    }
    return result, raw, parsed


def run_stage2(top_6_cover_titles: list[str], parent_run_id: str | None = None) -> dict[str, Any]:
    cfg = stage1.load_yaml(CONFIG_PATH)
    cfg, resolved_agents, ollama_models, anthropic_models, resolution_log, preflight = resolve_runtime_models(cfg)
    global_prompt, per_agent = extract_agent_sections(read_text(GEN_PROMPTS_PATH))
    judge_prompt = read_text(JUDGE_PROMPT_PATH)

    run_id = parent_run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = ROOT_DIR / "output" / run_id / "stage2"
    out_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    all_candidates: dict[str, list[dict[str, Any]]] = {}
    agent_raw_map: dict[str, dict[str, str]] = {}
    judge_raw_map: dict[str, str] = {}
    errors: list[dict[str, Any]] = []

    for cover_title in top_6_cover_titles:
        pairs, pair_errors, pair_raw = generate_pairs_for_cover_title(
            cover_title=cover_title,
            cfg=cfg,
            agents_cfg=resolved_agents,
            global_prompt=global_prompt,
            per_agent_prompt=per_agent,
        )
        errors.extend([{**e, "cover_title": cover_title} for e in pair_errors])
        all_candidates[cover_title] = pairs
        agent_raw_map[cover_title] = pair_raw
        winner_result, judge_raw, _ = choose_winner_pair(
            cover_title=cover_title,
            candidates=pairs,
            cfg=cfg,
            judge_prompt=judge_prompt,
        )
        judge_raw_map[cover_title] = judge_raw
        results.append(winner_result)

    summary = {
        "run_id": run_id,
        "stage": "stage2",
        "cover_titles_count": len(top_6_cover_titles),
        "winners_count": sum(1 for r in results if r.get("winner")),
        "available_models": {"ollama": ollama_models, "anthropic": anthropic_models},
        "preflight": preflight,
        "model_resolution_log": resolution_log,
        "results": results,
        "errors": errors,
    }

    (out_dir / "stage2_candidates.json").write_text(
        json.dumps(all_candidates, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "stage2_judge_raw.json").write_text(
        json.dumps(judge_raw_map, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "stage2_agent_raw.json").write_text(
        json.dumps(agent_raw_map, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "stage2_results.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summary


if __name__ == "__main__":
    # Demo run for one cover title. Replace with stage1 top-6 in production flow.
    demo = run_stage2(["I'm Not Arguing. I'm Just Explaining Why I'm Right."])
    print(json.dumps(demo, ensure_ascii=False, indent=2))
