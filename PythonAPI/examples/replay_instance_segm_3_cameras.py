#!/usr/bin/env python

# Copyright (c) 2019 Computer Vision Center (CVC) at the Universitat Autonoma de
# Barcelona (UAB).
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

import configparser
import glob
import os
import sys
import time
import cv2
import numpy as np
import pandas as pd
from PIL import Image

try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import carla

import argparse

try:
    import queue
except ImportError:
    import Queue as queue

from DReyeVR_utils import DReyeVRSensor, find_ego_vehicle, find_ego_sensor

def ReplayStat(s):
    idx = s.find("ReplayStatus")
    if idx == -1:
        return 0
    print(s[idx + len("ReplayStatus=")])
    return (s[idx + len("ReplayStatus=")] == '1')


class Sensor():
    def __init__(self, sensor_config_section, world, blueprint_library, ego_vehicle):
        self.world = world
        self.blueprint_library = blueprint_library
        self.ego_vehicle = ego_vehicle
        self.sensor_config_section = sensor_config_section
        self.rgb_sensor = None
        self.rgb_sensor_queue = None
        self.instseg_sensor = None
        self.instseg_sensor_queue = None
        self.init_rgb_camera()
        
        if 'fpv' not in sensor_config_section:
            self.init_instseg_camera

    # if for the type of the sensors
    def init_rgb_camera(self):
        self.rgb_sensor = self.world.spawn_actor(
            self.blueprint_library.find('sensor.camera.rgb'),
            carla.Transform(carla.Location(x=float(self.sensor_config_section['x']), z=float(self.sensor_config_section['z']), y=float(self.sensor_config_section['y'])), 
                            carla.Rotation(pitch=float(self.sensor_config_section['pitch']), yaw=float(self.sensor_config_section['yaw']))),
                            attach_to=self.ego_vehicle)
        self.rgb_sensor_queue = queue.Queue()
        self.rgb_sensor.listen(self.rgb_sensor_queue.put)
    
    def init_instseg_camera(self):
        self.instseg_sensor = self.world.spawn_actor(
            self.blueprint_library.find('sensor.camera.instance_segmentation'),
            carla.Transform(carla.Location(x=float(self.sensor_config_section['x']), z=float(self.sensor_config_section['z']), y=float(self.sensor_config_section['y'])), 
                            carla.Rotation(pitch=float(self.sensor_config_section['pitch']), yaw=float(self.sensor_config_section['yaw']))),
            attach_to=self.ego_vehicle)
        self.instseg_sensor_queue = queue.Queue()
        self.instseg_sensor.listen(self.instseg_sensor_queue.put)
                

def main():

    argparser = argparse.ArgumentParser(
        description=__doc__)
    argparser.add_argument(
        '--host',
        metavar='H',
        default='127.0.0.1',
        help='IP of the host server (default: 127.0.0.1)')
    argparser.add_argument(
        '-p', '--port',
        metavar='P',
        default=2000,
        type=int,
        help='TCP port to listen to (default: 2000)')
    argparser.add_argument(
        '-s', '--start',
        metavar='S',
        default=0.0,
        type=float,
        help='starting time (default: 0.0)')
    argparser.add_argument(
        '-d', '--duration',
        metavar='D',
        default=0.0,
        type=float,
        help='duration (default: 0.0)')
    argparser.add_argument(
        '-f', '--recorder-filename',
        metavar='F',
        default="test1.log",
        help='recorder filename (test1.log)')
    argparser.add_argument(
        '-c', '--camera',
        metavar='C',
        default=0,
        type=int,
        help='camera follows an actor (ex: 82)')
    argparser.add_argument(
        '-x', '--time-factor',
        metavar='X',
        default=1.0,
        type=float,
        help='time factor (default 1.0)')
    argparser.add_argument(
        '-i', '--ignore-hero',
        action='store_true',
        help='ignore hero vehicles')
    argparser.add_argument(
        '--spawn-sensors',
        action='store_true',
        help='spawn sensors in the replayed world')
    argparser.add_argument(
        '-n', '--frame-number',
        default=0,
        type=int,
        help='number of frames in the recording')
    argparser.add_argument(
        '-parse', '--recorder-parse',
        metavar='R',
        default="test1.log",
        help='recorder parse file outputted after running show_recorder_file_info.py')
    argparser.add_argument(
        '-config', '--sensor-config',
        default = 'sensor_config.ini',
        help = "sensor configuration deatils for camera orientation"
    )
    argparser.add_argument(
        '-aw', '--awareness-data',
        help = "awareness data frame in json form"
    )
    argparser.add_argument(
        '-o', '--out-dir',
        default=None,
        help = "output directory for the images"
    )

    args = argparser.parse_args()
    egosensor = None
    instseg_camera = None
    sensor_config = configparser.ConfigParser()
    print(args.sensor_config)
    sensor_config.read(args.sensor_config)
    
    num_frames_buffer = 500

    try:

        client = carla.Client(args.host, args.port)
        client.set_timeout(60.0)

        world = client.get_world()        

        # # set the time factor for the replayer
        # client.set_replayer_time_factor(args.time_factor)

        # load the town before starting replay to prevent reset of sync settings
        recorder_txt = client.show_recorder_file_info(args.recorder_filename, show_all=False).splitlines()
        town_str = recorder_txt[1] # eg.g 'Map: Town02'        
        town_name = town_str.strip('Map: ')
        client.load_world(town_name)        
        
        # Configure carla simulation in sync mode.
        settings = world.get_settings()
        settings.synchronous_mode = True
        settings.fixed_delta_seconds = 0.05
        world.apply_settings(settings)
        world.tick()

        
        # replay the session
        replay_info_str = client.replay_file(args.recorder_filename, args.start, args.duration, args.camera, args.spawn_sensors)
        time.sleep(1)

        # Configure carla simulation in sync mode.
        # client.set_timeout(60.0)
        
        blueprint_library = world.get_blueprint_library()
        
        #import time        
        
        for line in replay_info_str.split("\n"):
            if "Total time recorded" in line:
                replay_duration = float(line.split(": ")[-1])
                break
        
        ego_vehicle = find_ego_vehicle(world)
        egosensor = find_ego_sensor(world)
        ego_queue = queue.Queue()
        egosensor.listen(ego_queue.put)
                
        #Assigning the number of replay frames to run through
        total_replay_frames = 200
        if (args.frame_number is not 0):
            total_replay_frames = args.frame_number
        else:        
            for line in reversed(recorder_txt): # Frames is near the bottom
                if "Frames: " in line:
                    framesLine = line.strip()
                    total_replay_frames = int(framesLine.split(": ")[1])
                    print(total_replay_frames)
                    break
            print("Total num of recorded frames: ", total_replay_frames)
            

        # spawn sensors
        # Class for spawning sensors, change the way sensors are spawned 

        # cameras = {}
        # for section in sensor_config.sections():
        #     camera_object = Sensor(section, world, blueprint_library, ego_vehicle)
        #     cameras[section] = camera_object
        
        rgb_camera_fpv = world.spawn_actor(
            blueprint_library.find('sensor.camera.rgb'),
            carla.Transform(carla.Location(x=float(sensor_config['fpv']['x']), z=float(sensor_config['fpv']['z']), y=float(sensor_config['fpv']['y'])), carla.Rotation(pitch=float(sensor_config['rgb']['pitch']))),
            attach_to=ego_vehicle)
        rgb_queue_fpv = queue.Queue()
        rgb_camera_fpv.listen(rgb_queue_fpv.put)

        rgb_camera = world.spawn_actor(
            blueprint_library.find('sensor.camera.rgb'),
            carla.Transform(carla.Location(x=float(sensor_config['rgb']['x']), z=float(sensor_config['rgb']['z']), y=float(sensor_config['rgb']['y'])), carla.Rotation(pitch=float(sensor_config['rgb']['pitch']))),
            attach_to=ego_vehicle)
        rgb_queue = queue.Queue()
        rgb_camera.listen(rgb_queue.put)
        #     cameras['rgb_'+section] = [rgb_camera, rgb_queue]
            
        #     if section != 'fpv':    
        instseg_camera = world.spawn_actor(
        blueprint_library.find('sensor.camera.instance_segmentation'),
        carla.Transform(carla.Location(x=float(sensor_config['rgb']['x']), z=float(sensor_config['rgb']['z'])), carla.Rotation(pitch=float(sensor_config['rgb']['pitch']))),
        attach_to=ego_vehicle)

        instseg_queue = queue.Queue()
        instseg_camera.listen(instseg_queue.put)   
        #         cameras['instseg_' + section] = [instseg_camera, instseg_queue]
                

        rgb_camera_left = world.spawn_actor(
            blueprint_library.find('sensor.camera.rgb'),
            carla.Transform(carla.Location(x=float(sensor_config['rgb_left']['x']), z=float(sensor_config['rgb_left']['z']), y=float(sensor_config['rgb_left']['y'])), carla.Rotation(pitch=float(sensor_config['rgb_left']['pitch']), yaw=float(sensor_config['rgb_left']['yaw']))),
            attach_to=ego_vehicle)
        rgb_queue_left = queue.Queue()
        rgb_camera_left.listen(rgb_queue_left.put)
        #     cameras['rgb_'+section] = [rgb_camera, rgb_queue]
            
        #     if section != 'fpv':    
        instseg_camera_left = world.spawn_actor(
        blueprint_library.find('sensor.camera.instance_segmentation'),
        carla.Transform(carla.Location(x=float(sensor_config['rgb_left']['x']), z=float(sensor_config['rgb_left']['z'])), carla.Rotation(pitch=float(sensor_config['rgb_left']['pitch']), yaw=float(sensor_config['rgb_left']['yaw']))),
        attach_to=ego_vehicle)

        instseg_queue_left = queue.Queue()
        instseg_camera_left.listen(instseg_queue_left.put)
        
        rgb_camera_right = world.spawn_actor(
            blueprint_library.find('sensor.camera.rgb'),
            carla.Transform(carla.Location(x=float(sensor_config['rgb_right']['x']), z=float(sensor_config['rgb_right']['z']), y=float(sensor_config['rgb_right']['y'])), carla.Rotation(yaw=float(sensor_config['rgb_right']['yaw']))),
            attach_to=ego_vehicle)
        rgb_queue_right = queue.Queue()
        rgb_camera_right.listen(rgb_queue_right.put)
        #     cameras['rgb_'+section] = [rgb_camera, rgb_queue]
            
        #     if section != 'fpv':    
        instseg_camera_right = world.spawn_actor(
        blueprint_library.find('sensor.camera.instance_segmentation'),
        carla.Transform(carla.Location(x=float(sensor_config['rgb_right']['x']), z=float(sensor_config['rgb_right']['z'])), carla.Rotation(yaw=float(sensor_config['rgb_right']['yaw']))),
        attach_to=ego_vehicle)

        instseg_queue_right = queue.Queue()
        instseg_camera_right.listen(instseg_queue_right.put)
        
        

        world.tick()

        replay_started = 0
        replay_done = False
        replay_ctr = 0
        awdf_ctr = 0
        
        if args.out_dir is not None:
            rec_basename = args.out_dir
        else:
            rec_basename = os.path.basename(args.recorder_filename)
            rec_basename = os.path.splitext(rec_basename)[0]
        os.makedirs("%s/images/instance_segmentation_output/" % rec_basename, exist_ok=True)
        os.makedirs("%s/images/instance_segmentation_output_left/" % rec_basename, exist_ok=True)
        os.makedirs("%s/images/instance_segmentation_output_right/" % rec_basename, exist_ok=True)
        
        # while not replay_done:
        #     if not instseg_queue.empty():
        #         image = instseg_queue.get(2.0)
        #         raw_array = np.array(image.raw_data).reshape(image.height, image.width, 4)
        #         cv2.imwrite('%s/images/instance_segmentation_output/%.6d.png' % (filename, ctr + 1), raw_array)
        #     if not rgb_queue.empty():
        #         image = rgb_queue.get(2.0)
        #         image.save_to_disk('%s/images/rgb_output/%.6d.png' % (filename, ctr + 1))

        #     world.tick()
        #     ctr += 1

        #     if ctr > total_replay_frames:
        #         replay_done = True
        #         break
        
        awareness_parse_file = args.awareness_data
        awareness_df = pd.read_json(awareness_parse_file, orient='index')
                
        moving = False
        
        # find position at first move:
        # first_move = False
        # while not first_move:
        #     speed = abs(awareness_df["EgoVariables_VehicleVel"][awdf_ctr])
        #     throttle = abs(awareness_df["UserInputs_Throttle"][awdf_ctr])
        #     aw_loc = np.array(awareness_df["EgoVariables_VehicleLoc"][awdf_ctr])/100
        #     print(speed, throttle, aw_loc)
            
        #     if throttle > 0:
        #         first_move = True
        #         break            
        #     awdf_ctr+=1
        
        # first_valid = False
        print(world.get_settings())
        while not replay_done:
            if not instseg_queue.empty():
                inst_image = instseg_queue.get()
            if not instseg_queue_left.empty():
                inst_image_left = instseg_queue_left.get()
            if not instseg_queue_right.empty():
                inst_image_right = instseg_queue_right.get()
            if not rgb_queue.empty():
                rgb_image = rgb_queue.get()
            if not rgb_queue_left.empty():
                rgb_image_left = rgb_queue_left.get()
            if not rgb_queue_right.empty():
                rgb_image_right = rgb_queue_right.get()
            if not ego_queue.empty():
                ego_sensordata = ego_queue.get()
            if not rgb_queue_fpv.empty():
                rgb_image_fpv = rgb_queue_fpv.get()
                        
            replay_frame = ego_sensordata.timestamp_carla
            awdata_frame = awareness_df["TimestampCarla"][awdf_ctr]
            print(replay_ctr, awdf_ctr, replay_frame, awdata_frame)
            # ego_loc = np.array([ego_vehicle.get_location().x, ego_vehicle.get_location().y, ego_vehicle.get_location().z])
            # aw_loc = np.array(awareness_df["EgoVariables_VehicleLoc"][awdf_ctr])/100
            # valid_frame = np.allclose(ego_loc, aw_loc, atol=0.2)
            # speed = abs(awareness_df["EgoVariables_VehicleVel"][replay_ctr])
            

            if replay_frame < awdata_frame:
                print("ticking replay to catch up")
                while replay_frame < awdata_frame:
                    world.tick()
                    if not instseg_queue.empty():
                        inst_image = instseg_queue.get()
                    if not instseg_queue_left.empty():
                        inst_image_left = instseg_queue_left.get()
                    if not instseg_queue_right.empty():
                        inst_image_right = instseg_queue_right.get()
                    if not rgb_queue.empty():
                        rgb_image = rgb_queue.get()
                    if not rgb_queue_left.empty():
                        rgb_image_left = rgb_queue_left.get()
                    if not rgb_queue_right.empty():
                        rgb_image_right = rgb_queue_right.get()
                    if not rgb_queue_fpv.empty():
                        rgb_image_fpv = rgb_queue_fpv.get()
                    if not ego_queue.empty():
                        ego_sensordata = ego_queue.get()
                    replay_frame = ego_sensordata.timestamp_carla
                    print(replay_frame)                    
                    continue
            elif replay_frame > awdata_frame:                    
                    while replay_frame != awdata_frame:
                        awdf_ctr+=1
                        try:
                            awdata_frame = awareness_df["TimestampCarla"][awdf_ctr]
                        except KeyError:                           
                            replay_done = True
                            break
                        
            # replace this with a save function
            
            print(replay_ctr, awdf_ctr, replay_frame, awdata_frame)
            if replay_frame == awdata_frame: # synced_frame
                # replace this with a save function
                raw_array = np.array(inst_image.raw_data).reshape(inst_image.height, inst_image.width, 4)
                raw_array_left = np.array(inst_image_left.raw_data).reshape(inst_image_left.height, inst_image_left.width, 4)
                raw_array_right = np.array(inst_image_right.raw_data).reshape(inst_image_right.height, inst_image_right.width, 4)
                cv2.imwrite('%s/images/instance_segmentation_output/%.6d.png' % (rec_basename, awdf_ctr), raw_array)                
                cv2.imwrite('%s/images/instance_segmentation_output_left/%.6d.png' % (rec_basename, awdf_ctr), raw_array_left)                
                cv2.imwrite('%s/images/instance_segmentation_output_right/%.6d.png' % (rec_basename, awdf_ctr), raw_array_right)                
                rgb_image.save_to_disk('%s/images/rgb_output/%.6d.png' % (rec_basename, awdf_ctr))
                rgb_image_left.save_to_disk('%s/images/rgb_output_left/%.6d.png' % (rec_basename, awdf_ctr))
                rgb_image_right.save_to_disk('%s/images/rgb_output_right/%.6d.png' % (rec_basename, awdf_ctr))
                rgb_image_fpv.save_to_disk('%s/images/rgb_output_fpv/%.6d.png' % (rec_basename, awdf_ctr))
                # img_count +=1
                awdf_ctr+=1               

            world.tick()
            replay_ctr += 1
            
            if rgb_queue.qsize() > total_replay_frames + num_frames_buffer:
                rgb_camera.stop()
                rgb_camera_left.stop()
                rgb_camera_right.stop()
                rgb_camera_fpv.stop()
                instseg_camera.stop()
                instseg_camera_left.stop()
                instseg_camera_right.stop()
                egosensor.stop()


            if replay_ctr > total_replay_frames:
                replay_done = True
                break
            
        # check if replay has finished
        if replay_done:
            if egosensor:
                egosensor.destroy()
            if instseg_camera:
                instseg_camera.destroy()
            if instseg_camera_right:
                instseg_camera_right.destroy()
            if instseg_camera_left:
                instseg_camera_left.destroy()
            if rgb_camera:
                rgb_camera.destroy()
            if rgb_camera_left:
                rgb_camera_left.destroy()
            if rgb_camera_right:
                rgb_camera_right.destroy()
            if rgb_camera_fpv:
                rgb_camera_fpv.destroy()

            # reset the sim world to async in prep for next replay
            settings = world.get_settings()
            settings.synchronous_mode = False
            settings.fixed_delta_seconds = None
            world.apply_settings(settings)

    finally:
        pass
       

if __name__ == '__main__':

    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print('\ndone.')