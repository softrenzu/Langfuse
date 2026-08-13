from __future__ import annotations
import time
from collections import defaultdict
from .analytics import build_incidents, compare_variants, summarize
from .otel import parse_otlp_json
from .recording import load_spans, record_span

def overview(minutes=60):
    items=load_spans(time.time()-minutes*60); data=summarize(items)
    data['incidents']=len(build_incidents(items)); data['window_minutes']=minutes
    return data

def incidents(minutes=1440):
    return build_incidents(load_spans(time.time()-minutes*60))

def recommendations(minutes=1440):
    actions=[r for i in incidents(minutes) for r in i['recommendations']]
    return list(dict.fromkeys(actions))[:10]

def compare(key='prompt_version', minutes=10080):
    return compare_variants(load_spans(time.time()-minutes*60), key)

def traces(limit=100):
    groups=defaultdict(list)
    for s in load_spans(): groups[s['trace_id']].append(s)
    out=[]
    for trace_id,items in groups.items():
        out.append({'trace_id':trace_id,'span_count':len(items),'status':'error' if any(x['status']=='error' for x in items) else 'ok','cost_usd':round(sum(x['cost_usd'] for x in items),6),'latency_ms':round(max(x['latency_ms'] for x in items),2),'started_at':min(x['ts'] for x in items)})
    return sorted(out,key=lambda x:x['started_at'],reverse=True)[:limit]

def ingest_otlp(payload):
    items=parse_otlp_json(payload)
    for p in items: record_span(**{k:p[k] for k in p if k!='kind'})
    return len(items)
