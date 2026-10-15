#!/usr/bin/env node
// The `understudy` command - see src/cli.mjs.
import { main } from '../src/cli.mjs';

process.exitCode = await main(process.argv.slice(2));
