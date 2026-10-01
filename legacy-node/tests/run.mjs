import { addFailure, summary } from './harness.mjs';
import { runApiTests } from './api.test.mjs';
import { runPublicTests } from './public.test.mjs';
import { runAdminTests } from './admin.test.mjs';

const suites = [
  ['API y servidor', runApiTests],
  ['Sitio público', runPublicTests],
  ['Panel de administración', runAdminTests]
];

for (const [name, run] of suites) {
  try {
    await run();
  } catch (error) {
    console.log(`\n--- ${name} ---`);
    addFailure(`La suite ${name} se detuvo: ${error.message}`);
    console.log(error.stack.split('\n').slice(1, 4).join('\n'));
  }
}

const failures = summary();
if (failures > 0) process.exitCode = 1;
else console.log('\nTodo correcto.');
