import * as vscode from 'vscode';
import {
    DebugSession,
    InitializedEvent,
    StoppedEvent,
    Breakpoint,
    Thread,
    OutputEvent,
    Source,
    StackFrame,
    ContinuedEvent,
    TerminatedEvent
} from '@vscode/debugadapter';
import { DebugProtocol } from '@vscode/debugprotocol';
import * as path from 'path';
import { PolkaVMI } from './polkaVMInstructions';
import * as process from 'process';

export function activate(context: vscode.ExtensionContext) {
    console.log('[ink-trace] activate');
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

export function deactivate() { }

class InkDebugConfigurationProvider implements vscode.DebugConfigurationProvider {
    resolveDebugConfiguration(_folder: any, config: any) {
        console.log('[ink-trace] resolveDebugConfiguration', config);
        if (!config.program) {
            config.program = '${file}';
        }
        return config;
    }
}

class InkDebugAdapterDescriptorFactory implements vscode.DebugAdapterDescriptorFactory {
    createDebugAdapterDescriptor() {
        console.log('[ink-trace] createDebugAdapterDescriptor');
        return new vscode.DebugAdapterInlineImplementation(new InkDebugSession());
    }
}


class InkDebugSession extends DebugSession {
    private _breakpointMap = new Map<string, DebugProtocol.Breakpoint[]>();
    
    private _activeBreakpoints: DebugProtocol.Breakpoint[] = [];
    
    private _currentBreakpointIndex = 0;

    private _programPath: string | undefined;

    private readonly instr: Map<number, string>;
    private _project = vscode.workspace.workspaceFolders?.[0]
        ? path.basename(vscode.workspace.workspaceFolders[0].uri.fsPath)
        : 'unknown_project';

    constructor() {
        super();
        console.log('[ink-trace] InkDebugSession started');
        this.setDebuggerLinesStartAt1(true);
        this.setDebuggerColumnsStartAt1(true);
        this.instr = new PolkaVMI().load();
    }
    
    private normalizePath(filePath: string): string {
        if (process.platform === 'win32') {
            return filePath.toLowerCase().replace(/\\/g, '/');
        }
        return filePath.replace(/\\/g, '/');
    }


    protected initializeRequest(response: DebugProtocol.InitializeResponse, args: DebugProtocol.InitializeRequestArguments): void {
        response.body = response.body || {};
        response.body.supportsConfigurationDoneRequest = true; 
        this.sendResponse(response);
        this.sendEvent(new InitializedEvent());
    }

    protected setBreakPointsRequest(
        response: DebugProtocol.SetBreakpointsResponse,
        args: DebugProtocol.SetBreakpointsArguments
    ): void {
        const filePath = args.source.path;
        if (!filePath) {
            response.body = { breakpoints: [] };
            this.sendResponse(response);
            return;
        }

        const normalizedPath = this.normalizePath(filePath);
        const source = new Source(args.source.name || path.basename(normalizedPath), normalizedPath);

        const newBreakpoints = (args.breakpoints ?? [])
            .map(bp => new Breakpoint(true, bp.line, bp.column, source) as DebugProtocol.Breakpoint)
            .sort((a, b) => (a.line ?? 0) - (b.line ?? 0)); 

        this._breakpointMap.set(normalizedPath, newBreakpoints);

        response.body = { breakpoints: newBreakpoints };
        this.sendEvent(new OutputEvent(`[ink-trace] Set ${newBreakpoints.length} breakpoints in file: ${normalizedPath}\n`));
        this.sendResponse(response);
    }
    

    protected launchRequest(response: DebugProtocol.LaunchResponse, args: DebugProtocol.LaunchRequestArguments & { program?: string }): void {
        if (args.program) {
            this._programPath = this.normalizePath(args.program);
        }
        this.sendResponse(response);
    }
    
    protected configurationDoneRequest(response: DebugProtocol.ConfigurationDoneResponse, args: DebugProtocol.ConfigurationDoneArguments): void {
        super.configurationDoneRequest(response, args);
        
        if (!this._programPath) {
            this.sendEvent(new OutputEvent('Error: No program path was configured.\n', 'stderr'));
            this.sendEvent(new TerminatedEvent());
            return;
        }

        this._activeBreakpoints = this._breakpointMap.get(this._programPath) || [];

        if (this._activeBreakpoints.length > 0) {
            this._currentBreakpointIndex = 0; 
            const bp = this._activeBreakpoints[this._currentBreakpointIndex];
            
            const message = `Breakpoint hit! File: ${this._programPath}, Line: ${bp.line}\n`;
            this.sendEvent(new OutputEvent(message, 'console'));
            
            this.sendEvent(new StoppedEvent('breakpoint', 1));
        } else {
            this.sendEvent(new OutputEvent(`No breakpoints in ${this._programPath}. Finishing debug session.\n`, 'console'));
            this.sendEvent(new TerminatedEvent());
        }
    }

    protected nextRequest(response: DebugProtocol.NextResponse, args: DebugProtocol.NextArguments): void {
        this._currentBreakpointIndex++;

        if (this._currentBreakpointIndex < this._activeBreakpoints.length) {

            const bp = this._activeBreakpoints[this._currentBreakpointIndex];
            
            const message = `Step. Breakpoint hit! File: ${this._programPath}, Line: ${bp.line}\n`;
            this.sendEvent(new OutputEvent(message, 'console'));
            
            this.sendEvent(new StoppedEvent('step', 1));
        } else {
            this.sendEvent(new OutputEvent('End of breakpoints. Program finished.\n', 'console'));
            this.sendEvent(new TerminatedEvent());
        }

        this.sendResponse(response);
    }


    protected threadsRequest(response: DebugProtocol.ThreadsResponse): void {
        response.body = { threads: [new Thread(1, "main thread")] };
        this.sendResponse(response);
    }

    protected stackTraceRequest(
        response: DebugProtocol.StackTraceResponse,
        args: DebugProtocol.StackTraceArguments
    ): void {
        const currentBp = this._activeBreakpoints[this._currentBreakpointIndex];

        if (currentBp && currentBp.source) {
            const sourcePath = currentBp.source.path || '';
            const source = new Source(currentBp.source.name || 'unknown', this.normalizePath(sourcePath));

            response.body = {
                stackFrames: [
                    new StackFrame(1, 'breakpoint_stop', source, currentBp.line, currentBp.column)
                ],
                totalFrames: 1
            };
        } else {
            response.body = { stackFrames: [], totalFrames: 0 };
        }
        this.sendResponse(response);
    }

    protected scopesRequest(response: DebugProtocol.ScopesResponse, args: DebugProtocol.ScopesArguments): void {
        response.body = { scopes: [] };
        this.sendResponse(response);
    }

    protected variablesRequest(response: DebugProtocol.VariablesResponse, args: DebugProtocol.VariablesArguments): void {
        response.body = { variables: [] };
        this.sendResponse(response);
    }
    
    protected continueRequest(response: DebugProtocol.ContinueResponse, args: DebugProtocol.ContinueArguments): void {
        this.sendEvent(new OutputEvent('Continued to end. Program finished.\n', 'console'));
        this.sendEvent(new TerminatedEvent());
        this.sendResponse(response);
    }
}