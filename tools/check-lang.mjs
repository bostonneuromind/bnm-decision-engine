#!/usr/bin/env node
// check-lang.mjs — find .html pages that use language markers/toggles but do NOT
// load the shared bnm-lang-sync.js (i.e. potential "islands" missing the 4 principles).
//
//   node tools/check-lang.mjs [dir]      (default: cwd)
//
// Exit code 1 if any island is found (handy for CI). Skips *.bak* and backup dirs.
import fs from 'node:fs';
import path from 'node:path';

const ROOT = path.resolve(process.argv[2] || '.');
// A page "uses lang" if it has any of these signals…
const USES_LANG = /(class=["'](ko|en)-text)|(\bdata-lang=)|(\bsetLang\s*\()|(lang-btn)|(bnmSetLang)|(data-i18n)/;
// …and is "covered" if it loads a lang engine: the shared cross-domain script
// (bnm-lang-sync.js — full 4 principles incl. ?lang= link tagging) OR the
// symptom_catcher page engine (nc-lang.js — internal toggle/persist only; it does
// NOT tag cross-domain links, so those pages still rely on bnm-lang-sync for hop #4).
const COVERED = /bnm-lang-sync\.js|nc-lang\.js/;

function walk(dir, acc) {
  let ents;
  try { ents = fs.readdirSync(dir, { withFileTypes: true }); } catch { return acc; }
  for (const e of ents) {
    const fp = path.join(dir, e.name);
    if (e.isDirectory()) {
      if (e.name === '.git' || e.name === 'node_modules' || e.name === '.next') continue;
      if (/_backup_\d|\.bak/i.test(e.name)) continue;
      walk(fp, acc);
    } else if (/\.html$/i.test(e.name) && !/\.bak/i.test(e.name)) {
      acc.push(fp);
    }
  }
  return acc;
}

const files = walk(ROOT, []);
const islands = [];
for (const fp of files) {
  let src;
  try { src = fs.readFileSync(fp, 'utf8'); } catch { continue; }
  if (USES_LANG.test(src) && !COVERED.test(src)) islands.push(path.relative(ROOT, fp));
}

console.log(`check-lang: scanned ${files.length} .html under ${ROOT}`);
if (islands.length === 0) {
  console.log('✓ no islands — every lang-using page loads bnm-lang-sync.js');
  process.exit(0);
}
console.log(`✗ ${islands.length} page(s) use lang markers/toggle but load NO lang engine (neither bnm-lang-sync.js nor nc-lang.js):`);
for (const i of islands) console.log('   - ' + i);
console.log('\nThese keep an in-page toggle but miss cross-domain ?lang= propagation (and may default to ko).');
console.log('Fix: add <script src=".../bnm-lang-sync.js"></script> in <head> (adjust ../ depth). See LANG_HANDOFF.md.');
process.exit(1);
