import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import * as child_process from 'child_process';
import { InkCodeLensProvider } from './InkCodeLensProvider';

export function activate(context: vscode.ExtensionContext): void {
    console.log('Activating Ink! Trace Debugger extension...');

    const factory = new InkDebugAdapterDescriptorFactory(context);

    context.subscriptions.push(
        vscode.debug.registerDebugAdapterDescriptorFactory('ink-trace', factory),
        vscode.debug.registerDebugConfigurationProvider('ink-trace', new InkDebugConfigurationProvider(factory)),
        vscode.languages.registerCodeLensProvider({ language: 'rust' }, new InkCodeLensProvider()),
        vscode.commands.registerCommand('ink-trace.debugTest', async (uri: vscode.Uri, testName: string) => {
            const workspaceFolder = vscode.workspace.getWorkspaceFolder(uri);
            if (!workspaceFolder) {
                vscode.window.showErrorMessage("Cannot start debugging: no workspace folder found.");
                return;
            }

            const config: vscode.DebugConfiguration = {
                type: 'ink-trace',
                request: 'launch',
                name: `Debug: ${testName}`,
                program: uri.fsPath,
                stopOnEntry: true,
                testToRun: testName
            };

            const started = await vscode.debug.startDebugging(workspaceFolder, config);
            if (!started) {
                vscode.window.showErrorMessage("Failed to start the debug session.");
            }
        })
    );

    console.log('Ink! Trace Debugger extension activated successfully.');
}

export function deactivate(): void {
    console.log('Deactivating Ink! Trace Debugger extension.');
}

class InkDebugConfigurationProvider implements vscode.DebugConfigurationProvider {
    constructor(private readonly factory: InkDebugAdapterDescriptorFactory) {}

    async resolveDebugConfiguration(
        folder: vscode.WorkspaceFolder | undefined,
        config: vscode.DebugConfiguration,
        token?: vscode.CancellationToken
    ): Promise<vscode.DebugConfiguration | null> {
        if (!config.program) {
            vscode.window.showErrorMessage("Missing 'program' in debug configuration.");
            return null;
        }

        try {
            await this.factory.prepareEnvironment();
        } catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            vscode.window.showErrorMessage(`Failed to prepare Python debug environment: ${message}`);
            return null;
        }

        return config;
    }
}

class InkDebugAdapterDescriptorFactory implements vscode.DebugAdapterDescriptorFactory {
    private static isPreparingEnvironment = false;

    constructor(private readonly context: vscode.ExtensionContext) {}

    async prepareEnvironment(): Promise<void> {
        if (InkDebugAdapterDescriptorFactory.isPreparingEnvironment) return;

        InkDebugAdapterDescriptorFactory.isPreparingEnvironment = true;
        try {
            const dapServerRoot = path.join(this.context.extensionPath, '..', 'ink-dap-server');
            await this.ensurePythonEnvironment(dapServerRoot);
        } finally {
            InkDebugAdapterDescriptorFactory.isPreparingEnvironment = false;
        }
    }

    async createDebugAdapterDescriptor(): Promise<vscode.DebugAdapterDescriptor> {
        const dapServerRoot = path.join(this.context.extensionPath, '..', 'ink-dap-server');
        const pythonExecutable = this.getVenvExecutablePath(dapServerRoot, 'python');
        const serverScript = path.join(dapServerRoot, 'main.py');

        const options: vscode.DebugAdapterExecutableOptions = {
            cwd: dapServerRoot,
            env: this.getCleanEnvironment()
        };

        return new vscode.DebugAdapterExecutable(pythonExecutable, [serverScript], options);
    }

    private async ensurePythonEnvironment(dapServerRoot: string): Promise<void> {
        const venvPath = path.join(dapServerRoot, '.venv');
        if (fs.existsSync(venvPath)) return;

        const globalPython = await this.findGlobalPython();
        if (!globalPython) {
            throw new Error("Python 3 not found in PATH.");
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
            } catch (error) {
                const message = error instanceof Error ? error.message : String(error);
                vscode.window.showWarningMessage(`Failed to run '${cmd} --version': ${message}`);
            }
        }
        return null;
    }

    private getVenvExecutablePath(dapServerRoot: string, name: 'python' | 'pip'): string {
        const exe = process.platform === 'win32' ? `${name}.exe` : name;
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
        const env: { [key: string]: string } = {};
        for (const key in process.env) {
            const value = process.env[key];
            if (typeof value === 'string') {
                env[key] = value;
            }
        }
        return env;
    }
}