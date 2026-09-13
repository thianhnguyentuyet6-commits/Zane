# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

delegated: static HTML/CSS + vanilla JS ES modules, FastAPI backend on localhost:8000, no framework (keeps bundle minimal, offline-first, matches existing codebase)

## Users

Primary: Windows PC power users and developers who want a local, offline-first AGI assistant with deep Windows control. They run local LLM (Qwen3 30B-A3B MoE) via llama.cpp, want file/process/window management, memory, evolution, without cloud dependency.

Situation: Working on Windows PC (8GB VRAM 3060ti + 32GB RAM), needs to manage files, processes, windows, system resources, with AI assistance. Values privacy, offline capability, and Windows deep integration (WMI, Win32) over cloud APIs.

Job: Execute tasks via natural language, manage system, retain memory, evolve capabilities, with explicit permission control and undo.

## Product Purpose

Zane Windows PC专注版 is a local AGI housekeeper that runs entirely offline (optional cloud teacher), with deep Windows control (WMI CPU per-core, memory sticks, disk SMART, startup, services, Win32 HWND Z-order DPI, multi-monitor). It provides file/process/window/vision/input/system/clipboard/network/security tools via controlled typed interfaces, not arbitrary code.

Success means: User can say "整理下载文件夹" and it lists, sorts by importance (recent access + last task reference), confirms dangerous deletions via modal, moves to recycle bin, supports undo end-to-end, all with real Windows APIs, not simulation.

## Positioning

Unlike Operator/Claude Computer Use (cloud-only) or PowerToys/Raycast (no AI), Zane is offline-first with local LLM as primary engine, OpenAI-compatible llama.cpp, with tool registry + policy firewall explicit permission verification audit. Only local LLM is required; cloud APIs are optional teachers.

Unlike generic AI agents, it has 4-layer memory (conversational/episodic/semantic/procedural) + SimpleMem compression with use_llm switch (default false fixed-length offline, true LLM high-quality) + forgetting curves 7/30/90/180 days + DREAMS.md human-readable diary.

The mechanism competitors cannot copy: WMI real per-core CPU + memory sticks + disk SMART + startup registry + Win32 real HWND Z-order DPI + multi-monitor coordinate handling, all tested on real Windows, with 8GB VRAM support via CPU offload.

## Operating Context

Workflows: Chat → plan → tool execution → verification → final report, with execution stream showing observe/plan/act/verify steps.

Environments: Windows 10/11 primary (WMI+Win32 real), Linux demo (structure real, data simulated), iOS read-only optional (ZANE_ENABLE_IOS=true, 8 routes, dedicated token short-lived revocable).

Tools: 26 tools Windows real (file+process+window+vision+input+system+clipboard+network+security), each with contract risk level, reversible via undo_stack filelock persisted, with boundary tests for recycle bin cleared and permission changed.

Documents: config/*.json for evolution_schedule (default disabled idle N minutes + CPU/GPU threshold), replay_config (threshold 0.8 configurable), simplemem (use_llm), thinking_config (two-level eval), resource_config (5 dimensions + camera/mic meeting detection).

Rituals: Evolution dashboard with crash recovery + SSE reconnect exponential backoff, threshold validation via tests/test_threshold_validation.py running 0.5/0.6/0.7/0.8/0.9, real replay via tests/test_eval_real.py with agent_runtime tens of tasks success rate.

## Capabilities and Constraints

Capabilities:
- System: WMI real CPU per-core + GPU + memory sticks + disk SMART + processes tree parent+cmdline + startup registry HKCU/HKLM Run + startup folder + services, Win32 real EnumWindows Z-order DPI GetDpiForWindow + monitor detection + move/resize + virtual desktop + DWM thumbnail, screenshot full/window/region with DPI unification, OCR RapidOCR 50MB lazy download with cache check asking user, UIA tree for browser/explorer/Office (needs Windows real testing)
- Tools: 26 tools via tool_registry + policy_firewall L0 read L1 write L2 dangerous + protected paths + pending queue + frontend modal active reminder every 10s auto-popup, path+PID dual verification anti-spoofing, dangerous process interception
- Memory: 4 layers + SimpleMem use_llm switch + forgetting 4 curves + DREAMS.md + importance sorting recent access + last task reference weighted
- Runtime: Resource monitor 5 dimensions + camera/mic occupancy meeting detection more reliable than process name + idle N minutes + CPU/GPU threshold, thinking budget two-level keywords fast + LLM confirm fuzzy interval 0.3-0.7, data filter 100%
- Scheduler: Default disabled enabled=false, configurable env ZANE_AUTO_EVOLVE, cooldown/max_per_day/allow_nightly
- Model: Path priority env MODEL_PATH/QWEN_MODEL_PATH/LLM_MODEL_PATH/ZANE_MODEL_PATH/HF_MODEL_PATH > config/model_paths.json > default probe, error exit if not found, HF not auto-download cache missing prompt confirm, 8GB support VRAM detection + CPU offload
- Frontend: 10 views clean Windows-focused (was 23 messy), 14 JS files, platform_status real/demo distinction, pending_modal active reminder, WMI charts Canvas interactive, confirmation modal, preview diff window move dashed box + file delete recycle preview, importance sorting, error handling try-catch + aria-busy + skeleton, polling 30s adaptive 15s + hidden pause energy-saving, SSE reuse no WebSocket unless strong real-time loss curve
- Testing: 8 tests, P0 must 6 items all pass (tools real + security interception + undo E2E + forgetting + DREAMS.md + threshold + real replay), P1 important 8 items done (WMI+Win32 enhancement + SimpleMem switch + importance sorting + two-level eval + camera/mic + RapidOCR delay + frontend completion), P2 optional 3 items done (config center + polling optimization + docs)

Constraints:
- Must run offline: local LLM primary, cloud optional teacher, RapidOCR lazy download not forced in main install
- Must be safe: tool registry + policy firewall explicit permission + audit, read-only no confirm dangerous need confirm, context budget large output compression truncation summary, reliable error handling autonomous recovery retry limit circuit breaker
- Must be real: Real computer control tools not simulation, AI not direct arbitrary code, controlled typed interfaces, Windows depth control primary, iOS remote reserved, Windows real APIs need real Windows environment testing, Linux demo structure real
- Must be maintainable: Code realistic, explain realistic, single version clean, no legacy in main, version moved to legacy/ with deprecated stable weeks then delete
- Must be commercial-grade: Quality comparable to Operator/Claude Computer Use + Manus/Devin + PowerToys/Raycast, test coverage + security audit log + real environment testing are biggest gaps, performance can be optimized later not most urgent
- Language: Simplified Chinese priority for UI/logs/docs/replies natural concise, source identifiers English, files with Chinese UTF-8 BOM, Agent default Simplified Chinese spoken, demo data all Chinese
- iOS: Default disabled ZANE_ENABLE_IOS=false, focus Windows, 8 routes read-only REST/SSE no WebSocket needed, dedicated Token short-lived revocable not sharing Web JWT, control for later version lower risk

Undecided: Whether to use shadcn/ui or keep vanilla (currently vanilla for minimal bundle, but could adopt shadcn for consistency), whether to add WebSocket for training loss curve real-time (currently 30s polling acceptable reuse SSE, don't introduce WebSocket unless strong real-time)

## Brand Commitments

Name: Zane AGI, Zane Windows PC专注版 v0914

Voice: Technical, honest, concise, Simplified Chinese for UI/logs/docs, English for code identifiers. No hype, README writes technical implementation not tags, network security sandbox linux self-correction, solid foundation, 14-layer engine review.

Personality: Power user tool, like PowerToys/Raycast + Operator/Claude Computer Use + Manus/Devin fusion, with memory+verification+execution+thinking, target personal AGI housekeeper low config reference openclaw, allows innovation trial and error experimental features isolated.

Assets: Logo Z icon, existing frontend CSS styles.css+components.css+layout.css+themes.css, 110API (86 modular + 32 compatible, iOS 8 optional default disabled), 29 feedback fixes documented.

References: User explicitly wants PC Windows first, iOS default disabled, frontend functions written well, backend foundation solid. iOS code preserved via ZANE_ENABLE_IOS=true enable, focus Windows platform WMI+Win32 real, frontend 111API→103API alignment 12JS perfect views error handling confirmation modal preview Diff WMI charts platform status bar pending modal, backend foundation memory 4 layers+SimpleMem use_llm+forgetting 4 curves+DREAMS.md+runtime 5 dimensions+camera mic+security path PID verification+undo E2E+scheduler idle detection default disabled+crash recovery SSE reconnect exponential backoff+threshold configurable+real replay.

## Evidence on Hand

Real content:
- Backend: 86 py files, 13 main + 21 runtime + 6 memory + 18 routers (windows 7 routes Windows-focused) + 6 config, tests 8 files all P0 passing, docs WINDOWS_FOCUS_PLAN.md + WINDOWS_FOUNDATION_REPORT.md + DREAMS.md generated
- Frontend: index.html 44KB clean Windows-focused 10 views (was 23 messy 41KB), 14 JS files, backend serving on localhost:8000 with /api/health + /api/windows/foundation + /api/system/state + /api/security/pending all responding
- Data: data/DREAMS.md human-readable diary, data/memory/*.json 4 layers, data/undo_stack.json filelock persisted
- Tests: test_windows_foundation 4/4, test_forgetting 2/2, test_undo_e2e 3/3, test_threshold_validation, test_tools_impl, test_eval_real 50 tasks, test_eval_replay
- Running: Backend on 8000 with log ✅ 110API Windows专注 iOS默认禁用, frontend at / serving index.html

Absences that must not be fabricated:
- No real Windows environment testing yet (WMI temperature, process tree, startup, window move/resize DPI multi-monitor, screenshot DPI, UIA browser/explorer/Office, camera/mic meeting detection) - Linux demo structure real
- No real LLM running (llama.cpp 8080 not running, needs Windows start, Qwen3.6 35B A3B D:\llama.cpp\...gguf)
- No RapidOCR installed (50MB lazy download)
- No sentence-transformers/torch (keyword fallback, training unavailable inference available)
- No iOS real device testing (default disabled)

## Product Principles

1. **Windows专注，iOS默认禁用**：First version risk reduction, focus PC Windows real WMI+Win32, frontend functions well written, backend foundation solid, iOS code preserved via env flag, enable later. Lower risk, solid foundation first.

2. **测试夯实优先**：Test coverage is biggest gap vs commercial, system-level dangerous operations must be tested first, otherwise risk exposure grows. Priority: testing > SimpleMem > iOS > docs. Undo not psychological comfort, must be E2E verified with recycle cleared and permission changed boundaries.

3. **真实而非模拟**：Real computer control tools not simulation, AI not direct arbitrary code, controlled typed interfaces. Windows real APIs need real Windows environment testing, Linux demo structure real. 50条模拟仅冒烟，换真实agent_runtime几十条任务成功率可信度高.

4. **简洁而非简陋**：Simplicity ≠ feature-less, match complexity to actual task complexity. Reduce scope, progressive disclosure, one primary action, reduce color palette 1-2 plus neutrals, one font family 3-4 sizes, remove decorations that don't serve hierarchy, linear flow, generous white space. But preserve necessary functionality and information users need to make decisions.

5. **安全显式**：Tool registry + policy firewall explicit permission verification audit, read-only no confirm dangerous need confirm, path+PID dual verification anti-spoofing, dangerous process interception, protection paths System32, recycle bin + undo E2E, pending queue frontend modal active reminder every 10s auto-popup avoid ignored stuck queue or auto-release, security is 100% filter + sandbox realpath + whitelist + filelock.

## Accessibility & Inclusion

Known needs: Keyboard navigation, focus management, ARIA labels, screen reader support for dashboard tool. The clean frontend must have proper aria-current, aria-busy, aria-live, role attributes. Body and placeholder text contrast ≥4.5:1, large text ≥3:1. The current frontend has some ARIA but needs audit per impeccable craft-floor.

Standard: WCAG 2.1 AA as target, with keyboard focus visible, error states with problem and recovery, empty states designed.

Platform: web dashboard used in desktop browser, primarily Chrome/Edge on Windows, with 1920x1080 and multi-monitor scenarios, DPI scaling handling is critical and most easily tripped.
