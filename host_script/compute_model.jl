# using Pkg
# Pkg.add("JSON")
# Pkg.add("StaticArrays")

using LinearAlgebra
using Base.Threads
using JSON
using StaticArrays
using StatsBase
using Plots; pyplot()
# using Profile

const Vector3 = SVector{3, Float64}

function magnitude_vec(v::Vector3)::Float64
    return sqrt(v[1]*v[1] + v[2]*v[2] + v[3]*v[3])
end

function normalize_vec(v::Vector3)::Float64
    mag = magnitude_vec(v)
    return Vector3(v[1] / mag, v[2] / mag, v[3] / mag)
end

function line_sphere_intersection(line_origin::Vector3, line_slope_unit::Vector3, sphere_origin::Vector3, sphere_radius::Float64)::Float64
    origin_diff = line_origin - sphere_origin
    ls_dot_ordiff = dot(line_slope_unit, origin_diff)
    grad = (ls_dot_ordiff^2) - (magnitude_vec(origin_diff)^2 - sphere_radius^2)

    if grad < 0
        return NaN64
    end
    root_grad = sqrt(grad)
    if grad == 0
        return -ls_dot_ordiff + root_grad
    end
    return min(-ls_dot_ordiff + root_grad, -ls_dot_ordiff - root_grad)
end

function line_direction_from_angle(angleR::Float64, angleTheda::Float64)::Vector3
    angleR = deg2rad(angleR)
    angleTheda = deg2rad(angleTheda)
    z = cos(angleR)
    unitrad = sin(angleR)
    x = unitrad*cos(angleTheda)
    y = unitrad*sin(angleTheda)
    return Vector3(x, y, z)
end

function find_line_at_z_intersect(line_origin::Vector3, line_slope_unit::Vector3, z::Float64)
    return abs(z - line_origin[3]) / line_slope_unit[3]
end

function area_of_intersecting_circles(rad_1::Float64, rad_2::Float64, center_dist::Float64)::Float64
    if center_dist <= max(rad_1, rad_2) - min(rad_1, rad_2)
        return pi * min(rad_1, rad_2)^2
    end

    if center_dist == rad_1 + rad_2
        return 0
    end

    if center_dist > rad_1 + rad_2
        return NaN64
    end

    part_1 = (rad_1^2) * acos((center_dist^2 + rad_1^2 - rad_2^2) / (2 * center_dist * rad_1))
    part_2 = (rad_2^2) * acos((center_dist^2 + rad_2^2 - rad_1^2) / (2 * center_dist * rad_2))
    part_3 = 0.5 * sqrt((-center_dist + rad_1 + rad_2) * (center_dist + rad_1 - rad_2) * (center_dist - rad_1 + rad_2) * (center_dist + rad_1 + rad_1))
    return part_1 + part_2 - part_3
end

function calc_per_apple_in_fov(apple_pos::Vector3, fov_rad::Float64, apple_rad::Float64)::Float64
    fov_at_apple_rad = apple_pos[3]*tan(fov_rad / 2)
    area_apple_in_fov = area_of_intersecting_circles(apple_rad, fov_at_apple_rad, sqrt(apple_pos[1]^2 + apple_pos[2]^2))
    if isnan(area_apple_in_fov)
        return 0
    end
    return clamp(area_apple_in_fov / (pi * fov_at_apple_rad^2), 0, 1)
end

function precompute_line_directions(sensor_fov::Float64, integrate_step::Float64)::Matrix{Vector3}
    # angleR major
    rdim, tdim = floor(Int, sensor_fov / 2 / integrate_step), floor(Int, 360 / integrate_step)
    out = zeros(Vector3, (rdim, tdim))

    for r_i = 1:rdim, t_i = 1:tdim
        r_v, t_v = r_i * integrate_step, t_i * integrate_step
        out[r_i, t_i] = line_direction_from_angle(r_v, t_v)
    end

    return out
end

function area_scan_model(sphere_origin::Vector3, sphere_rad::Float64, backdrop_z::Float64, sensor_origin::Vector3, sensor_directions::Matrix{Vector3}, weight_factor::Float64)::Float64
    computed_mes = zeros(Float64, (size(sensor_directions, 1) * size(sensor_directions, 2)))
    idx = 1
    for r = 1:size(sensor_directions, 1), t = 1:size(sensor_directions, 2)
        dir_vect = sensor_directions[r, t]
        intersect = line_sphere_intersection(sensor_origin, dir_vect, sphere_origin, sphere_rad)

        if isnan(intersect)
            # hit the backdrop
            computed_mes[idx] = find_line_at_z_intersect(sensor_origin, dir_vect, backdrop_z)
        else
            # take the intersection earliest on the line
            computed_mes[idx] = intersect
        end
        idx += 1
    end

    return sum(computed_mes) / length(computed_mes)

    # sort!(computed_mes, rev=true)
    # sort!(computed_mes, rev=true)
    # half_len = length(computed_mes) ÷ 2
    # return sum(computed_mes[1:half_len]) / half_len
    # half_len = length(computed_mes) ÷ 2
    # return sum(computed_mes[1:half_len]) / half_len
end

function simplified_model(sphere_origin::Vector3, sphere_rad::Float64, sensor_fov_rad::Float64, backdrop_z::Float64, sensor_origin::Vector3)::Float64
    # calculate the percantage of the FOV which contains apple
    apple_pos = sphere_origin - sensor_origin - Vector3(0, 0, sphere_rad)
    per_apple_in_fov = calc_per_apple_in_fov(apple_pos, sensor_fov_rad, sphere_rad)

    # print(f'Apple fov: {per_apple_in_fov*100:.2f}%')
    # > 80% means the apple is basically correct
    if per_apple_in_fov >= 0.8
        return apple_pos[3]

    # < 80% means we get a linear interpolation between the apples center
    # and the backdrop
    elseif per_apple_in_fov > 0
        per_blur = .8 - per_apple_in_fov
        return apple_pos[3]*(1 - per_blur) + backdrop_z*per_blur
    
    # 0% means direct backdrop, bit of a discontinuity but oh well
    else
        return backdrop_z
    end
end


const FOV_DEG = 25.0
const SCAN_WH = 160.0
const SCAN_STEP = 4.0
const SPHERE_R = 40.0
const CLOSE_WGT = .1

function run_model(sphere_offset, backdrop_offset)
    x = 0:SCAN_STEP:SCAN_WH
    sphere_origin = Vector3(SCAN_WH/2, SCAN_WH/2, sphere_offset)

    precomputed_sensor_directions = precompute_line_directions(FOV_DEG, 0.1)

    z = zeros(Float64, (length(x), length(x)))
    iter = [(x_i, x_p, y_i, y_p) for (x_i, x_p) = enumerate(x), (y_i, y_p) = enumerate(x)]
    @threads for (x_i, x_p, y_i, y_p) in iter
        z[x_i, y_i] = area_scan_model(sphere_origin, SPHERE_R, backdrop_offset, Vector3(x_p, y_p, 0), precomputed_sensor_directions, CLOSE_WGT)
    end

    return z
end

function run_simplified_model(sphere_offset, backdrop_offset)
    x = 0:SCAN_STEP:SCAN_WH
    sphere_origin = Vector3(SCAN_WH/2, SCAN_WH/2, sphere_offset)

    z = zeros(Float64, (length(x), length(x)))
    iter = [(x_i, x_p, y_i, y_p) for (x_i, x_p) = enumerate(x), (y_i, y_p) = enumerate(x)]
    @threads for (x_i, x_p, y_i, y_p) in iter
        z[x_i, y_i] = simplified_model(sphere_origin, SPHERE_R, deg2rad(FOV_DEG), backdrop_offset, Vector3(x_p, y_p, 0))
    end

    return z
end

function main()
    println("Start!")

    x = 0:SCAN_STEP:SCAN_WH
    # zclose = run_simplified_model(150.0 + SPHERE_R, 400.0)
    zfar = run_simplified_model(150.0 + SPHERE_R, 1000.0)

    text = JSON.json(zfar)
    out = open("outjson.json", "w")
    println(out, text)
    close(out)

    # display(plot(x, x, zclose, st=:surface, camera=(-30, 30)))
    # display(plot(x, x, zfar, st=:surface, camera=(-30, 30)))
    # gui()
end

# outfd1 = open("profileout.txt", "w")
# outfd2 = open("profileoutflat.txt", "w")
# Profile.print(outfd1, format=:flat)
# Profile.print(outfd2)
# close(outfd1)
# close(outfd2)

main()