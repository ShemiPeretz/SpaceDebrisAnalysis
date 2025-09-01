import numpy as np

from sgp4 import api
from sgp4.conveniences import sat_epoch_datetime

import matplotlib.pyplot as plt
import plotly.graph_objects as go


# TLE
nm = '2023-132A     '
l1 = '1 57754U 23132A   23245.65206230 -.00000128  00000+0  00000+0 0  9999'
l2 = '2 57754  19.2862  21.4741 5934257 346.7698 165.0186  4.18358561    14'


# get satellite info
def get_satellite(l1, l2, print_info=True):
    global mu, r, a
    satellite = api.Satrec.twoline2rv(l1, l2, api.WGS72)

    # constants
    mu = satellite.mu  # Earth's gravitational parameter (km³/s²)
    r = satellite.radiusearthkm  # Radius of the earth (km).
    # orbital parameters
    a = satellite.a * r
    # Altitude of the satellite at perigee
    peri = satellite.altp * r
    # Altitude of the satellite at apogee
    apo = satellite.alta * r

    if print_info:
        print('a X e        : ', round(apo, 3), round(peri, 3))
        # Inclination
        i_deg = np.degrees(satellite.inclo)
        print('Inclination  : ', i_deg)
        # Eccentricity
        e = satellite.ecco
        print('Eccentricity : ', e)
        epoch = sat_epoch_datetime(satellite)
        print('Epoch        : ', epoch)
    else:
        epoch = sat_epoch_datetime(satellite)

    return satellite, epoch

# propagation starts at epoch and ends at full orbit time period
# function returns an array of datetime from start to end
def get_propagation_times(epoch, satellite):
    # DeprecationWarning: parsing timezone aware datetimes is deprecated;
    epoch = epoch.replace(tzinfo=None)

    # Epoch (start time)
    start = np.datetime64(epoch)

    # Period (end time)
    sat_a = satellite.a * r
    t = 2 * np.pi * (sat_a ** 3 / mu) ** 0.5
    # end time for full orbit
    end = t

    # time steps
    dt = 100

    # create time array
    time_end = np.arange(0.0, end, dt)
    time_arr = start + time_end.astype('timedelta64[s]')
    #
    return time_arr


# return state vectors for each datetime in the time array
def get_state_vectors(satellite, time_arr):
    position = [];
    velocity = [];
    for j in time_arr.tolist():
        jd, fr = api.jday(j.year, j.month, j.day, j.hour, j.minute, j.second)
        e, p, v = satellite.sgp4(jd, fr)
        if e == 0:
            position.append(p);
            velocity.append(v)
        else:
            print(p);
            print(v)

    # slice into columns
    pos, vel = list(zip(*position)), list(zip(*velocity))
    X, Y, Z = np.array(pos[0]), np.array(pos[1]), np.array(pos[2])
    VX, VY, VZ = np.array(vel[0]), np.array(vel[1]), np.array(vel[2])
    state_vectors = [X, Y, Z, VX, VY, VZ]
    #
    return state_vectors


# plot
# Set 3D plot axes to equal scale.
# Required since `ax.axis('equal')` and `ax.set_aspect('equal')` don't work on 3D.
def set_axes_equal_3d(ax: plt.Axes):
    """
    https://stackoverflow.com/questions/13685386/matplotlib-equal-unit-length-with-equal-aspect-ratio-z-axis-is-not-equal-to
    """

    # set axis limits
    def _set_axes_radius(ax, origin, radius):
        x, y, z = origin
        ax.set_xlim3d([x - radius, x + radius])
        ax.set_ylim3d([y - radius, y + radius])
        ax.set_zlim3d([z - radius, z + radius])
        return

    limits = np.array([
        ax.get_xlim3d(),
        ax.get_ylim3d(),
        ax.get_zlim3d(),
    ])
    origin = np.mean(limits, axis=1)
    radius = 0.5 * np.max(np.abs(limits[:, 1] - limits[:, 0]))
    _set_axes_radius(ax, origin, radius)
    return


# plot orbit
def plot_xyz(state_vectors, r):
    global fig, ax, orbit, satellite
    global X, Y, Z

    X, Y, Z = state_vectors[0], state_vectors[1], state_vectors[2]

    fig = plt.figure()
    # ax = plt3.Axes3D(fig)
    ax = plt.axes(projection='3d')
    # ax.set_facecolor('black')

    # set labels
    ax.set_xlabel('X axis')
    ax.set_ylabel('Y axis')
    ax.set_zlabel('Z axis')

    # set correct aspect ratio
    ax.set_box_aspect([1, 1, 1])
    set_axes_equal_3d(ax)
    # set view
    azm = 150;
    ele = 36;  # 39
    ax.view_init(elev=ele, azim=azm)
    # set limit
    size = 1.0
    # limit = max(max(X[0]), max(Y[0]), max(Z[0]))
    limit = max(max(X), max(Y), max(Z))
    ax.set_xlim(size * limit, -size * limit)
    ax.set_ylim(size * limit, -size * limit)
    ax.set_zlim(size * limit, -size * limit)

    # earth
    ax.scatter(0, 0, 0, marker='o', c='deepskyblue', s=r, alpha=0.5)

    # plot()
    orbit = ax.plot(X, Y, Z, linewidth=0.9, linestyle='dashed', c='k')

    # show
    plt.show()

    # finish
    return


# NEW: plot two orbits for comparison
def plot_xyz_dual(state_vectors1, state_vectors2, r, sat1_name="Satellite 1", sat2_name="Satellite 2"):
    """
    Plot two satellite orbits on the same 3D plot for comparison

    Parameters:
    state_vectors1: State vectors for first satellite [X, Y, Z, VX, VY, VZ]
    state_vectors2: State vectors for second satellite [X, Y, Z, VX, VY, VZ]
    r: Earth radius for scaling
    sat1_name: Name/label for first satellite
    sat2_name: Name/label for second satellite
    """

    X1, Y1, Z1 = state_vectors1[0], state_vectors1[1], state_vectors1[2]
    X2, Y2, Z2 = state_vectors2[0], state_vectors2[1], state_vectors2[2]

    fig = plt.figure(figsize=(12, 8))
    ax = plt.axes(projection='3d')

    # set labels
    ax.set_xlabel('X axis (km)')
    ax.set_ylabel('Y axis (km)')
    ax.set_zlabel('Z axis (km)')
    ax.set_title('Satellite Orbit Comparison')

    # set correct aspect ratio
    ax.set_box_aspect([1, 1, 1])

    # calculate limits based on both orbits
    all_x = np.concatenate([X1, X2])
    all_y = np.concatenate([Y1, Y2])
    all_z = np.concatenate([Z1, Z2])

    size = 1.1  # slightly larger for better visibility
    limit = max(max(abs(all_x)), max(abs(all_y)), max(abs(all_z)))
    # ax.set_xlim(-size * limit, size * limit)
    # ax.set_ylim(-size * limit, size * limit)
    # ax.set_zlim(-size * limit, size * limit)
    #
    ax.set_xlim(0, 6000)
    ax.set_ylim(-6000, 0)
    ax.set_zlim(-2000, 6000)



    set_axes_equal_3d(ax)

    # set view
    azm = 150
    ele = 36
    ax.view_init(elev=ele, azim=azm)

    # earth
    ax.scatter(0, 0, 0, marker='o', c='deepskyblue', s=r / 10, alpha=0.7, label='Earth')

    # plot both orbits with different colors and styles
    orbit1 = ax.plot(X1, Y1, Z1, linewidth=1.5, linestyle='-', c='red', label=sat1_name, alpha=0.8)
    orbit2 = ax.plot(X2, Y2, Z2, linewidth=1.5, linestyle='--', c='blue', label=sat2_name, alpha=0.8)

    # mark starting positions
    ax.scatter(X1[0], Y1[0], Z1[0], marker='o', c='red', s=50, alpha=1.0)
    ax.scatter(X2[0], Y2[0], Z2[0], marker='s', c='blue', s=50, alpha=1.0)

    # add legend
    ax.legend(loc='upper right')

    # show
    plt.show()

    return fig, ax


def plot_xyz_dual_plotly(state_vectors1, state_vectors2, r, sat1_name="Satellite 1", sat2_name="Satellite 2"):
    """
    Plot two satellite orbits on the same interactive 3D plot using Plotly.

    Parameters:
    state_vectors1: State vectors for the first satellite [X, Y, Z, VX, VY, VZ]
    state_vectors2: State vectors for the second satellite [X, Y, Z, VX, VY, VZ]
    r: Earth radius for scaling
    sat1_name: Name/label for the first satellite
    sat2_name: Name/label for the second satellite
    """
    X1, Y1, Z1 = state_vectors1[0], state_vectors1[1], state_vectors1[2]
    X2, Y2, Z2 = state_vectors2[0], state_vectors2[1], state_vectors2[2]

    # Initialize a Plotly Figure
    fig = go.Figure()

    # Add Satellite 1 Orbit Trace
    fig.add_trace(go.Scatter3d(
        x=X1, y=Y1, z=Z1,
        mode='lines',
        line=dict(color='red', width=4),
        name=sat1_name
    ))

    # Add Satellite 2 Orbit Trace
    fig.add_trace(go.Scatter3d(
        x=X2, y=Y2, z=Z2,
        mode='lines',
        line=dict(color='blue', width=4, dash='dash'),
        name=sat2_name
    ))

    # Add start position markers
    fig.add_trace(go.Scatter3d(
        x=[X1[0]], y=[Y1[0]], z=[Z1[0]],
        mode='markers',
        marker=dict(color='red', size=6, symbol='circle'),
        name=f'{sat1_name} Start'
    ))
    fig.add_trace(go.Scatter3d(
        x=[X2[0]], y=[Y2[0]], z=[Z2[0]],
        mode='markers',
        marker=dict(color='blue', size=6, symbol='square'),
        name=f'{sat2_name} Start'
    ))

    # Create a sphere for the Earth 🌍
    u, v = np.mgrid[0:2 * np.pi:100j, 0:np.pi:50j]
    x_earth = r * np.cos(u) * np.sin(v)
    y_earth = r * np.sin(u) * np.sin(v)
    z_earth = r * np.cos(v)
    fig.add_trace(go.Surface(
        x=x_earth, y=y_earth, z=z_earth,
        colorscale=[[0, 'deepskyblue'], [1, 'deepskyblue']],  # Single color
        showscale=False,
        name='Earth',
        opacity=0.7
    ))

    # Update the layout for a clean look
    fig.update_layout(
        title_text='Interactive Satellite Orbit Comparison',
        scene=dict(
            xaxis_title='X axis (km)',
            yaxis_title='Y axis (km)',
            zaxis_title='Z axis (km)',
            aspectmode='data'  # This is CRUCIAL for a 1:1:1 aspect ratio
        ),
        margin=dict(l=0, r=0, b=0, t=40),  # Reduce margins
        legend=dict(yanchor="top", y=0.9, xanchor="left", x=0.05)
    )

    # Show the interactive plot
    fig.show()


# NEW: method to compare two TLEs
def compare_orbits(l1_sat1, l2_sat1, l1_sat2, l2_sat2, sat1_name="Satellite 1", sat2_name="Satellite 2"):
    """
    Compare two satellites by plotting their orbits on the same 3D plot

    Parameters:
    l1_sat1, l2_sat1: TLE lines for first satellite
    l1_sat2, l2_sat2: TLE lines for second satellite
    sat1_name: Name/label for first satellite
    sat2_name: Name/label for second satellite
    """

    print(f"=== {sat1_name} ===")
    satellite1, epoch1 = get_satellite(l1_sat1, l2_sat1, print_info=True)

    print(f"\n=== {sat2_name} ===")
    satellite2, epoch2 = get_satellite(l1_sat2, l2_sat2, print_info=True)

    # Get propagation times for both satellites
    time_arr1 = get_propagation_times(epoch1, satellite1)
    time_arr2 = get_propagation_times(epoch2, satellite2)

    # Get state vectors for both satellites
    state_vectors1 = get_state_vectors(satellite1, time_arr1)
    state_vectors2 = get_state_vectors(satellite2, time_arr2)

    # Plot both orbits
    fig, ax = plot_xyz_dual(state_vectors1, state_vectors2, r, sat1_name, sat2_name)
    plot_xyz_dual_plotly(state_vectors1, state_vectors2, r, sat1_name, sat2_name)

    return fig, ax


def plot_orbits(l1, l2):
    satellite, epoch = get_satellite(l1, l2)
    time_arr = get_propagation_times(epoch)
    state_vectors = get_state_vectors(satellite, time_arr)
    plot_xyz(state_vectors, r)
    return
