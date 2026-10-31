const record = value => value && typeof value === 'object' && !Array.isArray(value);

export function hydrateState(primary, legacy, validIds) {
  primary = record(primary) ? primary : null;
  legacy = record(legacy) ? legacy : null;
  const drafts = {};
  for (const source of [legacy, primary]) {
    if (!record(source?.drafts)) continue;
    for (const [id, draft] of Object.entries(source.drafts)) {
      if (record(draft) && ['code', 'stdin', 'expected'].every(key => typeof draft[key] === 'string')) {
        drafts[id] = { code: draft.code, stdin: draft.stdin, expected: draft.expected, compare: draft.compare !== false };
      }
    }
  }
  const valid = new Set(validIds);
  const selected = primary?.mode ?? legacy?.mode;
  const mode = selected === 'free' || valid.has(selected) ? selected : '209';
  const lastProblem = valid.has(primary?.lastProblem) ? primary.lastProblem : mode === 'free' ? '209' : mode;
  const completed = record(primary?.completed)
    ? Object.fromEntries(Object.entries(primary.completed).filter(([id, value]) => valid.has(id) && value === true))
    : { '42': true }; // The user explicitly reported finishing this problem in this conversation.
  return { mode, lastProblem, drafts, completed };
}
