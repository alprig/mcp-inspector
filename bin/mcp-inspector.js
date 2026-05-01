#!/usr/bin/env node
import { spawn, execSync } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { existsSync, rmSync } from 'fs';

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
  rmSync(join(frontendDir, '.next'), { recursive: true, force: true });
  await run('npm', ['install', '--legacy-peer-deps'], { cwd: frontendDir });
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

  // Check ports before starting
  for (const port of [8000, 3333]) {
    try {
      execSync(`lsof -ti :${port}`, { stdio: 'pipe' });
      console.error(`\nError: port ${port} is already in use. Stop the process using it and try again.\n`);
      process.exit(1);
    } catch {
      // port is free
    }
  }

  console.log('\nStarting servers...\n');

  const nextBin = join(frontendDir, 'node_modules', '.bin', 'next');

  const backend = spawn(
    venvPython, ['-m', 'uvicorn', 'main:app', '--port', '8000', '--log-level', 'warning'],
    { stdio: 'inherit', cwd: backendDir }
  );

  const frontend = spawn(
    nextBin, ['dev', '--turbopack', '--port', '3333'],
    { stdio: 'inherit', cwd: frontendDir }
  );

  // Print URL only after Next.js signals it's ready
  frontend.stdout?.on('data', (d) => {
    if (d.toString().includes('Ready') || d.toString().includes('ready')) {
      console.log('\nMCP Inspector running at http://localhost:3333\n');
    }
  });

  // Fallback: print after 5s if stdout was piped away
  const urlTimer = setTimeout(() => {
    console.log('\nMCP Inspector running at http://localhost:3333\n');
  }, 5000);
  urlTimer.unref();

  function shutdown() {
    console.log('\nShutting down...');
    clearTimeout(urlTimer);
    backend.kill('SIGTERM');
    frontend.kill('SIGTERM');
    process.exit(0);
  }

  process.on('SIGINT', shutdown);
  process.on('SIGTERM', shutdown);

  backend.on('exit', (code) => {
    if (code !== null && code !== 0) {
      console.error(`\nBackend crashed (exit ${code}). Check logs above.\n`);
      frontend.kill('SIGTERM');
      process.exit(1);
    }
  });

  frontend.on('exit', (code) => {
    if (code !== null && code !== 0) {
      console.error(`\nFrontend crashed (exit ${code}). Check logs above.\n`);
      backend.kill('SIGTERM');
      process.exit(1);
    }
  });
}

main();
