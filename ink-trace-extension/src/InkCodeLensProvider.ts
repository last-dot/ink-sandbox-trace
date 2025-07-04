import * as vscode from 'vscode';

export class InkCodeLensProvider implements vscode.CodeLensProvider {

    public provideCodeLenses(document: vscode.TextDocument, token: vscode.CancellationToken): vscode.ProviderResult<vscode.CodeLens[]> {
        if (document.languageId !== 'rust') {
            return [];
        }

        const lenses: vscode.CodeLens[] = [];
        const text = document.getText();
        
        // This regex finds test attributes and captures the function name that follows.
        const regex = /#\[(?:drink|ink_e2e)::test\]\s*\n(?:pub\s+)?(?:async\s+)?fn\s+([a-zA-Z0-9_]+)/g;

        let match;
        while ((match = regex.exec(text)) !== null) {
            const functionName = match[1];
            const startPos = document.positionAt(match.index);
            const range = new vscode.Range(startPos, startPos);

            // Create a command that will be executed when the CodeLens is clicked.
            const debugCommand: vscode.Command = {
                title: "Debug",
                command: "ink-trace.debugTest",
                tooltip: `Debug the test '${functionName}' using the Ink! Tracer`,
                arguments: [document.uri, functionName]
            };

            lenses.push(new vscode.CodeLens(range, debugCommand));
        }

        return lenses;
    }
}