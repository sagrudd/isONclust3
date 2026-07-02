use crate::structs;
use crate::structs::FastqRecordIsonclInit;
use rustc_hash::FxHashMap;
use std::fs::File;
use std::io::{BufRead, BufReader};

fn shorten_header(header: &str) -> &str {
    header
        .split_once(' ')
        .map_or(header, |(short_header, _)| short_header)
}

pub(crate) fn parse_fastq_hashmap(
    file: File,
    records: &mut FxHashMap<String, structs::FastqRecordIsonclInit>,
) {
    parse_fastq_records(file, |record| {
        records.insert(record.header.clone(), record);
    });
}

pub(crate) fn parse_fastq_records(
    file: File,
    mut handle_record: impl FnMut(structs::FastqRecordIsonclInit),
) {
    let mut reader = BufReader::new(file);
    loop {
        let mut header = String::new();
        let header_read = reader.read_line(&mut header).expect("Should be contained");
        if header_read == 0 {
            break;
        }

        header = header.trim().to_owned();
        header = (header[1..]).to_string();
        header = shorten_header(&header).parse().unwrap();
        let mut sequence = String::new();
        let sequence_read = reader
            .read_line(&mut sequence)
            .expect("Should be contained");
        if sequence_read == 0 {
            break;
        }
        sequence = sequence.trim().to_owned();

        let mut quality_header = String::new();
        let quality_header_read = reader
            .read_line(&mut quality_header)
            .expect("Should be contained");
        if quality_header_read == 0 {
            break;
        }

        let mut quality = String::new();
        let quality_read = reader.read_line(&mut quality).expect("Should be contained");
        if quality_read == 0 {
            break;
        }
        quality = quality.trim().to_owned();
        handle_record(FastqRecordIsonclInit {
            header,
            sequence,
            quality,
        });
    }
}
