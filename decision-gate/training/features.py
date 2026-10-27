"""Documented feature schema v1 for accept/reject shell decisions.

Every feature: name, source, units, missing-handling, inclusion reason.
No undefined 32-vector. Extracted ONLY from Proposal fields (readable_state,
action, constraints) - no hidden state.

f01 goal_len_chars      len(goal), chars, missing->0, capacity signal
f02 state_cwd_depth     path separators in readable_state.cwd, count, missing->0, locality
f03 last_exit           readable_state.last_exit, int 0..255, missing-> -1, recent failure signal
f04 env_count           len(env), count, missing->0, context richness
f05 recent_files_n      len(recent_files), count, missing->0, activity
f06 running_jobs_n      len(running_jobs), count, missing->0, contention
f07 cmd_len             len(action.cmd), chars, missing->0, complexity
f08 has_recursive_flag  '-r' in cmd, bool, missing->False, blast radius
f09 has_force_flag      '-f' in cmd, bool, missing->False, blast radius
f10 has_sudo            'sudo' token, bool, missing->False, privilege
f11 targets_root        '/ ' prefix or '/*' in paths, bool, missing->False, blast radius
f12 redirects           '>' or '>>' present, bool, missing->False, mutation
f13 pipes_n             count '|', int, missing->0, compounding
f14 var_expansion       '$' present, bool, missing->False, nondeterminism
f15 quoted_paths_n      count quote pairs, int, missing->0, precision
f16 relative_path       no leading '/' in first path token, bool, missing->True, locality
"""
VERSION = 'features/shell-v1'

import re

def extract(proposal_dict):
    st = proposal_dict.get('readable_state') or {}
    act = proposal_dict.get('action') or {}
    cmd = str(act.get('cmd') or '')
    cwd = str(st.get('cwd') or '')
    goal = str(proposal_dict.get('goal') or '')
    paths = re.findall(r'[\w./~*-]+', cmd)
    return {
        'f01_goal_len': len(goal),
        'f02_cwd_depth': cwd.count('/'),
        'f03_last_exit': int(st['last_exit']) if isinstance(st.get('last_exit'), int) else -1,
        'f04_env_count': int(st.get('env_count') or 0),
        'f05_recent_files': len(st.get('recent_files') or []),
        'f06_jobs': len(st.get('running_jobs') or []),
        'f07_cmd_len': len(cmd),
        'f08_recursive': int('-r' in cmd or '-rf' in cmd),
        'f09_force': int('-f' in cmd),
        'f10_sudo': int('sudo' in cmd.split()),
        'f11_root_target': int(bool(re.search(r'(^|\s)/(?:\s|$)|/\*', cmd))),
        'f12_redirect': int(('>' in cmd)),
        'f13_pipes': cmd.count('|'),
        'f14_var_exp': int('$' in cmd),
        'f15_quoted': len(re.findall('"[^"]+"|\'[^\']+\'', cmd)),
        'f16_relative': int(bool(paths) and not paths[0].startswith('/') and not paths[0].startswith('~')),
    }

ORDER = ['f01_goal_len','f02_cwd_depth','f03_last_exit','f04_env_count','f05_recent_files',
         'f06_jobs','f07_cmd_len','f08_recursive','f09_force','f10_sudo','f11_root_target',
         'f12_redirect','f13_pipes','f14_var_exp','f15_quoted','f16_relative']

def vectorize(proposal_dict):
    d = extract(proposal_dict)
    return [float(d[k]) for k in ORDER], d
