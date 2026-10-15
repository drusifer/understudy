// The web example's adapter (docs/ADAPTERS.md): how understudy plays the
// sign-up wizard in index.html. The target is the page, driven through
// the `window.__understudy` hook that app.js exposes; the app hooks read
// that hook's view.

export default {
  name: 'signup-web',
  target: { kind: 'page', root: '.', page: 'index.html', hook: '__understudy' },
  app: {
    phase(view) {
      if (view.screen === 'welcome') return 'done';
      return view.buttons.length > 0 ? 'asking' : 'waiting';
    },
    project(view) {
      return { step: view.screen, question: view.prompt, note: view.note, answers: view.buttons };
    },
    options(state) {
      return state.answers.map(({ id, label }) => ({ id: `${state.step}:${id}`, what: `answer ${label}`, value: label }));
    },
    act(move) {
      return { actions: [{ press: move.id.split(':', 2)[1] }] };
    },
  },
};
