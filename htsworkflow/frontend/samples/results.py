from htsworkflow.frontend import settings

import glob
import os
import re

s_paren = re.compile("^\w+")

def get_flowcell_result_dict(flowcell_id):
    """
    returns a dictionary following the following pattern for
    a given flowcell_id:
    
     
    d['C1-33']['summary']           # Summary.htm file path
    d['C1-33']['eland_results'][5]  # C1-33 lane 5 file eland results file path
    d['C1-33']['run_xml']           # run_*.xml file path
    d['C1-33']['scores']            # scores.tar.gz file path
    """
    flowcell_id = flowcell_id.strip()
    
    d = {}
    
    ################################
    # Flowcell Directory
    fc_dir = glob.glob(os.path.join(settings.RESULT_HOME_DIR, flowcell_id))
    
    # Not found
    if len(fc_dir) == 0:
        return None
    
    # No duplicates!
    assert len(fc_dir) <= 1
    
    # Found fc dir
    fc_dir = fc_dir[0]
    
    ################################
    # C#-## dirs
    c_dir_list = glob.glob(os.path.join(fc_dir, 'C*'))
    
    # Not found
    if len(c_dir_list) == 0:
        return d
    
    for c_dir_path in c_dir_list:
        summary_file = glob.glob(os.path.join(c_dir_path, 'Summary.htm'))
        pathdir, c_dir = os.path.split(c_dir_path)
        
        # Create sub-dictionary
        d[c_dir] = {}
        
        
        ###############################
        # Summary.htm file
        
        # Not found
        if len(summary_file) == 0:
            d[c_dir]['summary'] = None
            
        # Found
        else:
            # No duplicates!
            assert len(summary_file) == 1
            
            summary_file = summary_file[0]
            d[c_dir]['summary'] = summary_file
            
        ###############################
        # Result files
        
        d[c_dir]['eland_results'] = {}
        
        result_filepaths = glob.glob(os.path.join(c_dir_path, 's_*_eland_*'))
        
        for filepath in result_filepaths:
            
            junk, result_name = os.path.split(filepath)
            
            #lanes 1-8, single digit, therefore s_#; # == index 2
            lane = int(result_name[2])
            d[c_dir]['eland_results'][lane] = filepath
            
        ###############################
        # run*.xml file
        run_xml_filepath = glob.glob(os.path.join(c_dir_path, 'run_*.xml'))
        
        if len(run_xml_filepath) == 0:
            d[c_dir]['run_xml'] = None
        else:
            # No duplicates
            assert len(run_xml_filepath) == 1
            
            d[c_dir]['run_xml'] = run_xml_filepath[0]
            
        ###############################
        # scores.tar.gz
        # restrict to only compressed files, so in case there are *.md5 files
        # we don't get confused.
        scores_filepath = []
        for pattern in ['scores*.tar.bz2', 'scores*.tar.gz', 'scores*.tgz']:
            scores_filepath += glob.glob(os.path.join(c_dir_path, pattern))
        
        if len(scores_filepath) == 0:
            d[c_dir]['scores'] = None
        else:
            # No duplicates
            assert len(scores_filepath) == 1
            
            d[c_dir]['scores'] = scores_filepath[0]
        
    return d

    
def cn_mTobp(cn_m):
    """
    Converts CN-M (i.e. C1-33, C1-26, C4-28) cycle information into
    number of base pairs.
    """
    pass


def parse_flowcell_id(flowcell_id):
    """
    Return flowcell id and any status encoded in the id
  
    We stored the status information in the flowcell id name.
    this was dumb, but database schemas are hard to update.
    """
    fields = flowcell_id.split()
    fcid = None
    status = None
    if len(fields) > 0:
        fcid = fields[0]
    if len(fields) > 1:
        status = fields[1]
    return fcid, status
    
