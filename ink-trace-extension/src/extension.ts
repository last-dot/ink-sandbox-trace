import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import * as child_process from 'child_process';
import { InkCodeLensProvider } from './InkCodeLensProvider';
import { InkDebugConfigurationProvider } from './InkDebugConfigurationProvider';

export function activate(context: vscode.ExtensionContext) {
    console.log('Activating Ink! Trace Debugger extension...');

    const debugAdapterFactory = new InkDebugAdapterDescriptorFactory(context);
    context.subscriptions.push(
        vscode.debug.registerDebugAdapterDescriptorFactory('ink-trace', debugAdapterFactory)
    );
    context.subscriptions.push(debugAdapterFactory); 


    context.subscriptions.push(
        vscode.debug.registerDebugConfigurationProvider('ink-trace', new InkDebugConfigurationProvider())
    );

    context.subscriptions.push(
        vscode.languages.registerCodeLensProvider({ language: 'rust' }, new InkCodeLensProvider())
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('ink-trace.debugTest', async (uri: vscode.Uri, testName: string) => {
            await handleDebugTestCommand(uri, testName);
        })
    );

    console.log('Ink! Trace Debugger extension activated successfully.');
}

export function deactivate() {
    console.log('Deactivating Ink! Trace Debugger extension.');
}

async function handleDebugTestCommand(uri: vscode.Uri, testName: string): Promise<void> {
    const workspaceFolder = vscode.workspace.getWorkspaceFolder(uri);
    if (!workspaceFolder) {
        vscode.window.showErrorMessage("Cannot start debugging: no workspace folder found for the current file.");
        return;
    }

    const debugConfiguration: vscode.DebugConfiguration = {
        type: 'ink-trace',
        request: 'launch',
        name: `Debug: ${testName}`,
        program: uri.fsPath,
        stopOnEntry: true,
        testToRun: testName
    };

    try {
        const success = await vscode.debug.startDebugging(workspaceFolder, debugConfiguration);
        if (!success) {
            vscode.window.showErrorMessage('Failed to start debugging.');
        }
    } catch (err: any) {
        vscode.window.showErrorMessage(`Debugging error: ${err.message}`);
    }
}

class InkDebugAdapterDescriptorFactory implements vscode.DebugAdapterDescriptorFactory, vscode.Disposable {
    private context: vscode.ExtensionContext;
    private static isPreparingEnvironment = false;
    private serverProcess: child_process.ChildProcess | null = null;

    constructor(context: vscode.ExtensionContext) {
        this.context = context;
    }

    async createDebugAdapterDescriptor(session: vscode.DebugSession): Promise<vscode.DebugAdapterDescriptor> {
        if (InkDebugAdapterDescriptorFactory.isPreparingEnvironment) {
            vscode.window.showWarningMessage("The debug environment is being prepared. Please wait and try again.");
            throw new Error("Environment preparation is already in progress.");
        }

        InkDebugAdapterDescriptorFactory.isPreparingEnvironment = true;
        try {
            const dapServerRoot = path.join(this.context.extensionPath, '..', 'ink-dap-server');
            await this.ensurePythonEnvironment(dapServerRoot);

            const pythonExecutable = this.getVenvExecutablePath(dapServerRoot, 'python');
            const serverScript = path.join(dapServerRoot, 'main.py');

            if (!fs.existsSync(pythonExecutable)) {
                throw new Error(`Failed to find Python executable in the virtual environment at: ${pythonExecutable}`);
            }

            if (!fs.existsSync(serverScript)) {
                throw new Error(`DAP server entry point not found at: ${serverScript}`);
            }

            return this.createExecutableDescriptor(dapServerRoot, pythonExecutable, serverScript);
            
        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to set up the debug environment: ${error.message}`);
            throw error;
        } finally {
            InkDebugAdapterDescriptorFactory.isPreparingEnvironment = false;
        }
    }

    private createExecutableDescriptor(dapServerRoot: string, pythonExecutable: string, serverScript: string): vscode.DebugAdapterExecutable {
        const options: vscode.DebugAdapterExecutableOptions = {
            cwd: dapServerRoot,
            env: {
                ...process.env,
                "PYTHONPATH": path.join(dapServerRoot, 'src'),
                "PYTHONUNBUFFERED": "1",
                "RUST_LOG": "debug"
            }
        };

        return new vscode.DebugAdapterExecutable(
            pythonExecutable,
            [serverScript],
            options
        );
    }

    private createServerDescriptor(dapServerRoot: string, pythonExecutable: string, serverScript: string): vscode.DebugAdapterServer {
        const port = 5678; 
        
        if (!this.serverProcess) {
            this.serverProcess = child_process.spawn(
                pythonExecutable,
                [serverScript, '--port', port.toString()],
                {
                    cwd: dapServerRoot,
                    env: {
                        ...process.env,
                        "PYTHONPATH": path.join(dapServerRoot, 'src'),
                        "PYTHONUNBUFFERED": "1",
                        "RUST_LOG": "debug"
                    },
                    stdio: ['pipe', 'pipe', 'pipe']
                }
            );

            this.serverProcess.stdout?.on('data', data => console.log(`DAP Server: ${data}`));
            this.serverProcess.stderr?.on('data', data => console.error(`DAP Server Error: ${data}`));
            this.serverProcess.on('close', code => console.log(`DAP Server exited with code ${code}`));
        }

        return new vscode.DebugAdapterServer(port);
    }

    private async ensurePythonEnvironment(dapServerRoot: string): Promise<void> {
        const venvPath = path.join(dapServerRoot, '.venv');
        if (fs.existsSync(venvPath)) return;

        const globalPython = await this.findGlobalPython();
        if (!globalPython) {
            throw new Error("Python 3 is not installed or not found in PATH. Please install it to continue.");
        }

        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Setting up Python environment for Ink! Tracer...",
            cancellable: false
        }, async (progress) => {
            progress.report({ message: "Creating virtual environment..." });
            await this.runCommand(globalPython, ['-m', 'venv', '.venv'], dapServerRoot);

            const pythonInVenv = this.getVenvExecutablePath(dapServerRoot, 'python');
            let attempts = 10;
            while (!fs.existsSync(pythonInVenv) && attempts > 0) {
                await new Promise(resolve => setTimeout(resolve, 500));
                attempts--;
            }

            if (!fs.existsSync(pythonInVenv)) {
                throw new Error(`Failed to create virtual environment. Python executable not found at ${pythonInVenv}.`);
            }

            progress.report({ message: "Installing dependencies..." });
            const pipExecutable = this.getVenvExecutablePath(dapServerRoot, 'pip');
            const requirementsPath = path.join(dapServerRoot, 'requirements.txt');
            await this.runCommand(pipExecutable, ['install', '-r', requirementsPath], dapServerRoot);

            progress.report({ message: "Setup complete!" });
            await new Promise(resolve => setTimeout(resolve, 1500));
        });
    }

    private async findGlobalPython(): Promise<string | null> {
        const candidates = ['python3', 'python', 'py'];
        for (const cmd of candidates) {
            try {
                const output = await this.runCommand(cmd, ['--version']);
                if (output.includes("Python 3")) return cmd;
            } catch {}
        }
        return null;
    }

    private getVenvExecutablePath(dapServerRoot: string, executableName: 'python' | 'pip'): string {
        const exe = process.platform === 'win32' ? `${executableName}.exe` : executableName;
        return path.join(dapServerRoot, '.venv', process.platform === 'win32' ? 'Scripts' : 'bin', exe);
    }

    private runCommand(cmd: string, args: string[], cwd?: string): Promise<string> {
        return new Promise((resolve, reject) => {
            const proc = child_process.execFile(cmd, args, { 
                cwd, 
                shell: process.platform === 'win32',
                timeout: 30000
            }, (error, stdout, stderr) => {
                if (error) {
                    reject(new Error(stderr || error.message));
                } else {
                    resolve(stdout);
                }
            });
        });
    }

    dispose() {
        if (this.serverProcess) {
            this.serverProcess.kill();
            this.serverProcess = null;
        }
    }
}