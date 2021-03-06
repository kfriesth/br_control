#!/usr/bin/env python
'''
This node runs indefinitelly  in a computer and waits for a client
to request connection to a/the robot(s)
'''

import rospy

from SimpleXMLRPCServer import SimpleXMLRPCServer
import subprocess
from time import sleep

START_ROS_ROVER = []    # stores rover program

def startProcess():
    '''
    This function starts roscore and the rovers software.
    The function is called when a client connects to the meta-server
    '''
    from tempfile import NamedTemporaryFile
    address_file = NamedTemporaryFile(delete=False)
    # pass temp file name as argument to br_swarm_rover node
    uri_file = address_file.name
    robot_address = []
    # TODO: put findConnectedRobot() in the main function
    # and include it as argument for startProcess()
    robot_address = findConnectedRobot()
    rospy.loginfo(str(len(robot_address)) + ' robots are connected \n')
    from threading import Thread
    rover_started = False    # true if rover program started
    sleep(3)      # give roscore time to start
    while not rover_started:
        try:
            # start a node/thread per robot
            for address in robot_address:
                # start main node to control rover
                br_cmd = ['rosrun', 'br_swarm_rover', 
                        'br_single_control.py', uri_file, address]
                rover_thread = \
                    Thread(target=lambda: START_ROS_ROVER.append(
                        subprocess.Popen(br_cmd)))
                rover_thread.start()
                # start optical flow node for each robot connected
                # 'compressed' dictates type of image to subscribe to
#                br_cmd = ['rosrun', 'br_swarm_rover', 
#                        'br_opt_flow', address.split('.')[3], 
#                        '_image_transport:=compressed']
#                flow_thread = \
#                    Thread(target=lambda: START_ROS_ROVER.append(
#                        subprocess.Popen(br_cmd)))
#                flow_thread.start()
            rover_started = True
        except BaseException:
            rospy.loginfo('trying to connect to rover(s)')
            pass
    import os
    robot_address.append(os.environ['ROS_MASTER_URI'])
#    line = None
#    while not line:
#        address_file.seek(0)
#        line =  address_file.readline()
    # change uri as first key
    robot_address.reverse()    # change uri as first key
    return robot_address#line       #threads

def findConnectedRobot():
    '''
    Finds which robots are connected to the computer and returns the
    addresses of the NIC they are connected to
    '''
    robot_address = []  # stores NIC address
    import netifaces 
    # get the list of availble NIC's
    for card in netifaces.interfaces():
        try:
            # get all NIC addresses
            temp = netifaces.ifaddresses(\
                    card)[netifaces.AF_INET][0]['addr']
            temp2 = temp.split('.')
#            # see if address matches common address given to NIC when
#            # NIC is connected to a robot
            if temp2[0] == '192' and int(temp2[3]) < 30:
                rospy.loginfo('appending address: ' + temp)
                robot_address.append(temp)
        except BaseException:
            pass
    return robot_address
            
def getServerAddress(file_name):
    '''
    Meta-server calls this function when requesting
    ROS server's address
    '''
    import tempfile
    tempfile.name

def main():
    """Main function to run meta-server functionality"""
    rospy.init_node('meta_server')
    threads = START_ROS_ROVER
    thread_started = False
    # FIXME: I'm not sure if "0.0.0.0" will allow remote access
    # it might not be a valid address
    server = SimpleXMLRPCServer(("0.0.0.0", 5007))
    server.register_function(startProcess, "startProcess")
    while not rospy.is_shutdown():
        try:
            if not thread_started:
                rospy.loginfo('\nwaiting for a client to connect...\n\n')
                server.handle_request() 
                thread_started = True
        except BaseException:
            try:
                del server.socket
            except BaseException:
                rospy.logwarn("could not close socket")
            rospy.loginfo('exiting ROS program')
            for thread in threads:
                thread.kill()
            from sys import exit
            exit()

if __name__ == '__main__':
    main()
