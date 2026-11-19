import json, re, time, resource, sys
from array import array
import numpy as np, scipy.sparse as sp
S = sys.argv[1]
words_in = re.compile(r"[a-z0-9]+").findall
K1, B, TOPK = 0.9, 0.4, 100
vocab, indptr, indices, tf, doc_len = {}, array("q", [0]), array("i"), array("f"), array("i")
t0 = time.time()
with open(f"{S}/corpus.jsonl", encoding="utf-8") as f:
    for line in f:
        words = words_in(json.loads(line)["text"].lower())
        doc_len.append(len(words)); counts = {}
        for w in words:
            j = vocab.setdefault(w, len(vocab)); counts[j] = counts.get(j, 0) + 1
        indices.extend(counts.keys()); tf.extend(counts.values()); indptr.append(len(indices))
t_tok = time.time() - t0
t1 = time.time()
N, V = len(doc_len), len(vocab)
tf_m = sp.csr_matrix((np.frombuffer(tf, dtype=np.float32), np.frombuffer(indices, dtype=np.int32), np.frombuffer(indptr, dtype=np.int64)), shape=(N, V))
dl = np.frombuffer(doc_len, dtype=np.int32).astype(np.float32)
df = np.bincount(tf_m.indices, minlength=V).astype(np.float32)
idf = np.log1p((N - df + 0.5) / (df + 0.5)).astype(np.float32)               # idf de Lucene
row_of_entry = np.repeat(np.arange(N), np.diff(tf_m.indptr))
norm = K1 * (1 - B + B * dl[row_of_entry] / dl.mean())
tf_m.data = (tf_m.data * (K1 + 1) / (tf_m.data + norm) * idf[tf_m.indices]).astype(np.float32)
W = tf_m.tocsc(); del tf_m, row_of_entry, norm
t_idx = time.time() - t1
queries = [json.loads(l)["text"].lower() for l in open(f"{S}/queries_2021.jsonl", encoding="utf-8")]
t2 = time.time()
for q in queries:
    cols = [vocab[w] for w in words_in(q) if w in vocab]          # avec répétitions, comme Lucene
    scores = np.asarray(W[:, cols].sum(axis=1)).ravel()
    top = np.argpartition(-scores, TOPK)[:TOPK]
t_q = (time.time() - t2) / len(queries)
print(json.dumps({"lib": "prototype_creux", "n_docs": N, "vocabulaire": V, "entrées_non_nulles": int(W.nnz),
                  "tokenisation_s": round(t_tok, 1), "indexation_s": round(t_idx, 1), "s_par_requete": round(t_q, 4),
                  "pic_memoire_Go": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6, 2)}))
