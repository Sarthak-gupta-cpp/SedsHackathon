import numpy as np

G = 2.959e-4  # AU^3 / (solar_mass * day^2)


class Planet:
    def __init__(self, mass, orbit_radius, orbital_velocity, color, name):
        self.mass = mass
        self.orbit_radius = orbit_radius
        self.orbital_velocity = orbital_velocity
        self.color = color
        self.name = name

    def get_position(self, t):
        if self.name == "Sun":
            return np.array([0.0, 0.0])
        angle = (self.orbital_velocity / self.orbit_radius) * t
        return np.array(
            [self.orbit_radius * np.cos(angle), self.orbit_radius * np.sin(angle)]
        )

    def update(self, dt, t, all_bodies, *args, **kwargs):
        accel = self.get_acceleration(all_bodies, t)
        if self.name == "Sun":
            return
        v = self.get_velocity_vector(t)
        v += accel * dt
        pos = self.get_position(t) + v * dt
        self.orbit_radius = np.linalg.norm(pos)
        self.orbital_velocity = np.linalg.norm(v)

    def get_acceleration(self, all_bodies, t):
        total_accel = np.zeros(2)
        my_pos = self.get_position(t)
        for body in all_bodies:
            if body is self:
                continue
            if hasattr(body, "pos"):
                body_pos = body.pos
            else:
                body_pos = body.get_position(t)
            r = my_pos - body_pos
            dist = np.linalg.norm(r)
            if dist == 0:
                continue
            total_accel += -G * body.mass * r / dist**3
        return total_accel

    def get_velocity_vector(self, t):
        if self.name == "Sun":
            return np.zeros(2)
        angle = (self.orbital_velocity / self.orbit_radius) * t
        vx = (
            -self.orbit_radius
            * np.sin(angle)
            * (self.orbital_velocity / self.orbit_radius)
        )
        vy = (
            self.orbit_radius
            * np.cos(angle)
            * (self.orbital_velocity / self.orbit_radius)
        )
        return np.array([vx, vy])


class Asteroid:
    def __init__(self, pos, vel, mass=1e-12):
        self.pos = np.array(pos, dtype=float)
        self.vel = np.array(vel, dtype=float)
        self.mass = mass
        self.trail = []

    def update(
        self,
        dt,
        t,
        all_bodies,
        laser_thrust=None,
        laser_start_time=None,
        laser_duration=None,
    ):
        accel = self.get_acceleration(
            all_bodies, t, laser_thrust, laser_start_time, laser_duration
        )
        self.vel += accel * dt
        self.pos += self.vel * dt
        self.trail.append(self.pos.copy())

    def get_acceleration(
        self, all_bodies, t, laser_thrust, laser_start_time, laser_duration
    ):
        total_accel = np.zeros(2)
        my_pos = self.pos
        for body in all_bodies:
            if body is self:
                continue
            if hasattr(body, "pos"):
                body_pos = body.pos
            else:
                body_pos = body.get_position(t)
            r = my_pos - body_pos
            dist = np.linalg.norm(r)
            if dist == 0:
                continue
            total_accel += -G * body.mass * r / dist**3
        if (
            laser_start_time is not None
            and laser_duration is not None
            and laser_thrust is not None
        ):
            if laser_start_time <= t < laser_start_time + laser_duration:
                if np.linalg.norm(self.vel) > 0:
                    thrust_direction = -self.vel / np.linalg.norm(self.vel)
                    total_accel += laser_thrust * thrust_direction
        return total_accel
