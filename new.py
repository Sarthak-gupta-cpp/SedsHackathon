import numpy as np
import matplotlib.pyplot as plt

# Gravitational constant (km^3/kg/s^2)
G = 6.67430e-20
M_sun = 1.989e30
M_earth = 5.972e24
M_jupiter = 1.898e27

# Positions and velocities (2D)
r_sun = np.array([0.0, 0.0])
r_earth = np.array([1.496e8, 0.0])  # km
v_earth = np.array([0.0, 29.78])  # km/s
r_jupiter = np.array([7.785e8, 0.0])
v_jupiter = np.array([0.0, 13.07])  # km/s

# Asteroid initial state (example)
r_ast = np.array([2.0e8, 1.0e7])
v_ast = np.array([-2.0, 25.0])

# Uncertainty
pos_uncertainty = 1e3  # km


def accel(pos, bodies):
    """
    pos: asteroid position
    bodies: list of tuples [(mass, position), ...]
    """
    a = np.zeros(2)
    for m, r in bodies:
        r_vec = r - pos
        r_mag = np.linalg.norm(r_vec)
        a += G * m * r_vec / r_mag**3
    return a


def rk4_step(pos, vel, dt, bodies):
    """One RK4 step"""
    k1_v = accel(pos, bodies) * dt
    k1_r = vel * dt

    k2_v = accel(pos + 0.5 * k1_r, bodies) * dt
    k2_r = (vel + 0.5 * k1_v) * dt

    k3_v = accel(pos + 0.5 * k2_r, bodies) * dt
    k3_r = (vel + 0.5 * k2_v) * dt

    k4_v = accel(pos + k3_r, bodies) * dt
    k4_r = (vel + k3_v) * dt

    pos_new = pos + (k1_r + 2 * k2_r + 2 * k3_r + k4_r) / 6
    vel_new = vel + (k1_v + 2 * k2_v + 2 * k3_v + k4_v) / 6
    return pos_new, vel_new


n_trials = 500
collision_count = 0
dt = 3600  # 1 hour
t_end = 365 * 24 * 3600  # 1 year

for _ in range(n_trials):
    r_ast_trial = r_ast + np.random.randn(2) * pos_uncertainty
    v_ast_trial = v_ast
    pos = r_ast_trial
    vel = v_ast_trial

    for t in range(0, t_end, dt):
        pos, vel = rk4_step(
            pos, vel, dt, [(M_sun, r_sun), (M_earth, r_earth), (M_jupiter, r_jupiter)]
        )
        # Check collision
        if np.linalg.norm(pos - r_earth) < 6371:  # Earth's radius km
            collision_count += 1
            break

collision_prob = collision_count / n_trials
print("Estimated collision probability:", collision_prob)
