#!/usr/bin/env node
import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, '..');

// Check Python version
function checkPython() {
  return new Promise((resolve, reject) => {
    const proc = spawn('python3', ['--version'], { stdio: 'pipe' });
    let output = '';
    proc.stdout.on('data', (d) => { output += d.toString(); });
    proc.stderr.on('data', (d) => { output += d.toString(); });
    proc.on('close', (code) => {
      if (code !== 0) {
        reject(new Error('python3 not found. Please install Python 3.11+'));
        return;
      }
      // output is like "Python 3.11.x"
      const match = output.match(/Python (\d+)\.(\d+)/);
      if (!match) {
        reject(new Error('Could not determine Python version. Please install Python 3.11+'));
        return;
      }
      const major = parseInt(match[1], 10);
      const minor = parseInt(match[2], 10);
      if (major < 3 || (major === 3 && minor < 11)) {
        reject(new Error(`Python 3.11+ required, found ${output.trim()}. Please upgrade Python.`));
        return;
      }
      resolve(output.trim());
    });
    proc.on('error', () => {
      reject(new Error('python3 not found. Please install Python 3.11+'));
    });
  });
}

async function main() {
  // Verify Python version
  try {
    const version = await checkPython();
    console.log(`Found ${version}`);
  } catch (err) {
    console.error(`\nError: ${err.message}\n`);
    process.exit(1);
  }

  // Spawn uvicorn for backend
  const backend = spawn(
    'python3',
    ['-m', 'uvicorn', 'main:app', '--port', '8000', '--app-dir', join(root, 'backend')],
    { stdio: 'inherit', cwd: root }
  );

  // Spawn Next.js dev for frontend
  const frontend = spawn(
    'npx',
    ['next', 'dev', '--port', '3333'],
    { stdio: 'inherit', cwd: join(root, 'frontend') }
  );

  console.log('\nMCP Inspector running at http://localhost:3333\n');

  // Graceful shutdown on SIGINT / SIGTERM
  function shutdown() {
    console.log('\nShutting down MCP Inspector...');
    backend.kill('SIGTERM');
    frontend.kill('SIGTERM');
    process.exit(0);
  }

  process.on('SIGINT', shutdown);
  process.on('SIGTERM', shutdown);

  backend.on('exit', (code) => {
    if (code !== null && code !== 0) {
      console.error(`Backend exited with code ${code}`);
    }
  });

  frontend.on('exit', (code) => {
    if (code !== null && code !== 0) {
      console.error(`Frontend exited with code ${code}`);
    }
  });
}

main();
