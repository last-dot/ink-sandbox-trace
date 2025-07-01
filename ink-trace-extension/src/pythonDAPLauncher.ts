import * as vscode from 'vscode';
import * as path from 'path';
import * as child_process from 'child_process';
import * as fs from 'fs';

export class PythonDAPLauncher {
    private readonly context: vscode.ExtensionContext;
    private readonly channel: vscode.OutputChannel;

    constructor(context: vscode.ExtensionContext, channel: vscode.OutputChannel) {
        this.context = context;
        this.channel = channel;
    }

    public async getDAPExecutable(config: vscode.DebugConfiguration): Promise<vscode.DebugAdapterExecutable> {
        this.channel.appendLine('Preparing to launch DAP server...');
        
        const pythonExecutable = await this.findPythonExecutable();
        const serverScript = this.resolveMainScript();

        const options: vscode.DebugAdapterExecutableOptions = {
            cwd: path.dirname(serverScript),
            env: {
                ...process.env,
                RUST_LOG: 'debug'
            }
        };

        this.channel.appendLine(`Starting DAP server using: ${pythonExecutable} ${serverScript}`);
        return new vscode.DebugAdapterExecutable(pythonExecutable, [serverScript], options);
    }

    private async findPythonExecutable(): Promise<string> {
        this.channel.appendLine('Searching for Python 3 executable...');
        const candidates = process.platform === 'win32' 
            ? ['python', 'py'] 
            : ['python3', 'python'];

        for (const cmd of candidates) {
            try {
                await this.isCommandAvailable(`${cmd} --version`);
                this.channel.appendLine(`Found available Python command: '${cmd}'`);
                return cmd;
            } catch (error) {
                this.channel.appendLine(`Command '${cmd}' not found or failed. Trying next...`);
            }
        }

        const message = 'Python 3 was not found in your PATH. Please install it and ensure it is available in your terminal to proceed.';
        vscode.window.showErrorMessage(message);
        this.channel.appendLine(`Error: ${message}`);
        throw new Error(message);
    }

    private async isCommandAvailable(command: string): Promise<void> {
        return new Promise((resolve, reject) => {
            child_process.exec(command, (err) => {
                if (err) {
                    reject(err);
                } else {
                    resolve();
                }
            });
        });
    }

    private resolveMainScript(): string {
        const scriptPath = path.join(this.context.extensionPath, 'ink-dap-server', 'main.py');
        this.channel.appendLine(`Checking for DAP server script at: ${scriptPath}`);

        if (!fs.existsSync(scriptPath)) {
            const message = `DAP server script not found at the expected location: ${scriptPath}`;
            vscode.window.showErrorMessage(message);
            this.channel.appendLine(`Error: ${message}`);
            throw new Error(message);
        }
        
        this.channel.appendLine('DAP server script found.');
        return scriptPath;
    }
}