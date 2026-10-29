"""Local fixture reduction; execute trusted oracles only."""
import argparse, csv, hashlib, io, json, subprocess, sys, tempfile
from pathlib import Path

def load(path):
    if path.suffix == '.json': data = json.loads(path.read_text(encoding='utf-8'))
    elif path.suffix == '.csv':
        with path.open(encoding='utf-8', newline='') as f: data = list(csv.DictReader(f))
    else: raise ValueError('input must be JSON or CSV')
    if not isinstance(data, list) or any(not isinstance(r, dict) or any(not isinstance(v, (str, int, float, bool, type(None))) for v in r.values()) for r in data): raise ValueError('expected flat records')
    return data

def prepare(rows, policy):
    fields = policy.get('fields')
    if not isinstance(fields, dict) or not fields or any(v not in ('keep','replace') for v in fields.values()): raise ValueError('fields must map names to keep or replace')
    groups = policy.get('relationships', [])
    if not isinstance(groups, list) or any(not isinstance(g,list) or len(g)<2 or any(f not in fields or fields[f]!='replace' for f in g) for g in groups): raise ValueError('invalid relationship groups')
    flat = [f for g in groups for f in g]
    if len(flat)!=len(set(flat)): raise ValueError('overlapping relationship groups')
    namespaces = {f: str(i) for i,g in enumerate(groups) for f in g}
    maps = {}; output = []
    for row in rows:
        out = {}
        for field, mode in fields.items():
            if field not in row: continue
            value = row[field]
            if mode == 'replace' and value is not None:
                mapping = maps.setdefault(('group',namespaces[field]) if field in namespaces else ('field',field), {})
                key = (type(value).__name__, json.dumps(value))
                if key not in mapping: mapping[key] = 'seed_' + str(len(mapping)+1)
                value = mapping[key]
            out[field] = value
        output.append(out)
    return output

def encode(rows, suffix, fields):
    if suffix == '.json': return (json.dumps(rows,indent=2,ensure_ascii=False)+'\n').encode()
    f=io.StringIO(newline=''); writer=csv.DictWriter(f,fieldnames=list(fields),lineterminator='\n'); writer.writeheader(); writer.writerows(rows)
    return f.getvalue().encode('utf-8')

def run(source, policy_path, output, command, timeout=5, budget=100):
    source, policy_path, output = map(Path,(source,policy_path,output))
    if timeout <= 0 or budget < 4: raise ValueError('timeout must be positive and budget at least 4')
    if command.count('{input}') != 1: raise ValueError('command needs exactly one {input} argument')
    if output.exists(): raise ValueError('output already exists')
    rows=load(source); policy=json.loads(policy_path.read_text(encoding='utf-8')); candidate=prepare(rows,policy); calls=0
    with tempfile.TemporaryDirectory(prefix='seed-') as tmp:
        path=Path(tmp)/('candidate'+source.suffix)
        def oracle(data, original=False):
            nonlocal calls
            calls += 1; path.write_bytes(encode(data,source.suffix,list(dict.fromkeys(k for r in rows for k in r)) if original else policy['fields']))
            try: p=subprocess.run([str(path) if a=='{input}' else a for a in command],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=timeout,shell=False)
            except (OSError,subprocess.TimeoutExpired) as e: raise ValueError('oracle failed or timed out') from e
            return p.returncode
        baseline=oracle(rows, True)
        if baseline<=0: raise ValueError('original did not produce a normal nonzero failure')
        if oracle(rows, True)!=baseline: raise ValueError('original failure is unstable')
        if oracle(candidate)!=baseline: raise ValueError('policy transformation changed failure')
        i=0
        while i<len(candidate) and calls<budget-1:
            trial=candidate[:i]+candidate[i+1:]
            if oracle(trial)==baseline: candidate=trial
            else: i+=1
        if oracle(candidate)!=baseline: raise ValueError('final failure is unstable')
    output.mkdir(parents=True)
    fixture=encode(candidate,source.suffix,policy['fields']); (output/('fixture'+source.suffix)).write_bytes(fixture)
    receipt={'status':'REVIEW_REQUIRED','privacy_guarantee':False,'failure_exit_code':baseline,'oracle_calls':calls,'input_records':len(rows),'output_records':len(candidate),'fixture_sha256':hashlib.sha256(fixture).hexdigest(),'note':'Review all retained data and derived facts before sharing.'}
    (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8'); return receipt

def main():
    p=argparse.ArgumentParser(); p.add_argument('--trust-oracle',action='store_true'); p.add_argument('--timeout',type=float,default=5); p.add_argument('--budget',type=int,default=100); p.add_argument('input'); p.add_argument('policy'); p.add_argument('output'); p.add_argument('command',nargs=argparse.REMAINDER)
    a=p.parse_args()
    if not a.trust_oracle: p.error('--trust-oracle is required')
    cmd=a.command[1:] if a.command[:1]==['--'] else a.command
    try: print(json.dumps(run(a.input,a.policy,a.output,cmd,a.timeout,a.budget),indent=2))
    except (ValueError,OSError) as e: print('Seed: '+str(e),file=sys.stderr); return 1
    return 0
if __name__=='__main__': sys.exit(main())
