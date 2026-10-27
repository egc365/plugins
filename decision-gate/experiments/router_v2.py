"""Router v2: discriminator-token scoring.

v1 lesson: full-completion NLL dilutes the signal. v2 scores ONLY the
discriminator tokens - the object-name token span inside the completion -
where task identity actually lives. Also 1-shot prompt per candidate and
length-normalized comparison. Same split, same freeze: threshold n/a (argmin),
C: beat 82.5% ngram on identical instance-LOO split.
"""
from __future__ import annotations
import json, re, sys
sys.path.insert(0, '/home/egc365/dg-worktree/decision-gate')
sys.path.insert(0, '/home/egc365/nanochat')
import nanochat.flash_attention as fa
fa._override_impl = 'sdpa'; fa.USE_FA3 = False
import torch
from training.blender_sft import load_pairs
from experiments.d8_router import nll_of

def ngrams(s, n=4):
    s = re.sub(r'[^a-z0-9 ]', '', s.lower())
    return set(s[i:i+n] for i in range(len(s)-n+1))
def sim(a, b):
    A, B = ngrams(a), ngrams(b)
    return len(A & B) / max(1, len(A | B))

def discriminator_span(task):
    # the object noun tokens: primitive_X_add -> X; suzanne->monkey head etc via map
    m = {'bbl-add-cube':['cube'],'bbl-suzanne':['monkey','Suzanne'],
         'bbl-uv-sphere':['sphere'],'bbl-torus':['torus','donut'],
         'bbl-cylinder':['cylinder'],'bbl-cone':['cone'],
         'bbl-icosphere':['icosphere'],'bbl-circle':['circle'],
         'bbl-plane':['plane'],'bbl-grid':['grid']}
    return m.get(task, [])

def main(cap=40, seed=7):
    import torch
    torch.manual_seed(seed)
    rows = [r for r in load_pairs() if r['label'] == 'accept']
    R = sys.modules['experiments.d8_router'] if 'experiments.d8_router' in sys.modules else None
    from experiments import d8_router as Rmod
    Rmod.CKPT = '/home/egc365/.cache/nanochat/base_checkpoints/d8'
    tok, model = Rmod.load()
    def ngrams_safe(s, n=4):
        return ngrams(s, n)
    cn = cd = total = 0
    for i, held in enumerate(rows):
        if i >= cap: break
        pool = [r for j, r in enumerate(rows) if j != i]
        goal = held['notes'].split('prompt=')[-1].split(' |')[0]
        by_t = {}
        for r in pool:
            g = r['notes'].split('prompt=')[-1].split(' |')[0]
            by_t.setdefault(r['task_id'], []).append(g)
        ng = max(by_t, key=lambda t: max(sim(goal, g) for g in by_t[t]))
        cn += ng == held['task_id']
        sc = {}
        for tid, pairs in by_t.items():
            ctx = '\n'.join(pairs[:2])
            # discriminator completion: the task's own phrase w/ object noun, short
            disco = ' '.join(discriminator_span(tid))
            p = f"Blender task examples:\n{ctx}\n\nNew task: {goal}\nThe key object here is the"
            try:
                ids = torch.tensor([tok.encode(p + '\n' + disco, prepend=tok.get_bos_token_id())], device='cuda')
                npre = len(tok.encode(p, prepend=tok.get_bos_token_id()))
                with torch.no_grad():
                    logits = model(ids)
                lg = logits[0, npre-1:-1, :]
                tgt = ids[0, npre:]
                m = min(lg.shape[0], tgt.shape[0])
                sc[tid] = float(torch.nn.functional.cross_entropy(lg[:m], tgt[:m], reduction='mean'))
            except Exception:
                continue
        if sc:
            dbest = min(sc, key=sc.get)
            cd += dbest == held['task_id']
        total += 1
    return {'n': total,
            'ngram_instance_acc': round(cn/total, 3),
            'd8v2_discriminator_acc': round(cd/total, 3),
            'beat_baseline': cd/total > 0.825}

if __name__ == '__main__':
    import json
    print(json.dumps(main(), indent=1))
