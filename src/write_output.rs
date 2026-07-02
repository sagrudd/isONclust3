use crate::{file_actions, ClusterIdMap};
use log::debug;
use log::info;
use rustc_hash::FxHashMap;
use std::fs;
use std::fs::File;
use std::io::{BufWriter, Write};
use std::path::Path;
use std::path::PathBuf;

pub(crate) fn write_ordered_fastq(
    score_vec: &[(i32, usize)],
    outfolder: &str,
    id_map: &FxHashMap<i32, String>,
    fastq: &str,
) {
    //writes the fastq file
    let _ = fs::create_dir_all(PathBuf::from(outfolder).join("clustering"));
    let fastq_file = File::open(fastq).unwrap();
    let mut fastq_records = FxHashMap::default();
    file_actions::parse_fastq_hashmap(fastq_file, &mut fastq_records);
    let f = File::create(outfolder.to_owned() + "/clustering/sorted.fastq")
        .expect("Unable to create file");
    let mut buf_write = BufWriter::new(&f);

    //for record in fastq_records {
    for score_tup in score_vec.iter() {
        let this_header = id_map.get(&score_tup.0).unwrap();
        let record = fastq_records.get(this_header).unwrap();
        write!(
            buf_write,
            "@{}\n{}\n+\n{}\n",
            record.get_header(),
            record.get_sequence(),
            record.get_quality()
        )
        .expect("Could not write file");
    }
    buf_write.flush().expect("Failed to flush the buffer");
}

fn write_final_clusters_tsv(
    outfolder: &Path,
    clusters: &ClusterIdMap,
    id_map: &FxHashMap<i32, String>,
    header_cluster_map: &mut FxHashMap<String, i32>,
) {
    let file_path = PathBuf::from(outfolder).join("final_clusters.tsv");

    let f = File::create(file_path).expect("unable to create file");
    let mut buf_write = BufWriter::new(&f);
    let mut nr_reads = 0;
    info!("{} different clusters identified", clusters.len());
    //let nr_clusters=clusters.len();
    for (cl_id, r_int_ids) in clusters.iter() {
        debug!("cl_id {}, nr_reads {:?}", cl_id, nr_reads);
        for r_int_id in r_int_ids {
            let read_id = id_map.get(r_int_id).unwrap();
            nr_reads += 1;
            let _ = writeln!(buf_write, "{}\t{}", cl_id, read_id);
            header_cluster_map.insert(read_id.clone(), *cl_id);
        }
    }
    // Flush the buffer to ensure all data is written to the underlying file
    buf_write.flush().expect("Failed to flush the buffer");
    // debug!("{} different clusters identified", nr_clusters);
    debug!("HCLM {:?}", header_cluster_map);
    info!("{} reads added to tsv file", nr_reads);
}

fn cluster_fastq_output_ids(clusters: &ClusterIdMap, n: usize) -> FxHashMap<i32, usize> {
    let mut cluster_ids: Vec<i32> = clusters
        .iter()
        .filter_map(|(cluster_id, reads)| (reads.len() >= n).then_some(*cluster_id))
        .collect();
    cluster_ids.sort_unstable();
    cluster_ids
        .into_iter()
        .enumerate()
        .map(|(output_id, cluster_id)| (cluster_id, output_id))
        .collect()
}

fn write_fastq_files_streaming(
    outfolder: &Path,
    clusters: &ClusterIdMap,
    header_cluster_map: &FxHashMap<String, i32>,
    fastq: &str,
    n: usize,
) {
    let mut read_cter = 0;
    let fastq_outfolder = PathBuf::from(outfolder);
    let cluster_output_ids = cluster_fastq_output_ids(clusters, n);
    let mut writers: FxHashMap<i32, BufWriter<File>> = FxHashMap::default();
    let fastq_file = File::open(fastq).unwrap();
    file_actions::parse_fastq_records(fastq_file, |record| {
        let Some(cluster_id) = header_cluster_map.get(record.header.as_str()) else {
            return;
        };
        let Some(output_id) = cluster_output_ids.get(cluster_id) else {
            return;
        };
        let writer = writers.entry(*cluster_id).or_insert_with(|| {
            let filename = format!("{output_id}.fastq");
            let file_path = fastq_outfolder.join(filename);
            let file = File::create(file_path).expect("unable to create file");
            BufWriter::new(file)
        });
        write!(
            writer,
            "@{}\n{}\n+\n{}\n",
            record.header, record.sequence, record.quality
        )
        .expect("We should be able to write the entries");
        read_cter += 1;
    });
    for writer in writers.values_mut() {
        writer.flush().expect("Failed to flush the buffer");
    }
    for cluster_id in cluster_output_ids.keys() {
        if !writers.contains_key(cluster_id) {
            debug!("cl id for writing: {}, {}", cluster_id, read_cter);
        }
    }
    info!("{} reads written", read_cter);
}

pub fn path_exists(path: &str) -> bool {
    fs::metadata(path).is_ok()
}

pub(crate) fn write_output(
    outfolder: String,
    clusters: &ClusterIdMap,
    fastq: String,
    id_map: &FxHashMap<i32, String>,
    n: usize,
    no_fastq: bool,
) {
    if !path_exists(&outfolder) {
        fs::create_dir(outfolder.clone()).expect("We should be able to create the directory");
    }
    //clustering_path: the outfolder of isONclust3
    let clustering_path = Path::new(&outfolder).join("clustering");
    if !clustering_path.exists() {
        let _ = fs::create_dir(clustering_path.clone());
    }
    //the subfolder of clustering in which we write the fastq_files ( as done in isONclust1)
    let fastq_path = clustering_path.join("fastq_files");
    if !fastq_path.exists() {
        let _ = fs::create_dir(fastq_path.clone());
    }
    let mut header_cluster_map = FxHashMap::default();
    write_final_clusters_tsv(&clustering_path, clusters, id_map, &mut header_cluster_map);
    //no_fastq: true -> we do not want to write the fastq files
    if !no_fastq {
        info!("Writing the fastq files");
        write_fastq_files_streaming(&fastq_path, clusters, &header_cluster_map, &fastq, n);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn cluster_fastq_output_ids_are_sorted_and_thresholded() {
        let mut clusters = ClusterIdMap::default();
        clusters.insert(4, vec![10, 11]);
        clusters.insert(2, vec![12]);
        clusters.insert(7, vec![13, 14, 15]);

        let output_ids = cluster_fastq_output_ids(&clusters, 2);

        assert_eq!(output_ids.get(&2), None);
        assert_eq!(output_ids.get(&4), Some(&0));
        assert_eq!(output_ids.get(&7), Some(&1));
    }
}
