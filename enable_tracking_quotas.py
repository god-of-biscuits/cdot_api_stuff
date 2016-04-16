#!/router/bin/python

import cdot_api_lib
import subprocess
import getopt
import sys
import time
import logging

argv = sys.argv[1:]

try: 
   opts, args = getopt.getopt(argv, 'c:v:h',['cluster=','vserver=','help'])
except getopt.error:
   usage()
   sys.exit(2)

for opt, arg in opts:
   if opt == 'h':
      print "enable_tracking_quotas.py -c <cluster> -v <svm/vserver>"
      sys.exit()
   elif opt in ("-c","--cluster"):
      cluster = arg
      local_cluster = arg
   elif opt in ("-v","--vserver"):
      vserver = arg
      local_vserver = arg

log_file = './logs/enable_tracking_quotas.log'
logging.basicConfig(filename=log_file, level=logging.DEBUG)
logger = logging.getLogger(__name__)


cluster = cdot_api_lib.cdot_cluster_mgmt(cluster)  #connect to cluster api
all_volumes = cluster.get_all_volumes(vserver)                         #get all the volumes for vserver
volumes_with_tracking_quotas = cluster.get_volumes_with_tracking_quota(vserver) #get all the volumes with tracking quota for vserver

all_volumes_list = sorted(set(all_volumes)) #sort all the volumes 
volumes_with_tracking_quotas_list = sorted(set(volumes_with_tracking_quotas)) #sort the volumes with tracking quotas 

volumes_without_tracking_quotas = list(set(all_volumes_list) - set(volumes_with_tracking_quotas_list)) #compare the two lists

for volume in volumes_without_tracking_quotas:
   cluster.set_quota(vserver,'-','-','true',volume,'','user','*','-','-','-')
   time.sleep(5)
   cluster.quota_off(vserver, volume)
   time.sleep(5)
   cluster.quota_on(vserver, volume)

#null_value = '\\"\\"' #null value important to pass the cluster for both space and file limits (or lack thereof) to enable tracking quotas
#
#"""for loop to display the vols without tracking quotas, and enable tracking quotas on said volumes
#"""
#for volume_without_tracking_quota in volumes_without_tracking_quotas:
#   logger.info( "Enabling tracking quota on {0}".format(volume_without_tracking_quota)) 
#   set_tracking_quota_command = 'ssh admin@{0} "quota policy rule create -vserver {1} -policy-name default -volume {2} -type user -target {3} -qtree {3} -user-mapping off; quota off -vserver {1} -volume {2} -foreground; quota on -vserver {1} -volume {2} -foreground"' 
#   popen_call = subprocess.Popen(set_tracking_quota_command.format(local_cluster,local_vserver,volume_without_tracking_quota,null_value),stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
#   local_output,local_error = popen_call.communicate()
#   popen_call.wait()
#   logger.info("info: {0}".format(local_output))
#   logger.error("error: {0}".format(local_error))
#   time.sleep(2)
