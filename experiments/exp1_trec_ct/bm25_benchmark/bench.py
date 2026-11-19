import sys, json, re, time, resource
lib, n = sys.argv[1], int(sys.argv[2])
S = sys.argv[3]
tok = lambda s: re.findall(r"[a-z0-9]+", s.lower())
texts = []
with open(f"{S}/corpus.jsonl", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if i >= n: break
        texts.append(json.loads(line)["text"])
queries = [json.loads(l)["text"] for l in open(f"{S}/queries_2021.jsonl", encoding="utf-8")]
K = 100
rss = lambda: resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6  # Go (Linux : Ko)
t0 = time.time()
if lib == "rank_bm25":
    from rank_bm25 import BM25Okapi
    docs = [tok(t) for t in texts]; t_tok = time.time() - t0
    t1 = time.time(); m = BM25Okapi(docs); t_idx = time.time() - t1
    qs = [list(dict.fromkeys(tok(q))) for q in queries[:5]]
    t2 = time.time(); [m.get_scores(q) for q in qs]; t_q = (time.time() - t2) / len(qs)
elif lib == "bm25s":
    import bm25s
    docs = [tok(t) for t in texts]; t_tok = time.time() - t0
    t1 = time.time(); m = bm25s.BM25(method="lucene", k1=0.9, b=0.4); m.index(docs, show_progress=False); t_idx = time.time() - t1
    qs = [tok(q) for q in queries]
    t2 = time.time()
    for q in qs: m.retrieve([q], k=K, show_progress=False)
    t_q = (time.time() - t2) / len(qs)
elif lib == "bm25_turbo":
    from bm25_turbo_python import BM25
    t_tok = 0.0
    t1 = time.time(); m = BM25(method="lucene", k1=0.9, b=0.4); m.index(texts); t_idx = time.time() - t1
    t2 = time.time()
    for q in queries: m.search(q, k=K)
    t_q = (time.time() - t2) / len(queries)
elif lib == "tantivy":
    import tantivy
    t_tok = 0.0
    sb = tantivy.SchemaBuilder(); sb.add_text_field("body", stored=False); schema = sb.build()
    t1 = time.time(); idx = tantivy.Index(schema); w = idx.writer()
    for t in texts: w.add_document(tantivy.Document(body=[t]))
    w.commit(); idx.reload(); t_idx = time.time() - t1
    s = idx.searcher()
    t2 = time.time()
    for q in queries: s.search(idx.parse_query_lenient(q, ["body"])[0], K)
    t_q = (time.time() - t2) / len(queries)
print(json.dumps({"lib": lib, "n_docs": n, "tokenisation_s": round(t_tok, 1), "indexation_s": round(t_idx, 1),
                  "s_par_requete": round(t_q, 4), "pic_memoire_Go": round(rss(), 2)}))
