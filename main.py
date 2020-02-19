import math
import json

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


def add_camera_points(playlist, circle_points, target, horizontal_fov, leg_duration_sec, loops):
    duration = 0
    count = len(circle_points)
    for i in range(loops):
        for j in range(count):
            duration = 0 if i == 0 and j == 0 else leg_duration_sec
            point = circle_points[j]
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


def generate_klv(name, origin, target, circle_points, output_options, horizontal_fov, leg_duration_sec, loops):
    klv = { 'test': [1, 2, 3] }

    with open(name + '_klv.json', 'w') as output:
        json.dump(klv, output)


def create_tour(name):
    # inputs: # TODO get inputs from command line/file
    target = { 'lat': 32.813580, 'lon': 34.983984, 'alt': 221 }
    origin_offset = { 'az': -90, 'el': 30, 'srange': 1500 }
    circle_steps = 360 # TODO combine options to dictionary
    leg_duration_sec = 0.1
    loops = 1
    horizontal_fov = 5
    output_options = { 'origin': True, 'target': True, 'route': True }

    # calculations
    origin = create_start_point(origin_offset, target)
    circle_center = { 'lat': target['lat'], 'lon': target['lon'], 'alt': origin['alt'] }
    radius_deg = calculate_air_distance_degrees(origin, target)
    circle_points = list(calculate_circle_points(circle_center, radius_deg,
        start_angle=origin_offset['az'], steps=circle_steps))
    
    # output
    generate_kml(name, origin, target, circle_points, output_options,
        horizontal_fov, leg_duration_sec, loops)
    generate_klv(name, origin, target, circle_points, output_options,
        horizontal_fov, leg_duration_sec, loops)


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
