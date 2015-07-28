#!/usr/bin/python -u

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import json, os, sys, hmac, hashlib, subprocess, time

def getenv_default(env_name, default_value):
    if env_name in os.environ and os.environ[env_name]:
        return os.environ[env_name]
    else:
        return default_value

class GitAutoDeploy(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            secret_url = self.path[1:].split("/")[-1]
            if secret_url == os.environ['SECRET_URL']:
                sig_received = self.headers.getheader('X-Hub-Signature')[5:]
                length = int(self.headers.getheader('content-length'))
                body = self.rfile.read(length)
                sig_calculated = hmac.new(os.environ['SECRET_KEY'], msg=body, digestmod=hashlib.sha1).hexdigest()
                if sig_calculated == sig_received:
                    print("Valid hook received, rebuilding page")
                    sys.stdout.flush()
                    if subprocess.call(['su', '-s', '/bin/sh', '-c', '/usr/sbin/deploy_app.sh', getenv_default('DEPLOY_USER', 'app')]) == 0:
                        retval=200
                    else:
                        retval=500
                else:
                    retval=403
            else:
                retval=403
        except:
            retval=500

        self.send_response(retval)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write('OHAI! STATUS: %d' % retval)

    def log_message(self, format, *args):
        return

def main():
    if not 'SECRET_KEY' in os.environ or not 'SECRET_URL' in os.environ:
        os.system("supervisorctl stop autodeploy")
        while True:
            time.sleep(1)

    try:
        server = None
        print('GitHub Autodeploy Service Thing v1.0.2-ultrastable started.')
        server = HTTPServer(('', 8888), GitAutoDeploy)
        server.serve_forever()
    except(KeyboardInterrupt, SystemExit) as e:
        if server:
            server.socket.close()

if __name__ == '__main__':
    main()
