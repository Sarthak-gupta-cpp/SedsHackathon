import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# ----- Simulation parameters -----
t_steps = 500
dt = 3600 * 24  # 1 day per step
r_earth_orbit = 1.496e8  # km
r_jupiter_orbit = 7.785e8

# Generate circular orbits for Earth and Jupiter
theta = np.linspace(0, 2 * np.pi, t_steps)
earth_x = r_earth_orbit * np.cos(theta)
earth_y = r_earth_orbit * np.sin(theta)

jupiter_x = r_jupiter_orbit * np.cos(theta * 0.5)
jupiter_y = r_jupiter_orbit * np.sin(theta * 0.5)

# Example asteroid trajectory (before and after deflection)
asteroid_x = r_earth_orbit * 1.2 * np.cos(theta + 0.5)
asteroid_y = r_earth_orbit * 1.2 * np.sin(theta + 0.5)

# Small deflection applied after step 200
asteroid_x_def = asteroid_x.copy()
asteroid_y_def = asteroid_y.copy()
asteroid_x_def[200:] += 0.05 * r_earth_orbit * np.sin(theta[200:] * 2)
asteroid_y_def[200:] += 0.05 * r_earth_orbit * np.cos(theta[200:] * 2)

# ----- Set up plot -----
fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xlim(-r_jupiter_orbit * 1.1, r_jupiter_orbit * 1.1)
ax.set_ylim(-r_jupiter_orbit * 1.1, r_jupiter_orbit * 1.1)
ax.set_xlabel("x (km)")
ax.set_ylabel("y (km)")
ax.set_title("Asteroid Deflection Animation")
ax.grid(True)
ax.set_aspect("equal")

# Plot initial orbits (for reference)
ax.plot(earth_x, earth_y, "b-", alpha=0.3)
ax.plot(jupiter_x, jupiter_y, "orange", alpha=0.3)

# Plot points for moving bodies
(earth_dot,) = ax.plot([], [], "bo", label="Earth")
(jupiter_dot,) = ax.plot([], [], "o", color="orange", label="Jupiter")
(asteroid_dot,) = ax.plot([], [], "ro", label="Asteroid")

ax.legend()


# ----- Animation function -----
def animate(i):
    earth_dot.set_data([earth_x[i]], [earth_y[i]])
    jupiter_dot.set_data([jupiter_x[i]], [jupiter_y[i]])
    asteroid_dot.set_data([asteroid_x_def[i]], [asteroid_y_def[i]])
    return earth_dot, jupiter_dot, asteroid_dot


anim = FuncAnimation(fig, animate, frames=t_steps, interval=50, blit=True)

plt.show()
