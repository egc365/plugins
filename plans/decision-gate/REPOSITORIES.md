# Repository inventory

Observed 2026-10-27. This list records discovery, not integration or compatibility results. Private integration details belong in a local manifest.

| Repository | Intended role | Evidence/status |
| --- | --- | --- |
| [egc365/plugins](https://github.com/egc365/plugins) | PStack source and build-plan home | Existing public fork of cursor/plugins; main commit 99743e9c151c8537cbbf1f98bb38f34ef3368453; PStack manifest and relevant skills inspected |
| [egc365/autoresearch](https://github.com/egc365/autoresearch) | Bounded experiment workflow reference | Existing public fork of karpathy/autoresearch; README inspected; its original language-model metric is not an action-correctness evaluator |
| [karpathy/micrograd](https://github.com/karpathy/micrograd) | Tiny autograd and classifier training baseline | Upstream master commit 7bc720e951fe422b8f8814aa5aa1b64121d26b4c; README inspected; no user fork found among accessible repos; fork/reuse pending |
| [egc365/Qwen3.8-27B-SGLang-DGX-Spark](https://github.com/egc365/Qwen3.8-27B-SGLang-DGX-Spark) | Standard Qwen serving reference | Existing public fork; README inspected; does not establish support for Clef's custom head on Spark |
| [egc365/awesome-jev-by-typesafe](https://github.com/egc365/awesome-jev-by-typesafe) | Jev references | Repository existence verified; implementation suitability to inspect |
| [egc365/deepseek-harness](https://github.com/egc365/deepseek-harness) | Local harness candidate | Existence verified; inspect before selection |
| [egc365/dsh-codex-connect](https://github.com/egc365/dsh-codex-connect) | Agent connection candidate | Existence verified; inspect before selection |
| [egc365/dsh-xai](https://github.com/egc365/dsh-xai) | Action capture candidate | Existence verified; inspect exposed data and terms |
| [egc365/sgl-cookbook](https://github.com/egc365/sgl-cookbook) | Serving recipes | Existence verified; pin applicable version |
| [egc365/ms-swift](https://github.com/egc365/ms-swift) | Training framework candidate | Existence verified; suitability not yet tested |
| [egc365/dgx-spark-playbooks](https://github.com/egc365/dgx-spark-playbooks) | Hardware recipes | Existence verified; hardware access not established |

No forks, model downloads, training runs, or runtime integrations are implied by this inventory. The launch workflow should pin all selected dependencies and preserve their licenses.
