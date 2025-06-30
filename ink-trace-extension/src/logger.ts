import { OutputEvent } from '@vscode/debugadapter';

export class Logger {
    private sendEvent: (event: OutputEvent) => void;

    constructor(sendEvent: (event: OutputEvent) => void) {
        this.sendEvent = sendEvent;
    }

    info(message: string): void {
        this.log('info', message);
    }

    debug(message: string): void {
        this.log('debug', message);
    }

    error(message: string): void {
        this.log('error', message);
    }

    private log(level: 'info' | 'debug' | 'error', message: string): void {
        const prefix = `[${level.toUpperCase()}] `;
        this.sendEvent(new OutputEvent(prefix + message + '\n'));
    }
}
