# Protego Behavioral Testing

## Run: `$ python run.py`

Stages of script:
 * Install Protego serverless Plugin
 * download the protego-config.json which contains relevnat protego tokens (put that protego-config.json next to your serverless file) 
 * sls deploy (to deploy function with protego FSP)
 * get endpoint from aws
 * start sending requests to create the whitelist

Or, use the following options: 

```
optional arguments:
  -h, --help                         show this help message and exit
  -p PROFILE, --profile PROFILE      your aws profile.
  -r REGION, --region REGION         your aws region (default: us-east-1)
  -s STAGE, --stage STAGE            api gateway stage, from serverless.yml (default: dev)
  -e ENDPOINT, --endpoint ENDPOINT   function's endpoint. Automatic if --profile (-p) used
  -t THREADS, --threads THREADS      number of parallel threads (defualt: 32)
  -l LIMIT, --limit LIMIT            how many requests the send (default: 1000)
                        
  -i INPUT, --input INPUT            payload to create whitelist. Default is: 
  {"mode": "whitelist", "payloads": {"host": "https://www.protego.io", "process": ["echo", "/tmp/file.txt"], "file": "/tmp/file.txt"}}
                   
  -a ATTACK, --attack ATTACK         send attack payload
  -d, --demo                         runs demo attack:
  {'mode': 'attack', 'payloads': {'code': 'import boto3\ns=boto3.client("s3")\nr=s.create_bucket(Bucket=free_bucket)\nprint(r)', 'host': 'evil.com', 'cmd': ["curl", "fraud.com"], 'file': '/tmp/target'}}
  
  -y, --deploy-attacker              deploy attacker chronjob
```

## To simulate attack, run (after whitelist was created):
### `$ python run.py --attack '{"mode": "attack", "payloads": {_PAYLOAD_}}'`


Where `_PAYLOAD_` can be any or a combination of:
* host
* file
* [cmd, arg] (process)
* code (api)

or

### `$ python run.py --demo`
