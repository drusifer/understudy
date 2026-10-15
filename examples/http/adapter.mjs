// The HTTP example's adapter (docs/ADAPTERS.md): how understudy plays the
// vending machine API in server.mjs. The target starts the server on a
// free port and reads GET /machine as the view; the app hooks turn that
// state into the moves a customer has.

const COINS = [1, 2];

export default {
  name: 'vending-http',
  target: { kind: 'http', command: 'node', args: ['server.mjs'], url: 'http://127.0.0.1:{port}', state: '/machine' },
  app: {
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
  },
};
