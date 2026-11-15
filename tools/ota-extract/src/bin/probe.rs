use anyhow::{Context, Result};
use std::sync::Arc;
use unpayload::{LocalFile, Payload, ReadAt, Slice};

fn main() -> Result<()> {
    let mut args = std::env::args().skip(1);
    let path = args.next().context("zip")?;
    let offset: u64 = args.next().context("payload offset")?.parse()?;
    let f = LocalFile::open(std::path::Path::new(&path))?;
    let len = f.size() - offset;
    let slice = Slice::new(Arc::new(f), offset, len)?;
    let p = Payload::from_reader(Arc::new(slice))?;
    println!("block size {} partitions {}", p.block_size(), p.partitions().len());
    for part in p.partitions() {
        let mut max_end = 0u64;
        let mut bytes = 0u64;
        for op in &part.operations {
            if let (Some(o), Some(l)) = (op.data_offset, op.data_length) {
                max_end = max_end.max(o + l);
                bytes += l;
            }
        }
        let size = part.new_partition_info.as_ref().and_then(|i| i.size).unwrap_or(0);
        println!("{:<16} size {:>12} data_end {:>12} data_bytes {:>12} ops {}", part.partition_name, size, max_end, bytes, part.operations.len());
    }
    Ok(())
}
