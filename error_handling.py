import sys
import os
import subprocess

def check_string(variable):
   if not (isinstance(variable, basestring)):
      print ("{0} should be a string".format(variable))
      sys.exit(os.EX_CONFIG)

def check_int(variable):
   if not isinstance(variable, int) and variable != '-':
      print ("{0} should be a number".format(variable))
      sys.exit(os.EX_CONFIG)

def check_true_or_false(variable):
   if (variable is not 'true') and (variable is not 'false'):
      print ("{0} needs to be true or false".format(variable))
      sys.exit(os.EX_CONFIG)

def get_yp_users():
   ypcat_passwd_cmd ="ypcat passwd"
   ypcat_call = subprocess.Popen(ypcat_passwd_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell = True)
   ypcat_output, ypcat_error= ypcat_call.communicate()
     
   userids_list = [] 

   ypcat_output = ypcat_output.strip()
   for user_entry in (ypcat_output.split("\n")):   
      userids,foo,uids,gids,real_names,homedirs,shells = user_entry.split(":")
      userids_list.append(userids)

   return userids_list

def check_userid(variable):
   if not (variable in get_yp_users()) and (variable != '-'):
      return ('False')
   else:
      return ('True')

