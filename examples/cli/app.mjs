#!/usr/bin/env node
// The CLI example's app: a coffee counter that asks three questions and
// places the order. Nothing in it knows about understudy - a person could
// use it the same way. Each question is one line, `? <topic> [a|b|c]`,
// followed by a `> ` prompt; an answer that is not on the menu is refused
// and the question is asked again.
import readline from 'node:readline';

const QUESTIONS = [
  ['size', ['small', 'medium', 'large']],
  ['milk', ['none', 'whole', 'oat']],
  ['confirm', ['order', 'start over']],
];

const answers = {};
let index = 0;

function ask() {
  const [topic, choices] = QUESTIONS[index];
  if (topic === 'confirm') process.stdout.write(`Your order: a ${answers.size} coffee, milk: ${answers.milk}.\n`);
  process.stdout.write(`? ${topic} [${choices.join('|')}]\n> `);
}

process.stdout.write('Welcome to the coffee counter.\n');
ask();
readline.createInterface({ input: process.stdin }).on('line', (line) => {
  const answer = line.trim();
  const [topic, choices] = QUESTIONS[index];
  if (!choices.includes(answer)) {
    process.stdout.write(`! "${answer}" is not on the menu for ${topic}\n`);
    ask();
    return;
  }
  if (topic === 'confirm' && answer === 'order') {
    process.stdout.write(`Order placed: a ${answers.size} coffee, milk: ${answers.milk}. Goodbye.\n`);
    process.exit(0);
  }
  if (topic === 'confirm') {
    index = 0;
  } else {
    answers[topic] = answer;
    index += 1;
  }
  ask();
});
