import copy


klv_frame_template = {
    "pid": 498,
    "pts": 22272185,
    "crc": "aecc",
    "precision_time_stamp": "2018-04-16T14:37:02.927Z",
    "platform_tail_number": "252",
    "platform_heading_angle": 296.6628519111925,
    "platform_pitch_angle": -1.054719687490463,
    "platform_roll_angle": 3.6912137211218603,
    "platform_indicated_airspeed": 33,
    "image_source_sensor": "EO",
    "image_coordinate_system": "WGS-84",
    "sensor_latitude": 32.50152597320337,
    "sensor_longitude": 35.0476475409454,
    "sensor_true_altitude": 3104.899671931029,
    "sensor_horizontal_field_of_view": 2.422522316319524,
    "sensor_vertical_field_of_view": 1.3705653467612726,
    "sensor_relative_azimuth_angle": 334.1431726641355,
    "sensor_relative_elevation_angle": -13.002721924801694,
    "sensor_relative_roll_angle": 0,
    "slant_range": 13024.000221170485,
    "target_width": 571.9081406881819,
    "frame_center_latitude": 32.501432431163934,
    "frame_center_longitude": 34.896046405144055,
    "frame_center_elevation": 10.05264362554351,
    "offset_corner_latitude_point_1": -0.0029068880275887323,
    "offset_corner_longitude_point_1": -0.009958952604754785,
    "offset_corner_latitude_point_2": 0.0030945768608661153,
    "offset_corner_longitude_point_2": -0.009716330454420606,
    "offset_corner_latitude_point_3": 0.002595599230933561,
    "offset_corner_longitude_point_3": 0.00890606402783288,
    "offset_corner_latitude_point_4": -0.0027352214117862482,
    "offset_corner_longitude_point_4": 0.009070863979003266,
    "wind_direction": 0,
    "wind_speed": 0,
    "outside_air_temperature": 10,
    "security_local_set": "01010102010403022F2F0C0102160204B5",
    "airfield_elevation": 3043.5614557106887,
    "platform_ground_speed": 0,
    "version_number": 11,
    "target_error_estimate-ce90": 0,
    "checksum": "AECC",
    "sensor_geoid_height": 22.01858488721831,
    "frame_center_geoid_height": 21.8022942795335
}


def get_klv_frame():
    return copy.copy(klv_frame_template)
