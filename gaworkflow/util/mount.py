"""
Utilities for working with unix-style mounts.
"""
import os
import subprocess

def list_mount_points():
    """
    Return list of current mount points

    Note: unix-like OS specific
    """
    mount_points = []
    likely_locations = ['/sbin/mount', '/bin/mount']
    for mount in likely_locations:
        if os.path.exists(mount):
            p = subprocess.Popen(mount, stdout=subprocess.PIPE)
            p.wait()
            for l in p.stdout.readlines():
                rec = l.split()
                device = rec[0]            
                mount_point = rec[2]
                assert rec[1] == 'on'
                # looking at the output of mount on linux, osx, and 
                # sunos, the first 3 elements are always the same
                # devicename on path
                # everything after that displays the attributes
                # of the mount points in wildly differing formats
                mount_points.append(mount_point)
            return mount_points
    else:
        raise RuntimeError("Couldn't find a mount executable")

def is_mounted(point_to_check):
    """
    Return true if argument exactly matches a current mount point.
    """
    for mount_point in list_mount_points():
        if point_to_check == mount_point:
            return True
    else:
        return False

def find_mount_point_for(pathname):
    """
    Find the deepest mount point pathname is located on
    """
    realpath = os.path.realpath(pathname)
    mount_points = list_mount_points()

    prefixes = set()
    for current_mount in mount_points:
        cp = os.path.commonprefix([current_mount, realpath])
        prefixes.add((len(cp), cp))

    prefixes = list(prefixes)
    prefixes.sort()
    if len(prefixes) == 0:
        return None
    else:
        print prefixes
        # return longest common prefix
        return prefixes[-1][1]


