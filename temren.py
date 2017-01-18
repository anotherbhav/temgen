#!/usr/local/bin/python3

'''
temren - Network Template Renderer - A CLI network [tem]plate [ren]derer takes variables (from a JSON), a template (from a JINJA2) and renders the result
'''

import argparse
import jinja2
import json
import os
import ipaddress
import logging
import sys
import yaml
import dns.resolver
## //TODO
# - [ ] complete the --update argument, so that the hosts.json can get updated
# - [ ] list all available variables that need to be entered? or at least checked




p = argparse.ArgumentParser( description='A Config Generator that renders jinja2 temlates using variables from JSON Configuration Files', epilog="Examples found on GitHub")
p.add_argument('--config', help='Specify a JSON Configuration file, you usually start here')
p.add_argument('--output', help='Specify an output file for the rendered templates')
p.add_argument('--template', help='add a jinja2 template to the display \'stack\'')
p.add_argument('--verbose', help="print verbose/debug output", action="store_true")
p.add_argument('--debug', help="print verbose/debug output", action="store_true")
p.add_argument('--list', help="lists available templates and configs", action="store_true")
p.add_argument('--noresolve', help="do not resolve {resolve} entries", action="store_true")

variables = {}
template_queue = []
config_queue = []
dictionary = {}
config_vars = {}

flags = ['cidr_ips_flag', 'resolve_flag', 'netmask_ips_flag']


# search locations
home_dir = os.path.join(os.path.expanduser("~"),'temren')
script_dir = os.path.dirname(os.path.realpath(__file__))
cwd_dir =os.getcwd()

def __init__(self):
    self.dictionary = {}

# returns a list of files in a set of directories with a given extension
def get_file_list(fname='', search_dirs = [], file_extension='nothing'):
    logging.debug('entering function: ' +'get_file_list')
    logging.debug("Going to search the following locations:" +str(search_dirs))
    logging.debug("Going to search the following extension:" +file_extension)

    # add period for file extnsion if it does not exist
    if (len(file_extension) > 0) and (file_extension[0] != '.'):
        file_extension = '.'+file_extension

    # remove duplicates
    search_dirs = list(set(search_dirs))

    flist = []
    for d in search_dirs:
        logging.debug("searching directory" +d)
        try:
            for f in os.listdir(d):
                if f.endswith(file_extension):
                    flist.append(f)
                    logging.debug("found file:" +os.path.join(d,f))
        except FileNotFoundError:
            logging.info("Directory not found: " +d)

    return flist


# locate a file based on search directories and file extension
# locates FIRST instance of file located
# search file by arguments (search_dirs) first, followed by file name, , followed by cwd
def locate_file(fname, search_dirs = [], file_extension=''):
    logging.debug('entering function: ' +'locate_file')

    # add period for file extnsion if it does not exist
    if (len(file_extension) > 0) and (file_extension[0] != '.'):
        file_extension = '.'+file_extension

    fpath = False

    search_paths =[]
    for d in search_dirs:
        search_paths.append(os.path.join(d, fname))
    search_paths.append(fname)

    # load the local directory as an initial search path
    search_paths.append(os.path.join(os.getcwd(), fname))

    logging.debug("going to search the following file locations for a file: " +str(search_paths))

    # search for with and without the extension
    for f in search_paths:
        if os.path.isfile(f):
            fpath = f
            break
        elif os.path.isfile(f+file_extension):
            fpath = f+file_extension
            break

    if not fpath:
        logging.warning('could not find file in any location: ' +fname)
        return

    return fpath


## Parse Aruments from CLI
def parse_cli_arguments(argument_parser):
    args = argument_parser.parse_args()

    if args.verbose or args.debug:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
        logging.debug("Setting Logging to DEBUG")
    else:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.WARN)

    # this line can only be run after logging level has been established
    logging.debug('entering function: ' +'parse_cli_arguments')

    if len(sys.argv) <= 1:
        argument_parser.print_help()
        exit(1)

    if args.list:
        home = os.path.expanduser("~")
        sub_dir = 'configs'

        flist = get_file_list(search_dirs=[os.path.join(script_dir,sub_dir), os.path.join(cwd_dir,sub_dir), os.path.join(home_dir,sub_dir)],file_extension='yaml')
        print("\n# Configurations (yaml)")
        if len(flist) <= 0:
            print("- No Configurations Found")
        for f in flist:
            basefname, ext = os.path.splitext(f)
            # print("- " +basefname)
            print("- " +f)

        flist = get_file_list(search_dirs=[os.path.join(script_dir,sub_dir), os.path.join(cwd_dir,sub_dir), os.path.join(home_dir,sub_dir)],file_extension='json')
        print("\n# Configurations (json)")
        if len(flist) <= 0:
            print("- No Configurations Found")
        for f in flist:
            basefname, ext = os.path.splitext(f)
            # print("- " +basefname)
            print("- " +f)

        sub_dir = 'templates'
        flist = get_file_list(search_dirs=[os.path.join(script_dir,sub_dir), os.path.join(cwd_dir,sub_dir), os.path.join(home_dir,sub_dir)],file_extension='jinja2')
        print("\n# Templates")
        if len(flist) <= 0:
            print("- None Found")
        for f in flist:
            basefname, ext = os.path.splitext(f)
            # print("- " +basefname)
            print("- " +f)

    if args.template:
        logging.debug("attempting to locate template file from CLI args: " +args.template)
        append_to_templates(template_file_names=args.template)

    if args.noresolve:
        logging.debug("noresolve flag has been triggered")
        set_flag(flag_name='resolve_flag', flag_value=False)

    if args.config:
        logging.debug("the config flag has been triggered")
        template_vars_new = load_variables_from_json(json_file_names=args.config)

    return True


# locates a file and appends the path it to the template stack to be processed
def append_to_templates(template_file_names=[]):
    logging.debug('entering function: ' +'append_to_templates')

    for f in template_file_names:
        logging.debug("locate this template: " +f)

        sub_dir = 'templates'
        fpath = locate_file(fname=f, search_dirs=[os.path.join(script_dir,sub_dir), os.path.join(cwd_dir,sub_dir), os.path.join(home_dir,sub_dir)], file_extension='jinja2')
        if fpath:
            logging.info("add template to queue: " +f)
            template_queue.append(fpath)


# add a cidr mask
# returns the same value if its not an IP address
def add_cidr(value=False):
    logging.debug('entering function: ' +'add_cidr')
    if type(value) != str:
        return value

    # test to see if this is an actual IP address
    try:
        ipaddr = ipaddress.ip_network(value)
        logging.debug("value is an IP address, adding cidr mask. Before: " +value +" | After: " +str(ipaddr))
        value = str(ipaddr)
    except ValueError:
        True

    return value


def add_netmask(value=False):
    logging.debug('entering function: ' +'add_netmask')
    if type(value) != str:
        return value

    # test to see if this is an actual IP address
    try:
        ipaddr = ipaddress.ip_network(value)
        logging.debug("value is an IP address, adding cidr mask. Before: " +value +" | After: " +str(ipaddr))
        value = (str(ipaddr.network_address) +' ' +str(ipaddr.netmask))
    except ValueError:
        True

    return value


def set_flag(flag_name='', flag_value=False):
    # logging.debug('entering function: ' +'set_flag')
    if not flag_name:
        return False
    logging.debug('set flag: ' +flag_name +' to: ' +str(flag_value))
    variables[flag_name] = flag_value


def get_flag(flag_name=''):
    # logging.debug('entering function: ' +'get_flag' ", flag_name=" +flag_name)
    if not flag_name:
        return False

    flag_value=False

    # the resolve flag should return 'True if it has no value
    if flag_name in variables:
        flag_value = variables[flag_name]
    elif(flag_name == 'resolve_flag'):
        # resolve flag should return true if it is not set
        flag_value = True
    return flag_value


def resolve_entry(key=None):
    logging.debug('entering function: ' +'resolve_entry' +', key: ' +key)
    if not key:
        return False

    global dictionary

    val = False
    if len(dictionary) <= 0:
        try:
            sub_dir = 'configs'
            fpath = locate_file(fname='resolve_dictionary', search_dirs=[os.path.join(script_dir,sub_dir), os.path.join(cwd_dir,sub_dir), os.path.join(home_dir,sub_dir)], file_extension='yaml')

            if not fpath:
                return False

            basefname, ext = os.path.splitext(fpath)
            if ext == '.yaml':
                with open(fpath) as data_file:
                    dictionary = yaml.load(data_file)
            elif ext == '.json':
                with open(fpath) as data_file:
                    dictionary = json.load(data_file)

            # with open(fpath) as data_file:
            #     dictionary = json.load(data_file)
        except FileNotFoundError:
            logging.warn("dictionary (resolve entry) file not found:" +hosts_file_path)
            return False
    if key in dictionary:
        logging.debug("value found in dictionary file")
        val = dictionary[key]
        return val
    # else:
    #     val = False


    # No entr was found
    import dns.resolver

    r = dns.resolver.Resolver()
    answer = r.query('google.com')
    print(answer[0])
    - lookup google.com

    r.nameservers = ['8.8.8.8']


    ## DNS lookup


    return val




# Method for processing JSON variables
# - this is where the flags are matched and possibly processed come into play
def process_variables(variable_dict={}, cidr_ips=False):
    logging.debug('entering function: ' +'process_variables')

    logging.debug("variable count prior: " +str(len(variable_dict)))

    template_vars = {}

    logging.debug("iterate through variables")
    for key,val in variable_dict.items():

        # found a json array, so you need to iterate through the list and do more
        processed_var = []
        logging.debug("variable key: " +key +" | type: " +str(type(val)))

        if type(val) is str:
            logging.debug("  str")
            processed_var = val
            if get_flag('cidr_ips_flag'):
                processed_var = add_cidr(processed_var)
            elif get_flag('netmask_ips_flag'):
                processed_var = add_netmask(processed_var)

        elif type(val) is list:
            # process further, it could be an array of str or more dict items
            for i in val:
                process_val_flag = True
                logging.debug("  val: " +str(i))

                if type(i) is str:
                    process_val = True
                elif ('value') in i:
                    logging.debug("    value, take value as-is: " +str(i['value']))
                    i = i['value']
                    process_val_flag = False
                elif ('resolve') in i:
                    # this resolves some value
                    to_resolve = i['resolve']
                    logging.debug("    resolve entry, need to lookup: " +to_resolve)
                    if get_flag('resolve_flag'):
                        h = resolve_entry(key=to_resolve)
                        if h:
                            i = h
                        else:
                            logging.warn("no host entry found for: " +to_resolve +" leaving it as static value")
                            i = to_resolve
                    else:
                        logging.debug("    resolve_flag is false, do not lookup")
                        i = to_resolve


                elif ('to_dict') in i:
                    # this resolves some value and enters the value into a key-val dictionary
                    # it honours resolve_flag
                    to_dict = i['to_dict']
                    logging.debug("    to_dict entry, need to lookup: " +to_dict)
                    if get_flag('resolve_flag'):
                        h = resolve_entry(key=to_dict)
                        if h:
                            i = h
                        else:
                            logging.warn("no host entry found for: " +to_dict +" leaving it as static value")
                            i = to_dict
                    else:
                        logging.debug("    resolve_flag is false, do not lookup")
                        i = to_dict

                    ## Process Variables in some way
                    if process_val_flag:
                        if get_flag('cidr_ips_flag'):
                            i = add_cidr(i)
                        elif get_flag('netmask_ips_flag'):
                            i = add_netmask(i)

                    process_val_flag = False
                    i = { to_dict : i }



                ## Process Variables in some way
                if process_val_flag:
                    if get_flag('cidr_ips_flag'):
                        i = add_cidr(i)
                    elif get_flag('netmask_ips_flag'):
                        i = add_netmask(i)

                processed_var.append(i)
        else:
            logging.debug("unsupported type, forwarding the value on")
            processed_var = val

        template_vars[key] = processed_var

    variable_dict = template_vars
    logging.debug("variable count post: " +str(len(variable_dict)))
    return variable_dict





# loads template variables from json file into the global dictionary 'variables'
# - 'host' entries will be translated to IP addresses
# - a string or json list can be passed in json_file_names
def load_variables_from_json(site='', json_file_names=False, cidr_ips=False):
    logging.debug('entering function: ' +'load_variables_from_json')

    if type(json_file_names) == str:
        logging.debug("single config file")
        json_file_names = [json_file_names]

    logging.debug("json_file_names: " +str(json_file_names))

    for f in json_file_names:
        logging.debug("attemping to locate config file: " +f)
        sub_dir = 'configs'
        fpath = locate_file(fname=f, search_dirs=[os.path.join(script_dir,sub_dir), os.path.join(cwd_dir,sub_dir), os.path.join(home_dir,sub_dir)], file_extension='yaml')

        if not fpath:
            logging.warning('could not find config file: ' +f)
            return False

        logging.debug("found config file at location: " +fpath)

        try:

            basefname, ext = os.path.splitext(fpath)
            logging.debug("load variables from " +ext +" file: " +fpath)

            new_variables = []
            if ext == '.yaml':
                with open(fpath) as data_file:
                    new_variables = yaml.load(data_file)
            elif ext == '.json':
                with open(fpath) as data_file:
                    new_variables = json.load(data_file)

            logging.info("loading variables from: " +f)

            # in case these are not set, search for if they should be set

            for flag in flags:
                if (flag not in variables) and (flag in new_variables) :
                    set_flag(flag_name=flag, flag_value=new_variables[flag])
                    logging.debug("setting flag: " +flag +" to: " +str(new_variables[flag]))

            new_variables = process_variables(variable_dict=new_variables,cidr_ips=cidr_ips)
            logging.debug(new_variables)
            logging.debug("existing variables: " +str(len(variables)) +" | new variables: " +str(len(new_variables)))
            variables.update(new_variables)
            logging.debug("merged count: " +str(len(variables)))





            # add the config to a config stack to show where variables were loaded from
            config_queue.append(fpath)
            try:
                append_to_templates(new_variables['templates'])
            except KeyError:
                False

        except ValueError:
            logging.warn("could not load JSON file.. possible issue with the file or it does not exist")
            return {}


        # this try block will only succeed if there is a nested config
        try:
            nested_config_file = new_variables['configurations']
            logging.debug("found nested config: ")

            nested_cidr_ips = False
            nested_resolve_hosts = False
            if type(nested_config_file) == str:
                # in case these are not set, search for if they should be set
                try:
                    nested_cidr_ips = new_variables['cidr_ips']
                    logging.debug("setting cidr_ips to " +str(cidr_ips))
                except KeyError:
                    True

            secondary_variables = load_variables_from_json(json_file_names=nested_config_file, cidr_ips=nested_cidr_ips)

        except KeyError:
            False

    return variables


# renders the template
def render_template_new(template_path):
    logging.debug('entering function: ' +'render_template_new')

    # jinja2 needs template directory and file separately
    # if we give jinja2 the full path in searchpath, it fails
    template_dir, template_fname  = os.path.split(template_path)

    ## Prep jinja2
    template_loader = jinja2.FileSystemLoader(searchpath=template_dir )
    template_env = jinja2.Environment( loader=template_loader, extensions=["jinja2.ext.do",])

    try:
        j2_template = template_env.get_template( template_fname )
    except jinja2.exceptions.TemplateNotFound:
        logging.critical("could not find the following jinja2 template: " +template_path)
        return

    # render the template and return results
    return j2_template.render( variables )


def output_to_file(file_name=False, file_content=False):
    logging.debug('entering function: ' +'output_to_file, file_name=' +file_name)

    if not file_name or not file_content:
        logging.warn("no file name or no file_content")
        return False

    fpath = os.path.join(os.getcwd(), file_name)
    logging.debug("file path: " +fpath)

    with open(fpath, 'w') as outfile:
        outfile.write(file_content)
        return True

    return False



def load_config_vars(fpath=False):
    logging.debug('entering function: ' +'load_config_vars, fpath=' +fpath)

    try:
        with open(fpath) as data_file:
            config_vars = yaml.load(data_file)
            return config_vars
    except FileNotFoundError:
            logging.info("dictionary (resolve entry) file not found:" +fpath)

    return {}

# --- Script Starts Here ---

# parse inputs from CLI
config_vars = load_config_vars(fpath = os.path.join(home_dir, "config.yaml"))
sys.exit(1)
parse_cli_arguments(argument_parser=p)


print("\n\n")


if len(template_queue) <= 0:
    logging.debug("no templates to render")
    exit(0)


print("--- Pre Render Info ---")
print("loading " +str(len(variables)) +" variables into " +str(len(template_queue)) +" templates\n")

print("# Variables Loaded From")
for t in config_queue:
    fdir, fname  = os.path.split(t)
    print("- " +fname)
    logging.debug("full path: " +t)

print("\n")
print("# Template Order")
for t in template_queue:
    fdir, fname  = os.path.split(t)
    print("- " +fname)
    logging.debug("full path: " +t)

print("\n\n")



print("--- Template Output ---")
output = ""
for t in template_queue:
    output += render_template_new(template_path=t)
    output += "\n"


# Output to a file if its a valid argument
args = p.parse_args()
if args.output:
    fname = args.output
    err_code = output_to_file(file_name=args.output, file_content=output)
    if err_code:
        print("Output File: " +fname)
    else:
        print("there was an error in writing the file to" +fname)
else:
    print(output)
