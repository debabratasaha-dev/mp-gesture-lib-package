# Contributing to mp-gesture-lib

Thanks for your interest! Contributions are welcome.

---

## Before You Start

> **Open an issue before making any changes or submitting a PR.**  
> Discuss the change first — avoids wasted effort if it's out of scope or already being worked on.

---

## Ways to Contribute

- **Bug reports** — Open an issue with steps to reproduce
- **Bug fixes** — Fork → fix → PR
- **New bundled models** — Drop a `.task` file into `mp_gesture_lib/models/` (auto-discovered)
- **Docs / examples** — Improvements always welcome

---

## Setup

```bash
git clone https://github.com/debabratasaha-dev/mp-gesture-lib-package
cd mp-gesture-lib-package
pip install -e .          # editable install
python example_usage.py   # test it works
```

---

## Adding a Bundled Model

1. Train a MediaPipe GestureRecognizer `.task` model
2. Drop it into `mp_gesture_lib/models/`
3. Test with `example_usage.py` — it loads automatically, no code change needed

---

## Pull Request Guidelines

- One thing per PR
- Test manually before submitting
- Bump version in `pyproject.toml` and `__init__.py` if changing behaviour

---

## Code Style

- Python type hints where practical
- Docstrings on public functions
- No hard-coded gesture label mappings — keep it model-agnostic

---

<p align="center">Built with ❤️ — all contributions appreciated</p>
