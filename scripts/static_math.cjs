'use strict';

const fs = require('node:fs');
const path = require('node:path');

const projectRoot = process.cwd();
const outputDirectory = process.env.QUARTO_PROJECT_OUTPUT_DIR || '_site';
const katex = require(path.resolve(projectRoot, 'assets/katex/katex.min.js'));

function decodeHtml(value) {
  return value
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'");
}

function escapeAttribute(value) {
  return value
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function outputFiles() {
  const listed = (process.env.QUARTO_PROJECT_OUTPUT_FILES || '')
    .split(/\r?\n/)
    .filter(Boolean)
    .map((file) => path.resolve(projectRoot, file))
    .filter((file) => file.toLowerCase().endsWith('.html'));

  if (listed.length > 0) {
    return listed;
  }

  return fs
    .readdirSync(path.resolve(projectRoot, outputDirectory))
    .filter((file) => file.toLowerCase().endsWith('.html'))
    .map((file) => path.resolve(projectRoot, outputDirectory, file));
}

function staticTypeset(html) {
  let count = 0;
  const rendered = html.replace(
    /<span class="math (inline|display)">([\s\S]*?)<\/span>/g,
    (_match, mode, source) => {
      const tex = decodeHtml(source);
      const mathHtml = katex.renderToString(tex, {
        displayMode: mode === 'display',
        output: 'html',
        throwOnError: false,
      });
      count += 1;
      return '<span class="math-static ' + mode + '" role="img" aria-label="' +
        escapeAttribute(tex) + '">' + mathHtml + '</span>';
    },
  );

  const withoutRuntimeScript = rendered.replace(
    /\s*<script defer="" src="assets\/katex\/katex\.min\.js"><\/script>\s*/g,
    '\n',
  );
  const listenerStart = withoutRuntimeScript.indexOf(
    '<script>document.addEventListener("DOMContentLoaded"',
  );
  let withoutListener = withoutRuntimeScript;
  if (listenerStart >= 0) {
    const listenerEnd = withoutRuntimeScript.indexOf('</script>', listenerStart);
    if (listenerEnd < 0) {
      throw new Error('KaTeX listener has no closing script tag');
    }
    withoutListener =
      withoutRuntimeScript.slice(0, listenerStart) +
      withoutRuntimeScript.slice(listenerEnd + '</script>'.length);
  }

  return { html: withoutListener, count };
}

let total = 0;
for (const file of outputFiles()) {
  const source = fs.readFileSync(file, 'utf8');
  const result = staticTypeset(source);
  fs.writeFileSync(file, result.html);
  total += result.count;
  console.log('Static math: ' + result.count + ' expressions in ' + path.relative(projectRoot, file));
}
console.log('Static math total: ' + total);
