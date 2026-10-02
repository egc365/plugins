# Vendored files

`ste-lint.py` is an unchanged copy of `scripts/ste-lint.py` from [egc365/asd-ste100-skill](https://github.com/egc365/asd-ste100-skill) at commit `7d4a135a199a5d7447c4886bcd7ffe742a627bc9`. `LICENSE` is that repository's MIT license, which covers the copy.

`../unslop-hook.py` loads `ste-lint.py` by path and calls its `lint()` function. To update, copy the new `scripts/ste-lint.py` over this file, record the new commit here, and run `python3 hooks/unslop-hook.py --selftest`.
