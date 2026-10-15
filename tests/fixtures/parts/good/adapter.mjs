// A known-good adapter for the part-loader tests. Nothing here is ever
// started: the tests only load and check it.
export default {
  name: 'fixture-good',
  target: { kind: 'process', command: 'node', args: ['app.mjs'] },
  app: {
    phase: (view) => view.screen,
    project: (view) => ({ screen: view.screen }),
    options: () => [{ id: 'order', what: 'place the order' }, { id: 'cancel', what: 'stop' }],
    act: (move) => ({ actions: [{ input: move.id }] }),
  },
  library: {
    guards: { sold_out: { doc: 'the app says the item is sold out', fn: ({ event }) => event.output?.soldOut === true } },
  },
};
