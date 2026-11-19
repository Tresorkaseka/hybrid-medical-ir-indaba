"""Read-only coherence audit of completed Indaba artifacts; no inference or GPU access."""
import gzip
import hashlib
import json
import math
import re
from pathlib import Path
from hybrid_ir.decision.reranking import unique_pairs, load_checkpoint_scores, rerank_with_scores
from hybrid_ir.decision.reranker_control import load_control_scores, rerank_with_logits
from hybrid_ir.evaluation.significance import holm_adjust
from hybrid_ir.evaluation.run_scoring import score_run
from hybrid_ir.data.trec_files import load_judgments
ROOT=Path(__file__).resolve().parents[1]
checks=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes())
def check(label,condition):
 if not condition:raise AssertionError(label)
 checks.append(label)
def close(a,b):return math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12)
report=load(ROOT/'results/exp1_decision_eos_bge.json')
source_path=ROOT/'results/exp1_rankings_bc.json.gz';bc=load(source_path)
payload_path=ROOT/'data/processed/decision_inputs.json.gz';payload=load(payload_path)
check('125 descriptions, 6256 trial texts, 7340 unique patient-trial pairs',len(payload['queries'])==125 and len(payload['trials'])==6256 and len(unique_pairs(payload))==7340)
check('source rankings match frozen decision input hash',payload['source_rankings_sha256']==sha(source_path))
check('complete evaluation with eight configurations',report['status']=='complete' and set(report['2021']['systems'])=={'BM25','A','B','C','D','E','Dprime','Eprime'})
for kind,path,checkpoint,loader,reranker in [
 ('D/E','exp1_rankings_de.json.gz','eos-v2-raw/scores-07340.jsonl',load_checkpoint_scores,rerank_with_scores),
 ('Dprime/Eprime','exp1_rankings_bge_controls.json.gz','bge-control-raw/scores_logits-07340.jsonl',load_control_scores,rerank_with_logits)]:
 artifact_path=ROOT/'results'/path;artifact=load(artifact_path);cp=ROOT/'results'/checkpoint
 check(kind+' input provenance',artifact['provenance']['input_sha256']==sha(payload_path))
 check(kind+' source provenance',artifact['source_rankings_sha256']==sha(source_path))
 check(kind+' checkpoint hash',artifact['checkpoint_sha256']==sha(cp))
 check(kind+' evaluation input hash',report['input_sha256'][kind]==sha(artifact_path))
 scores=loader(payload,cp,artifact['provenance'],require_complete=True)
 check(kind+' exact stable reconstruction from raw scores',reranker(bc['rankings'],scores)==artifact['rankings'])
 for config,base in [('D','B'),('E','C')] if kind=='D/E' else [('Dprime','B'),('Eprime','C')]:
  check(config+' top50 pool and 950 unchanged tail IDs',all(len(ids)==1000 and set(ids[:50])==set(bc['rankings'][base][q][:50]) and ids[50:]==bc['rankings'][base][q][50:] for q,ids in artifact['rankings'][config].items()))
  for y in ['2021','2022']:
   qrels=load_judgments(ROOT/f'data/processed/qrels_{y}.tsv');runs={k.split('/')[1]:v for k,v in artifact['rankings'][config].items() if k.startswith(y+'/')}
   recomputed=score_run(runs,qrels)
   check(f'{y} {config} all per-query metrics from original qrels',all(close(v,report[y]['per_query'][config][m][q]) for m,values in recomputed.items() for q,v in values.items()))
check('B/C evaluation input hash',report['input_sha256']['B/C']==sha(source_path))
for y,nq in [('2021',75),('2022',50)]:
 a=report[y];f=a['holm_family'];check(y+' 99 observed tests, zero reserved',f['n_tests']==f['n_observed_tests']==99 and f['n_reserved_tests']==0)
 check(y+' exact metric count',a['values_crosschecked_with_ir_measures']==nq*8*10)
 raw=[];saved=[]
 for pair,metrics in a['pairs'].items():
  for metric,v in metrics.items():
   if metric=='Judged@10':continue
   raw.append(v['p']);saved.append(v['p_holm'])
   first,second=pair.split(' − ');delta=a['systems'][first][metric]['mean']-a['systems'][second][metric]['mean']
   check(f'{y} {pair} {metric} mean difference',close(delta,v['difference']['mean']))
 check(y+' Holm independently recomputed from 99 raw p-values',all(close(a,b) for a,b in zip(holm_adjust(raw),saved)))
 for config,metrics in a['per_query'].items():
  for metric,values in metrics.items():check(f'{y} {config} {metric} mean',len(values)==nq and close(sum(values.values())/nq,a['systems'][config][metric]['mean']))
 pool=load(ROOT/'results/exp1_pool_recall50.json');qrels=load_judgments(ROOT/f'data/processed/qrels_{y}.tsv')
 for config in ['B','C']:
  values={q:len(set(bc['rankings'][config][f'{y}/{q}'][:50]) & {d for d,l in labels.items() if l==2})/sum(l==2 for l in labels.values()) for q,labels in qrels.items()}
  check(y+' '+config+' pool recall50',values==pool[y][config]['per_query'] and close(sum(values.values())/nq,pool[y][config]['mean_recall_at_50']))
for name in ['main.tex','main_fr.tex']:
 s=(ROOT/'paper'/name).read_text();start=s.index('    2021 & BM25');end=s.index('\\bottomrule',start);n=0;y=None
 for line in s[start:end].splitlines():
  if '&' not in line:continue
  fields=[x.strip() for x in line.replace('{,}','.').split('&')]
  if fields[0]:y=fields[0]
  config=fields[1].replace("D$'$",'Dprime').replace("E$'$",'Eprime')
  for value,metric in zip(fields[2:],['P@10','R@10','RPrec','MRR','nDCG@10','Judged@10']):
   check(name+' '+y+' '+config+' '+metric,float(value.replace('\\\\','').strip())==round(report[y]['systems'][config][metric]['mean'],3));n+=1
 check(name+' 96 table values',n==96)
js=(ROOT/'presentation/slides.js').read_text();quality=json.loads(re.search(r'const quality = (.*?);',js)[1]);configs=['BM25','A','B','C','D','E','Dprime','Eprime']
check('16 chart values',all(quality[y]==[report[y]['systems'][c]['nDCG@10']['mean'] for c in configs] for y in quality))
check('presentation JSON identical to canonical report',(ROOT/'presentation/data/exp1_decision_eos_bge.json').read_bytes()==(ROOT/'results/exp1_decision_eos_bge.json').read_bytes())
bge=load(ROOT/'results/bge-control-raw/run_report.json');pre=load(ROOT/'results/bge-control-raw/preflight.json')
check('BGE report complete and untruncated',bge['status']=='complete' and bge['n_saved']==bge['n_pairs']==7340 and bge['truncation'] is False and pre['n_valid']==pre['n_pairs']==7340 and not pre['invalid'] and pre['max_tokens']<=pre['context_limit'])
result={'status':'pass','date':'2026-11-19','n_checks':len(checks),'checks':checks,'canonical_report_sha256':sha(ROOT/'results/exp1_decision_eos_bge.json'),'scope':'read-only scores, provenance, reconstruction, means, Holm, pool recall and document data; no inference, no clinical or bibliographic validation'}
(ROOT/'results/indaba_coherence_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(f'PASS: {len(checks)} checks. No inference. results/indaba_coherence_audit.json')
