import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import * as child_process from 'child_process';
import { InkCodeLensProvider } from './InkCodeLensProvider';

export function activate(context: vscode.ExtensionContext) {
    console.log('Activating Ink! Trace Debugger extension...');

    context.subscriptions.push(
        vscode.debug.registerDebugAdapterDescriptorFactory('ink-trace', new InkDebugAdapterDescriptorFactory(context))
    );

    context.subscriptions.push(
        vscode.languages.registerCodeLensProvider({ language: 'rust' }, new InkCodeLensProvider())
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('ink-trace.debugTest', (uri: vscode.Uri, testName: string) => {
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
            
            vscode.debug.startDebugging(workspaceFolder, debugConfiguration);
        })
    );

    console.log('Ink! Trace Debugger extension activated successfully.');
}

export function deactivate() {
    console.log('Deactivating Ink! Trace Debugger extension.');
}

class InkDebugAdapterDescriptorFactory implements vscode.DebugAdapterDescriptorFactory {
    private context: vscode.ExtensionContext;
    private static isPreparingEnvironment = false; 

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

            if (!pythonExecutable || !fs.existsSync(pythonExecutable)) {
                throw new Error("Failed to find Python executable in the virtual environment after setup.");
            }
            if (!fs.existsSync(serverScript)) {
                throw new Error(`DAP server entry point not found at: ${serverScript}.`);
            }

            const options: vscode.DebugAdapterExecutableOptions = {
                cwd: dapServerRoot, 
                env: this.getCleanEnvironment()
            };

            return new vscode.DebugAdapterExecutable(pythonExecutable, [serverScript], options);
        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to set up the debug environment: ${error.message}`);
            throw error;
        } finally {
            InkDebugAdapterDescriptorFactory.isPreparingEnvironment = false;
        }
    }

    private async ensurePythonEnvironment(dapServerRoot: string): Promise<void> {
        const venvPath = path.join(dapServerRoot, '.venv');
        if (fs.existsSync(venvPath)) {
            return; 
        }

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
                if (output.includes("Python 3")) {
                    return cmd;
                }
            } catch {
            }
        }
        return null;
    }
    
    private getVenvExecutablePath(dapServerRoot: string, executableName: 'python' | 'pip'): string {
        const exe = process.platform === 'win32' ? `${executableName}.exe` : executableName;
        return path.join(dapServerRoot, '.venv', process.platform === 'win32' ? 'Scripts' : 'bin', exe);
    }

    private runCommand(cmd: string, args: string[], cwd?: string): Promise<string> {
        return new Promise((resolve, reject) => {
            child_process.execFile(cmd, args, { cwd, shell: process.platform === 'win32' }, (error, stdout, stderr) => {
                if (error) {
                    reject(new Error(stderr || error.message));
                } else {
                    resolve(stdout);
                }
            });
        });
    }

    private getCleanEnvironment(): { [key: string]: string } {
        const cleanEnv: { [key: string]: string } = {};
        for (const key in process.env) {
            const value = process.env[key];
            if (typeof value === 'string') {
                cleanEnv[key] = value;
            }
        }
        return cleanEnv;
    }
}