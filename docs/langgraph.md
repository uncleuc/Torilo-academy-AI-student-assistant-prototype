# LangGraph and Assistant

## Public Contract

Group 2 exports `run_student_assistant(message, conversation_id=None)`. It returns exactly the API handoff fields:

```python
{
	"answer": "...",
	"sources": [],
	"conversation_id": "..."
}
```

The graph is constructed with three injected dependencies: a Group 1 retriever, a mapping of Group 3 database tool callables, and an `invoke(messages)` chat model. It does not own a database or vector-store connection.

## Routes

| Route | Behavior |
| --- | --- |
| `SAFETY` | Deterministic screen blocks direct override/fabrication/secret-extraction attempts; fixed response; no services called. |
| `RAG` | Fresh approved context retrieved from `retrieve_documents(query)`; model runs only if usable evidence exists. |
| `DATABASE` | One fixed allowlisted tool is called; ID-based course tools require one unique `course_id` search match. |
| `GENERAL` | Model handles a simple greeting/social turn without academy claims. |
| `CLARIFY` | Ask a short question when the request or referent is genuinely ambiguous; no data tool is called. |
| `UNAVAILABLE` | Explain that current/private data cannot be verified and provide Student Support contact details. |
| `UNKNOWN` | Fixed insufficient-information response; no retrieval, database, or model call. |

After the safety check, a structured-output classifier produces a validated intent, entities, time-sensitivity, confidence, and clarification decision. It never selects a tool. A fixed policy maps public stable facts to RAG, current schedules to the schedule tool, and private student data to unavailable. If structured output fails, a conservative local classifier is used. Ambiguous requests clarify; unsupported Academy facts receive a safe support handoff.

RAG query expansion runs only after the fixed policy selects RAG. It retains the original query first and adds at most two deterministic spelling/phrase variants. The original student message is still used to generate the answer. General course catalog questions use the approved KB, not database fixtures.

Database tools and public course endpoints are unavailable unless `DATABASE_DATA_VERIFIED=true`. This flag defaults to false and is an explicit operator assertion that records are maintained, current, authorized Academy data; it is not an automated verification mechanism.

## State and Evidence

`AssistantState` contains the current message, conversation ID, bounded role/content history, validated classification, route, retrieval/tool results, answer and sources. It must not contain secrets, ORM sessions, service clients or raw exception objects. Retrieved text, database values and history are untrusted data, not instructions.

The response node applies an evidence-presence gate. RAG context must be non-empty and approved; database results must be non-empty. This is not a semantic entailment proof, so prompts, citations, scenario tests and review remain important.

## Conversation Memory

The current `InMemoryConversationMemory` is process-local, bounded, and isolated by conversation ID. It is suitable for local development/single-process demonstrations only; history disappears on restart and is not shared across replicas. Conversation IDs are not credentials or authorization.

## Safety Limitations

Regex screening is defense in depth, not a complete prompt-injection defense. Harder guarantees come from fixed routes/tool allowlists, no service calls on blocked/unknown paths, approved evidence gates, source whitelisting and not trusting instructions embedded in documents or records.
