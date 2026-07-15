# Huobz AI Library

Shared AI utilities library (prompts, adapters) consumed by HuobzAi/HuobzEdge — not a full agent OS.

## Quick start

```bash
python3 src/app.py
# open http://127.0.0.1:8765
```

## Tests

```bash
python3 -m pytest -q || python3 -c "import pathlib,importlib.util; p=pathlib.Path('src/app.py'); s=importlib.util.spec_from_file_location('app',p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print('ok')"
```

## Portfolio

See [PORTFOLIO.md](PORTFOLIO.md) for how this product differs from other badrpk repositories.
