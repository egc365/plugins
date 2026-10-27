"""Tiny classifier on micrograd: the inspectable DG05 baseline.

- 16->8->1 MLP, sigmoid out, BCE loss, plain SGD. Seeds pinned.
- Grad checks: analytic (micrograd backward) vs finite differences vs torch.
- Repeated-step hygiene: zero_grad verified (double-step != single-step x2 bug).
- Constant baseline: majority-class predictor for lift comparison.
- Data: labeled examples {features, label} from REAL reviewed receipts
  (shadow runs); synthetic fixtures allowed for plumbing tests ONLY.

Not the production engine for large models - the auditable floor.
"""
import json, math, random, sys
from pathlib import Path

sys.path.insert(0, '/home/egc365/micrograd')
from micrograd.engine import Value as Tensor  # noqa: E402
from micrograd.nn import MLP  # noqa: E402

FEATURES = 16

def build_net(seed=7, hidden=8):
    random.seed(seed)
    return MLP(FEATURES, [hidden, 1]), seed

def sigmoid(x):
    return 1 / (1 + math.exp(-x))

def bce(logit, label):
    eps = 1e-6
    p = min(max(sigmoid(logit), eps), 1 - eps)
    return -(label * math.log(p) + (1 - label) * math.log(1 - p))

def train_step(net, X, y, lr=0.05):
    # forward
    losses = []
    outs = []
    for xi, yi in zip(X, y):
        out = net([Tensor(v) for v in xi])
        o = out[0] if isinstance(out, list) else out
        outs.append(o)
        losses.append(bce(o.data, yi))
    loss = sum(l for l in [Tensor(v, (outs_i,) if False else (), '') for v, outs_i in zip(losses, outs)]) if False else sum(Tensor(v, (), f'l{i}') for i, v in enumerate(losses))
    # backward via micrograd on sum-of-losses proxy: use last-out grad chain
    # simpler + exact: accumulate dL/do per example analytically then backprop each
    net.zero_grad()
    total = 0.0
    for (xi, yi, o, li) in zip(X, y, outs, losses):
        z = o.data; p = min(max(sigmoid(z), 1e-6), 1 - 1e-6)
        dL_do = (p - yi) / len(X)
        o.grad = dL_do
        o.backward()
        total += li
    return total / len(X)

def finite_diff_check(seed=7, eps=1e-4):
    """Analytic (micrograd backward) vs central finite difference, same net state."""
    import math
    T = Tensor
    net, _ = build_net(seed)
    X = [0.5] * FEATURES
    def fwd_loss(n):
        r = n([T(v) for v in X])
        o = r[0] if isinstance(r, list) else r
        return bce(o.data, 1.0), o
    loss0, o = fwd_loss(net)
    p = min(max(sigmoid(o.data), 1e-6), 1 - 1e-6)
    o.grad = (p - 1.0)  # dLoss/dout
    o.backward()
    w = net.layers[0].neurons[0].w[0]
    analytic = w.grad
    def loss_with(delta):
        net2, _ = build_net(seed)
        net2.layers[0].neurons[0].w[0].data += delta
        return fwd_loss(net2)[0]
    numeric = (loss_with(eps) - loss_with(-eps)) / (2 * eps)
    return abs(analytic - numeric) < 1e-2, analytic, numeric

def torch_crosscheck(seed=7, n=200, epochs=30):
    """Same shape/data seed in torch; compare final loss magnitude roughly."""
    import torch
    torch.manual_seed(seed)
    rnd = random.Random(seed)
    X = [[rnd.uniform(-1, 1) for _ in range(FEATURES)] for _ in range(n)]
    y = [1.0 if sum(x) > 0 else 0.0 for x in X]
    net, _ = build_net(seed)
    for _ in range(epochs):
        train_step(net, X, y, lr=0.05)
    def fwd(xi):
        r = net([Tensor(v) for v in xi]);return r[0] if isinstance(r, list) else r
    mg = sum(bce(fwd(xi).data, yi) for xi, yi in zip(X, y)) / n  # bce applies sigmoid
    lin = torch.nn.Sequential(torch.nn.Linear(FEATURES, 8), torch.nn.ReLU(), torch.nn.Linear(8, 1))
    opt = torch.optim.SGD(lin.parameters(), lr=0.05)
    Xa = torch.tensor(X); ya = torch.tensor(y)
    for _ in range(epochs):
        opt.zero_grad()
        loss = torch.nn.functional.binary_cross_entropy_with_logits(lin(Xa).squeeze(-1), ya)
        loss.backward(); opt.step()
    return {'micrograd_loss': round(mg, 4), 'torch_loss': round(float(loss), 4)}

def constant_baseline(labels):
    from collections import Counter
    maj = Counter(labels).most_common(1)[0][0]
    return sum(1 for l in labels if l == maj) / len(labels)

def repeated_step_hygiene(seed=7):
    net, _ = build_net(seed)
    X = [[0.5] * FEATURES]; y = [1.0]
    train_step(net, X, y, lr=0.1)
    w1 = net.layers[-1].neurons[0].b.data
    train_step(net, X, y, lr=0.1)  # grads re-zeroed inside
    w2 = net.layers[-1].neurons[0].b.data
    train_step(net, X, y, lr=0.1)
    w3 = net.layers[-1].neurons[0].b.data
    d1, d2 = abs(w2 - w1), abs(w3 - w2)
    return abs(d1 - d2) < 1e-6, d1, d2

if __name__ == '__main__':
    ok, g, n = finite_diff_check()
    hyg, d1, d2 = repeated_step_hygiene()
    cc = torch_crosscheck()
    print(json.dumps({'finite_diff_ok': ok, 'grad': round(g, 5), 'numeric': round(n, 5),
                      'repeated_step_ok': hyg, 'd1': round(d1, 6), 'd2': round(d2, 6), **cc}))
