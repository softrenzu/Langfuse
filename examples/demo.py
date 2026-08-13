from aiops.costops import budget_status, set_budget
from aiops.ops import compare, incidents, overview, recommendations
from aiops.promptops import put_prompt
from aiops.recording import record_span

set_budget("monthly", 25.0)
put_prompt("answer", "Answer concisely", ["production"])

for i in range(20):
    record_span(
        name="answer",
        model="demo-model",
        latency_ms=9000 if i == 19 else 300 + i * 20,
        cost_usd=0.004,
        status="error" if i == 7 else "ok",
        error="rate limit exceeded" if i == 7 else None,
        metadata={"prompt_version": "v2" if i >= 10 else "v1"},
    )

print("overview", overview(60))
print("incidents", incidents(60))
print("recommendations", recommendations(60))
print("comparison", compare("prompt_version"))
print("budget", budget_status())
