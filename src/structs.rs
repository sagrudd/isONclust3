use std::fmt;

#[derive(Debug, Eq, PartialEq, Clone)]
pub struct MinimizerHashed {
    pub sequence: u64,
    pub position: usize,
    // pub is_representative: bool
}

pub(crate) struct FastqRecordIsonclInit {
    //a struct used to store fastq records
    pub header: String,
    pub sequence: String,
    pub quality: String,
}

impl FastqRecordIsonclInit {
    pub fn get_header(&self) -> &str {
        &self.header
    }
    //pub fn get_int_id(&self)->&i32{
    // &self.internal_id
    //}
    pub fn get_sequence(&self) -> &str {
        &self.sequence
    }
    pub fn get_quality(&self) -> &str {
        &self.quality
    }
}

impl fmt::Display for FastqRecordIsonclInit {
    // enables displaying the fastq record
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{}\n{}", self.header, self.sequence)
    }
}
