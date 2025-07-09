import * as vscode from 'vscode';

export class InkCodeLensProvider implements vscode.CodeLensProvider {
    public provideCodeLenses(
        document: vscode.TextDocument,
        _token: vscode.CancellationToken
    ): vscode.ProviderResult<vscode.CodeLens[]> {
        if (document.languageId !== 'rust') {
            return [];
        }

        const text = document.getText();
        const regex = /#\[drink::test\]\s*\n(?:pub\s+)?(?:async\s+)?fn\s+([a-zA-Z0-9_]+)/g;

        const lenses: vscode.CodeLens[] = [];
        let match: RegExpExecArray | null;

        while ((match = regex.exec(text)) !== null) {
            const functionName = match[1];
            const position = document.positionAt(match.index);
            const range = new vscode.Range(position, position);

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
