use hm_core::native::{gated_deltanet_kernel, validate_kernel};

fn main() {
    let kernel = gated_deltanet_kernel();
    let report = validate_kernel(&kernel);
    println!(
        "family={:?} passed={} bridges={}",
        report.family, report.passed, report.bridge_count
    );
}
