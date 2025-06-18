export class Logger {
    private static debugMode = false;

    public static enableDebug() {
        Logger.debugMode = true;
    }

    public static disableDebug() {
        Logger.debugMode = false;
    }

    public static log(message: string, ...optionalParams: any[]) {
        if (Logger.debugMode) {
            console.log(`[ink-trace LOG] ${message}`, ...optionalParams);
        }
    }

    public static warn(message: string, ...optionalParams: any[]) {
        if (Logger.debugMode) {
            console.warn(`[ink-trace WARN] ${message}`, ...optionalParams);
        }
    }

    public static error(message: string, ...optionalParams: any[]) {
        if (Logger.debugMode) {
            console.error(`[ink-trace ERROR] ${message}`, ...optionalParams);
        }
    }
}