use crate::clustering::reverse_complement;
use crate::structs::MinimizerHashed;
use log::debug;
use std::collections::hash_map::DefaultHasher;
use std::collections::VecDeque;
use std::hash::{Hash, Hasher};

//takes an object T and hashes it via DefaultHasher. Used to improve search for minimizers in the data
pub fn calculate_hash<T: Hash + ?Sized>(t: &T) -> u64 {
    let mut s = DefaultHasher::new();
    t.hash(&mut s);
    s.finish()
}

pub fn compute_d_no_min() -> [f64; 128] {
    let mut d = [0.0; 128];

    for (i, value) in d.iter_mut().enumerate() {
        let chr_i = i as u8 as char;
        let ord_i = chr_i as i8;
        let exponent = -(ord_i - 33) as f64 / 10.0;
        *value = (10.0_f64).powf(exponent);
    }
    d
}

//TODO: add neccessity that the user should give only valid combinations of s t and k
pub(crate) fn syncmers_canonical(
    seq: &[u8],
    k: usize,
    s: usize,
    t: usize,
    syncmers: &mut Vec<MinimizerHashed>,
) {
    // Calculate reverse complement
    let seq_rc = reverse_complement(std::str::from_utf8(seq).unwrap());
    let seq_len = seq.len();
    debug!("seqlen {}", seq_len);
    debug!("seq_len {}", seq_len);
    // Initialize deques for forward and reverse complement sequences (stores the hashs of the smers)
    let mut window_smers_fw: VecDeque<u64> = (0..k - s + 1)
        .map(|i| calculate_hash(&seq[i..i + s]))
        .collect();
    //Initialize the reverse complement deque. We store the hash of the smer, however we have to generate the smer first. For this we take
    let mut window_smers_rc: VecDeque<u64> = (0..k - s + 1)
        .map(|i| calculate_hash(&seq_rc[seq_len - (i + s)..seq_len - i]))
        .collect();
    debug!("{} elements in our deque", window_smers_fw.len());
    // Find initial minimums (fw and rc)
    let mut curr_min_fw = *window_smers_fw.iter().min().unwrap();
    let mut curr_min_rc = *window_smers_rc.iter().min().unwrap();
    //find the minimum positions (fw and rc)
    let pos_min_fw = window_smers_fw
        .iter()
        .position(|&x| x == curr_min_fw)
        .unwrap();
    let pos_min_rc = window_smers_rc
        .iter()
        .position(|&x| x == curr_min_rc)
        .unwrap();
    let rc_hash =
        calculate_hash(reverse_complement(std::str::from_utf8(&seq[0..k]).unwrap()).as_str());
    // Choose minimum position
    let (pos_min, seq_tmp) = if curr_min_fw < curr_min_rc {
        (pos_min_fw, calculate_hash(&seq[0..k]))
    } else {
        (pos_min_rc, rc_hash)
    };

    // Initialize syncmers list
    if pos_min == t {
        syncmers.push(MinimizerHashed {
            sequence: seq_tmp,
            position: 0,
        });
    }

    // Iterate over the sequence
    for i in (k - s) + 1..seq.len() - k {
        debug!("i {}", i);
        let new_smer_fw = calculate_hash(&seq[i..i + s]);
        let rev_slice = &seq_rc[seq_len - (i + s)..seq_len - i];
        let new_smer_rc = calculate_hash(rev_slice);
        debug!(
            "fw_len: {}, rc_len: {}",
            &seq[i..i + s].len(),
            &seq_rc[seq_len - (i + 1) - s..seq_len - (i + 1)].len()
        );
        // Update windows
        let _ = window_smers_fw.pop_front();
        window_smers_fw.push_back(new_smer_fw);
        let _ = window_smers_rc.pop_front();
        window_smers_rc.push_back(new_smer_rc);

        // Update minimums and positions
        curr_min_fw = *window_smers_fw.iter().min().unwrap();
        curr_min_rc = *window_smers_rc.iter().min().unwrap();
        let pos_min_fw = window_smers_fw
            .iter()
            .position(|&x| x == curr_min_fw)
            .unwrap();
        let pos_min_rc = window_smers_rc
            .iter()
            .position(|&x| x == curr_min_rc)
            .unwrap();
        // Choose minimum position
        debug!("startpos {} end {}", i - (k - s), i - (k - s) + k);
        let rc_hash = calculate_hash(
            reverse_complement(std::str::from_utf8(&seq[i - (k - s)..i - (k - s) + k]).unwrap())
                .as_str(),
        );
        let (pos_min, kmer) = if curr_min_fw < curr_min_rc {
            (
                pos_min_fw,
                calculate_hash(&seq[i - (k - s)..i - (k - s) + k]),
            )
        } else {
            (pos_min_rc, rc_hash)
        };

        // Add syncmer to the list
        if pos_min == t {
            syncmers.push(MinimizerHashed {
                sequence: kmer,
                position: i,
            });
        }
    }
}

///Used to detect significant minimizers by checking the read qualities and estimating the overall quality of the area of the read
/// Input: quality_interval: the quality values of the area we want to check
/// Output: significance_indicator: a bool stating whether the minimizer is significant( true: yes, false: no)
///
pub fn is_significant(
    quality_interval: &[u8],
    d_no_min: [f64; 128],
    quality_threshold: &f64,
) -> bool {
    let mut significance_indicator = false;
    let mut qualities: Vec<f64> = vec![];
    let mut quality = 1.0;
    let mut index;
    let mut q_value;
    let mut probability_error;
    //for each character in quality string:
    for c in quality_interval {
        index = c.to_ascii_lowercase() as usize;
        //q_value gives the PHRED quality score: i.e. '+' gives us 0.1
        q_value = d_no_min[index];
        //here we get the base call accuracy
        probability_error = 1.0 - q_value;
        qualities.push(probability_error);
        quality *= probability_error
    }

    //TODO: let quality be dependent on length of quality_interval (e.g. 1*E-len)
    if quality > *quality_threshold {
        significance_indicator = true;
    }
    significance_indicator
}

//filter out minimizers for which the quality of the minimizer_impact range is too bad
pub fn filter_seeds_by_quality(
    this_minimizers: &Vec<MinimizerHashed>,
    fastq_quality: &[u8],
    k: usize,
    d_no_min: [f64; 128],
    minimizers_filtered: &mut Vec<MinimizerHashed>,
    quality_threshold: &f64,
    verbose: bool,
) {
    let mut skipped_cter = 0;
    let mut minimizer_range_start: usize;
    let mut significant;
    debug!("Number of minimizers: {}", this_minimizers.len());
    for mini in this_minimizers {
        //TODO: test whether into_par_iter works here
        minimizer_range_start = mini.position;
        let qualitiy_interval = &fastq_quality[minimizer_range_start..minimizer_range_start + k];
        debug!("Quality_interval len {}", qualitiy_interval.len());
        significant = is_significant(qualitiy_interval, d_no_min, quality_threshold);
        debug!("Quality intervallen {}", qualitiy_interval.len());
        if significant {
            minimizers_filtered.push(mini.clone())
        } else {
            skipped_cter += 1;
        }
    }
    if verbose {
        debug!("Number of insignificant seeds: {}", skipped_cter);
        debug!("Number of significant seeds: {}", minimizers_filtered.len());
    }
}

///Method used to generate syncmers from reads
/// INPUT:  seq: a string reference to the original read sequence
///         k_size: The size of the k_mer used
///         s_size: The size of s
///         t: The size of parameter t
///OUTPUT:  syncmers: A vector storing all syncmers (we use the minimizer struct to store them as essentially the same infos)
pub(crate) fn get_kmer_syncmers(
    seq: &[u8],
    k: usize,
    s: usize,
    t: usize,
    syncmers: &mut Vec<MinimizerHashed>,
) {
    //TODO: add neccessity that the user should give only valid combinations of s t and k
    // Calculate reverse complement
    //let seq_rc = reverse_complement(std::str::from_utf8(seq).unwrap());
    let seq_len = seq.len();
    debug!("seqlen {}", seq_len);
    debug!("seq_len {}", seq_len);
    // Initialize deques for forward and reverse complement sequences (stores the hashs of the smers)
    let mut window_smers_fw: VecDeque<u64> = (0..k - s + 1)
        .map(|i| calculate_hash(&seq[i..i + s]))
        .collect();
    //Initialize the reverse complement deque. We store the hash of the smer, however we have to generate the smer first. For this we take
    //let mut window_smers_rc: VecDeque<u64> = (0..k - s + 1)
    //    .map(|i| calculate_hash(&seq_rc[seq_len-(i+s)..seq_len-i]))
    //    .collect();
    debug!("{} elements in our deque", window_smers_fw.len());
    // Find initial minimums (fw and rc)
    let mut curr_min_fw = *window_smers_fw.iter().min().unwrap();
    //let mut curr_min_rc = *window_smers_rc.iter().min().unwrap();
    //find the minimum positions (fw and rc)
    let pos_min_fw = window_smers_fw
        .iter()
        .position(|&x| x == curr_min_fw)
        .unwrap();
    //let pos_min_rc = window_smers_rc.iter().position(|&x| x == curr_min_rc).unwrap();
    //let rc_hash=calculate_hash(reverse_complement(std::str::from_utf8(&seq[0..k]).unwrap()).as_str());
    // Choose minimum position
    //let (pos_min, seq_tmp) = if curr_min_fw < curr_min_rc {
    //    (pos_min_fw, calculate_hash(&seq[0..k]))
    //} else {
    //
    //    (pos_min_rc, rc_hash)
    //};

    // Initialize syncmers list
    if pos_min_fw == t {
        syncmers.push(MinimizerHashed {
            sequence: calculate_hash(&seq[0..k]),
            position: 0,
        });
    }

    // Iterate over the sequence
    for i in (k - s) + 1..seq.len() - k {
        debug!("i {}", i);
        let new_smer_fw = calculate_hash(&seq[i..i + s]);
        //let rev_slice=&seq_rc[seq_len-(i+s)..seq_len-i];
        //let new_smer_rc = calculate_hash(rev_slice);
        // Update windows
        let _ = window_smers_fw.pop_front();
        window_smers_fw.push_back(new_smer_fw);
        //let _ = window_smers_rc.pop_front();
        //window_smers_rc.push_back(new_smer_rc);

        // Update minimums and positions
        curr_min_fw = *window_smers_fw.iter().min().unwrap();
        //curr_min_rc = *window_smers_rc.iter().min().unwrap();
        let pos_min_fw = window_smers_fw
            .iter()
            .position(|&x| x == curr_min_fw)
            .unwrap();
        //let pos_min_rc = window_smers_rc.iter().position(|&x| x == curr_min_rc).unwrap();
        // Choose minimum position
        debug!("startpos {} end {}", i - (k - s), i - (k - s) + k);
        //let rc_hash= calculate_hash(reverse_complement(std::str::from_utf8(&seq[i-(k-s)..i-(k-s)+k]).unwrap()).as_str());
        //let (pos_min, kmer) = if curr_min_fw < curr_min_rc {
        //    (pos_min_fw, calculate_hash(&seq[i-(k-s)..i-(k-s)+k]))
        //} else {
        //    (pos_min_rc,rc_hash)
        //};

        // Add syncmer to the list
        if pos_min_fw == t {
            syncmers.push(MinimizerHashed {
                sequence: calculate_hash(&seq[i - (k - s)..i - (k - s) + k]),
                position: i,
            });
        }
    }
}

// #[cfg(test)]
// mod tests {
//     use super::*;

//     //#[test]
//     /*fn test_kmer_minimizers_0() {
//         let input = "ATGCTAGCATGCTAGCATGCTAGC";
//         let window_size = 8;
//         let k = 3;
//         let actual_minimizers = get_kmer_minimizers(input, k, window_size);
//         println!("Generated Minimizers: {:?}", actual_minimizers);
//         let expected_minimizers = vec![
//             Minimizer { sequence: "ATG".to_string(), position: 0 },
//             Minimizer { sequence: "AGC".to_string(), position: 5 },
//             Minimizer { sequence: "ATG".to_string(), position: 8 },
//             Minimizer { sequence: "AGC".to_string(), position: 13 },
//             Minimizer { sequence: "ATG".to_string(), position: 16 },
//             Minimizer { sequence: "AGC".to_string(), position: 21 },
//         ];
//         assert_eq!(actual_minimizers, expected_minimizers);
//     }
//     #[test]
//     fn test_kmer_minimizers_1() {
//         let input = "CAATTTAAGGCCCGGG";
//         let window_size = 10;
//         let k = 5;
//         let actual_minimizers = get_kmer_minimizers(input, k, window_size);
//         println!("Generated Minimizers: {:?}", actual_minimizers);
//         let expected_minimizers = vec![
//             Minimizer { sequence: "AATTT".to_string(), position: 1 },
//             Minimizer { sequence: "AAGGC".to_string(), position: 6 },
//             Minimizer { sequence: "AGGCC".to_string(), position: 7 },
//         ];
//         assert_eq!(actual_minimizers, expected_minimizers);
//     }

//     #[test]
//     fn test_kmer_minimizers_2() {
//         let input = "CAAAGTAAGGCCCTCC";
//         let window_size = 10;
//         let k = 5;
//         let actual_minimizers = get_kmer_minimizers(input, k, window_size);
//         println!("Generated Minimizers: {:?}", actual_minimizers);
//         let expected_minimizers = vec![
//             Minimizer { sequence: "AAAGT".to_string(), position: 1 },
//             Minimizer { sequence: "AAGGC".to_string(), position: 6 },
//             Minimizer { sequence: "AGGCC".to_string(), position: 7 },
//         ];
//         assert_eq!(actual_minimizers, expected_minimizers);
//     }
//     #[test]
//     fn test_kmer_minimizers_3() {
//         let input = "CAATGA";
//         let window_size = 10;
//         let k = 5;
//         let actual_minimizers = get_kmer_minimizers(input, k, window_size);
//         println!("Generated Minimizers: {:?}", actual_minimizers);
//         let expected_minimizers = vec![
//             Minimizer { sequence: "AATGA".to_string(), position: 1 },
//         ];
//         assert_eq!(actual_minimizers, expected_minimizers);
//     }
//     #[test]
//     fn test_canonical_minis_1(){
//         let input ="GGGTAACTTTTCA";
//         let window_size=12;
//         let k =6;
//         let actual_minimizers=get_canonical_kmer_minimizers(input,k,window_size);
//         println!("Generated Minimizers: {:?}", actual_minimizers);
//         let expected_minimizers = vec![
//             Minimizer { sequence: "AAAAGT".to_string(), position: 5 },
//         ];
//         assert_eq!(actual_minimizers, expected_minimizers);
//     }
//     /*#[test]
//     fn test_kmer_syncmers(){
//         let input ="CATTCAGGAATC";
//         let k=5;
//         let s=2;
//         let t=2;
//         let retreived_syncmers=get_kmer_syncmers(input,k,s,t);
//         let expected_syncmers=vec![
//             Minimizer { sequence: "TCAGG".to_string(), position: 3 },
//             Minimizer { sequence: "GGAAT".to_string(),position: 6},

//         ];
//         assert_eq!(retreived_syncmers, expected_syncmers);
//     }*/
//     #[test]
//     fn test_average_0(){
//         let mut input=vec![];
//         input.push(0.5);
//         input.push(0.75);
//         input.push(0.25);
//         let average_res=average(&*input);
//         assert_eq!(average_res,0.5);
//     }
//     #[test]
//     fn test_average_1(){
//         let mut input=vec![];
//         input.push(1.0);
//         input.push(2.0);
//         input.push(3.0);
//         let average_res=average(&*input);
//         assert_eq!(average_res,2.0);
//     }*/
// }
