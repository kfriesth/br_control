#!/usr/bin/env python
'''
Client specifically for AsteroidRoamsSim derived from the
PygameClientInterface
'''

import kivy
kivy.require('1.7.1')

#from os.path import join, dirname
from kivy.uix.floatlayout import FloatLayout
from kivy.app import App
from kivy.graphics import Rectangle
from kivy.clock import Clock
from kivy.core.image import ImageData
from kivy.graphics.texture import Texture
from kivy.logger import Logger
from kivy.base import EventLoop
EventLoop.ensure_window()
# FIXME this shouldn't be necessary
#from kivy.core.window import Window

from pygame.image import tostring

class AsteroidSimClientInterface():
    def __init__(self, server_uri, update_image):

        self.__has_control = True

    def hasControl(self):
        '''Return True if user wants to send control commands.
        Tab key and shift-tab toggle this.
        '''
        # Check if control flag should be toggled.
        import pygame
        if pygame.key.get_pressed()[pygame.K_TAB]:
            self.__has_control = not (pygame.key.get_mods() & pygame.KMOD_LSHIFT)

            if self.__has_control:
                print('Take control')
            else:
                print('Release control')

        return self.__has_control

class ControlClass(FloatLayout):
    def __init__(self, **kwargs):
        '''
        We use __init__ mainly because _args cannot be initialized
        to an ObjectProperty for some reason, so we gotta initialize
        it this way
        '''
        super(ControlClass, self).__init__(**kwargs)
        self._args = self.parser_arguments()
        self.started = False     # true if client connected
        self.client = None       # server client object

        # original image size (from server)
        self.ori_im_width = 1280.0
        self.ori_im_height = 720.0
        # TODO: make sure that aspect ratio is kept on the server
        # side as well, in order to avoid conflict between Pygame
        # and the "object clicking" functionality

    def parser_arguments(self):
        '''
        Gets the parsing arguments for the simulation
        '''
        import argparse
        parser = argparse.ArgumentParser('asteroid_sim_client')
        parser.add_argument('--round-trip-time-delay', type=float,
                default=0., help='time delay for client to emulate')
        parser.add_argument('--joystick', action='store_true',
                help='use joystick instead of keyboard')
        parser.add_argument('--render',
                help='render image to file then exit immediately')
        parser.add_argument('--server-uri',
                default='http://localhost:54321',
                help='URI of server')
        parser.add_argument('--no-image-updates',
                dest='image_updates', action='store_false',
                help='disable image display updates')
        parser.add_argument('--joystick-id', type=int, default=0,
                help='select a joystick')
        parser.add_argument('--hostname', help='meta-server address')
        return parser.parse_args()

    def schedule_client(self, *args):
        '''
        starts the thead to to run the server simulation
        '''
        Clock.schedule_interval(self.start_server, 1.0 / 25.0)

    def start_server(self, dt):
        '''
        initializes the client connection, and gets image data
        '''
        hostname = "vostro"
        # Keep trying in case server is not up yet
        print('before true statement')
        if not self.started:
            print('before while')
            count = 0
            while True:
                print('beggining of while')
                import socket
                try:
                    from xmlrpclib import ServerProxy
                    # connect to meta server first
                    prox = ServerProxy("http://" + hostname+":12345")
                    # get servers address from the meta server
                    ros_uri = prox.getHostAddress()
                    Logger.info('Server Address\n <%s>', ros_uri)
#                    self.client = \
#                    AsteroidSimClientInterface(ros_uri,
#                    self._args.image_updates)
                    self.started = True
                    Logger.info('Client Connected...')
                    break
                except socket.error:
                    print('in exception')
                    count += 1
                    import time
                    time.sleep(.1)

                print('before count')
                if count > 5:
                    print('in count')
                    waiting = 'Waiting for meta server at %s'
                    uri="http://" + hostname + ":12345"
                    Logger.info(waiting, uri)
        try:
#            self.client.processClients() # get all pygame events
            # TODO: get image string data from br_cam.py
            # size of all incoming images
            im_size = self.client.getImageSize()
            retrieve = self.client.retrieveImage()
            # convert pygame surface to Kivy data
            buf = tostring(retrieve, 'RGB', True)
            imdata = ImageData(im_size[0], im_size[1],
                               'rgb', buf)
            tex = Texture.create_from_data(imdata)

            # calculate new image size
            aspect_ratio = self.ori_im_height / self.ori_im_width
            w = 3.0*self.width/4.0      # desired width
            h = aspect_ratio * w        # desired height

            # image's origin starts from buttom left
            (pos_x, pos_y) = (self.center_x/4, self.center_y/4)

            # transform image's bottom origin to the top left
            # which agrees with the mouse's origin
            x_0 = pos_x
            y_0 = self.height - (h + pos_y)
            im_translation = []
            im_translation.append(x_0)
            im_translation.append(y_0)

            # size difference ratio between GUI window and picture
            im_translation.append(self.width/w)    # x ratio
            im_translation.append(self.height/h)   # y ratio
            self.client.setMouseRatio(im_translation)
            self.canvas.clear()   # clear to upate canvas
            with self.canvas:     #display image
                Rectangle(texture=tex,
                      pos= (pos_x, pos_y),
                      size=(w, h))
        except BaseException:
            Logger.warning('closing simulation connection')
#            self.stop_connection()

    def stop_connection(self):
        self.client.quit()
        from sys import exit
        exit()

class KivyGui(App):
    def build(self):
        return ControlClass()

if __name__ == '__main__':
    KivyGui().run()