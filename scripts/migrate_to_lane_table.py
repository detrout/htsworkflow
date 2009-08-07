#!/usr/bin/env python

from htsworkflow.frontend.experiments.models import FlowCell, Lane


if __name__ == '__main__':
    
    print "Migration starting..."
    
    #Get all flowcells
    for flowcell in FlowCell.objects.all():
        
        ##################
        # Lane 1
        lane1 = Lane()
        
        # ForeignKey Links
        lane1.flowcell = flowcell
        lane1.library = flowcell.lane_1_library
        
        # Meta Data
        lane1.lane_number = 1
        lane1.pm = flowcell.lane_1_pM
        lane1.cluster_estimate = flowcell.lane_1_cluster_estimate
        
        # Save
        lane1.save()
        
        ##################
        # Lane 2
        lane2 = Lane()
        
        # ForeignKey Links
        lane2.flowcell = flowcell
        lane2.library = flowcell.lane_2_library
        
        # Meta Data
        lane2.lane_number = 2
        lane2.pm = flowcell.lane_2_pM
        lane2.cluster_estimate = flowcell.lane_2_cluster_estimate
        
        # Save
        lane2.save()
        
        ##################
        # Lane 3
        lane3 = Lane()
        
        # ForeignKey Links
        lane3.flowcell = flowcell
        lane3.library = flowcell.lane_3_library
        
        # Meta Data
        lane3.lane_number = 3
        lane3.pm = flowcell.lane_3_pM
        lane3.cluster_estimate = flowcell.lane_3_cluster_estimate
        
        # Save
        lane3.save()
        
        ##################
        # Lane 4
        lane4 = Lane()
        
        # ForeignKey Links
        lane4.flowcell = flowcell
        lane4.library = flowcell.lane_4_library
        
        # Meta Data
        lane4.lane_number = 4
        lane4.pm = flowcell.lane_4_pM
        lane4.cluster_estimate = flowcell.lane_4_cluster_estimate
        
        # Save
        lane4.save()
        
        ##################
        # Lane 5
        lane5 = Lane()
        
        # ForeignKey Links
        lane5.flowcell = flowcell
        lane5.library = flowcell.lane_5_library
        
        # Meta Data
        lane5.lane_number = 5
        lane5.pm = flowcell.lane_5_pM
        lane5.cluster_estimate = flowcell.lane_5_cluster_estimate
        
        # Save
        lane5.save()
        
        ##################
        # Lane 6
        lane6 = Lane()
        
        # ForeignKey Links
        lane6.flowcell = flowcell
        lane6.library = flowcell.lane_6_library
        
        # Meta Data
        lane6.lane_number = 6
        lane6.pm = flowcell.lane_6_pM
        lane6.cluster_estimate = flowcell.lane_6_cluster_estimate
        
        # Save
        lane6.save()
        
        ##################
        # Lane 7
        lane7 = Lane()
        
        # ForeignKey Links
        lane7.flowcell = flowcell
        lane7.library = flowcell.lane_7_library
        
        # Meta Data
        lane7.lane_number = 7
        lane7.pm = flowcell.lane_7_pM
        lane7.cluster_estimate = flowcell.lane_7_cluster_estimate
        
        # Save
        lane7.save()
        
        ##################
        # Lane 8
        lane8 = Lane()
        
        # ForeignKey Links
        lane8.flowcell = flowcell
        lane8.library = flowcell.lane_8_library
        
        # Meta Data
        lane8.lane_number = 8
        lane8.pm = flowcell.lane_1_pM
        lane8.cluster_estimate = flowcell.lane_8_cluster_estimate
        
        # Save
        lane8.save()

    print "Migration Complete."