use anyhow::{Context, Result};
use std::path::PathBuf;
use std::sync::Arc;
use unpayload::{ExtractOptions, LocalFile, Payload, ReadAt, Slice};

fn main() -> Result<()> {
    let mut args = std::env::args().skip(1);
    let path: PathBuf = args.next().context("zip")?.into();
    let offset: u64 = args.next().context("payload offset")?.parse()?;
    let out: PathBuf = args.next().context("out dir")?.into();
    let partitions: Vec<String> = args.collect();
    let f = LocalFile::open(&path)?;
    let len = f.size() - offset;
    let slice = Slice::new(Arc::new(f), offset, len)?;
    let payload = Payload::from_reader(Arc::new(slice))?;
    let options = ExtractOptions { output_dir: out, partitions, ..Default::default() };
    let report = |event: unpayload::Event<'_>| match event {
        unpayload::Event::Started { partitions } => eprintln!("partitions: {partitions:?}"),
        unpayload::Event::Extracted(image) => eprintln!("extracted {}: {} bytes", image.partition, image.size),
        unpayload::Event::Progress { .. } => {}
    };
    payload.extract(&options, &report)?;
    Ok(())
}
