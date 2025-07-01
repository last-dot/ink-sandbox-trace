import * as vscode from 'vscode';
import * as path from 'path';
import * as child_process from 'child_process';
import * as fs from 'fs';

export class PythonDAPLauncher {
    private context: vscode.ExtensionContext;

    constructor(context: vscode.ExtensionContext) {
        this.context = context;
    }

    private async checkPythonInstallation(): Promise<string | null> {
        const commands = process.platform === 'win32'
            ? ['python', 'py']
            : ['python3', 'python'];

        for (const cmd of commands) {
            try {
                await new Promise<void>((resolve, reject) => {
                    child_process.exec(`${cmd} --version`, (err) => {
                        if (err) reject(err);
                        else resolve();
                    });
                });
                return cmd;
            } catch {
                continue;
            }
        }

        return null;
    }

    async getDAPExecutable(sessionConfig: vscode.DebugConfiguration): Promise<vscode.DebugAdapterExecutable> {
        const pythonCmd = await this.checkPythonInstallation();
        if (!pythonCmd) {
            const msg = "Python 3 not found in PATH.";
            vscode.window.showErrorMessage(msg);
            throw new Error(msg);
        }

        const scriptPath = path.join(this.context.extensionPath, 'ink-dap-server', 'main.py');
        if (!fs.existsSync(scriptPath)) {
            const msg = `main.py not found at: ${scriptPath}`;
            vscode.window.showErrorMessage(msg);
            throw new Error(msg);
        }

        return new vscode.DebugAdapterExecutable(
            pythonCmd,
            [scriptPath],
            {
                cwd: path.dirname(scriptPath),
                env: {
                    ...process.env,
                    RUST_LOG: "debug"
                }
            }
        );
    }
}
