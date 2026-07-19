const fs = require('fs');
const files = [
  'electron/src/js/api.js',
  'electron/src/js/popup.js',
  'electron/src/js/result.js',
  'electron/src/js/settings.js',
  'electron/main.js',
  'electron/preload.js'
];
let allOk = true;
for (const f of files) {
  try {
    const src = fs.readFileSync(f, 'utf8');
    new Function(src);
    console.log(f + ': OK');
  } catch(e) {
    console.log(f + ': ERROR - ' + e.message.slice(0, 120));
    allOk = false;
  }
}
if (allOk) console.log('\nAll syntax checks passed!');
