import sys
import time
import openvr
import multiprocessing
import psutil
import getopt

import pylsl as lsl
impoer numpy as np

LINEAR_ACCELERATION_X = 0
LINEAR_ACCELERATION_Y = 1
LINEAR_ACCELERATION_Z = 2
ANGULAR_ACCELERATION_X = 3
ANGULAR_ACCELERATION_Y = 4
ANGULAR_ACCELERATION_Z = 5

channel_count = 6


def start_vr(queue, is_running, framerate=60.):  # defaults at 120 frames per second
    openvr.init(openvr.VRApplication_Background)
    pose = []
    start = time.time()
    while is_running.value:
        prev_pose = pose
        frame_duration = 1./framerate
        prev_time = start
        start = time.time()
        pose = openvr.VRSystem().getDeviceToAbsoluteTrackingPose(
            origin=openvr.TrackingUniverseStanding,
            predictedSecondsToPhotonsFromNow=0,
            trackedDevicePoseArray=pose
        )[0]

        if not prev_pose:
            time.sleep(frame_duration)
            continue
        pre_list = time.time()
        acceleration = [(ai - bi)/(start - prev_time) for ai, bi in zip(prev_pose.vVelocity, pose.vVelocity)]
        acceleration_angular = [
            (ai - bi)*(start - prev_time)
            for ai, bi in
            zip(prev_pose.vAngularVelocity, pose.vAngularVelocity)
        ]
        list_time = time.time()-pre_list
        pre_sleep = time.time()
        # time.sleep(frame_duration-list_time)
        while time.time()-pre_sleep < frame_duration-list_time:
            continue
        # print('time used: {} time expected to use: {}'.format(
        #     time.time()-pre_sleep,
        #     frame_duration))
        # print('acceleration: {} angular acceleration: {}'.format(print_list(acceleration),
        #                                                          print_list(acceleration_angular)))
        queue.put((acceleration, acceleration_angular),)
    print('Ended openvr extraction')


def print_list(arr):
    return ['{:.2f}'.format(item) for item in arr]


if __name__ == '__main__':
    multiprocessing.set_start_method('spawn')
    queue_ = multiprocessing.Queue()
    isRunning = multiprocessing.Value('B', True)
    process = None
    try:
        print('Press Ctrl-C to end process')
        frameRate = 60
        batchSize = 1
        help_string = 'main.py -f <frame_rate> -b <batch_size>'
        try:
            opts, args = getopt.getopt(sys.argv[1:], "f:b:",longopts=['frame_rate=', "batch_size="])
        except getopt.GetoptError:
            print(help_string)
            sys.exit(-1)
        for opt, arg in opts:
            if opt in ('-f', '--frame_rate'):
                try:
                    frameRate = float(arg)
                except ValueError:
                    print('ERROR: Frame rate must be a number')
                    print(arg)
                    exit(-2)
            elif opt in ('-b', '--batch_size'):
                try:
                    batchSize = int(arg)
                except ValueError:
                    print('ERROR: Batch size must be an integer')
                    exit(-3)

        print('Using a framerate of {} fps and batch size of {} samples per lsl package'.format(frameRate, batchSize))

        process = multiprocessing.Process(target=start_vr, args=(queue_, isRunning, frameRate))
        process.start()
        psutil.Process(process.pid).nice(psutil.HIGH_PRIORITY_CLASS)
        # Starting LabStreamLayer collecting
        lsl_info = {
            'name': 'openVR-acceleration+angular-acceleration',
            'type': 'hmd-acceleration',
            'channel_count': channel_count,
            'nominal_srate': frameRate,
            'channel_format': lsl.cf_float32,
            'source_id': 'HTC Vive Pro Eye'  # Change this to either random number or a set run id
        }
        dataBuffer = np.zeros((batchSize, channel_count))
        stream = lsl.stream_info(
            name=lsl_info['name'],
            type=lsl_info['type'],
            channel_count=lsl_info['channel_count'],
            nominal_srate=lsl_info['nominal_srate'],
            channel_format=lsl_info['channel_format'],
            source_id=lsl_info['source_id']
        )
        outlet = lsl.stream_outlet(stream)
        stream_start = lsl.local_clock()
        sent_samples = 0
        batch = 0
        while True:
            elapsed_time = lsl.local_clock()-stream_start
            required_samples = int(frameRate*elapsed_time)-sent_samples
            if batchSize == 1:  # sample wise transmission
                for _ in range(required_samples):
                    sample = queue_.get()
                    sample[0].extend(sample[1])
                    outlet.push_sample(sample[0])

            else:  # Chuck wise transmission
                for _ in range(required_samples):
                    sample = queue_.get()
                    sample[0].extend(sample[1])
                    dataBuffer[batch] = sample[0]
                    batch += 1

                    if batchSize == batch:
                        batch = 0
                        outlet.push_chunk(dataBuffer)
            # time.sleep(0.01)
            sent_samples += required_samples
    except KeyboardInterrupt:
        print('Ending main process')
        isRunning.value = False
        process.join(1)
        openvr.shutdown()
