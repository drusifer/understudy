// The web example's app: a three-step sign-up wizard. A person clicks
// buttons; understudy uses the same buttons through `window.__understudy`
// (docs/ADAPTERS.md), which only READS the page and CLICKS what is on it.

const STEPS = [
  { screen: 'plan', prompt: 'Which plan would you like?', buttons: [['free', 'Free'], ['pro', 'Pro (paid monthly)']] },
  { screen: 'theme', prompt: 'Pick a look for your account.', buttons: [['light', 'Light'], ['dark', 'Dark']] },
  { screen: 'terms', prompt: 'Do you accept the terms of service?', buttons: [['accept', 'Accept'], ['decline', 'Decline']] },
];

const wizard = { chosen: {}, index: 0, seq: 0, screen: 'plan', notice: '' };
const { chosen } = wizard;

const element = (id) => document.querySelector(`#${id}`);

function render() {
  wizard.seq += 1;
  const buttons = element('buttons');
  buttons.replaceChildren();
  if (wizard.screen === 'welcome') {
    element('prompt').textContent = `Welcome aboard! Your ${chosen.plan} account with the ${chosen.theme} look is ready.`;
    element('summary').textContent = '';
    return;
  }
  const step = STEPS[wizard.index];
  element('prompt').textContent = step.prompt;
  for (const [id, label] of step.buttons) {
    const button = document.createElement('button');
    button.id = id;
    button.textContent = label;
    button.addEventListener('click', () => choose(step.screen, id));
    buttons.append(button);
  }
  const summary = Object.entries(chosen).map(([key, value]) => `${key}: ${value}`).join(', ');
  element('summary').textContent = [wizard.notice, summary].filter(Boolean).join(' - ');
}

function choose(step, id) {
  wizard.notice = '';
  if (step === 'terms' && id === 'decline') {
    wizard.notice = 'You need to accept the terms to sign up.';
  } else if (step === 'terms') {
    wizard.screen = 'welcome';
  } else {
    chosen[step] = id;
    wizard.index += 1;
    wizard.screen = STEPS[wizard.index].screen;
  }
  render();
}

render();

// The hook IS a global: it is how understudy finds the page's moves (docs/ADAPTERS.md).
// eslint-disable-next-line unicorn/no-global-object-property-assignment
globalThis.__understudy = {
  view: () => ({
    screen: wizard.screen,
    seq: wizard.seq,
    prompt: element('prompt').textContent,
    note: element('summary').textContent,
    buttons: [...element('buttons').querySelectorAll('button')].map((button) => ({ id: button.id, label: button.textContent })),
  }),
  act: ({ press }) => {
    const button = element('buttons').querySelector(`#${press}`);
    if (!button) throw new Error(`no button "${press}" on the ${wizard.screen} screen`);
    button.click();
  },
};
