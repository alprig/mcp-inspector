#!/usr/bin/env node
import { spawn, execSync } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { existsSync } from 'fs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, '..');
const backendDir = join(root, 'backend');
const frontendDir = join(root, 'frontend');
const venvPython = join(backendDir, '.venv', 'bin', 'python3');
const venvPip = join(backendDir, '.venv', 'bin', 'pip');

function run(cmd, args, opts = {}) {
  return new Promise((resolve, reject) => {
    const proc = spawn(cmd, args, { stdio: 'inherit', ...opts });
    proc.on('close', (code) => code === 0 ? resolve() : reject(new Error(`${cmd} exited ${code}`)));
    proc.on('error', reject);
  });
}

function checkPython() {
  try {
    const out = execSync('python3 --version 2>&1').toString().trim();
    const match = out.match(/Python (\d+)\.(\d+)/);
    if (!match) throw new Error('Cannot parse Python version');
    const [, major, minor] = match.map(Number);
    if (major < 3 || (major === 3 && minor < 11)) {
      throw new Error(`Python 3.11+ required, found ${out}. Please upgrade.`);
    }
    return out;
  } catch (e) {
    if (e.message.includes('required')) throw e;
    throw new Error('python3 not found. Please install Python 3.11+');
  }
}

async function setupBackend() {
  if (!existsSync(venvPython)) {
    console.log('  Creating Python venv...');
    await run('python3', ['-m', 'venv', '.venv'], { cwd: backendDir });
  }
  // Check if uvicorn is installed
  try {
    execSync(`${venvPython} -m uvicorn --version 2>&1`);
  } catch {
    console.log('  Installing backend dependencies...');
    await run(venvPip, [
      'install', '-q',
      'fastapi', 'uvicorn[standard]', 'mcp', 'websockets', 'pydantic', 'python-dotenv'
    ], { cwd: backendDir });
  }
}

async function setupFrontend() {
  const nextBin = join(frontendDir, 'node_modules', '.bin', 'next');
  if (!existsSync(nextBin)) {
    console.log('  Installing frontend dependencies (this takes ~30s the first time)...');
    await run('npm', ['install', '--legacy-peer-deps', '--silent'], { cwd: frontendDir });
  }
}

async function main() {
  console.log('\n🔍 MCP Inspector — starting up\n');

  // Check Python
  try {
    const version = checkPython();
    console.log(`✓ ${version}`);
  } catch (e) {
    console.error(`\nError: ${e.message}\n`);
    process.exit(1);
  }

  // Setup backend venv + deps
  process.stdout.write('Setting up backend');
  try {
    await setupBackend();
    console.log(' ✓');
  } catch (e) {
    console.error(`\nBackend setup failed: ${e.message}\n`);
    process.exit(1);
  }

  // Setup frontend deps
  process.stdout.write('Setting up frontend');
  try {
    await setupFrontend();
    console.log(' ✓');
  } catch (e) {
    console.error(`\nFrontend setup failed: ${e.message}\n`);
    process.exit(1);
  }

  console.log('\nStarting servers...\n');

  // Start backend
  const nextBin = join(frontendDir, 'node_modules', '.bin', 'next');
  const backend = spawn(
    venvPython, ['-m', 'uvicorn', 'main:app', '--port', '8000', '--log-level', 'warning'],
    { stdio: 'inherit', cwd: backendDir }
  );

  // Start frontend
  const frontend = spawn(
    nextBin, ['dev', '--port', '3333'],
    { stdio: 'inherit', cwd: frontendDir }
  );

  setTimeout(() => {
    console.log('\nMCP Inspector running at http://localhost:3333\n');
  }, 2000);

  function shutdown() {
    console.log('\nShutting down...');
    backend.kill('SIGTERM');
    frontend.kill('SIGTERM');
    process.exit(0);
  }

  process.on('SIGINT', shutdown);
  process.on('SIGTERM', shutdown);

  backend.on('exit', (code) => {
    if (code !== null && code !== 0) {
      console.error(`Backend exited (${code})`);
      frontend.kill('SIGTERM');
      process.exit(1);
    }
  });

  frontend.on('exit', (code) => {
    if (code !== null && code !== 0) {
      console.error(`Frontend exited (${code})`);
      backend.kill('SIGTERM');
      process.exit(1);
    }
  });
}

main();
