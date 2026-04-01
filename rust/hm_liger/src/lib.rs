use hm_core::family::{descriptor_for, FamilyDescriptor, TransportFamilyKind};
use hm_core::migration::MigrationBackend;

#[derive(Clone, Debug, PartialEq)]
pub struct LigerConfig {
    pub family: TransportFamilyKind,
    pub sequence_length: u32,
    pub bridge_cadence: u16,
}

#[derive(Clone, Debug, PartialEq)]
pub struct LigerRuntimeHandle {
    pub backend_name: &'static str,
    pub config: LigerConfig,
}

#[derive(Clone, Debug)]
pub struct LigerMigrationBackend {
    descriptor: FamilyDescriptor,
}

impl LigerMigrationBackend {
    pub fn new(family: TransportFamilyKind) -> Self {
        Self {
            descriptor: descriptor_for(family),
        }
    }
}

impl MigrationBackend<LigerConfig, LigerRuntimeHandle> for LigerMigrationBackend {
    type Error = &'static str;

    fn name(&self) -> &'static str {
        "liger"
    }

    fn descriptor(&self) -> &FamilyDescriptor {
        &self.descriptor
    }

    fn translate_config(&self, config: &LigerConfig) -> Result<LigerConfig, Self::Error> {
        Ok(LigerConfig {
            family: config.family,
            sequence_length: config.sequence_length.max(1024),
            bridge_cadence: config.bridge_cadence.max(1),
        })
    }

    fn load_runtime(&self, config: &LigerConfig) -> Result<LigerRuntimeHandle, Self::Error> {
        Ok(LigerRuntimeHandle {
            backend_name: self.name(),
            config: self.translate_config(config)?,
        })
    }
}
