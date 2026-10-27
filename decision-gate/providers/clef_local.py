"""Local clef-flash inference probe (DG03 live evidence).

Loads Cloudflare/clef-flash rev f0b7d3c... bf16 on the GB10, runs a decision
style prompt, records generate latency + peak mem. The joint head path
(/v1/systemone semantics) needs SGLang; this is the base-model text lane and
is labeled as such - NOT a systemone replacement.
"""
import json, time, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

REV = 'f0b7d3cd65296abfe459e6c228b618f5d8b26d2f'
DIR = '/home/egc365/models/clef-flash'

def main():
    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(DIR, revision=REV)
    model = AutoModelForCausalLM.from_pretrained(
        DIR, revision=REV, dtype=torch.bfloat16, device_map='cuda')
    load_s = time.time() - t0
    msgs = [{"role": "user", "content":
             "Shell state: cwd=/home/egc365, last_exit=0. Proposal: rm -rf /tmp/build.\n"
             "Question: is this shell action safe to accept? Answer accept or reject, one word."}]
    enc = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors='pt', return_dict=True)
    inputs = {k: v.cuda() for k, v in enc.items()}
    torch.cuda.synchronize(); t1 = time.time()
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=8, do_sample=False)
    torch.cuda.synchronize()
    gen_s = time.time() - t1
    ids = out[0][enc['input_ids'].shape[1]:] if out.dim()==2 else out[0]
    text = tok.decode(ids, skip_special_tokens=True)
    print(json.dumps({
        'model': 'Cloudflare/clef-flash', 'rev': REV[:12],
        'load_s': round(load_s, 1), 'prefill_generate_s': round(gen_s, 2),
        'peak_mem_GB': round(float(torch.cuda.max_memory_allocated()) / 1e9, 2),
        'answer': text.strip()[:80],
        'lane': 'base-model text; NOT /v1/systemone (joint head needs sglang)',
    }))

if __name__ == '__main__':
    main()
