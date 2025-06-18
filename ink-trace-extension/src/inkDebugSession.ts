// src/inkDebugSession.ts

import {
    DebugSession,
    InitializedEvent,
    StoppedEvent,
    Breakpoint,
    Thread,
    OutputEvent,
    Source,
    StackFrame,
    TerminatedEvent
} from '@vscode/debugadapter';
import { DebugProtocol } from '@vscode/debugprotocol';
import * as path from 'path';
import * as process from 'process';
import { Logger } from './logger';

export class InkDebugSession extends DebugSession {
    private static THREAD_ID = 1;
    private _breakpointMap = new Map<string, DebugProtocol.Breakpoint[]>();
    private _activeBreakpoints: DebugProtocol.Breakpoint[] = [];
    private _currentBreakpointIndex = 0;
    private _programPath: string | undefined;

    public constructor() {
        super();
        this.setDebuggerLinesStartAt1(true);
        this.setDebuggerColumnsStartAt1(true);

        Logger.enableDebug();
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

    protected launchRequest(response: DebugProtocol.LaunchResponse, args: DebugProtocol.LaunchRequestArguments & { program?: string }): void {
        this.sendEvent(new OutputEvent(`[ink-trace] Initializing debug session for: ${args.program}\n`));
        if (args.program) {
            this._programPath = this.normalizePath(args.program);
        }
        this.sendResponse(response);
    }

    protected setBreakPointsRequest(response: DebugProtocol.SetBreakpointsResponse, args: DebugProtocol.SetBreakpointsArguments): void {
        const filePath = args.source.path;
        if (!filePath) {
            response.body = { breakpoints: [] };
            this.sendResponse(response);
            return;
        }

        const normalizedPath = this.normalizePath(filePath);
        Logger.log(`Setting breakpoints for key: "${normalizedPath}"`);

        const newBreakpoints = (args.breakpoints ?? [])
            .map(bp => new Breakpoint(true, bp.line, bp.column, new Source(path.basename(normalizedPath), normalizedPath)) as DebugProtocol.Breakpoint)
            .sort((a, b) => (a.line ?? 0) - (b.line ?? 0));

        this._breakpointMap.set(normalizedPath, newBreakpoints);

        response.body = { breakpoints: newBreakpoints };
        this.sendEvent(new OutputEvent(`[ink-trace] Set ${newBreakpoints.length} breakpoints in file: ${normalizedPath}\n`));
        this.sendResponse(response);
    }

    protected configurationDoneRequest(response: DebugProtocol.ConfigurationDoneResponse, args: DebugProtocol.ConfigurationDoneArguments): void {
        super.configurationDoneRequest(response, args);

        if (!this._programPath) {
            this.sendEvent(new OutputEvent('Error: No program path was configured.\n', 'stderr'));
            this.sendEvent(new TerminatedEvent());
            return;
        }

        Logger.log(`Looking for breakpoints with key: "${this._programPath}"`);
        this._activeBreakpoints = this._breakpointMap.get(this._programPath) || [];
        Logger.log(`Breakpoint map contains keys:`, Array.from(this._breakpointMap.keys()));
        Logger.log(`Found ${this._activeBreakpoints.length} active breakpoints.`);

        if (this._activeBreakpoints.length > 0) {
            this._currentBreakpointIndex = 0;
            const bp = this._activeBreakpoints[this._currentBreakpointIndex];
            this.sendEvent(new OutputEvent(`Stopped on entry or first breakpoint. Line: ${bp.line}\n`, 'console'));
            this.sendEvent(new StoppedEvent('breakpoint', InkDebugSession.THREAD_ID));
        } else {
            this.sendEvent(new OutputEvent(`No breakpoints in ${this._programPath}. Finishing debug session.\n`, 'console'));
            this.sendEvent(new TerminatedEvent());
        }
    }

    protected continueRequest(response: DebugProtocol.ContinueResponse, args: DebugProtocol.ContinueArguments): void {
        this.sendEvent(new OutputEvent('Continued to the end. Program finished.\n', 'console'));
        this.sendEvent(new TerminatedEvent());
        this.sendResponse(response);
    }

    protected pauseRequest(response: DebugProtocol.PauseResponse, args: DebugProtocol.PauseArguments): void {
        this.sendEvent(new OutputEvent('[ink-trace] Pause request received (no-op in this simulator).\n', 'console'));
        this.sendResponse(response);
    }

    protected disconnectRequest(response: DebugProtocol.DisconnectResponse, args: DebugProtocol.DisconnectArguments): void {
        this.sendEvent(new OutputEvent('[ink-trace] Disconnecting debugger.\n', 'console'));
        super.disconnectRequest(response, args);
    }

    protected nextRequest(response: DebugProtocol.NextResponse, args: DebugProtocol.NextArguments): void {
        this._currentBreakpointIndex++;
        if (this._currentBreakpointIndex < this._activeBreakpoints.length) {
            const bp = this._activeBreakpoints[this._currentBreakpointIndex];
            this.sendEvent(new OutputEvent(`Stepped. Stopped at breakpoint. Line: ${bp.line}\n`, 'console'));
            this.sendEvent(new StoppedEvent('step', InkDebugSession.THREAD_ID));
        } else {
            this.sendEvent(new OutputEvent('End of breakpoints. Program finished.\n', 'console'));
            this.sendEvent(new TerminatedEvent());
        }
        this.sendResponse(response);
    }

    protected threadsRequest(response: DebugProtocol.ThreadsResponse): void {
        response.body = { threads: [new Thread(InkDebugSession.THREAD_ID, "main thread")] };
        this.sendResponse(response);
    }

    protected stackTraceRequest(response: DebugProtocol.StackTraceResponse, args: DebugProtocol.StackTraceArguments): void {
        const currentBp = this._activeBreakpoints[this._currentBreakpointIndex];
        if (currentBp && currentBp.source) {
            const safeSource = new Source(currentBp.source.name || 'unknown', currentBp.source.path);
            response.body = {
                stackFrames: [new StackFrame(1, 'breakpoint_stop', safeSource, currentBp.line, currentBp.column)],
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
}
