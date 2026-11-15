use anyhow::{Context, Result};
use std::path::PathBuf;
use unpayload::{ExtractOptions, Payload};

fn main() -> Result<()> {
    let mut args = std::env::args().skip(1);
    let zip: PathBuf = args.next().context("usage: ota-extract <ota.zip> <out-dir> [partition...]")?.into();
    let out: PathBuf = args.next().context("usage: ota-extract <ota.zip> <out-dir> [partition...]")?.into();
    let partitions: Vec<String> = args.collect();
    let payload = Payload::open(&zip).with_context(|| format!("open {}", zip.display()))?;
    let options = ExtractOptions { output_dir: out, partitions, ..Default::default() };
    let report = |event: unpayload::Event<'_>| match event {
        unpayload::Event::Started { partitions } => eprintln!("partitions: {partitions:?}"),
        unpayload::Event::Extracted(image) => eprintln!("extracted {}: {} bytes", image.partition, image.size),
        unpayload::Event::Progress { .. } => {}
    };
    payload.extract(&options, &report)?;
    Ok(())
}
