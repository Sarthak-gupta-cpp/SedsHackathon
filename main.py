import numpy as np
import matplotlib.pyplot as plt
from ipywidgets import interact, FloatSlider, IntSlider, Dropdown

# ======================
# Backend Physics (imported from earlier code)
# ======================

AU = 1.496e11
YEAR = 365.25 * 24 * 3600
mu_sun = 4 * np.pi**2
EARTH_RADIUS_AU = 6371e3 / AU


def m_s2_to_AU_per_yr2(a_m_s2):
    return a_m_s2 * (YEAR**2) / AU


DEFAULT_THRUST_m_s2 = 1e-9
DEFAULT_THRUST_AUyr2 = m_s2_to_AU_per_yr2(DEFAULT_THRUST_m_s2)


def earth_position(t):
    return np.array([np.cos(2 * np.pi * t), np.sin(2 * np.pi * t)])


def gravity_sun(r):
    dist = np.linalg.norm(r)
    return -mu_sun * r / dist**3


def gravity_earth_on_body(r, t):
    r_earth = earth_position(t)
    diff = r - r_earth
    dist = np.linalg.norm(diff)
    mu_earth = 3.003e-6 * mu_sun
    return -mu_earth * diff / dist**3


def rk4_step(r, v, t, dt, thrust_func=None, include_earth=False):
    def accel(r_, t_):
        a = gravity_sun(r_)
        if include_earth:
            a += gravity_earth_on_body(r_, t_)
        if thrust_func is not None:
            a += thrust_func(r_, v, t_)
        return a

    k1v = accel(r, t) * dt
    k1r = v * dt
    k2v = accel(r + 0.5 * k1r, t + 0.5 * dt) * dt
    k2r = (v + 0.5 * k1v) * dt
    k3v = accel(r + 0.5 * k2r, t + 0.5 * dt) * dt
    k3r = (v + 0.5 * k2v) * dt
    k4v = accel(r + k3r, t + dt) * dt
    k4r = (v + k3v) * dt

    v_new = v + (k1v + 2 * k2v + 2 * k3v + k4v) / 6
    r_new = r + (k1r + 2 * k2r + 2 * k3r + k4r) / 6
    return r_new, v_new


def integrate_trajectory(
    r0,
    v0,
    t_max=1.0,
    dt=1 / 365,
    laser_start=0.0,
    laser_duration=0.0,
    thrust_AUyr2=DEFAULT_THRUST_AUyr2,
    thrust_strategy="away_from_earth",
    include_earth=False,
):
    r = r0.copy()
    v = v0.copy()
    t = 0.0
    path = [r.copy()]
    collided = False
    min_dist = np.inf

    while t < t_max:

        def thrust_func(r_, v_, t_):
            if laser_start <= t_ <= laser_start + laser_duration:
                if thrust_strategy == "away_from_earth":
                    earth_pos = earth_position(t_)
                    diff = r_ - earth_pos
                    return thrust_AUyr2 * diff / np.linalg.norm(diff)
                elif thrust_strategy == "anti_velocity":
                    return -thrust_AUyr2 * v_ / np.linalg.norm(v_)
                else:
                    return np.array([thrust_AUyr2, 0.0])
            return np.zeros(2)

        r, v = rk4_step(
            r, v, t, dt, thrust_func=thrust_func, include_earth=include_earth
        )
        t += dt
        path.append(r.copy())

        dist = np.linalg.norm(r - earth_position(t))
        min_dist = min(min_dist, dist)
        if dist <= EARTH_RADIUS_AU:
            collided = True
            break

    return collided, min_dist, np.array(path)


def monte_carlo(N, r_base, v_base, pos_sigma=1e-5, vel_sigma=1e-6, **kwargs):
    rng = np.random.default_rng()
    collisions = 0
    min_dists = []
    sample_paths = []

    for i in range(N):
        r0 = r_base + rng.normal(0, pos_sigma, 2)
        v0 = v_base + rng.normal(0, vel_sigma, 2)
        collided, min_dist, path = integrate_trajectory(r0, v0, **kwargs)
        if collided:
            collisions += 1
        min_dists.append(min_dist)
        if i < 10:  # store only a few for plotting
            sample_paths.append(path)

    return collisions / N, np.array(min_dists), sample_paths


# ======================
# 7. Interactive GUI
# ======================
def run_simulation(
    x0=1.1,
    y0=0.0,
    vx0=0.0,
    vy0=6.0,
    pos_sigma=1e-5,
    vel_sigma=1e-6,
    N=200,
    laser_start=0.2,
    laser_duration=0.05,
    strategy="away_from_earth",
):
    r_base = np.array([x0, y0])
    v_base = np.array([vx0, vy0]) / (AU / YEAR)  # convert m/s -> AU/yr

    prob, dists, paths = monte_carlo(
        N,
        r_base,
        v_base,
        pos_sigma=pos_sigma,
        vel_sigma=vel_sigma,
        t_max=2.0,
        dt=1 / 365,
        laser_start=laser_start,
        laser_duration=laser_duration,
        thrust_strategy=strategy,
        include_earth=True,
    )

    # Plot results
    plt.figure(figsize=(6, 6))
    # Earth orbit
    theta = np.linspace(0, 2 * np.pi, 500)
    plt.plot(np.cos(theta), np.sin(theta), "b--", label="Earth orbit")
    plt.scatter(1, 0, color="blue", marker="o", label="Earth start")
    # Asteroid paths (sampled)
    for path in paths:
        plt.plot(path[:, 0], path[:, 1], alpha=0.6)
    plt.scatter(0, 0, color="yellow", s=200, marker="*", label="Sun")
    plt.axis("equal")
    plt.legend()
    plt.title(f"Impact probability ≈ {prob:.3f} (N={N})")
    plt.show()


# ======================
# 8. Interactive Widgets
# ======================
interact(
    run_simulation,
    x0=FloatSlider(value=1.0, min=0.5, max=2.0, step=0.1, description="x0"),
    y0=FloatSlider(0.0, -1.0, 1.0, 0.01),
    vx0=FloatSlider(0.0, -10.0, 10.0, 0.1),
    vy0=FloatSlider(6.0, -10.0, 10.0, 0.1),
    pos_sigma=FloatSlider(1e-5, 1e-7, 1e-3, 1e-6, readout_format=".1e"),
    vel_sigma=FloatSlider(1e-6, 1e-8, 1e-3, 1e-7, readout_format=".1e"),
    N=IntSlider(200, 50, 2000, 50),
    laser_start=FloatSlider(0.2, 0.0, 1.0, 0.01),
    laser_duration=FloatSlider(0.05, 0.0, 0.2, 0.01),
    strategy=Dropdown(options=["away_from_earth", "anti_velocity", "fixed_inertial"]),
)
