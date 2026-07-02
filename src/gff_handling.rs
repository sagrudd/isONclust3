use crate::structs::MinimizerHashed;
use std::fs::File;
use std::io::BufReader;

use bio::io::gff::GffType::GFF3;
use log::info;

use bio::io::fasta;
use bio::io::gff;
use minimizer_iter::MinimizerBuilder;
use std::path::Path;
extern crate rayon;
use crate::clustering;
use crate::{seeding_and_filtering_seeds, ClusterIdMap, SeedMap};
use log::debug;

pub(crate) struct GffClusteringConfig<'a> {
    pub gff_path: Option<&'a str>,
    pub fasta_path: Option<&'a str>,
    pub k: usize,
    pub w: usize,
    pub seeding: &'a str,
    pub s: usize,
    pub t: usize,
    pub noncanonical: bool,
}

fn gff_feature_sequence<'a>(sequence: &'a str, start: &u64, end: &u64) -> &'a str {
    let start_index = start
        .checked_sub(1)
        .expect("GFF coordinates are 1-based and must start at 1") as usize;
    let end_index = *end as usize;
    &sequence[start_index..end_index]
}

fn collect_feature_minimizers(
    feature_sequence: &str,
    config: &GffClusteringConfig<'_>,
) -> Vec<MinimizerHashed> {
    let mut minimizers = vec![];
    if config.seeding == "minimizer" {
        if config.noncanonical {
            let min_iter = MinimizerBuilder::<u64, _>::new()
                .minimizer_size(config.k)
                .width((config.w) as u16)
                .iter(feature_sequence.as_bytes());
            for (minimizer, position) in min_iter {
                minimizers.push(MinimizerHashed {
                    sequence: minimizer,
                    position,
                });
            }
        } else {
            let min_iter = MinimizerBuilder::<u64, _>::new()
                .canonical()
                .minimizer_size(config.k)
                .width((config.w) as u16)
                .iter(feature_sequence.as_bytes());
            for (minimizer, position, _) in min_iter {
                minimizers.push(MinimizerHashed {
                    sequence: minimizer,
                    position,
                });
            }
        }
    } else if config.seeding == "syncmer" && feature_sequence.len() > config.s {
        seeding_and_filtering_seeds::syncmers_canonical(
            feature_sequence.as_bytes(),
            config.k,
            config.s,
            config.t,
            &mut minimizers,
        );
    }
    minimizers
}

fn is_protein_coding_gene(record: &gff::Record) -> bool {
    record.feature_type() == "gene"
        && record
            .attributes()
            .get("gene_biotype")
            .expect("This algorithm requires a gene_biotype to extract the coding genes")
            == "protein_coding"
}

pub(crate) fn gff_based_clustering(
    config: &GffClusteringConfig<'_>,
    clusters: &mut ClusterIdMap,
    cluster_map: &mut SeedMap,
) {
    // Read the FASTA file
    let fasta_reader = File::open(Path::new(config.fasta_path.unwrap())).unwrap();
    let fasta_buf_reader = BufReader::new(fasta_reader);
    let fasta_records = fasta::Reader::new(fasta_buf_reader).records();
    // Read the GFF file
    let gff_reader = File::open(Path::new(config.gff_path.unwrap())).unwrap();
    let gff_buf_reader = BufReader::new(gff_reader);
    let mut binding = gff::Reader::new(gff_buf_reader, GFF3);
    let mut gff_records = binding.records();
    let mut gene_id = -1;
    let mut previous_genes = 0;
    // Iterate through FASTA records
    for fasta_record in fasta_records {
        let fasta_record = fasta_record.expect("Error reading FASTA record");
        let scaffold_id = fasta_record.id().to_string();
        let sequence = std::str::from_utf8(fasta_record.seq())
            .unwrap()
            .to_uppercase();
        debug!("scaffold {}", scaffold_id);
        // Process GFF records for the current scaffold ID
        for gff_record in gff_records.by_ref() {
            let gff_record = gff_record.expect("Error reading GFF record");
            let gff_scaffold_id = gff_record.seqname().to_string();
            // Check if the scaffold IDs match
            if scaffold_id == gff_scaffold_id {
                if is_protein_coding_gene(&gff_record) {
                    gene_id += 1;
                } else if gff_record.feature_type() == "exon" && gene_id >= 0 {
                    let exon_seq =
                        gff_feature_sequence(&sequence, gff_record.start(), gff_record.end());
                    let this_minimizers = collect_feature_minimizers(exon_seq, config);
                    clustering::generate_initial_cluster_map(
                        &this_minimizers,
                        cluster_map,
                        gene_id,
                    );
                    clusters.entry(gene_id).or_default();
                }
            } else {
                info!(
                    "found {} genes in {}",
                    gene_id - previous_genes,
                    scaffold_id
                );
                previous_genes = gene_id;
                if is_protein_coding_gene(&gff_record) {
                    gene_id += 1;
                }
                // If scaffold IDs don't match, break the inner loop
                break;
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn converts_gff_coordinates_to_rust_slice_bounds() {
        assert_eq!(gff_feature_sequence("ACGT", &1, &4), "ACGT");
        assert_eq!(gff_feature_sequence("ACGT", &2, &3), "CG");
    }
}
