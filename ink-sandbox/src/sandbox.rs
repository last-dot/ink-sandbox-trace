use std::fs;

use polkavm::{ArcBytes, Error, GasMeteringKind, InterruptKind, Linker, ProgramBlob, ProgramCounter};

pub type SandboxError = Box<dyn std::error::Error>;
pub type SandProgram = (String, ProgramCounter);
pub struct Sandbox {
    blob: ProgramBlob,
    engine: polkavm::Engine,
    module: polkavm::Module,
    module_config: polkavm::ModuleConfig,
    programs: Vec<SandProgram>,
}

impl Sandbox {
    pub fn from_uri(uri: &str) -> Result<Self, SandboxError> {
        let bytecode = fs::read(uri)?;
        let blob = ProgramBlob::parse(ArcBytes::from(bytecode))
            .map_err(|e| anyhow::anyhow!("Failed to parse program blob: {}", e))?;
        let config = polkavm::Config::new();
        let engine = polkavm::Engine::new(&config)?;
        let mut module_config = polkavm::ModuleConfig::new();
        module_config.set_gas_metering(Some(GasMeteringKind::Sync));
        let module = polkavm::Module::from_blob(&engine, &module_config, blob.clone())?;

        let mut program_counters = vec![];

        for export in blob.exports() {
            let name_bytes = export.symbol().as_bytes();
            let name = std::str::from_utf8(name_bytes)?;
            let pc = export.program_counter();
            let _ = &program_counters.push((name.to_string(), pc));
        }

        Ok(Sandbox {
            blob,
            engine,
            module,
            module_config,
            programs: program_counters,
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

    pub fn selectors(&self) {
        let mut instance = self.instantiate().unwrap();
        match instance.run().unwrap() {
            InterruptKind::Finished => {}
            InterruptKind::Trap => {}
            InterruptKind::Ecalli(_) => {}
            InterruptKind::Segfault(_) => {}
            InterruptKind::NotEnoughGas => {}
            InterruptKind::Step => {}
        }

        for (name, pc) in &self.programs {
            println!("{}: {}", name, pc);
        }
    }
}
