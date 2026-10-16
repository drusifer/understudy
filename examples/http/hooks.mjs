// The HTTP example's app hooks (docs/SKETCHES.md): how understudy reads
// the vending machine API in server.mjs. The target, in sketch.yaml,
// starts the server on a free port and reads GET /machine as the view;
// these hooks turn that state into the moves a customer has.

const COINS = [1, 2];

export default {
  phase(view) {
    return view.body.dispensed?.length > 0 ? 'done' : 'asking';
  },
  project(view) {
    const { credit, items, message } = view.body;
    return {
      credit,
      items: items.map(({ name, price, stock }) => ({ name, price, left: stock })),
      machine_says: view.last?.body?.error ?? message,
    };
  },
  options(state) {
    const coins = COINS.map((coin) => ({ id: `coin:${coin}`, what: `insert a ${coin} coin`, value: String(coin) }));
    const buys = state.items.filter((item) => item.left > 0).map((item) => ({ id: `buy:${item.name}`, what: `buy ${item.name}`, value: item.name }));
    // The last option is the safe fallback.
    return [...coins, ...buys, { id: 'refund:all', what: 'ask for the credit back' }];
  },
  act(move) {
    const [kind] = move.id.split(':', 1);
    if (kind === 'coin') return { actions: [{ method: 'POST', path: '/coins', body: { coin: Number(move.value) } }] };
    if (kind === 'buy') return { actions: [{ method: 'POST', path: '/select', body: { item: move.value } }] };
    return { actions: [{ method: 'POST', path: '/refund' }] };
  },
};
