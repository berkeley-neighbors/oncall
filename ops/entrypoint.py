# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

import logging
import subprocess
from os import environ, path, execv
import socket
import time
import sys
from glob import glob

dbpath = '/home/oncall/db'
initializedfile = '/home/oncall/db_initialized'

logger = logging.getLogger()

SCHEME = 'mysql+pymysql'
PORT = 3306
CHARSET = 'utf8'
USER = 'root'
DATABASE = 'oncall'
HOST = environ.get('MYSQL_HOST', 'localhost')
PASSWORD = environ.get('MYSQL_ROOT_PASSWORD')

def load_sqldump(sqlfile, one_db=True):
    print('Importing %s...' % sqlfile)
    with open(sqlfile) as h:
        cmd = ['/usr/bin/mysql', '-h', HOST, '-u',
               USER, '-p' + PASSWORD,'-P' + str(PORT)]
        if one_db:
            cmd += ['-o', DATABASE]
        proc = subprocess.Popen(cmd, stdin=h)
        proc.communicate()

        if proc.returncode == 0:
            print('DB successfully loaded ' + sqlfile)
            return True
        else:
            print(('Ran into problems during DB bootstrap. '
                   'oncall will likely not function correctly. '
                   'mysql exit code: %s for %s') % (proc.returncode, sqlfile))
            return False


def wait_for_mysql():
    print('Checking MySQL liveness on %s...' % HOST)
    db_address = (HOST, PORT)
    tries = 0
    while True:
        try:
            sock = socket.socket()
            sock.connect(db_address)
            sock.close()
            break
        except socket.error:
            if tries > 20:
                print('Waited too long for DB to come up. Bailing.')
                sys.exit(1)

            print('DB not up yet. Waiting a few seconds..')
            time.sleep(2)
            tries += 1
            continue


def initialize_mysql_schema():
    print('Initializing oncall database')
    # disable one_db to let schema.v0.sql create the database
    re = load_sqldump(path.join(dbpath, 'schema.v0.sql'), one_db=False)
    if not re:
        sys.exit('Failed to load schema into DB.')

    for f in glob(path.join(dbpath, 'patches', '*.sql')):
        re = load_sqldump(f)
        if not re:
            sys.exit('Failed to load DB patche: %s.' % f)

    re = load_sqldump(path.join(dbpath, 'dummy_data.sql'))
    if not re:
        sys.stderr.write('Failed to load dummy data.')

    with open(initializedfile, 'w'):
        print('Wrote %s so we don\'t bootstrap db again' % initializedfile)


def main():
    # It often takes several seconds for MySQL to start up. oncall dies upon start
    # if it can't immediately connect to MySQL, so we have to wait for it.
    wait_for_mysql()

    if environ.get('DOCKER_DB_BOOTSTRAP') != '0':
        if not path.exists(initializedfile):
            initialize_mysql_schema()

    execv('/usr/bin/uwsgi',
             ['/usr/bin/uwsgi', '--yaml', '/home/oncall/daemons/uwsgi.yaml:prod'])


if __name__ == '__main__':
    main()
