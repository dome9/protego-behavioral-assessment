import sys
import pkg_resources
dependencies = open("requirements.txt").readlines()
try:
    pkg_resources.require(dependencies)
except Exception as e:
    sys.exit("missing requirements: {}".format(str(e)))

import urllib2
import json
import os
import sys
import argparse
import signal
import boto3
from multiprocessing.dummy import Pool as ThreadPool
import tqdm

# region defaults
PROFILE="default"
REGION="us-east-1"
ENDPOINT = None
STAGE="dev"
LIMIT = 1000
DEMO_STAGE = "conductor"
THREADS = 32
pbar = None
PROTEGO_PLUGIN_FOLDER = "node_modules/serverless-protego-plugin"
PROTEGO_CONF_FILE = "protego-config.json"
PAYLOAD = {'mode': 'whitelist', 'payloads': {'file': '/tmp/file.txt', 'host': 'https://www.protego.io', 'process': ['echo', 'this is a test']}}

DEMO_ATTACK_PAYLOAD = {'mode': 'attack', 'payloads': {
    'host': 'evil.com',
    'file': '/tmp/target',
    'cmd': ['cat', '/var/task/lambda_handler.py'],
    'code': 'import boto3\ns=boto3.client("s3")\nr=s.create_bucket(Bucket="protego_demo_free_bucket")\nprint(r)'
}}

ATTACK = {}
DEMO_ATTACK = False
# endregion


def deploy_attacker():
    os.system ("cd attacker; sls deploy --aws-profile {} --region {}".format(PROFILE, REGION))


def add_endpoint_to_attacker(endpoint):
    try:
        with open ("attacker/sls.template.yml") as f:
            content = f.read()
            f.close()
            content = content.replace("target_endpoint: XXXXX", "target_endpoint: {}".format(endpoint))
            content = content.replace("normal_payload: XXXXX", "normal_payload: '{}'".format(json.dumps(PAYLOAD)))
            s = open("attacker/serverless.yml", "w+")
            s.write((content))
            s.close()
    except:
        print ("could not add endoint to attacker")
        return False

    return True


# function to be mapped over
def calculateParallel():
    pool = ThreadPool(THREADS)
    global pbar
    pbar = tqdm.tqdm(total=LIMIT)
    #print ("PRESS CTRL+C to stop.")
    for _ in tqdm.tqdm(pool.imap_unordered(send_messages, range(LIMIT)), total=LIMIT):
        pass
    pool.close()
    pool.join()
    pbar.close()
    sys.exit("\n\nAll done.\nYour function should have a whitelist profile within a few minutes.\n"
        "After you see the profile in the bashboard, use this script to submit attack payloads (--attack or --demo).\n"
        "Run $ python run.py --help for more info.")


# whitelist creation through api gateway
def send_messages(i):
    req = urllib2.Request(url=ENDPOINT, data=json.dumps(PAYLOAD))
    try:
        urllib2.urlopen(req)
    except:
        pass


# sending attack payloads
def send_attack_payload(attack_payload):
    try:
        payload = json.dumps(attack_payload)
        print(payload)
        req = urllib2.Request(url=ENDPOINT, data=payload)
        urllib2.urlopen(req)
    except Exception as e:
        print("[ERROR] {}".format(str(e)))


def signal_handler(sig, frame):
    print ("\n")
    print('You pressed Ctrl+C! , exiting')
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


######################## Main ########################
def main():

    # region globals
    global ENDPOINT
    global LIMIT
    global THREADS
    global PROFILE
    global REGION
    global STAGE
    global PAYLOAD
    global ATTACK
    global DEMO_ATTACK
    global DEMO_ATTACK_PAYLOAD
    # endregion

    # region Args
    parser = argparse.ArgumentParser(
        description="deploy stages ."
    )
    parser.add_argument("-p", "--profile", required=False, default=PROFILE ,help="your aws profile. ")
    parser.add_argument("-r", "--region", required=False, default=REGION, help="your aws region (default: {})".format(REGION))
    parser.add_argument("-s", "--stage", required=False, default=STAGE, help="api gateway stage, from serverless.yml (default: {})".format(STAGE))
    parser.add_argument("-e", "--endpoint", required=False, default=ENDPOINT,  help="function's endpoint. Automatic if --profile (-p) used")
    parser.add_argument("-t", "--threads", required=False, default=THREADS,  help="number of parallel threads (defualt: {})".format(THREADS))
    parser.add_argument("-l", "--limit", required=False, default=LIMIT, help="how many requests the send (default: {})".format(LIMIT))
    parser.add_argument("-i", "--input", required=False, default=PAYLOAD, help="payload to create whitelist. Default is: {}".format(json.dumps(PAYLOAD)))
    parser.add_argument("-x", "--attack", required=False, default=ATTACK, help="send the received attack payload (use only after whitelist was created)")
    parser.add_argument("-d", "--demo", required=False, default=DEMO_ATTACK, action="store_true", help="(after whitelist) runs demo attack: {}".format(json.dumps(DEMO_ATTACK_PAYLOAD)))

    args = parser.parse_args()

    ENDPOINT = args.endpoint
    LIMIT = int(args.limit)
    THREADS = int(args.threads)
    PROFILE = args.profile
    REGION = args.region
    STAGE = args.stage
    PAYLOAD = args.input
    ATTACK = args.attack
    DEMO_ATTACK = args.demo
    # endregion

    # get AWS Profile
    if PROFILE == "default":
        try:
            prof = os.environ["AWS_PROFILE"]
            PROFILE = prof
        except KeyError:
            PROFILE = "default"

    if PROFILE == "default":
        print("No AWS profile was provided. Trying 'default'. To set a profile, run script with --profile (-p).")

    # check if protgeo serverless plugin is installed
    if os.path.isdir(PROTEGO_PLUGIN_FOLDER):
        pass
    else:
        os.system('npm install -D https://artifactory.app.protego.io/protego-serverless-plugin.tgz')

    # check if Protego config file exists OR token in serverless.yml
    if os.path.exists(PROTEGO_CONF_FILE):
        pass
    else:
        sys.exit("Protego credentials could not be found. "
                 "Please, download `{}` from the integration page in Protego dashboard. "
                 "Then, run again.".format(PROTEGO_CONF_FILE))

    # check if function is deployed. If not, deploys function
    if os.path.isdir(".serverless"):
        pass
    else:
        os.system ("sls deploy --aws-profile {} --region {}".format(PROFILE, REGION))

    # get function endpoint
    if ENDPOINT is None:
        session = boto3.Session(profile_name=PROFILE, region_name=REGION)
        client = session.client('apigateway')
        res = client.get_rest_apis()
        for api in res["items"]:
            if api["name"].find("protego-behavioral") > -1:
                ENDPOINT = "https://{}.execute-api.{}.amazonaws.com/{}/test-protego".format(api["id"], REGION, STAGE)
                ep_added = add_endpoint_to_attacker(ENDPOINT)
        if ENDPOINT is None or not ep_added:
            sys.exit("could not find the function's endpoint (did you delete the function?). "
                     "Please run script with the --endpoint (-e) option.")
    else:
        ep_added = add_endpoint_to_attacker(ENDPOINT)
        if not ep_added:
            print "could not add endpoint to attacker/serverless.yml. Please, add it manually"

    if ep_added:
        deploy_attacker()

    # WHITELIST or ATTACK MODE
    if len(ATTACK) == 0 and not DEMO_ATTACK:
        print "Starting behavioural profiling on: {}".format(str(ENDPOINT))
        calculateParallel()
    else:
        if DEMO_ATTACK:
            print "Sending attack demo..."
            send_attack_payload(DEMO_ATTACK_PAYLOAD)
        else:
            attack_payload = json.loads(ATTACK)
            send_attack_payload(attack_payload)


def print_headline(msg):
    delim = "*"
    print(delim * 100)
    print(delim)
    print(delim + "\t\t " + msg)
    print(delim)
    print(delim * 100)


if __name__ == "__main__":
    main()