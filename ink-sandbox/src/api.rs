use crate::api::DapCommand::*;
use crate::dap_handler::DapHandler;
use crate::domain::params::{ContinueParams, InitParams};
use crate::domain::rpc::{JsonRpcRequest, JsonRpcResponse};

pub type RpcRequest = Result<JsonRpcRequest, SandboxError>;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DapCommand {
    //{"jsonrpc": "2.0", "method": "initialize", "params": {"polkavm": "/Users/maliketh/ink/ink-sandbox-trace/ink-trace-extension/sampleWorkspace/target/ink/flipper.polkavm"}, "id": "1"}
    //Content-Length: 123\r\n\r\n{"jsonrpc": "2.0", "method": "initialize", "params": {"path": "/Users/maliketh/ink/ink-sandbox-trace/ink-trace-extension/sampleWorkspace/target/ink/flipper.polkavm"}, "id": 1}
    Initialize(InitParams), // Инициализация отладчика
    // {"jsonrpc": "2.0", "method": "pause", "id": "2"}
    Pause, // Приостановить выполнение
    // {"jsonrpc": "2.0", "method": "continue", "id": "3"}
    Continue(ContinueParams), // Продолжить выполнение
    // Content-Length: 69\r\n\r\n{"jsonrpc": "2.0", "method": "disconnect", "params": {}, "id": 9}
    Disconnect, // Отключение отладчика
    // {"jsonrpc": "2.0", "method": "next", "id": "5"}
    Next, // Шаг через (Step Over)

    // ConfigurationDone,          // Завершение конфигурации
    // SetBreakpoints(Vec<usize>), // Установка брейкпоинтов
    // StepIn,                     // Step In (шаг внутрь)
    // StepOut,                    // Step Out (шаг наружу)
    // Threads,                    // Список потоков (один поток)
    // StackTrace,                 // Стек вызовов
    // Scopes,                     // Области видимости переменных
    // Variables,                  // Переменные
    Unknown(String), // Любая неподдерживаемая команда
}

pub fn dispatch_request<H: DapHandler<JsonRpcResponse>>(
    handler: &mut H,
    json_rpc_request: &RpcRequest,
) -> JsonRpcResponse {
    match json_rpc_request {
        Ok(request) => {
            let req = request.as_command();
            if let Err(err) = &req {
                return JsonRpcResponse::error(err.to_string().as_str(), request.id);
            }
            let req = req.unwrap();
            let response = match req {
                Initialize(path) => handler.handle_initialize(path.polkavm),
                Disconnect => handler.handle_disconnect(),
                Continue(params) => handler.handle_continue(params),
                Next => handler.handle_next(),
                Pause => handler.handle_pause(),
                Unknown(name) => handler.handle_unknown(name),
            };

            match response {
                Ok(mut result) => {
                    if let Some(id) = &request.id {
                        result.set_request_id(*id);
                    }
                    result
                }
                Err(err) => JsonRpcResponse::error(err.to_string().as_str(), request.clone().id),
            }
        }
        Err(err) => JsonRpcResponse::error(err.to_string().as_str(), None),
    }
}

impl TryFrom<&JsonRpcRequest> for DapCommand {
    type Error = SandboxError;

    fn try_from(req: &JsonRpcRequest) -> Result<Self, Self::Error> {
        match req.method.as_str() {
            "initialize" => {
                let init_params = InitParams::try_from(req)?;
                Ok(Initialize(init_params))
            }
            "pause" => Ok(Pause),
            "continue" => {
                let params = ContinueParams::try_from(req)?;
                Ok(Continue(params))
            },
            "disconnect" => Ok(Disconnect),
            "next" => Ok(Next),
            other => Ok(Unknown(other.to_string())),
        }
    }
}

