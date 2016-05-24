#!/router/bin/python

import cdot_api_lib
import getopt
import sys
import time

argv = sys.argv[1:]

try:
   opts, args = getopt.getopt(argv, 'c:h',['cluster=','help'])
except getopt.error:
   usage()
   sys.exit(2)

for opt, arg in opts:
   if opt in ("-h","--help"):
      print "fix_malformed_quotas.py -c <cluster> -v <svm/vserver>"
      sys.exit()
   elif opt in ("-c","--cluster"):
      cluster = arg


cluster_connection = cdot_api_lib.cdot_cluster_mgmt(cluster)
malformed_quota_rules = cluster_connection.get_malformed_quotas()

for malformed_quota_rule in malformed_quota_rules:
   volume, vserver, disk_limit, file_limit, user_mapping, qtree, quota_type, quota_target, soft_disk, soft_file, threshold = malformed_quota_rules[malformed_quota_rule]

   users = quota_target.split(',')
   for user in users:
      cluster_connection.set_quota(vserver, disk_limit, file_limit, 'true', volume, qtree, quota_type, user, soft_disk, soft_file, threshold)
      time.sleep(5)
      
   cluster_connection.delete_quota(vserver, 'default', qtree, quota_target, quota_type, volume)    
   time.sleep(5)
   cluster_connection.quota_off(vserver, volume)
   time.sleep(5)
   cluster_connection.quota_on(vserver, volume)
   time.sleep(5)
