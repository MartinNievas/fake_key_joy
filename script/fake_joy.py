#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 PAL Robotics SL.
# Released under the BSD License.
#
# Authors:
#   * Original work: Siegfried-A. Gevatter
#   * Modifications
#       - Martin Nievas

import curses
import math

import rospy
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Joy

class TextWindow():

    _screen = None
    _window = None
    _num_lines = None

    def __init__(self, stdscr, lines=10):
        self._screen = stdscr
        self._screen.nodelay(True)
        curses.curs_set(0)

        self._num_lines = lines

    def read_key(self):
        keycode = self._screen.getch()
        return keycode if keycode != -1 else None

    def clear(self):
        self._screen.clear()

    def write_line(self, lineno, message):
        if lineno < 0 or lineno >= self._num_lines:
            raise ValueError('lineno out of bounds')
        height, width = self._screen.getmaxyx()
        y = int((height / self._num_lines) * lineno)
        x = 10
        for text in message.split('\n'):
            text = text.ljust(width)
            self._screen.addstr(y, x, text)
            y += 1

    def refresh(self):
        self._screen.refresh()

    def beep(self):
        curses.flash()


LogitechF710 = {
    'A_BUTTON' : 0,
    'B_BUTTON' : 1,
    'X_BUTTON' : 2,
    'Y_BUTTON' : 3,
    'LEFT_BUMPER' : 4,
    'RIGHT_BUMPER' : 5,
    'BACK' : 6,
    'START' : 7,
    'LOGITECH' : 8,
    'LEFT_JOYSTICK' : 9,
    'RIGHT_JOYSTICK' : 10,
    }

class SimpleKeyTeleop():
    def __init__(self, interface):
        self._interface = interface
        self._pub_cmd = rospy.Publisher('key_vel', Twist)
        self._pub_joy = rospy.Publisher('joy', Joy)

        self._hz = rospy.get_param('~hz', 10)

        self._forward_rate = rospy.get_param('~forward_rate', 0.8)
        self._backward_rate = rospy.get_param('~backward_rate', 0.5)
        self._rotation_rate = rospy.get_param('~rotation_rate', 1.0)
        self._angular = 0
        self._linear = 0
        self._joy_model = LogitechF710
        self._buttons = []

        for button in self._joy_model:
            self._buttons.append(0)


    def run(self):
        rate = rospy.Rate(self._hz)
        self._running = True
        self._keycode = 'a'
        while self._running:
            while True:
                keycode = self._interface.read_key()
                if keycode is None:
                    break
                self._key_pressed(keycode)
            self._publish()
            rate.sleep()

    def _get_joy(self):

        joy = Joy()

        for status in self._buttons:
            joy.buttons.append(status)
        return joy

    def _reset_buttons(self):
        for i,button in enumerate(self._joy_model):
            self._buttons[i] = 0

    def _key_pressed(self, keycode):
        self._keycode = keycode
        if keycode == ord('q'):
            self._running = False
            rospy.signal_shutdown('Bye')
        if keycode == ord('j'):
            self._buttons[self._joy_model['X_BUTTON']] = True
        if keycode == ord('i'):
            self._buttons[self._joy_model['Y_BUTTON']] = True
        if keycode == ord('m'):
            self._buttons[self._joy_model['A_BUTTON']] = True
        if keycode == ord('k'):
            self._buttons[self._joy_model['B_BUTTON']] = True
        if keycode == ord('u'):
            self._buttons[self._joy_model['LEFT_BUMPER']] = True
        if keycode == ord('o'):
            self._buttons[self._joy_model['RIGHT_BUMPER']] = True
        if keycode == ord('a'):
            self._buttons[self._joy_model['BACK']] = True
        if keycode == ord('s'):
            self._buttons[self._joy_model['LOGITECH']] = True
        if keycode == ord('d'):
            self._buttons[self._joy_model['START']] = True
        if keycode == ord('e'):
            self._buttons[self._joy_model['LEFT_JOYSTICK']] = True
        if keycode == ord('r'):
            self._buttons[self._joy_model['RIGHT_JOYSTICK']] = True


    def _publish(self):
        self._interface.clear()
        self._interface.write_line(2, 'Linear: %f, Angular: %f' % (self._linear, self._angular))
        self._interface.write_line(3, 'keycode: %c' % (self._keycode))
        self._interface.write_line(4, 'keycode: %d' % (len(self._buttons)))
        self._interface.write_line(5, 'Use arrow keys to move, q to exit.')
        self._interface.refresh()

        joy = self._get_joy()
        self._pub_joy.publish(joy)
        self._reset_buttons()


def main(stdscr):
    rospy.init_node('fake_joy_teleop')
    app = SimpleKeyTeleop(TextWindow(stdscr))
    app.run()

if __name__ == '__main__':
    try:
        curses.wrapper(main)
    except rospy.ROSInterruptException:
        pass
