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
    let mut gene_id = 0;
    let mut previous_genes = 0;
    // Iterate through FASTA records
    for fasta_record in fasta_records {
        let fasta_record = fasta_record.expect("Error reading FASTA record");
        let scaffold_id = fasta_record.id().to_string();
        let sequence = std::str::from_utf8(fasta_record.seq())
            .unwrap()
            .to_uppercase();
        let record_minis = vec![];
        debug!("scaffold {}", scaffold_id);
        // Process GFF records for the current scaffold ID
        for gff_record in gff_records.by_ref() {
            let gff_record = gff_record.expect("Error reading GFF record");
            let gff_scaffold_id = gff_record.seqname().to_string();
            // Check if the scaffold IDs match
            if scaffold_id == gff_scaffold_id {
                if gff_record.feature_type() == "gene"
                    && gff_record.attributes().get("gene_biotype").expect(
                        "This algorithm requires a gene_biotype to extract the coding genes",
                    ) == "protein_coding"
                {
                    gene_id += 1;
                } else if gff_record.feature_type() == "exon" {
                    let exon_seq =
                        &sequence[*gff_record.start() as usize..*gff_record.end() as usize];
                    let mut this_minimizers = vec![];
                    if config.seeding == "minimizer" {
                        if config.noncanonical {
                            let min_iter = MinimizerBuilder::<u64, _>::new()
                                .minimizer_size(config.k)
                                .width((config.w) as u16)
                                .iter(sequence.as_bytes());
                            for (minimizer, position) in min_iter {
                                let mini = MinimizerHashed {
                                    sequence: minimizer,
                                    position,
                                };
                                this_minimizers.push(mini);
                            }
                        } else {
                            let min_iter = MinimizerBuilder::<u64, _>::new()
                                .canonical()
                                .minimizer_size(config.k)
                                .width((config.w) as u16)
                                .iter(sequence.as_bytes());
                            for (minimizer, position, _) in min_iter {
                                let mini = MinimizerHashed {
                                    sequence: minimizer,
                                    position,
                                };
                                this_minimizers.push(mini);
                            }
                        }
                    } else if config.seeding == "syncmer" && exon_seq.len() > config.s {
                        seeding_and_filtering_seeds::syncmers_canonical(
                            exon_seq.as_bytes(),
                            config.k,
                            config.s,
                            config.t,
                            &mut this_minimizers,
                        );
                    }
                }
                clustering::generate_initial_cluster_map(&record_minis, cluster_map, gene_id);
                let id_vec = vec![];
                clusters.insert(gene_id, id_vec);
            } else {
                info!(
                    "found {} genes in {}",
                    gene_id - previous_genes,
                    scaffold_id
                );
                previous_genes = gene_id;
                if gff_record.feature_type() == "gene"
                    && gff_record.attributes().get("gene_biotype").expect(
                        "This algorithm requires a gene_biotype to extract the coding genes",
                    ) == "protein_coding"
                {
                    gene_id += 1;
                }
                // If scaffold IDs don't match, break the inner loop
                break;
            }
        }
    }
}
