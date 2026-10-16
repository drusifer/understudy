// Sprint 3 UND-10 (ARCH §3, ADR-0012): the MCP SDK's transport interface
// over a program understudy started itself (`program.mjs`), so a local MCP
// server is started, watched and stopped like every other program - its
// exit code and its last stderr lines are known when it ends early. The
// framing (one JSON-RPC message per line) is the SDK's own.

import { ReadBuffer, serializeMessage } from '@modelcontextprotocol/sdk/shared/stdio.js';

export class ProgramTransport {
  #program;
  #buffer = new ReadBuffer();

  /**
   * @param {Awaited<ReturnType<import('./program.mjs').startProgram>>} program
   */
  constructor(program) {
    this.#program = program;
    // The SDK's Transport interface: the client sets these three.
    /* eslint-disable unicorn/prefer-add-event-listener -- callbacks the SDK's Transport interface defines */
    this.onmessage = undefined;
    this.onerror = undefined;
    this.onclose = undefined;
    /* eslint-enable unicorn/prefer-add-event-listener */
  }

  async start() {
    const { child } = this.#program;
    child.stdout.on('data', (chunk) => {
      this.#buffer.append(chunk);
      this.#drain();
    });
    child.once('close', () => this.onclose?.());
  }

  #drain() {
    for (;;) {
      let message;
      try {
        message = this.#buffer.readMessage();
      } catch (error) {
        // A line that is not JSON-RPC (a server printing to stdout) is
        // reported and skipped, never fatal.
        this.onerror?.(error);
        continue;
      }
      if (message === null) return;
      this.onmessage?.(message);
    }
  }

  /**
   * @param {object} message
   */
  async send(message) {
    const { stdin } = this.#program.child;
    if (stdin.write(serializeMessage(message))) return;
    await new Promise((resolve) => stdin.once('drain', resolve));
  }

  async close() {
    await this.#program.close();
  }
}
