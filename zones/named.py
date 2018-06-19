#!/usr/bin/env python

from __future__ import print_function

import argparse
import datetime
import hashlib
import os
import re
import shutil
import subprocess
import sys
import time

from .zone import Zone, EPOCH_OFFSET


def to_wire(name):
    parts = name.split('.')
    return ''.join(chr(len(x)) + x for x in parts)
assert hashlib.sha1(to_wire('domain.example.')).hexdigest() == '5960775ba382e7a4e09263fc06e7c00569b6a05c'


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument('-c', '--clean', action='store_true')
    parser.add_argument('-b', '--build', action='store_true')
    parser.add_argument('-d', '--deploy', action='store_true')

    parser.add_argument('-s', '--slave', action='append', dest='slaves', default=[])
    
    parser.add_argument('-e', '--epoch-offset', type=int, default=EPOCH_OFFSET)
    
    parser.add_argument('--primary-nameserver')
    parser.add_argument('--hostmaster-email')
    parser.add_argument('--ttl', type=int, default=300)

    parser.add_argument('-z', '--zones-dir', default='zones')
    parser.add_argument('--build-root', default='build')
    parser.add_argument('--build-name', default=datetime.datetime.utcnow().strftime('%Y%m%d-%H%M%S'))

    parser.add_argument('--reload-cmd')

    parser.add_argument('--no-conf-check', action='store_true')
    parser.add_argument('--no-live-check', action='store_true')
    parser.add_argument('--no-reload', action='store_true')

    args = parser.parse_args()

    # Allow group to write.
    os.umask(0o002)

    latest_build_symlink = os.path.join(args.build_root, 'latest')
    if args.build:
        build_dir = build(args)
        try:
            os.unlink(latest_build_symlink)
        except OSError:
            pass
        os.symlink(os.path.abspath(build_dir), latest_build_symlink)
    else:
        try:
            build_dir = os.readlink(latest_build_symlink)
        except OSError:
            print("No build dir exists; cannot continue.")
            return 2

    if args.clean:
        clean(args, build_dir)

    if not args.no_conf_check:
        print('Checking zones and config...')
        check_conf(args, build_dir)

    if args.deploy:

        live_link = os.path.abspath(os.path.join(args.build_root, 'live'))
        print('Linking to build/live...')
        try:
            os.unlink(live_link)
        except OSError:
            pass
        os.symlink(os.path.abspath(build_dir), live_link)

        if not args.no_conf_check:
            print('Checking again...')
            check_conf(args, build_dir)

        if not args.no_reload:
            print('Reloading service...')
            if args.reload_cmd:
                subprocess.check_call(args.reload_cmd, shell=True)
            else:
                subprocess.check_call(['sudo', 'systemctl', 'reload', 'bind9'])

        if not args.no_live_check:
            print('Checking live local records...')
            check_live(args)
            for host in args.slaves:
                print('Checking live remote ({}) records...'.format(host))
                check_live(args, host, delay=0.25, tries=10)



def build(args):

    build_dir = os.path.abspath(os.path.join(args.build_root, args.build_name))
    build_zones_dir = os.path.join(build_dir, 'zones')
    os.makedirs(build_zones_dir)

    zones = []
    def create_zone(zonename):
        zone = Zone(zonename,
            primary_nameserver=args.primary_nameserver,
            hostmaster_email=args.hostmaster_email,
            ttl=args.ttl,
            epoch_offset=args.epoch_offset,
        )
        zones.append(zone)
        return zone

    for filename in os.listdir(args.zones_dir):
        if filename.startswith('.') or not filename.endswith('.py'):
            continue
        
        domain = os.path.splitext(filename)[0]
        zonename = domain + '.'
        print(domain)

        zone = create_zone(zonename)
        if args.slaves:
            zone.extra_conf['also-notify'] = args.slaves
        
        # Create the zone and eval the script.
        namespace = {'zone': zone, 'z': zone}
        execfile(os.path.join(args.zones_dir, filename), namespace)

        # Add our check to it.
        zone.comment('Deployment check')
        zone.TXT('_serial', zone.serial_number, ttl=1)

        path = os.path.join(build_zones_dir, domain)
        with open(path, 'wb') as fh:
            fh.write(zone.dumps_zone())

    # Write out the conf.
    with open(os.path.join(build_dir, 'named.conf'), 'wb') as fh:
        for zone in zones:
            fh.write(zone.dumps_conf(file='"{}"'.format(os.path.join(build_dir, 'zones', zone.origin.strip('.')))))
            fh.write('\n') # An extra newline is required!

    return build_dir


def clean(args, build_dir):

    print('Cleaning old builds...')

    dont_clean = set(('latest', os.path.basename(build_dir)))
    for name in os.listdir(args.build_root):
        if name in dont_clean:
            continue

        print('   ', name)
        path = os.path.join(args.build_root, name)
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.unlink(path)


def check_conf(args, build_dir):
    try:

        subprocess.check_call(['named-checkconf', os.path.join(build_dir, 'named.conf')])

        zone_dir = os.path.join(build_dir, 'zones')
        for name in os.listdir(zone_dir):
            subprocess.check_call(['named-checkzone', name + '.', os.path.join(zone_dir, name)])

        # The full thing as it stands.
        subprocess.check_call(['named-checkconf'])

    except subprocess.CalledProcessError:
        print('Failed check!')
        exit(1)


def check_live(args, server='localhost', delay=0.1, tries=3):

    did_error = False
    live_dir = os.path.join(args.build_root, 'live', 'zones')
    for name in os.listdir(live_dir):

        # TODO: Signal this another way.
        if name.startswith('rpz'):
            continue

        content = open(os.path.join(live_dir, name), 'rb').read()
        m = re.search(r'_serial 1 IN TXT (\w+)', content)
        if not m:
            continue
        serial = m.group(1)
        print('    %s %s ' % (name, serial), end='')
        
        # Try twice. Sometimes it takes the kick from the first request
        # to clear the caches.
        for _ in xrange(tries):
            output = subprocess.check_output(['dig', '@' + server, '+short', '_serial.' + name.strip('.'), 'TXT'])
            output = output.strip().strip('"')
            if serial == output:
                print(' OK')
                break
            
            # We need to give it a fraction of a second.
            sys.stdout.write('.')
            sys.stdout.flush()
            time.sleep(delay)
        
        else:
            print('    ERROR: Got %s' % output)
            did_error = True

    if did_error:
        print()
        print('THE RUNTIME CHECKS DID NOT PASS!!!')
        print()
        exit(4)

    print('Everything checks out!')





if __name__ == '__main__':
    exit(main() or 0)

