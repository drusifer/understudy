// The CLI example's adapter (docs/ADAPTERS.md): how understudy plays the
// coffee counter in app.mjs. The target is the program itself; the app
// hooks read its terminal output.
//
// The counter asks `? <topic> [a|b|c]`. A question is still waiting for an
// answer only while more questions have been printed than answers sent -
// so a look that lands before the program has replied never answers the
// same question twice.

const QUESTION = /^\? (\S+) \[([^\]]*)\]$/;

/**
 * The questions printed so far, oldest first.
 */
function questionsIn(lines) {
  return lines.map((line) => QUESTION.exec(line)).filter(Boolean)
    .map(([, topic, choices]) => ({ topic, choices: choices.split('|') }));
}

/**
 * What has been chosen so far, from the echoed answers (`> medium`).
 */
function answersIn(lines) {
  return lines.filter((line) => line.startsWith('> ') && line.length > 2).map((line) => line.slice(2));
}

export default {
  name: 'coffee-cli',
  target: { kind: 'process', command: 'node', args: ['app.mjs'] },
  app: {
    phase(view) {
      if (view.lines.some((line) => line.startsWith('Order placed'))) return 'done';
      return questionsIn(view.lines).length > view.sent ? 'asking' : 'waiting';
    },
    project(view) {
      const current = questionsIn(view.lines).at(-1);
      return {
        topic: current?.topic ?? null,
        choices: current?.choices ?? [],
        answered_so_far: answersIn(view.lines),
        counter_says: view.lines.filter((line) => !line.startsWith('> ') && !QUESTION.test(line)).slice(-3),
      };
    },
    options(state) {
      return state.choices.map((choice) => ({ id: `${state.topic}:${choice}`, what: `answer ${choice}`, value: choice }));
    },
    act(move) {
      return { actions: [{ input: move.value }] };
    },
  },
};
