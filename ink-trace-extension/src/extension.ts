import * as vscode from 'vscode';
import * as path from 'path';
import * as child_process from 'child_process';
import * as fs from 'fs';

export function activate(context: vscode.ExtensionContext) {
    console.log('Ink Trace Debugger extension activated');
    vscode.window.showInformationMessage('Ink Trace Debugger: Activated');

    context.subscriptions.push(
        vscode.debug.registerDebugAdapterDescriptorFactory(
            'ink-trace',
            new InkDebugAdapterDescriptorFactory(context)
        )
    );

    context.subscriptions.push(
        vscode.debug.registerDebugConfigurationProvider('ink-trace', {
            provideDebugConfigurations(folder: vscode.WorkspaceFolder | undefined): vscode.ProviderResult<vscode.DebugConfiguration[]> {
                return [
                    {
                        type: 'ink-trace',
                        request: 'launch',
                        name: 'Debug Ink Contract',
                        program: '${file}',
                        stopOnEntry: true
                    }
                ];
            }
        })
    );
}

export function deactivate() {
    console.log('Ink Trace Debugger extension deactivated');
}

class InkDebugAdapterDescriptorFactory implements vscode.DebugAdapterDescriptorFactory {
    private context: vscode.ExtensionContext;

    constructor(context: vscode.ExtensionContext) {
        this.context = context;
    }

    private async checkPythonInstallation(): Promise<boolean> {
        console.log('Checking Python installation...');
        const isWindows = process.platform === 'win32';
        const commands = isWindows ? ['python --version', 'py --version'] : ['python3 --version'];

        for (const command of commands) {
            try {
                const result = await new Promise<boolean>((resolve) => {
                    child_process.exec(command, (error) => {
                        resolve(error === null);
                    });
                });
                if (result) {
                    console.log(`Python found via: ${command}`);
                    return true;
                }
            } catch (e) {
                console.warn(`Command failed: ${command}`, e);
            }
        }

        return false;
    }

    async createDebugAdapterDescriptor(
        session: vscode.DebugSession
    ): Promise<vscode.DebugAdapterDescriptor> {
        console.log('Creating debug adapter descriptor');
        console.log('Configuration:', JSON.stringify(session.configuration, null, 2));

        const hasPython = await this.checkPythonInstallation();
        if (!hasPython) {
            const message = "Python 3 not found. Please install Python and add it to PATH.";
            vscode.window.showErrorMessage(message);
            throw new Error(message);
        }

        const serverScript = path.join(this.context.extensionPath, 'ink-dap-server', 'main.py');
        console.log(`Looking for server script at: ${serverScript}`);

        if (!fs.existsSync(serverScript)) {
            const message = `DAP server not found at: ${serverScript}`;
            console.error(message);
            vscode.window.showErrorMessage(message);
            throw new Error(message);
        }

        console.log('Server script found');

        try {
            const pythonExecutable = process.platform === 'win32' ? 'python' : 'python3';
            const options: vscode.DebugAdapterExecutableOptions = {
                cwd: path.dirname(serverScript),
                env: {
                    ...process.env,
                    RUST_LOG: "debug"
                }
            };

            console.log('Launching DAP server with:', {
                python: pythonExecutable,
                script: serverScript,
                args: session.configuration,
                cwd: options.cwd
            });

            vscode.window.showInformationMessage('Starting Ink Debug Adapter...');
            return new vscode.DebugAdapterExecutable(
                pythonExecutable,
                [serverScript],
                options
            );
        } catch (error) {
            const message = `Failed to launch DAP server: ${error}`;
            console.error('Error:', error);
            vscode.window.showErrorMessage(message);
            throw error;
        }
    }
}
