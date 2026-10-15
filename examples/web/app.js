// The web example's app: a three-step sign-up wizard. A plain page - a
// person clicks its buttons, and so does an understudy, reading the page
// the way a screen reader does. Nothing here is written for understudy.

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
