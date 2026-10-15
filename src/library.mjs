// US-129/D154: the names a part's turn file may use - the whole
// vocabulary between the files and the code. Every entry says in one line
// what it means (`doc`), and that line is what `understudy library` lists.
//
// App-agnostic (sprint 1, ADR-U3). An app plugs in through its adapter's
// `services.app` hooks - which phase the app is in, how to read its view
// into state, which moves are offered, what the rules check, what a move
// does - and may add names of its own. `services.target` is how the app
// is seen and moved (a process, a page).

import { decide } from './decide.mjs';
import { verdictOf, askTable, floorFallback } from './escalate.mjs';
import { askChannel } from './table.mjs';
import { RunError } from './errors.mjs';

const verdictFromAnswer = (answer) => {
  if (answer === true) return 'yes';
  if (answer === false) return 'no';
  return 'unsure';
};

/**
 * A Choice's criteria for this step's options, in the questions file's
 * own words: an option's KIND (`size` in `size:large`) picks the wording,
 * and its `value`, when there is one, is shown in backticks because it is
 * computed at play time, never written in the file. With no wording for
 * its kind, an option is described by its own `what`.
 */
export function criteriaFor(question, options) {
  return Object.fromEntries(options.map((option) => {
    const [kind] = option.id.split(':', 1);
    const described = question.criteria?.[kind] ?? option.what;
    return [option.id, option.value ? `${described} (\`${option.value}\`)` : described];
  }));
}

/**
 * A question as TypeSafe takes it: only its own fields. Anything else in
 * a questions file (`applies_to`) is for the interpreter.
 */
function asked({ type, instructions, criteria, levels }) {
  return { type, instructions, ...(criteria && { criteria }), ...(levels && { levels }) };
}

function escalationFor({ player, target, name, answerMs, answerPollMs }) {
  if (player.escalation === 'ask') {
    return askTable((question) => askChannel({ target, name, question, timeoutMs: answerMs, pollMs: answerPollMs }));
  }
  return floorFallback();
}

/**
 * @param {{ target: object, judge: { systemOne: Function }, name: string,
 *   questions: Record<string, object>, player?: { floor?: number, escalation?: string },
 *   app: { phase: Function, project: Function, options: Function, propose?: Function, act: Function },
 *   answerMs?: number, answerPollMs?: number, seat?: { markSeen: Function },
 *   onRecord?: (record: object) => void }} services
 *   `seat` and `onRecord` are filled in by the seat after this is built.
 */
export function genericLibrary(services) {
  return {
    guards: {
      verdict: {
        doc: 'the last judgment or talk-channel answer was `is` (yes | no | unsure) - or, with `of`, that answer to question `of` asked alongside it',
        fn: ({ event }, parameters) => {
          const reading = parameters.of === undefined ? event.output?.verdict : verdictOf(event.output?.checks?.[parameters.of] ?? 0);
          return reading === parameters.is;
        },
      },
      changed: {
        doc: 'the app\'s view or its talk moved since the last look (the understudy\'s own lines excluded)',
        fn: ({ event }) => event.changed === true,
      },
      quiet: {
        doc: 'the view changed and nobody has spoken for `ms` since',
        fn: ({ event }, parameters) => (event.quietFor ?? 0) >= parameters.ms,
      },
      phase: {
        doc: 'the last `look` found the app in phase `is`',
        fn: ({ event }, parameters) => event.output?.phase === parameters.is,
      },
      counted: {
        doc: 'context `field` has reached `at_least` (a number, or another context field)',
        fn: ({ context }, parameters) => {
          const limit = typeof parameters.at_least === 'string' ? context[parameters.at_least] : parameters.at_least;
          return context[parameters.field] >= limit;
        },
      },
      played: {
        doc: 'the step just taken was a move of kind `move` (the part of its id before any `:`)',
        fn: ({ event }, parameters) => event.output?.kind === parameters.move,
      },
    },

    actions: {
      count: {
        doc: 'add one to context `field`',
        assign: ({ context }, parameters) => ({ [parameters.field]: (context[parameters.field] ?? 0) + 1 }),
      },
      track: {
        doc: 'keep what the last move changed (its `tracks`) in context',
        assign: ({ event }) => event.output?.tracks ?? {},
      },
      reset: {
        doc: 'set context fields to the values given in `to`',
        assign: (_, parameters) => ({ ...parameters.to }),
      },
      say: {
        doc: 'say `text` on the app\'s talk channel (ignored by a target without one)',
        fn: (_, parameters) => { services.target.say(parameters.text); },
      },
    },

    actors: {
      judge: {
        doc: 'ask Jev `question` (a Noul) about the app\'s view and talk; output verdict yes | no | unsure',
        fn: async ({ input }) => {
          const view = input.event.view ?? await services.target.view();
          const talk = input.event.talk ?? await services.target.talk();
          const projected = services.app.project(view, input.context, input.phase);
          const state = { ...projected, talk: talk.map(({ name, text }) => ({ name, text })) };
          const names = [input.question, ...(input.also ?? [])];
          const questions = Object.fromEntries(names.map((each) => [each, asked(services.questions[each])]));
          const response = await services.judge.systemOne({ state, questions });
          const answers = response.answers ?? {};
          return { verdict: verdictOf(answers[input.question]?.noul ?? 0), checks: Object.fromEntries(names.map((each) => [each, answers[each]?.noul ?? null])) };
        },
      },
      ask: {
        doc: 'say ONE yes/no question (`say`) on the talk channel and wait for a person\'s answer; output verdict yes | no | unsure',
        fn: async ({ input }) => {
          const { target, name, answerMs, answerPollMs } = services;
          const answer = await askChannel({ target, name, question: input.say, timeoutMs: answerMs, pollMs: answerPollMs });
          await services.seat?.markSeen();
          return { verdict: verdictFromAnswer(answer), answered: answer };
        },
      },
      look: {
        doc: 'read the app\'s view and find its phase (the adapter decides); output phase for the `phase` guard',
        fn: async ({ input }) => {
          const view = input.event?.view ?? await services.target.view();
          return { phase: services.app.phase(view, input.context) };
        },
      },
      play: {
        doc: 'one step in `phase`: Jev picks from the offered moves (`question`), the rules check it, and the move is made',
        fn: async ({ input }) => play(services, input),
      },
    },
  };
}

async function play(services, { context, phase, question: questionName }) {
  const { target, judge, app, player = {} } = services;
  const view = await target.view();
  const state = app.project(view, context, phase);
  const options = app.options(state, phase, context);
  const question = services.questions[questionName];
  const criteria = criteriaFor(question, options);
  const byId = (id) => options.find((option) => option.id === id);
  const choose = () => decide({
    judge, state,
    choice: { key: questionName, instructions: question.instructions, criteria },
    unsure: services.unsure,
    floor: player.floor ?? 0,
    verify: (id) => verification(services, byId(id), state, context),
    escalation: escalationFor({ ...services, player }),
    fallback: options.at(-1).id, // the last option is the one that is always safe
  });
  // ADR-U4: a pick that was not offered is never sent. Ask once more; a
  // second miss means the question or the options are broken - stop.
  let result = await choose();
  const offList = offListAnswer(result, criteria);
  if (offList !== undefined) {
    result = await choose();
    const again = offListAnswer(result, criteria);
    if (again !== undefined) {
      throw new RunError(`in phase "${phase}" Jev answered off the list twice ("${offList}", then "${again}") - offered: ${Object.keys(criteria).join(', ')}`, { outcome: 'off-list' });
    }
  }
  const move = byId(result.option);
  const { actions = [], say = null, tracks = {}, data } = app.act(move, state, view, context);
  for (const action of actions) await target.act(action);
  if (say) await target.say(say, data ?? { kind: 'understudy-move', move: move.id });
  const record = {
    at: new Date().toISOString(), phase, options: options.map((option) => option.id), picked: result.picked,
    move: move.id, confidence: result.confidence, checks: result.checks, asked: result.asked,
    ...(offList !== undefined && { offList: true, answer: offList }),
    ...(result.blocked && { blocked: { ...result.blocked, move: result.picked } }),
  };
  services.onRecord?.(record);
  return { record, move: move.id, kind: move.id.split(':', 1)[0], tracks };
}

/**
 * What Jev chose when it was not one of the offered ids (`null` for no
 * choice at all), or `undefined` when the choice was offered.
 */
function offListAnswer(result, criteria) {
  const chosen = result.answers.choice?.choice ?? null;
  return chosen !== null && Object.hasOwn(criteria, chosen) ? undefined : chosen;
}

/**
 * The rule questions that bear on `option`: those whose `applies_to`
 * names its kind (a questions-file fact, not code). The game describes
 * the proposed move; nothing to check means nothing is asked.
 */
function verification(services, option, state, context) {
  const [kind] = option.id.split(':', 1);
  const rules = Object.entries(services.questions).filter(([, question]) => question.applies_to?.includes(kind));
  if (rules.length === 0) return null;
  const proposed = services.app.propose?.(option, state, context) ?? { what: option.what, value: option.value ?? null };
  const value = option.value ? ` with ${option.value}` : '';
  return {
    state: { ...state, proposed },
    questions: Object.fromEntries(rules.map(([name, question]) => [name, asked(question)])),
    question: `Can I ${option.what}${value}?`,
  };
}

/**
 * Several libraries as one - an adapter's own names beside the generic ones.
 * A name defined twice is a mistake, not an override.
 */
export function mergeLibraries(...libraries) {
  const merged = { guards: {}, actions: {}, actors: {} };
  for (const library of libraries) {
    for (const [kind, names] of Object.entries(merged)) {
      const entries = Object.entries(library[kind] ?? {});
      for (const [name, entry] of entries) {
        if (Object.hasOwn(names, name)) throw new Error(`the library defines ${kind.slice(0, -1)} "${name}" twice`);
        names[name] = entry;
      }
    }
  }
  return merged;
}
