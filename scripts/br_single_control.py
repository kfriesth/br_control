#!/usr/bin/env python
'''
This is the main file that the meta-server calls when you want you
run just one robot at the time
'''

import roslib; roslib.load_manifest('br_swarm_rover')
import rospy
from std_msgs.msg import String

import br_cam
from br_control import RovCon
from time import sleep

# meta_server.py creates the file where the shall write its network
# address, then the address is passed as an argument here
import argparse
parser = argparse.ArgumentParser('br_single_control')
parser.add_argument('file', type=str, default=None,
                    help='temporary file to store server uri')
arg = parser.parse_args()

if __name__ == '__main__':
    try:
        # open file to save ROS server address
        address_file = open(arg.file, 'w+b')
        # store ROS server address
        #TODO: change the local host part to a normal address
        # for now the wanted address is exported manually in the
        # .bashrc file
        import os
        address = os.environ['ROS_MASTER_URI']
        address_file.write(address)
        address_file.close()

        rover = RovCon() 
        rover_video = br_cam.RovCam(rover.return_data())

        pub = rospy.Publisher('image', String) # robot camera data
        rospy.init_node('br_single_control')
#        distance = 0.5    # feet
#        speed = 1         # foot/sec
        # obtain publshed move command
        #TODO: also obtain speed and distance
        rospy.Subscriber("move", String, rover.set_move)

        # thread to run the subscriber
        from threading import Thread
        spin_thread = Thread(target=lambda: rospy.spin())
        spin_thread.start()
        while not rospy.is_shutdown(): 
#            str = "robot moves %s" % rospy.get_time()
 #           rospy.loginfo(str)
            buf = rover_video.receive_image()
            pub.publish(String(buf))
            sleep(0.033)

    except rospy.ROSInterruptException:
        rover.disconnect_rover()
        rover_video.disconnect_video()
        pass