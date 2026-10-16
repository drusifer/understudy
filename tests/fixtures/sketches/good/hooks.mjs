// Known-good hooks for the sketch-loader tests. Nothing here is ever
// started: the tests only load and check it.
export default {
  phase: (view) => view.screen,
  project: (view) => ({ screen: view.screen }),
  options: () => [{ id: 'order', what: 'place the order' }, { id: 'cancel', what: 'stop' }],
  act: (move) => ({ actions: [{ input: move.id }] }),
};

export const library = {
  guards: { sold_out: { doc: 'the app says the item is sold out', fn: ({ event }) => event.output?.soldOut === true } },
};
