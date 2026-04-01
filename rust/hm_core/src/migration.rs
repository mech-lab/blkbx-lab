#![allow(dead_code)]

use crate::family::FamilyDescriptor;

pub trait MigrationBackend<Config, Handle> {
    type Error;

    fn name(&self) -> &'static str;
    fn descriptor(&self) -> &FamilyDescriptor;
    fn translate_config(&self, config: &Config) -> Result<Config, Self::Error>;
    fn load_runtime(&self, config: &Config) -> Result<Handle, Self::Error>;
}
