import math
import json
from datetime import datetime, timedelta

import simplekml
import pymap3d

from klv_frame import get_klv_frame

# target: lat, lon, alt
# route mode: manual route or circle
# - manual route is simpler but requires to create one, recalculate geodetic2aer on every point
# start point
# - lat, lon, alt
# - az, el, srange
# circle: total loop time, steps, radius (only if input is LLA), loops
# steps:
# - generate start point if needed (input is az, el, srange)
#   - calculate air distance as radius
# - else: calculate center point of circle (using start angle, lat, lon and radius)
# - calculate circle points
# - for each point
#   - calculate azimuth, elevation, roll=0 from point to target
# - create tour file including target pinpoint (text = target position)
# MVP: circle + az/el/srange input

# TODO refactor to files


def create_start_point(origin_offset, target):
    point = pymap3d.aer2geodetic(origin_offset['az'], origin_offset['el'], origin_offset['srange'],
        target['lat'], target['lon'], target['alt'])
    return { 'lat': point[0], 'lon': point[1], 'alt': point[2] }


def calculate_aer(origin, target):
    aer = pymap3d.geodetic2aer(target['lat'], target['lon'], target['alt'],
        origin['lat'], origin['lon'], origin['alt'])
    return { 'az': aer[0], 'el': aer[1], 'srange': aer[2] }


def calculate_air_distance_meters(origin, target):
    alt = origin['alt']
    aer = pymap3d.geodetic2aer(origin['lat'], origin['lon'], alt,
        target['lat'], target['lon'], alt)
    distance = aer[2]
    return distance


def calculate_air_distance_degrees(origin, target):
    lat_factor = math.pow(origin['lat'] - target['lat'], 2)
    lon_factor = math.pow(origin['lon'] - target['lon'], 2)
    distance = math.sqrt(lat_factor + lon_factor)
    return distance


def calculate_circle_points(center, radius_deg, steps=360, start_angle=0):
    step_size = 360 / steps
    alt = center['alt']
    for i in range(steps):
        angle_deg = (start_angle + (i * step_size))
        angle_rad = math.radians(angle_deg)
        lon = center['lon'] + (radius_deg * math.sin(angle_rad))
        lat = center['lat'] + (radius_deg * math.cos(angle_rad))
        yield { 'lat': lat, 'lon': lon, 'alt': alt }


def generate_coords(points):
    for point in points:
        yield (point['lon'], point['lat'], point['alt'])


def add_camera_point(point, target, horizontal_fov, playlist, duration):
    aer = calculate_aer(point, target)
    
    flyto = playlist.newgxflyto(gxduration=duration)
    flyto.gxflytomode = 'smooth'
    flyto.camera.longitude = point['lon']
    flyto.camera.latitude = point['lat']
    flyto.camera.altitude = point['alt']
    flyto.camera.altitudemode = 'absolute'
    flyto.camera.heading = aer['az']
    flyto.camera.tilt = aer['el'] + 90 # from [-90,90] to [0,180]
    flyto.camera.roll = 0
    flyto.camera.gxhorizfov = horizontal_fov


def calculate_geo_point(point, az, el, srange):
    target = pymap3d.aer2geodetic(az, el, srange,
        point['lat'], point['lon'], point['alt'])
    return { 'lat': target[0], 'lon': target[1], 'alt': target[2] }


def generate_klv_frame(point, target, next_point, horizontal_fov, time, base_time, video_ratio):
    base_pts = 126000
    timestamp = base_time + timedelta(seconds=time)
    aer_next = calculate_aer(point, next_point)
    aer_target = calculate_aer(point, target)

    vertical_fov = horizontal_fov / video_ratio
    half_hfov = horizontal_fov / 2
    half_vfov = vertical_fov / 2
    point1 = calculate_geo_point(point, aer_target['az'] + half_hfov, aer_target['el'] + half_vfov, aer_target['srange'])
    point2 = calculate_geo_point(point, aer_target['az'] - half_hfov, aer_target['el'] + half_vfov, aer_target['srange'])
    point3 = calculate_geo_point(point, aer_target['az'] - half_hfov, aer_target['el'] - half_vfov, aer_target['srange'])
    point4 = calculate_geo_point(point, aer_target['az'] + half_hfov, aer_target['el'] - half_vfov, aer_target['srange'])

    frame = get_klv_frame()
    frame['pts'] = base_pts + (time * 90000) # 90khz clock
    frame['precision_time_stamp'] = timestamp.isoformat()
    frame['platform_heading_angle'] = aer_next['az']
    frame['platform_pitch_angle'] = 0
    frame['platform_roll_angle'] = 0
    frame['sensor_latitude'] = point['lat']
    frame['sensor_longitude'] = point['lon']
    frame['sensor_true_altitude'] = point['alt']
    frame['sensor_horizontal_field_of_view'] = horizontal_fov
    frame['sensor_vertical_field_of_view'] = vertical_fov
    frame['sensor_relative_azimuth_angle'] = aer_target['az'] - aer_next['az'] # TODO validate!
    frame['sensor_relative_elevation_angle'] = aer_target['el']
    frame['sensor_relative_roll_angle'] = 0
    frame['slant_range'] = aer_target['srange']
    frame['frame_center_latitude'] = target['lat']
    frame['frame_center_longitude'] = target['lon']
    frame['frame_center_elevation'] = target['alt']
    frame['offset_corner_latitude_point_1'] = target['lat'] - point1['lat']
    frame['offset_corner_longitude_point_1'] = target['lon'] - point1['lon']
    frame['offset_corner_latitude_point_2'] = target['lat'] - point2['lat']
    frame['offset_corner_longitude_point_2'] = target['lon'] - point2['lon']
    frame['offset_corner_latitude_point_3'] = target['lat'] - point3['lat']
    frame['offset_corner_longitude_point_3'] = target['lon'] - point3['lon']
    frame['offset_corner_latitude_point_4'] = target['lat'] - point4['lat']
    frame['offset_corner_longitude_point_4'] = target['lon'] - point4['lon']
    frame['sensor_geoid_height'] = 0
    frame['frame_center_geoid_height'] = 0
    return frame


def add_camera_points(playlist, circle_points, target, horizontal_fov, leg_duration_sec, loops):
    duration = 0
    for i in range(loops):
        for j, point in enumerate(circle_points):
            duration = 0 if i == 0 and j == 0 else leg_duration_sec
            add_camera_point(point, target, horizontal_fov, playlist, duration)
    add_camera_point(circle_points[0], target, horizontal_fov, playlist, leg_duration_sec) # close the loop


def generate_kml(name, origin, target, circle_points, output_options, horizontal_fov, leg_duration_sec, loops):
    kml = simplekml.Kml(name=name, open=1)
    tour = kml.newgxtour(name=name)
    playlist = tour.newgxplaylist()

    if output_options['target']:
        kml.newpoint(name=f"target(alt={target['alt']})", altitudemode='absolute', coords=[(target['lon'], target['lat'], target['alt'])])
    if output_options['origin']:
        kml.newpoint(name="origin", altitudemode='absolute', coords=[(origin['lon'], origin['lat'], origin['alt'])])
    if output_options['route']:
        route_points = circle_points + [circle_points[0]] # close route
        kml.newlinestring(name='route', altitudemode='absolute', coords=list(generate_coords(route_points)))
    
    add_camera_points(playlist, circle_points, target, horizontal_fov, leg_duration_sec, loops)

    kml.save(name + '.kml')


def generate_klv(name, origin, target, circle_points, output_options, 
    horizontal_fov, leg_duration_sec, loops, base_time, video_ratio):
    klv = []

    count = len(circle_points)
    time = 0
    for i in range(loops):
        for j, point in enumerate(circle_points):
            time = ((i * count) + j) * leg_duration_sec
            next_point = circle_points[(j + 1) % count]
            klv_frame = generate_klv_frame(point, target, next_point,
                horizontal_fov, time, base_time, video_ratio)
            klv.append(klv_frame)
    
    # close the circle
    time = loops * count * leg_duration_sec
    klv_frame = generate_klv_frame(circle_points[0], target, circle_points[1],
        horizontal_fov, time, base_time, video_ratio)
    klv.append(klv_frame)

    with open(name + '_klv.json', 'w') as output:
        json.dump(klv, output)


def create_tour(name):
    # inputs: # TODO get inputs from command line/file
    target = { 'lat': 32.813580, 'lon': 34.983984, 'alt': 221 }
    origin_offset = { 'az': -90, 'el': 30, 'srange': 1500 }
    circle_steps = 360 # TODO combine options to dictionary
    leg_duration_sec = 0.1
    loops = 2
    horizontal_fov = 5
    output_options = { 'origin': True, 'target': True, 'route': True, 'kml': True, 'klv': True }
    base_time = datetime(2020, 2, 19, 10, 0, 0)
    video_ratio = 4.0 / 3

    # calculations
    origin = create_start_point(origin_offset, target)
    circle_center = { 'lat': target['lat'], 'lon': target['lon'], 'alt': origin['alt'] }
    radius_deg = calculate_air_distance_degrees(origin, target)
    circle_points = list(calculate_circle_points(circle_center, radius_deg,
        start_angle=origin_offset['az'], steps=circle_steps))
    
    # output
    if output_options['kml']:
        generate_kml(name, origin, target, circle_points, output_options,
            horizontal_fov, leg_duration_sec, loops)
    if output_options['klv']:
        generate_klv(name, origin, target, circle_points, output_options,
            horizontal_fov, leg_duration_sec, loops, base_time, video_ratio)


def create_line_tour(name):
    kml = simplekml.Kml(name=name, open=1)
    tour = kml.newgxtour(name=name)
    playlist = tour.newgxplaylist()

    for i in range(5):
        duration = 0 if i == 0 else 2
        flyto = playlist.newgxflyto(gxduration=duration)
        flyto.gxflytomode = 'smooth'
        flyto.camera.longitude = 35.7
        flyto.camera.latitude = 32.4 + (i * 0.001)
        flyto.camera.altitude = 1500
        flyto.camera.altitudemode = 'absolute'
        flyto.camera.heading = 0
        flyto.camera.tilt = 33.5
        flyto.camera.roll = 0
        # playlist.newgxwait(gxduration=0)

    kml.save(name + '.kml')


def create_test_tour(output_path = 'test.kml'):
    kml = simplekml.Kml(name='9_tours', open=1)

    pnt = kml.newpoint(name="New Zealand's Southern Alps", coords=[(170.144,-43.605)])
    pnt.style.iconstyle.scale = 1.0

    tour = kml.newgxtour(name="Play me!")
    playlist = tour.newgxplaylist()

    soundcue = playlist.newgxsoundcue()
    soundcue.href = "http://code.google.com/p/simplekml/source/browse/samples/drum_roll_1.wav"
    soundcue.gxdelayedstart = 2

    animatedupdate = playlist.newgxanimatedupdate(gxduration=6.5)
    animatedupdate.update.change = '<IconStyle targetId="{0}"><scale>10.0</scale></IconStyle>'.format(pnt.style.iconstyle.id)

    flyto = playlist.newgxflyto(gxduration=4.1)
    flyto.camera.longitude = 170.157
    flyto.camera.latitude = -43.671
    flyto.camera.altitude = 9700
    flyto.camera.heading = -6.333
    flyto.camera.tilt = 33.5
    flyto.camera.roll = 0

    wait = playlist.newgxwait(gxduration=2.4)

    kml.save(output_path)

if __name__ == '__main__':
    create_tour(name='test2')
