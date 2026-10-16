// Sprint 3 UND-10 AC4-5 (ARCH §4 "Candidate values", ADR-0013): Jev
// chooses a tool's open arguments; it never writes them. Each open
// argument gets a finite list of candidates, first non-empty wins:
//
//   1. the values the sketch lists for it (`values: { <tool>: { <arg>: [...] } }`)
//   2. what its schema allows: every `enum` value, true/false, or each
//      whole number of an integer whose minimum and maximum are close
//   3. the strings or numbers in the last result that was not an error
//      (structured content, or text that is JSON), at most `MAX_CANDIDATES`
//
// and Jev answers one Choice per argument, in one request.

const MAX_RANGE = 20;
export const MAX_CANDIDATES = 20;
const MAX_LENGTH = 200;

/**
 * Every string and number inside a value, in order, however deep.
 */
function leaves(value) {
  if (typeof value === 'string' || typeof value === 'number') return [value];
  if (Array.isArray(value)) return value.flatMap((each) => leaves(each));
  if (value && typeof value === 'object') return Object.values(value).flatMap((each) => leaves(each));
  return [];
}

/**
 * What the last result offers as values: its structured content, and its
 * text when that is JSON.
 * @param {{ text?: string, structured?: object }|null} last
 */
export function resultValues(last) {
  if (!last || last.isError) return [];
  const found = leaves(last.structured ?? null);
  try {
    found.push(...leaves(JSON.parse(last.text ?? '')));
  } catch { /* plain text offers no values */ }
  return found;
}

function fromSchema(schema) {
  if (Array.isArray(schema.enum)) return [...schema.enum];
  if (schema.type === 'boolean') return [true, false];
  const { minimum, maximum } = schema;
  if (schema.type === 'integer' && Number.isSafeInteger(minimum) && Number.isSafeInteger(maximum) && maximum - minimum < MAX_RANGE) {
    return Array.from({ length: maximum - minimum + 1 }, (_, index) => minimum + index);
  }
  return [];
}

function fitsType(value, type) {
  if (type === 'string') return typeof value === 'string' && value.length <= MAX_LENGTH;
  if (type === 'integer') return Number.isSafeInteger(value);
  if (type === 'number') return typeof value === 'number';
  return false;
}

/**
 * The values Jev may choose from for one argument.
 * @param {object} schema the argument's JSON schema
 * @param {{ listed?: unknown[], last?: object|null }} sources
 */
export function candidatesFor(schema = {}, { listed, last = null } = {}) {
  if (Array.isArray(listed) && listed.length > 0) return [...listed];
  const allowed = fromSchema(schema);
  if (allowed.length > 0) return allowed;
  const seen = new Set();
  const values = [];
  for (const value of resultValues(last)) {
    if (!fitsType(value, schema.type) || seen.has(value)) continue;
    seen.add(value);
    values.push(value);
    if (values.length === MAX_CANDIDATES) break;
  }
  return values;
}

const keyFor = (name) => `argument_${name}`;

/**
 * One Choice per open argument; `valueOf` turns each answer back into the
 * value sent.
 * @param {{ instructions: string, tool: string, open: { name: string, schema: object, candidates: unknown[] }[] }} input
 */
export function argumentQuestions({ instructions, tool, open }) {
  const questions = {};
  for (const { name, schema, candidates } of open) {
    const about = schema?.description ? ` (${schema.description})` : '';
    questions[keyFor(name)] = {
      type: 'choice',
      instructions: `${instructions} You are calling \`${tool}\`: choose the value of its argument \`${name}\`${about}.`,
      criteria: Object.fromEntries(candidates.map((value, index) => [`v${index + 1}`, `\`${JSON.stringify(value)}\``])),
    };
  }
  return {
    questions,
    /**
     * The chosen value of each argument, or the first off-list answer.
     * @returns {{ filled: object }|{ offList: { name: string, answer: string|null } }}
     */
    read(answers) {
      const filled = {};
      for (const { name, candidates } of open) {
        const choice = answers?.[keyFor(name)]?.choice ?? null;
        const index = /^v(\d+)$/.exec(choice ?? '')?.[1];
        const value = index === undefined ? undefined : candidates[Number(index) - 1];
        if (value === undefined) return { offList: { name, answer: choice } };
        filled[name] = value;
      }
      return { filled };
    },
  };
}
