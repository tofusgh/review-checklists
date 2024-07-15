#######################################
#
# Module to convert v1 checklist files
#   to v2.
#
#######################################

# Dependencies
import sys
import yaml
import json
import os


# Get the standard service name from the service dictionary
def get_standard_service_name(service_name, service_dictionary=None):
    svc_match_found = False
    if service_dictionary:
        for svc in service_dictionary:
            if service_name in svc['names']:
                svc_match_found = True
                return svc['service']
        if not svc_match_found:
            return service_name
    else:
        return service_name

# Function that returns a data structure with the objects in v1 format
def generate_v2(input_file, service_dictionary=None, labels=None, verbose=False):
    # Banner
    if verbose: print("DEBUG: Converting file", input_file)
    try:
        with open(input_file) as f:
            checklist = json.load(f)
        if 'items' in checklist:
            if verbose: print("DEBUG: {0} items found in JSON file {1}".format(len(checklist['items']), input_file))
            # Create a list of objects in v2 format
            v2recos = []
            for item in checklist['items']:
                # Create a dictionary with the v2 object
                v2reco = {}
                if 'guid' in item:
                    v2reco['guid'] = item['guid']
                if 'text' in item:
                    v2reco['text'] = item['text']
                if 'description' in item:
                    v2reco['description'] = item['description']
                v2reco['waf'] = item['waf']
                if item['severity'].lower() == 'high':
                    v2reco['severity'] = 0
                elif item['severity'].lower() == 'medium':
                    v2reco['severity'] = 1
                elif item['severity'].lower() == 'low':
                    v2reco['severity'] = 2
                v2reco['labels'] = []
                if 'category' in item:
                    v2reco['labels'].append({'area': item['category']})
                if 'subcategory' in item:
                    v2reco['labels'].append({'subarea': item['subcategory']})
                v2reco['queries'] = []
                if 'graph' in item:
                    v2reco['queries'].append({'arg': item['graph']})
                v2reco['links'] = []
                if 'link' in item:
                    v2reco['links'].append(item['link'])
                if 'source' in item:
                    if '.yaml' in item['source']:   # If it was imported from YAML it is coming from APRL
                        v2reco['labels'].append({'sourceType': 'aprl'})
                    v2reco['labels'].append({'source': item['source']})
                if 'service' in item:
                    v2reco['service'] = get_standard_service_name(item['service'], service_dictionary=service_dictionary)
                v2reco['resourceTypes'] = []
                if 'recommendationResourceType' in item:
                    v2reco['resourceTypes'].append(item['recommendationResourceType'])
                # If additional labels were specified as parameter, add them to the object
                if labels:
                    for label in labels:
                        v2reco['labels'].append(label)
                # Add to the list of v2 objects
                v2recos.append(v2reco)
            return v2recos
        else:
            print("ERROR: No items found in JSON file", input_file)
            return None
    except Exception as e:
        print("ERROR: Error when processing JSON file, nothing changed", input_file, ":", str(e))
        return None

# Function that stores an object generated by generate_v2 in files in the output folder
def store_v2(output_folder, checklist, output_format='yaml', verbose=False):
    if verbose: print("DEBUG: Storing v2 objects in folder", output_folder)
    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    # Store each object in a separate YAML file
    for item in checklist:
        # ToDo: create folder structure for the output files:
        #   output_folder/service/waf_pillar/recos.yaml
        if 'guid' in item:
            # Append service and WAF pillar to output folder if available
            this_output_folder = output_folder
            if 'service' in item:
                this_output_folder = os.path.join(output_folder, item['service'].replace(" ", ""))
                if 'waf' in item:
                    this_output_folder = os.path.join(this_output_folder, item['waf'].replace(" ", ""))
            # Create the output folder if it doesn't exist
            if not os.path.exists(this_output_folder):
                os.makedirs(this_output_folder)
            # Export JSON or YAML, depending on the output format
            if output_format in ['yaml', 'yml']:
                output_file = os.path.join(this_output_folder, item['guid'] + ".yaml")
                with open(output_file, 'w') as f:
                    yaml.dump(item, f)
                if verbose: print("DEBUG: Stored recommendation in", output_file)
            elif output_format == 'json':
                output_file = os.path.join(this_output_folder, item['guid'] + ".json")
                with open(output_file, 'w') as f:
                    json.dump(item, f)
                if verbose: print("DEBUG: Stored recommendation in", output_file)
            else:
                print("ERROR: Unsupported output format", output_format)
                sys.exit(1)
        else:
            print("ERROR: No GUID found in recommendation, skipping", item['text'])
            continue