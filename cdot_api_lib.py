#!/router/bin/python

import NetApp
from NetApp.NaServer import *   #Need this to do NetApp API magic 
import os                     #Need this to get stuff from my shell 
import base64                 #Mind your own business 
import error_handling         #Stupid error_handling method I need to re-write
import logging                #for logging

__author__ = 'Geoff Sutton <gesutton@cisco.com>'

app_dir = '/auto/smt/bin/cdot_api_lib2'

#configure some logging
#TODO: Configure logging outside of code. 
logfile = '{0}/logs/cdot_api.log'.format(app_dir)              
logging.basicConfig(filename=logfile, 
                    level=logging.DEBUG,
                    format='%(asctime)s %(message)s'
                    )

#get creds from shell 
auth1 = os.environ.get('NTAP_ADMIN')
auth2 = base64.b64decode(auth1)




class cdot_cluster_mgmt(object):
   """declare the 'object', this is establishes a connection to a cluster's rest API, it needs to be passed a cluster managemnt IP/host
   imput: cluster name
   dependancies: linux,
                 python 2.6 
                 error_handling.py
                 NetApp API python library
                 a directory called logs
                 base64 encoded password for api user stored as a shell variable NTAP_ADMIN"""
   
   
   def __init__(self, cluster):
      self.cluster = cluster 
      self.server = NaServer(cluster, 1, 31)
      self.server.set_server_type("FILER")
      if (cluster == "sjc5-netapp-tst"):
         self.server.set_transport_type("HTTP")
         self.server.set_port("80")
         self.server.set_style("LOGIN")
         self.server.set_admin_user("admin", "cisco123")
      else:
         self.server.set_transport_type("HTTPS")
         self.server.set_port("443")
         self.server.set_style("LOGIN")
         self.server.set_admin_user("admin", auth2)
   

   def get_all_volumes(self, vserver): 
      """get volumes for a given namespace
      input: namespace/SVM/vserver
      output: list of volumes"""

      api = NaElement("volume-get-iter")

      xi = NaElement("desired-attributes")
      api.child_add(xi)

      xi1 = NaElement("volume-attributes")
      xi.child_add(xi1)

      xi2 = NaElement("volume-id-attributes")
      xi1.child_add(xi2)

      xi2.child_add_string("name","<name>")
      xi2.child_add_string("owning-vserver-name","<owning-vserver-name>")
      api.child_add_string("max-records","100000")

      xi3 = NaElement("query")
      api.child_add(xi3)

      xi4 = NaElement("volume-attributes")
      xi3.child_add(xi4)

      xi5 = NaElement("volume-id-attributes")
      xi4.child_add(xi5)

      xi5.child_add_string("owning-vserver-name",vserver)
      
      volumes = self.server.invoke_elem(api)

      if (volumes.results_status() == 'failed'):
         logging.error(volumes.sprintf())
         sys.exit (1)

      out_list = []

      output = volumes.child_get("attributes-list")
      output_nl1_children = output.children_get()

      for output_nl1_child in output_nl1_children:
         output_nl2_children = output_nl1_child.child_get("volume-id-attributes")
         volume_name=output_nl2_children.child_get_string("name")
         out_list.append (volume_name)

      return (out_list)

   def get_volumes_with_tracking_quota(self, vserver): 
      """get all the volumes with 'tracking quotas' enabled
         input: namespace/SVM/vserver
         output: list of volumes with "tracking quotas" """

      api = NaElement("quota-list-entries-iter")
      
      xi = NaElement("desired-attributes")
      api.child_add(xi)


      xi1 = NaElement("quota-entry")
      xi.child_add(xi1)

      xi1.child_add_string("volume","<volume>")
      api.child_add_string("max-records","10000")

      xi2 = NaElement("query")
      api.child_add(xi2)


      xi3 = NaElement("quota-entry")
      xi2.child_add(xi3)

      xi3.child_add_string("quota-target","*")
      xi3.child_add_string("quota-type","user")
      xi3.child_add_string("vserver",vserver)
      
      volumes_with_tracking_quotas = self.server.invoke_elem(api)

      if (volumes_with_tracking_quotas.results_status() == "failed"):
         logging.error(volumes_with_tracking_quotas.sprintf())
         sys.exit(1)

      out_list = []

      output = volumes_with_tracking_quotas.child_get("attributes-list")
      output_nl1_children = output.children_get()

      for output_nl1_child in output_nl1_children:
         volume_name = output_nl1_child.child_get_string("volume")
         out_list.append (volume_name)

      return (out_list)
   
   def set_quota(self, vserver, disk_limit, file_limit, perform_user_mapping, volume, qtree, quota_type, quota_target, soft_disk_limit, soft_file_limit, threshold):
      """sets quota in default quota policy 
      input: vserver name, 
      space limit(can be set to null with hyphen), 
      inode limit(can be set to null with hyphen), 
      if you want AD/Unix usermapping (true/false)
      volume name,
      qtree name (can be * if no qtree)
      quota type(user/qtree)
      quota target(user/qtree name)
      soft_disk_limit(warning email sent to user when this much disk is used, hyphen for null)
      soft_file_limit(warning email sent to user when this many inodes are used, hyphen for null) 
      threshold (can be set to hyphen)
      output: if failed, will return failure from ontapi/if succedded, will return that set quota successeded
      TODO: need to turn the strange error handling into exeptions"""

      self.server.set_vserver(vserver)
      policy = 'default'
     
      self.check_for_vserver(vserver)
      logging.debug("vserver: {0}".format(vserver))

      error_handling.check_string(disk_limit) 
      logging.debug("disk-limit: {0}".format(disk_limit))

      error_handling.check_string(file_limit)
      logging.debug("file-limit: {0}".format(file_limit))
     
      error_handling.check_true_or_false(perform_user_mapping)
      logging.debug("perform-user-mapping: {0}".format(perform_user_mapping))
     
      self.check_volume(volume, vserver)
      logging.debug("volume: {0}".format(volume))

      self.check_qtrees_for_volume(volume, qtree)
      logging.debug("qtree: {0}".format(qtree))
      
      logging.debug("quota-type: {0}".format(quota_type))
      
      if (quota_type is 'user'):
         error_handling.check_userid(quota_target) 
         logging.debug("quota-target: {0}".format(quota_target))
      elif (quota_type is 'qtree'):
         self.check_qtrees_for_volume(volume, qtree)
         logging.debug("quota-target: {0}".format(quota_target))
     
      logging.debug("policy: {0}".format(policy))
      
      error_handling.check_string(soft_disk_limit)
      logging.debug("soft-disk-limit: {0}".format(soft_disk_limit))

      error_handling.check_string(soft_file_limit)
      logging.debug("soft-file-limit: {0}.".format(soft_file_limit))

      error_handling.check_string(threshold)
      logging.debug("threshold: {0}".format(threshold))

      api = NaElement("quota-add-entry")
      api.child_add_string("disk-limit", disk_limit)
      api.child_add_string("file-limit", file_limit)
      api.child_add_string("perform-user-mapping", perform_user_mapping)
      api.child_add_string("policy","default")
      api.child_add_string("qtree", qtree)
      api.child_add_string("quota-target", quota_target)  
      api.child_add_string("quota-type", quota_type)
      api.child_add_string("soft-disk-limit", soft_disk_limit) 
      api.child_add_string("soft-file-limit", soft_file_limit)
      api.child_add_string("threshold", threshold)
      api.child_add_string("volume", volume) 

      invoke_set_quota = self.server.invoke_elem(api)

      if (invoke_set_quota.results_status() == "failed"):
         #print ("Error:\n")
         logging.warning(invoke_set_quota.sprintf())
         #sys.exit(1)
      else:
         logging.info("Quota for {0} applied successfully".format(volume))

   def check_for_vserver(self, vserver):
      """checks for vserver against list of vservers
      input: vserver/SVM 
      output: true/false"""

      vserver_list = self.get_vservers() 

   def get_vservers(self):
      """produces a list of vservers/SVMs for a given cluster
      output: list of vservers"""

      api = NaElement("vserver-get-iter")

      xi = NaElement("desired-attributes")
      api.child_add(xi)

      xi1 = NaElement("vserver-info")
      xi.child_add(xi1)

      xi1.child_add_string("vserver-name","<vserver-name>")
      api.child_add_string("max-records","10")

      xi2 = NaElement("query")
      api.child_add(xi2)

      xi3 = NaElement("vserver-info")
      xi2.child_add(xi3)

      xi3.child_add_string("state","running")

      vservers = self.server.invoke_elem(api)
      if (vservers.results_status() == "failed") :
         print ("Error:\n")
         logging.error(vservers.sprintf())
         sys.exit (1)

      out_list = []

      output = vservers.child_get("attributes-list")
      output_nl1_children = output.children_get()

      for output_nl1_child in output_nl1_children:
         vserver_name = output_nl1_child.child_get_string("vserver-name")
         out_list.append (vserver_name)

      return (out_list)

   def check_volume(self, volume, vserver):
      """checks if volume exists on vserver/VSM
      input: volume name,vserver/SVM   
      output: volume doesn't exist on vserver if failure"""

      volume_list = self.get_all_volumes(vserver)
      if not (volume in volume_list):
         logging.error("{0} doesn't exist on vserver:{1}".format(volume,vserver))
         sys.exit(os.EX_CONFIG)

   def get_qtrees_for_volume(self, volume):
      """gets list of qtrees for a given volume
      input: volume name 
      output: list of volumes"""

      api = NaElement("qtree-list-iter")

      xi = NaElement("desired-attributes")
      api.child_add(xi)

      xi1 = NaElement("qtree-info")
      xi.child_add(xi1)
      
      xi1.child_add_string("qtree","<qtree>")
      api.child_add_string("max-records","1024")

      xi2 = NaElement("query")
      api.child_add(xi2)

      xi3 = NaElement("qtree-info")
      xi2.child_add(xi3)

      xi3.child_add_string("volume",volume)

      qtrees = self.server.invoke_elem(api)

      output = qtrees.child_get("num-records")
      
      if (qtrees.results_status() == "failed") or (qtrees.child_get_int('num-records') == 0):
         logging.error(qtrees.sprintf())
      else:
         out_list = []
         output = qtrees.child_get("attributes-list")
         output_nl1_children = output.children_get()

         for output_nl1_child in output_nl1_children:
            qtree_name = output_nl1_child.child_get_string("qtree")
            out_list.append (qtree_name)

         return (out_list)

   def check_qtrees_for_volume(self, volume, qtree):
      """checks for a qtree with in a volume
      input: volume name
             qtree to check for
      output: <qtree_name> doesn't exist in volume <vol_name> (if failure)""" 

      qtree_list = self.get_qtrees_for_volume(volume)
      if qtree_list is None:
         logging.debug("No qtrees for volume {0}".format(volume))
      else:
         if not (qtree in qtree_list) and (qtree != '-'):
            logging.error("{0} doesn't exist in volume {1}".format(qtree,volume))
            sys.exit(os.EX_CONFIG)

   def quota_off(self, vserver, volume):
      """turns quotas off for a given volume
      input: vserver/SVM name 
             volume name
      output: if error: logs output from ontapi 
              if success: "Quota turned off for <volume_name>"""

      self.server.set_vserver(vserver) 
      
      api = NaElement("quota-off")
      api.child_add_string("volume",volume)

      quota_off = self.server.invoke_elem(api)
      if (quota_off.results_status() == "failed"):
         #print ("Error:\n")
         logging.error(quota_off.sprintf())
      else:
         logging.info("Quota turned off for {0}".format(volume))

   def quota_on(self, vserver, volume):
      """turns quotas on for a given volume
      input: vserver/SVM name
             volume name 
      output: if error: logs output from ontapi 
      if success: "Quota turned on for <volume_name>"""  

      self.server.set_vserver(vserver)

      api = NaElement("quota-on")
      api.child_add_string("volume",volume)

      quota_on = self.server.invoke_elem(api)
      if (quota_on.results_status() == "failed"):
         logging.error(quota_on.sprintf())
      else:
         logging.error("Quota turned on for {0}".format(volume))


   def get_quotas(self, cluster, vserver):
      
      api = NaElement("quota-list-entries-iter")
      
      xi = NaElement("desired-attributes")
      api.child_add(xi)

      xi1 = NaElement("quota-entry")
      xi.child_add(xi1)

      xi1.child_add_string("volume","<volume>")
      xi1.child_add_string("quota-target","<quota-target>")
      xi1.child_add_string("disk-limit","<disk-limit>")
      xi1.child_add_string("file-limit","<file-limit>")
      xi1.child_add_string("perform-user-mapping","<perform-user-mapping>")
      xi1.child_add_string("qtree","<qtree>")
      xi1.child_add_string("type","<type>")
      xi1.child_add_string("soft-disk-limit","<soft-disk-limit>")
      xi1.child_add_string("soft-file-limit","<soft-file-limit>")
      xi1.child_add_string("threshold","<threshold>")

      api.child_add_string("max-records","10000")

      xi2 = NaElement("query")
      api.child_add(xi2)

      xi3 = NaElement("quota-entry")
      xi2.child_add(xi3)
      
      if (field == "target"):
         xi3.child_add_string("quota-target",search)
      xi3.child_add_string("quota-type","user")
      xi3.child_add_string("vserver",vserver)
      
      volumes_with_malformed_quotas = self.server.invoke_elem(api)

      if (volumes_with_malformed_quotas.results_status() == "failed"):
         logging.error(volumes_with_malformed_quotas.sprintf())
         sys.exit(1)

      output = volumes_with_malformed_quotas.child_get("attributes-list")
      output_nl1_children = output.children_get()
      
      quotas= {}

      for output_nl1_child in output_nl1_children:
         volume_name = output_nl1_child.child_get_string("volume")
         quota_target = output_nl1_child.child_get_string("quota-target")
         disk_limit = output_nl1_child.child_get_string("disk-limit")
         file_limit = output_nl1_child.child_get_string("file-limit")
         user_mapping = output_nl1_child.child_get_string("perform-user-mapping")
         qtree = output_nl1_child.child_get_string("qtree")
         soft_disk_limit = output_nl1_child.child_get_string("soft-disk-limit")
         soft_file_limit = output_nl1_child.child_get_string("soft-file-limit")
         threshold = output_nl1_child.child_get_string("threshold") 

         quotas[volume_name] = [quota_target, disk_limit, file_limit, user_mapping, qtree, soft_disk_limit, soft_file_limit, threshold]

      return quotas


