// Sprint 5 UND-21 (ARCH §4 "Answer rows", ADR-0017): what the servers have
// answered so far, as rows a decision can test.
//
// Every answer that was not an error (its structured content, or its text
// when that is JSON) is kept for the run. A row is any JSON object inside
// an answer; its fields are its own scalars (and lists of them) plus
// those of the objects around it, the nearest winning - so a showing nested in a film
// carries the film's title and genre. A value's facts are its row joined
// with the rows of other answers that share its `join` field.

export const MAX_ROWS = 500;

const isScalar = (value) => ['string', 'number', 'boolean'].includes(typeof value);
// A list of plain values (a film's reviews) is a fact too; a list of objects is more rows.
const isFact = (value) => isScalar(value) || (Array.isArray(value) && value.length > 0 && value.every((each) => isScalar(each)));
const isMapping = (value) => Boolean(value) && typeof value === 'object' && !Array.isArray(value);

/**
 * The JSON an answer carries, or null.
 */
function contentOf(answer) {
  if (!answer || answer.isError) return null;
  if (answer.structured) return answer.structured;
  try {
    return JSON.parse(answer.text ?? '');
  } catch {
    return null;
  }
}

/**
 * Every object inside `value` as a row, with the scalars it inherits.
 */
function rowsIn(value, inherited = {}) {
  if (Array.isArray(value)) return value.flatMap((each) => rowsIn(each, inherited));
  if (!isMapping(value)) return [];
  const own = Object.fromEntries(Object.entries(value).filter(([, each]) => isFact(each)));
  const row = { ...inherited, ...own };
  return [{ fields: row, own: new Set(Object.keys(own)) }, ...Object.values(value).flatMap((each) => rowsIn(each, row))];
}

/**
 * The run's answer memory.
 * @param {{ notify?: (line: string) => void }} [options]
 */
export function answerRows({ notify } = {}) {
  const seen = new WeakSet();
  let rows = [];
  let isTrimmed = false;
  return {
    /**
     * Keeps an answer's rows; the same answer object is kept once.
     */
    remember(answer) {
      if (!answer || seen.has(answer)) return;
      seen.add(answer);
      const content = contentOf(answer);
      if (content === null) return;
      rows.push(...rowsIn(content));
      if (rows.length > MAX_ROWS) {
        rows = rows.slice(-MAX_ROWS);
        if (!isTrimmed) notify?.(`keeping the last ${MAX_ROWS} answer rows`);
        isTrimmed = true;
      }
    },

    /**
     * Each distinct value of `field` with the latest row that has it as
     * its own (a seat's inherited `showing` does not make it a showing).
     * @returns {{ value: string|number|boolean, row: object }[]}
     */
    valuesOf(field) {
      const latest = new Map();
      for (const { fields, own } of rows) {
        if (!own.has(field)) continue;
        latest.delete(fields[field]);
        latest.set(fields[field], fields);
      }
      return [...latest].map(([value, row]) => ({ value, row }));
    },

    /**
     * A row's facts: the row, then every row that has the same `join`
     * value as its own field filling the fields it lacks (the row's win).
     */
    factsOf(row, join) {
      if (join === undefined || !Object.hasOwn(row, join)) return row;
      const facts = {};
      for (const { fields, own } of rows) {
        if (own.has(join) && fields[join] === row[join]) Object.assign(facts, fields);
      }
      return { ...facts, ...row };
    },
  };
}
