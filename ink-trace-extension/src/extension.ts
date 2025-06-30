import * as vscode from 'vscode';
import { InkDebugSession } from './inkDebugSession';

export function activate(context: vscode.ExtensionContext) {
    context.subscriptions.push(
        vscode.debug.registerDebugAdapterDescriptorFactory(
            'ink-trace',
            new InkDebugAdapterDescriptorFactory()
        ),
        vscode.debug.registerDebugConfigurationProvider(
            'ink-trace',
            new InkDebugConfigurationProvider()
        )
    );
}

export function deactivate() {}

class InkDebugConfigurationProvider implements vscode.DebugConfigurationProvider {
    resolveDebugConfiguration(
        _folder: vscode.WorkspaceFolder | undefined, 
        config: vscode.DebugConfiguration
    ): vscode.ProviderResult<vscode.DebugConfiguration> {
        
        if (!config.program) {
            config.program = '${file}';
        }
        
        return config;
    }
}

class InkDebugAdapterDescriptorFactory implements vscode.DebugAdapterDescriptorFactory {
    createDebugAdapterDescriptor(session: vscode.DebugSession): vscode.ProviderResult<vscode.DebugAdapterDescriptor> {
        return new vscode.DebugAdapterInlineImplementation(new InkDebugSession());
    }
}