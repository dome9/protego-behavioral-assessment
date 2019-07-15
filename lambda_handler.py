import os
import urllib2
import boto3
import subprocess
import json


def lambda_handler(event, context):
  skip = False
  try:
    body = json.loads(event["body"])
  except:
    skip = True
  response = {}

  # region attack mode
  if not skip and "mode" in body and body["mode"] == "attack":
    payloads = {}
    if "payloads" in body:
      payloads = body["payloads"]
      response["attacks"] = []

    # attack file
    if len(payloads) > 0 and "file" in payloads:
      response["attacks"].append("file")
      try:
        fname = payloads["file"]
        f = open(fname, 'w+')
        f.write('attack')
        f.close()
      except Exception as e:
        print "[WARN] {}".format(str(e))
        pass

    # attack host
    if len(payloads) > 0 and "host" in payloads:
      response["attacks"].append("host")
      try:
        url = payloads["host"]
        if not url.startswith("http"):
          url = "https://" + url
        urllib2.urlopen(url)
      except Exception as e:
        print "[WARN] {}".format(str(e))
        pass

    # attack process
    if len(payloads) > 0 and "cmd" in payloads:
      response["attacks"].append("process")
      try:
        cmd = payloads["cmd"]
        subprocess.call(cmd)
      except Exception as e:
        print "[WARN] {}".format(str(e))
        pass
    
    # attack api call
    if len(payloads) > 0 and "code" in payloads:
      response["attacks"].append("api")
      try:
        code = payloads["code"]
        exec(code)
      except Exception as e:
        print "[WARN] {}".format(str(e))
        pass
  # endregion

  # region create whitelist mode
  elif not skip and "mode" in body and body["mode"] == "whitelist":
    default_fname = "/tmp/test_file"
    default_url = "https://www.protego.io"
    default_proc = ["echo", "this is a test"]
    payloads = {}
    # argument initialization
    if "payloads" in body:
      payloads = body["payloads"]

    if len(payloads) > 0 and "file" in payloads:
      fname = payloads["file"]
    else:
      fname = default_fname

    if len(payloads) > 0 and "host" in payloads:
      url = payloads["host"]
      if not url.startswith("http"):
        url = "https://" + url
    else:
      url = default_url

    if len(payloads) > 0 and  "process" in payloads:
      process = payloads["process"]
    else:
      process = default_proc

    # whitelist file
    try:
      rf = {}
      f = open(fname, 'w+')
      f.write('test!')
      f.close()
      rf["status"] = "ok"
      rf["msg"] = fname
    except Exception as e:
      rf["status"] = "err"
      rf["msg"] = str(e)
      pass
    response["file"] = rf

    # whitelist host
    try:
      ru = {}
      urllib2.urlopen(url)
      ru["status"] = "ok"
      ru["msg"] = url

    except urllib2.HTTPError:
      ru["status"] = "ok"
      ru["msg"] = url

    except Exception as e:
      ru["status"] = "err"
      ru["msg"] = str(e)
      pass

    response["host"] = ru

    # whitelist process
    try:
      rp = {}
      subprocess.call(process)
      rp["status"] = "ok"
      rp["msg"] = process[0]
    except Exception as e:
      rp["status"] = "err"
      rp["msg"] = str(e)
      pass
    response["process"] = rp

    # whitelist api
    ra = {}
    try:
      client = boto3.client('lambda')
      client.list_functions()
      ra[str(client.__dict__["_endpoint"]).split('(')[0]] = {}
      ra[str(client.__dict__["_endpoint"]).split('(')[0]]["status"] = "ok"
      ra[str(client.__dict__["_endpoint"]).split('(')[0]]["msg"] = "list_functions"
    except Exception as e:
      ra[str(client.__dict__["_endpoint"]).split('(')[0]] = {}
      ra[str(client.__dict__["_endpoint"]).split('(')[0]]["status"] = "err"
      ra[str(client.__dict__["_endpoint"]).split('(')[0]]["msg"] = str(e)

    try:
      client = boto3.client('s3')
      client.list_buckets()
      ra[str(client.__dict__["_endpoint"]).split('(')[0]] = {}
      ra[str(client.__dict__["_endpoint"]).split('(')[0]]["status"] = "ok"
      ra[str(client.__dict__["_endpoint"]).split('(')[0]]["msg"] = "list_buckets"
    except Exception as e:
      ra[str(client.__dict__["_endpoint"]).split('(')[0]] = {}
      ra[str(client.__dict__["_endpoint"]).split('(')[0]]["status"] = "err"
      ra[str(client.__dict__["_endpoint"]).split('(')[0]]["msg"] = str(e)

    try:
      client = boto3.client('iam')
      client.list_roles()
      ra[str(client.__dict__["_endpoint"]).split('(')[0]] = {}
      ra[str(client.__dict__["_endpoint"]).split('(')[0]]["status"] = "ok"
      ra[str(client.__dict__["_endpoint"]).split('(')[0]]["msg"] = "list_roles"
    except Exception as e:
      ra[str(client.__dict__["_endpoint"]).split('(')[0]] = {}
      ra[str(client.__dict__["_endpoint"]).split('(')[0]]["status"] = "err"
      ra[str(client.__dict__["_endpoint"]).split('(')[0]]["msg"] = str(e)

    response["api"] = ra
  # endregion

  else:
    response = {"status": "err", "msg": "invalid input:"}
    print(json.dumps(body))

  print (json.dumps(response))

  return {
    'statusCode': 200,
    'body': json.dumps(response)
  }

