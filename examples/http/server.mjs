#!/usr/bin/env node
// The HTTP example's app: a vending machine as a small JSON API. Nothing in
// it knows about understudy - any client could use it the same way.
//
//   GET  /machine   what the machine shows: credit, items, what it dispensed, its last message
//   POST /coins     { "coin": 1 | 2 }        adds credit (400 for any other coin)
//   POST /select    { "item": "<name>" }     dispenses it (402 without enough credit, 409 when sold out)
//   POST /refund                             returns the credit
import http from 'node:http';

const machine = {
  credit: 0,
  items: [{ name: 'water', price: 1, stock: 3 }, { name: 'tea', price: 2, stock: 2 }, { name: 'coffee', price: 3, stock: 0 }],
  dispensed: [],
  message: 'Insert coins, then choose a drink.',
};

function readBody(request) {
  return new Promise((resolve) => {
    let text = '';
    request.on('data', (chunk) => { text += chunk; });
    request.on('end', () => {
      try {
        resolve(text ? JSON.parse(text) : {});
      } catch {
        resolve(null);
      }
    });
  });
}

function answer(response, status, body) {
  response.writeHead(status, { 'Content-Type': 'application/json' });
  response.end(JSON.stringify(body));
}

const routes = {
  'GET /machine': () => [200, machine],
  'POST /coins': ({ coin }) => {
    if (coin !== 1 && coin !== 2) return [400, { error: 'the machine takes 1 and 2 coins only' }];
    machine.credit += coin;
    machine.message = `Credit: ${machine.credit}.`;
    return [200, machine];
  },
  'POST /select': ({ item }) => {
    const wanted = machine.items.find((each) => each.name === item);
    if (!wanted) return [404, { error: `no item "${item}"` }];
    if (wanted.stock === 0) return [409, { error: `${item} is sold out` }];
    if (machine.credit < wanted.price) return [402, { error: `${item} costs ${wanted.price}, credit is ${machine.credit}` }];
    wanted.stock -= 1;
    machine.credit -= wanted.price;
    machine.dispensed.push(item);
    machine.message = `Dispensed ${item}. Enjoy!`;
    return [200, machine];
  },
  'POST /refund': () => {
    machine.message = `Returned ${machine.credit}.`;
    machine.credit = 0;
    return [200, machine];
  },
};

const server = http.createServer(async (request, response) => {
  const route = routes[`${request.method} ${request.url}`];
  if (!route) return answer(response, 404, { error: `no ${request.method} ${request.url}` });
  const body = await readBody(request);
  if (body === null) return answer(response, 400, { error: 'the body is not JSON' });
  const [status, result] = route(body);
  answer(response, status, result);
});

server.listen(Number(process.env.PORT ?? 8080), '0.0.0.0');
