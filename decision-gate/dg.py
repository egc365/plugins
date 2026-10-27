"""Decision-gate CLI. Missing implementations exit nonzero NOT_IMPLEMENTED."""
import argparse, json, sys
sys.path.insert(0, __file__.rsplit('/', 2)[0] + '/decision-gate')
from contracts.schemas import Proposal, Decision, ExecutionReceipt, ContractError  # noqa


def cmd_proposal(args):
    p = Proposal.create(
        task_id=args.task, app_id=args.app, goal=args.goal,
        constraints={}, readable_state={}, action={'op': args.op})
    print(p.to_json())


def cmd_validate_decision(args):
    d = Decision(proposal_hash=args.hash, model_id=args.model,
                 runtime_rev='r0', route=args.route, schema_rev='dg1',
                 probabilities={'accept': float(args.p)},
                 policy_outcome=args.outcome, threshold_config={},
                 evaluated_at=0.0)
    d.validate(); print(d.to_json())


def cmd_stub(name):
    print(json.dumps({'status': 'NOT_IMPLEMENTED', 'command': name}))
    return 2


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    sp = sub.add_parser('proposal'); sp.add_argument('--task', required=True)
    sp.add_argument('--app', required=True); sp.add_argument('--goal', required=True)
    sp.add_argument('--op', default='noop')
    sp.set_defaults(fn=cmd_proposal)
    sd = sub.add_parser('decision'); sd.add_argument('--hash', required=True)
    sd.add_argument('--model', required=True); sd.add_argument('--route', default='/v1/decisions')
    sd.add_argument('--p', required=True); sd.add_argument('--outcome', default='accept')
    sd.set_defaults(fn=cmd_validate_decision)
    for name in ('execute', 'evaluate', 'serve', 'bench', 'live-check'):
        s = sub.add_parser(name); s.set_defaults(fn=lambda a, n=name: cmd_stub(n))
    args = ap.parse_args()
    sys.exit(args.fn(args) or 0)


if __name__ == '__main__':
    main()
