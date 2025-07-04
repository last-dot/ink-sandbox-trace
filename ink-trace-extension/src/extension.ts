import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { InkCodeLensProvider } from './InkCodeLensProvider';

export function activate(context: vscode.ExtensionContext) {
    console.log('Activating Ink! Trace Debugger extension...');

    // Register the factory for creating debug adapter descriptors.
    context.subscriptions.push(
        vscode.debug.registerDebugAdapterDescriptorFactory('ink-trace', new InkDebugAdapterDescriptorFactory(context))
    );

    // Register the CodeLens provider for Rust files.
    context.subscriptions.push(
        vscode.languages.registerCodeLensProvider({ language: 'rust' }, new InkCodeLensProvider())
    );

    // Register the command that is invoked by the "Debug" CodeLens.
    context.subscriptions.push(
        vscode.commands.registerCommand('ink-trace.debugTest', (uri: vscode.Uri, testName: string) => {
            const workspaceFolder = vscode.workspace.getWorkspaceFolder(uri);
            if (!workspaceFolder) {
                vscode.window.showErrorMessage("Cannot start debugging: no workspace folder found for the current file.");
                return;
            }

            // Create and start a debug session programmatically.
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

/**
 * This function is called when the extension is deactivated.
 */
export function deactivate() {
    console.log('Deactivating Ink! Trace Debugger extension.');
}

/**
 * A factory for creating and configuring the debug adapter executable (the Python DAP server).
 */
class InkDebugAdapterDescriptorFactory implements vscode.DebugAdapterDescriptorFactory {
    private context: vscode.ExtensionContext;

    constructor(context: vscode.ExtensionContext) {
        this.context = context;
    }

    /**
     * Called by VS Code to get the debug adapter executable.
     */
    async createDebugAdapterDescriptor(session: vscode.DebugSession): Promise<vscode.DebugAdapterDescriptor> {
        const dapServerRoot = path.join(this.context.extensionPath, '..', 'ink-dap-server');

        const pythonExecutable = this.findPythonInVenv(dapServerRoot);
        if (!pythonExecutable) {
            const message = `Python virtual environment not found. Please run 'python -m venv .venv' and 'pip install -r requirements.txt' in the 'ink-dap-server' directory.`;
            vscode.window.showErrorMessage(message);
            throw new Error(message);
        }
        
        const serverScript = path.join(dapServerRoot, 'main.py');
        if (!fs.existsSync(serverScript)) {
            const message = `DAP server entry point not found at: ${serverScript}.`;
            vscode.window.showErrorMessage(message);
            throw new Error(message);
        }

        const options: vscode.DebugAdapterExecutableOptions = {
            cwd: dapServerRoot, 
            env: this.getCleanEnvironment()
        };

        return new vscode.DebugAdapterExecutable(pythonExecutable, [serverScript], options);
    }

    private findPythonInVenv(dapServerRoot: string): string | null {
        const pythonExecutableName = process.platform === 'win32' ? 'python.exe' : 'python';
        const venvPath = path.join(
            dapServerRoot, 
            '.venv', 
            process.platform === 'win32' ? 'Scripts' : 'bin', 
            pythonExecutableName
        );

        return fs.existsSync(venvPath) ? venvPath : null;
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