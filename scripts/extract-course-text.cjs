// The parser is a development-only dependency, installed outside the project.
const acorn = require('/tmp/verification-localize/node_modules/acorn');
const fs = require('fs');
const sources = JSON.parse(fs.readFileSync(0, 'utf8'));
const results = [];
for (const source of sources) {
  const strings = [];
  try {
    const ast = acorn.parse(source, {ecmaVersion: 'latest', sourceType: 'script'});
    const visit = node => {
      if (!node || typeof node !== 'object') return;
      if (node.type === 'Literal' && typeof node.value === 'string') strings.push(node.value);
      if (node.type === 'TemplateElement') strings.push(node.value.cooked || node.value.raw);
      for (const [key, value] of Object.entries(node)) {
        if (key === 'start' || key === 'end') continue;
        if (Array.isArray(value)) value.forEach(visit);
        else if (value && typeof value === 'object') visit(value);
      }
    };
    visit(ast);
    results.push({strings});
  } catch (error) { results.push({error: error.message, strings}); }
}
process.stdout.write(JSON.stringify(results));
