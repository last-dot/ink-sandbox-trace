import * as vscode from 'vscode';
import { PythonDAPLauncher } from './pythonDAPLauncher';

const outputChannel = vscode.window.createOutputChannel('Ink Trace Debugger');

export function activate(context: vscode.ExtensionContext) {
    outputChannel.appendLine('Ink Trace Debugger: Activated');

    const factory = new InkDebugAdapterDescriptorFactory(context, outputChannel);

    context.subscriptions.push(
        vscode.debug.registerDebugAdapterDescriptorFactory('ink-trace', factory),
        
        vscode.debug.registerDebugConfigurationProvider('ink-trace', {
            provideDebugConfigurations(): vscode.ProviderResult<vscode.DebugConfiguration[]> {
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
        }),
        outputChannel
    );
}

export function deactivate() {
    outputChannel.appendLine('Ink Trace Debugger: Deactivated');
}

class InkDebugAdapterDescriptorFactory implements vscode.DebugAdapterDescriptorFactory {
    private readonly launcher: PythonDAPLauncher;

    constructor(context: vscode.ExtensionContext, channel: vscode.OutputChannel) {
        this.launcher = new PythonDAPLauncher(context, channel);
    }

    async createDebugAdapterDescriptor(
        session: vscode.DebugSession
    ): Promise<vscode.DebugAdapterDescriptor> {
        return this.launcher.getDAPExecutable(session.configuration);
    }
}