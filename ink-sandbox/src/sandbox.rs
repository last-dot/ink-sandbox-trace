use std::fs;

use polkavm::debug_info::{FrameKind, SourceCache};
use polkavm::{ArcBytes, ProgramBlob, ProgramCounter};

pub type SandboxError = Box<dyn std::error::Error>;

pub struct Sandbox {
    blob: ProgramBlob,
    engine: polkavm::Engine,
    module: polkavm::Module,
    module_config: polkavm::ModuleConfig,
}

impl Sandbox {
    pub fn from_uri(uri: &str) -> Result<Self, SandboxError> {
        let bytecode = fs::read(uri)?;
        let blob = ProgramBlob::parse(ArcBytes::from(bytecode))
            .map_err(|e| anyhow::anyhow!("Failed to parse program blob: {}", e))?;

        let config = polkavm::Config::new();
        let engine = polkavm::Engine::new(&config)?;
        let module_config = polkavm::ModuleConfig::new();

        let module = polkavm::Module::from_blob(&engine, &module_config, blob.clone())?;
        Ok(Sandbox {
            blob,
            engine,
            module,
            module_config,
        })
    }

    pub fn enable_step_tracing(&mut self) {
        self.module_config.set_step_tracing(true);
        self.module =
            polkavm::Module::from_blob(&self.engine, &self.module_config, self.blob.clone())
                .expect("Failed to re-instantiate module with new config");
    }

    pub fn instantiate(&self) -> Result<polkavm::RawInstance, SandboxError> {
        let mut instance = self.module.instantiate()?;
        instance.set_reg(polkavm::Reg::RA, polkavm::RETURN_TO_HOST);
        instance.set_reg(polkavm::Reg::SP, self.module.default_sp());
        Ok(instance)
    }

    pub fn get_source_location_for_pc(&self, pc: ProgramCounter) {
        if let Ok(Some(line_program)) = self.blob.get_debug_line_program_at(pc) {
            let mut line_program = line_program;

            while let Ok(Some(region_info)) = line_program.run() {
                if region_info.instruction_range().contains(&pc) {
                    for frame in region_info.frames() {
                        if frame.kind() == FrameKind::Line {
                            if let Ok(Some(location)) = frame.location() {
                                let function_name = frame.function_name_without_namespace()
                                    .ok()
                                    .flatten()
                                    .map(|s| s.to_string());

                                println!("Location {:?} name: {:?}", location, function_name);
                            }
                        }
                    }
                }
            }
        }
    }
}
