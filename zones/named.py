#!/usr/bin/env python

import argparse
import datetime
import hashlib
import os
import re
import shutil
import subprocess
import sys
import time


here = os.path.dirname(__file__)
os.chdir(here)
sys.path.append('lib/zones')

from zones import Zone
import shared


parser = argparse.ArgumentParser()
parser.add_argument('-b', '--build', action='store_true')
parser.add_argument('--no-conf-check', action='store_true')
parser.add_argument('-c', '--clean', action='store_true')
parser.add_argument('-d', '--deploy', action='store_true')
parser.add_argument('--no-reload', action='store_true')
parser.add_argument('--no-live-check', action='store_true')
args = parser.parse_args()


now = datetime.datetime.utcnow()
master_zone_names = []

def create_zone(zonename):
    master_zone_names.append(zonename)
    return Zone(zonename,
        primary_nameserver='ns1.mminternals.com.',
        hostmaster_email='it+hostmaster@markmedia.co.',
        ttl=300,
    )

def to_wire(name):
    parts = name.split('.')
    return ''.join(chr(len(x)) + x for x in parts)
assert hashlib.sha1(to_wire('domain.example.')).hexdigest() == '5960775ba382e7a4e09263fc06e7c00569b6a05c'


# We use bind9's "catalog" feature for transferring zones to our
# slave servers.
catalog = create_zone('catalog.mminternals.com.')
shared.mminternals_ns_v1(catalog)
catalog.comment('Bind catalog')
catalog.A('masters', '159.203.32.178') # This should be us.
catalog.TXT('version', '1') # Required


if args.build:

    build_dir = os.path.join('build', now.strftime('%Y%m%d-%H%M%S'))
    os.makedirs(build_dir)

    for filename in os.listdir('zones'):
        if filename.startswith('.') or not filename.endswith('.py'):
            continue
        
        domain = os.path.splitext(filename)[0]
        zonename = domain + '.'
        print domain


        # Add it to the master catalog.
        hash_ = hashlib.sha1(to_wire(zonename)).hexdigest()
        catalog.PTR(hash_ + '.zones', zonename)

        # Create the zone and eval the script.
        zone = create_zone(zonename)
        namespace = {'zone': zone, 'z': zone}
        execfile(os.path.join('zones', filename), namespace)

        # Add our check to it.
        zone.comment('Deployment check')
        zone.TXT('_serial', zone.serial_number, ttl=1)

        path = os.path.join(build_dir, domain)
        with open(path, 'wb') as fh:
            fh.write(''.join(zone.iterdumps()))

    # Write out the catalog.
    with open(os.path.join(build_dir, 'catalog.mminternals.com'), 'wb') as fh:
        fh.write(''.join(catalog.iterdumps()))
    
    # Write out the conf.
    with open(os.path.join(build_dir, 'named.conf.zones'), 'wb') as fh:
        for name in master_zone_names:
            if name.startswith('rpz'):
                extra = 'allow-query { none; };'
            else:
                extra = ''

            fh.write('''zone "%(zonename)s" {
                type master;
                file "/etc/bind/build/live/%(filename)s";
                %(extra)s
            };''' % dict(zonename=name, filename=name.strip('.'), extra=extra))
            fh.write('\n\n') # An extra newline is required!

    try:
        os.unlink('build/latest')
    except OSError:
        pass
    os.symlink(os.path.abspath(build_dir), 'build/latest')

else:

    build_dir = os.readlink('build/latest')


if args.clean:
    print 'Cleaning old builds...'
    dont_clean = set(('live', 'latest', os.path.basename(build_dir)))
    try:
        dont_clean.add(os.path.basename(os.readlink('build/live')))
    except:
        pass
    for name in os.listdir('build'):
        if name not in dont_clean:
            print '   ', name
            path = os.path.join('build', name)
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.unlink(path)


def check_conf(live=False):
    try:
        for name in os.listdir(build_dir):
            if name.startswith('named.conf'):
                if live:
                    subprocess.check_call(['named-checkconf', os.path.join(build_dir, name)])
                else:
                    continue
            zonepath = os.path.join(build_dir, name)
            subprocess.check_call(['named-checkzone', name + '.', zonepath])
        subprocess.check_call(['named-checkconf', 'named.conf'])
    except:
        print 'Failed check!'
        exit(1)

def check_live(server='localhost', delay=0.1, tries=3):

    
    did_error = False
    for name in os.listdir('build/live'):

        if name.startswith('rpz'):
            continue

        content = open(os.path.join('build/live', name), 'rb').read()
        m = re.search(r'_serial 1 IN TXT (\w+)', content)
        if not m:
            continue
        serial = m.group(1)
        print ('    %s %s ' % (name, serial)), 
        
        # Try twice. Sometimes it takes the kick from the first request
        # to clear the caches.
        for _ in xrange(tries):
            output = subprocess.check_output(['dig', '@' + server, '+short', '_serial.' + name.strip('.'), 'TXT'])
            output = output.strip().strip('"')
            if serial == output:
                print ' OK'
                break
            
            # We need to give it a fraction of a second.
            sys.stdout.write('.')
            sys.stdout.flush()
            time.sleep(delay)
        
        else:
            print '    ERROR: Got %s' % output
            did_error = True

    if did_error:
        print
        print 'THE RUNTIME CHECKS DID NOT PASS!!!'
        print
        exit(4)

        print 'Everything checks out!'



if not args.no_conf_check:
    print 'Checking zones and config...'
    check_conf()


if args.deploy:
    print 'Linking to build/live...'
    try:
        os.unlink('build/live')
    except OSError:
        pass
    os.symlink(os.path.abspath(build_dir), 'build/live')

    if not args.no_conf_check:
        print 'Checking again...'
        check_conf()

    if not args.no_reload:
        print 'Reloading service...'
        subprocess.check_call(['sudo', 'systemctl', 'reload', 'bind9'])

    if not args.no_live_check:
        print 'Checking local records...'
        check_live()
        print 'Checking remote (oxford) records...'
        check_live('23.239.9.70', delay=0.25, tries=10)

