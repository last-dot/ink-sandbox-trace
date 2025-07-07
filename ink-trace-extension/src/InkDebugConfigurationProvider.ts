import * as vscode from 'vscode';
import * as fs from 'fs';

export class InkDebugConfigurationProvider implements vscode.DebugConfigurationProvider {
    resolveDebugConfiguration(
        folder: vscode.WorkspaceFolder | undefined,
        config: vscode.DebugConfiguration,
        token?: vscode.CancellationToken
    ): vscode.DebugConfiguration | null | undefined {
        if (!config.type && !config.request && !config.name) {
            const editor = vscode.window.activeTextEditor;
            if (editor && editor.document.languageId === 'rust') {
                config.type = 'ink-trace';
                config.name = 'Debug Rust file';
                config.request = 'launch';
                config.program = editor.document.fileName;
                config.stopOnEntry = true;
            } else {
                vscode.window.showErrorMessage("Open a Rust (.rs) file to debug.");
                return null;
            }
        }

        if (!config.program) {
            vscode.window.showErrorMessage("Missing required field 'program' in debug configuration.");
            return null;
        }
        if (!fs.existsSync(config.program) || !config.program.endsWith('.rs')) {
            vscode.window.showErrorMessage("The 'program' field must point to an existing Rust (.rs) file.");
            return null;
        }
        return config;
    }
}