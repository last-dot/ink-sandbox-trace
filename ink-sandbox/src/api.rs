use crate::api::DapCommand::*;
use crate::dap_handler::DapHandler;
use crate::domain::params::InitParams;
use crate::domain::rpc::{JsonRpcRequest, JsonRpcResponse};
use crate::sandbox::SandboxError;

pub type RpcRequest = Result<JsonRpcRequest, SandboxError>;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DapCommand {
    Initialize(Option<InitParams>), // Инициализация отладчика
    Pause,                          // Приостановить выполнение
    Continue,                       // Продолжить выполнение
    Disconnect,                     // Отключение отладчика
    Next,                           // Step Over (шаг через)

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
    json_rpc_request: RpcRequest,
) -> JsonRpcResponse {
    match json_rpc_request {
        Ok(request) => {
            let response = match request.as_command() {
                Initialize(path) => handler.handle_initialize(path.map(|x| x.polkavm)),
                Disconnect => handler.handle_disconnect(),
                Continue => handler.handle_continue(),
                Next => handler.handle_next(),
                Pause => handler.handle_pause(),
                Unknown(name) => handler.handle_unknown(name),
            };

            match response {
                Ok(mut result) => {
                    if let Some(id) = request.id {
                        result.set_request_id(&id);
                    }
                    result
                }
                Err(err) => JsonRpcResponse::error(err.to_string().as_str(), request.id),
            }
        }
        Err(err) => JsonRpcResponse::error(err.to_string().as_str(), None),
    }
}

impl From<&JsonRpcRequest> for DapCommand {
    fn from(req: &JsonRpcRequest) -> Self {
        match req.method.as_str() {
            "initialize" => Initialize(Some(InitParams::from(req))),
            "pause" => Pause,
            "continue" => Continue,
            "disconnect" => Disconnect,
            "next" => Next,
            other => Unknown(other.to_string()),
        }
    }
}
