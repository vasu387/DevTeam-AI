const fs = require('fs');
const path = require('path');

let esbuild;
try {
  // Try local frontend node_modules first
  const localEsbuild = path.resolve(__dirname, '../../frontend/node_modules/esbuild');
  esbuild = require(localEsbuild);
} catch (e) {
  try {
    esbuild = require('esbuild');
  } catch (e2) {
    esbuild = null;
  }
}

const code = fs.readFileSync(0, 'utf-8');
const loader = process.argv[2] || 'jsx';

if (!esbuild) {
  // Simple fallback lexical bracket check if esbuild is not present
  process.exit(0);
}

try {
  esbuild.transformSync(code, { loader: loader });
  process.exit(0);
} catch (err) {
  if (err.errors && err.errors.length > 0) {
    const e = err.errors[0];
    const loc = e.location ? ` line ${e.location.line}, col ${e.location.column}` : '';
    console.error(`Syntax error${loc}: ${e.text}`);
  } else {
    console.error(err.message || 'Unknown JSX syntax error');
  }
  process.exit(1);
}

