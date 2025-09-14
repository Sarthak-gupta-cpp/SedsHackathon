# --- Asteroid and Planet Classes ---

import pygame
import numpy as np
import sys


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
        # Circular orbit, starting at +x axis
        angle = (self.orbital_velocity / self.orbit_radius) * t
        return np.array(
            [self.orbit_radius * np.cos(angle), self.orbit_radius * np.sin(angle)]
        )


class Asteroid:
    def __init__(self, pos, vel, mass=1e-12):
        self.pos = np.array(pos, dtype=float)
        self.vel = np.array(vel, dtype=float)
        self.mass = mass
        self.trail = []

    def update(self, dt, t, all_bodies, *args, **kwargs):
        # Planets are affected by gravity of all other bodies (including asteroids, sun, other planets)
        accel = self.get_acceleration(all_bodies, t)
        # For sun, skip movement
        if self.name == "Sun":
            return
        # Update velocity and position
        v = self.get_velocity_vector(t)
        v += accel * dt
        # Update orbital parameters (approximate)
        pos = self.get_position(t) + v * dt
        self.orbit_radius = np.linalg.norm(pos)
        self.orbital_velocity = np.linalg.norm(v)

    def get_acceleration(self, all_bodies, t):
        total_accel = np.zeros(2)
        my_pos = self.get_position(t)
        for body in all_bodies:
            if body is self:
                continue
            if isinstance(body, Asteroid):
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
        # Returns the velocity vector in 2D for the current orbit
        if self.name == "Sun":
            return np.zeros(2)
        angle = (self.orbital_velocity / self.orbit_radius) * t
        # Perpendicular to radius vector (counterclockwise)
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

    def draw(self, screen, center, scale, color, show_trail):
        asteroid_screen = (
            int(center[0] + self.pos[0] * scale),
            int(center[1] + self.pos[1] * scale),
        )
        if show_trail and len(self.trail) > 1:
            points = [
                (int(center[0] + p[0] * scale), int(center[1] + p[1] * scale))
                for p in self.trail
            ]
            pygame.draw.lines(screen, (180, 180, 180), False, points, 2)
        pygame.draw.circle(screen, color, asteroid_screen, 4)


# --- Physics Constants ---
G = 2.959e-4  # AU^3 / (solar_mass * day^2)
M_SUN = 1.0
M_EARTH = 3.003e-6
M_JUPITER = 9.548e-4
R_EARTH = 4.26e-5  # AU

# --- Orbital Parameters ---
EARTH_ORBIT_RADIUS = 1.0
JUPITER_ORBIT_RADIUS = 5.2
EARTH_ORBITAL_VELOCITY = np.sqrt(G * M_SUN / EARTH_ORBIT_RADIUS)
JUPITER_ORBITAL_VELOCITY = np.sqrt(G * M_SUN / JUPITER_ORBIT_RADIUS)


# --- Pygame Setup ---
pygame.init()
INFO = pygame.display.Info()
WIDTH, HEIGHT = INFO.current_w, INFO.current_h
CENTER = (WIDTH // 2, HEIGHT // 2)
SCALE = min(WIDTH, HEIGHT) // 3  # AU to pixels, keep orbits visible
FPS = 60

# --- Asteroid Colors ---
COLOR1 = (200, 200, 200)  # Light gray
COLOR2 = (255, 80, 80)  # Red

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Asteroid Deflection Game")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 20)


# --- Slider UI ---
class Slider:
    def __init__(self, x, y, w, minv, maxv, value, label, step=0.0, fmt="{:.3g}"):
        self.rect = pygame.Rect(x, y, w, 20)
        self.minv = minv
        self.maxv = maxv
        self.value = value
        self.label = label
        self.step = step
        self.fmt = fmt
        self.dragging = False

    def draw(self, surf):
        # Bar
        pygame.draw.rect(surf, (80, 80, 80), self.rect, border_radius=6)
        # Fill
        fillw = int((self.value - self.minv) / (self.maxv - self.minv) * self.rect.w)
        pygame.draw.rect(
            surf,
            (180, 180, 255),
            (self.rect.x, self.rect.y, fillw, self.rect.h),
            border_radius=6,
        )
        # Handle
        handlex = self.rect.x + fillw
        pygame.draw.circle(surf, (40, 40, 200), (handlex, self.rect.centery), 9)
        # Label
        txt = font.render(
            f"{self.label}: {self.fmt.format(self.value)}", True, (255, 255, 255)
        )
        surf.blit(txt, (self.rect.x, self.rect.y - 22))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            relx = (event.pos[0] - self.rect.x) / self.rect.w
            relx = min(max(relx, 0), 1)
            v = self.minv + relx * (self.maxv - self.minv)
            if self.step:
                v = round(v / self.step) * self.step
            self.value = v
            return True
        return False


# --- Simulation Parameters (User can change these in-game) ---

# Sun
M_SUN = 1.0

# Earth
M_EARTH = 3.003e-6
EARTH_ORBIT_RADIUS = 1.0
EARTH_ORBITAL_VELOCITY = np.sqrt(G * M_SUN / EARTH_ORBIT_RADIUS)

# Jupiter
M_JUPITER = 9.548e-4
JUPITER_ORBIT_RADIUS = 5.2
JUPITER_ORBITAL_VELOCITY = np.sqrt(G * M_SUN / JUPITER_ORBIT_RADIUS)


# Asteroid uncertainty and multiple objects
ASTEROID_BASE_POS = np.array([-1.1, 0.3])
ASTEROID_BASE_VEL = np.array([-0.005, -0.015])
ASTEROID_MASS = 1e-12  # Solar masses (arbitrary, not used in gravity)
ASTEROID_UNC_POS = 0.03  # Uncertainty range for position (AU)
ASTEROID_UNC_VEL = 0.003  # Uncertainty range for velocity (AU/day)
NUM_ASTEROIDS = 7


# Helper to generate asteroid objects
def generate_asteroids():
    asteroids = []
    for _ in range(NUM_ASTEROIDS):
        pos = ASTEROID_BASE_POS + np.random.uniform(
            -ASTEROID_UNC_POS, ASTEROID_UNC_POS, 2
        )
        vel = ASTEROID_BASE_VEL + np.random.uniform(
            -ASTEROID_UNC_VEL, ASTEROID_UNC_VEL, 2
        )
        asteroids.append(Asteroid(pos, vel, ASTEROID_MASS))
    return asteroids


asteroids = generate_asteroids()

# Laser
laser_thrust = 5e-9
laser_duration = 20
laser_start_time = 100

# Simulation
dt = 0.5  # days per frame
show_trail = True

# Generate star positions once
NUM_STARS = 80
star_positions = [
    (np.random.randint(0, 900), np.random.randint(0, 900)) for _ in range(NUM_STARS)
]


# --- Game Loop ---
def main():
    global laser_thrust, laser_duration, laser_start_time
    global \
        asteroids, \
        ASTEROID_BASE_POS, \
        ASTEROID_BASE_VEL, \
        ASTEROID_UNC_POS, \
        ASTEROID_UNC_VEL, \
        NUM_ASTEROIDS
    global M_SUN, M_EARTH, EARTH_ORBIT_RADIUS, EARTH_ORBITAL_VELOCITY
    global M_JUPITER, JUPITER_ORBIT_RADIUS, JUPITER_ORBITAL_VELOCITY
    global dt, show_trail
    running = True
    t = 0
    # Create celestial bodies: Sun, planets, asteroids
    sun = Planet(M_SUN, 0.0, 0.0, (255, 215, 0), "Sun")
    earth = Planet(
        M_EARTH, EARTH_ORBIT_RADIUS, EARTH_ORBITAL_VELOCITY, (0, 100, 255), "Earth"
    )
    jupiter = Planet(
        M_JUPITER,
        JUPITER_ORBIT_RADIUS,
        JUPITER_ORBITAL_VELOCITY,
        (255, 140, 0),
        "Jupiter",
    )
    planets = [sun, earth, jupiter]
    paused = False
    # All sliders on the left side, vertical stack
    slider_x = 30
    slider_y = 60
    slider_w = 350 if WIDTH > 1400 else 250
    slider_gap = 50
    sliders = [
        Slider(
            slider_x,
            slider_y + slider_gap * 0,
            slider_w,
            1e-9,
            1e-7,
            laser_thrust,
            "Laser Thrust",
            step=1e-10,
            fmt="{:.1e}",
        ),
        Slider(
            slider_x,
            slider_y + slider_gap * 1,
            slider_w,
            1,
            100,
            laser_duration,
            "Laser Duration",
            step=1,
            fmt="{:.0f}",
        ),
        Slider(
            slider_x,
            slider_y + slider_gap * 2,
            slider_w,
            0.01,
            0.2,
            ASTEROID_UNC_POS,
            "Ast Unc Pos",
            step=0.01,
        ),
        Slider(
            slider_x,
            slider_y + slider_gap * 3,
            slider_w,
            0.001,
            0.01,
            ASTEROID_UNC_VEL,
            "Ast Unc Vel",
            step=0.001,
        ),
        Slider(
            slider_x,
            slider_y + slider_gap * 4,
            slider_w,
            1,
            2000,
            NUM_ASTEROIDS,
            "Num Asteroids",
            step=1,
            fmt="{:.0f}",
        ),
        Slider(
            slider_x,
            slider_y + slider_gap * 5,
            slider_w,
            0.5,
            2.0,
            EARTH_ORBIT_RADIUS,
            "Earth Radius",
            step=0.01,
        ),
        Slider(
            slider_x,
            slider_y + slider_gap * 6,
            slider_w,
            1.0,
            7.0,
            JUPITER_ORBIT_RADIUS,
            "Jupiter Radius",
            step=0.01,
        ),
        Slider(
            slider_x,
            slider_y + slider_gap * 7,
            slider_w,
            1e-6,
            1e-5,
            M_EARTH,
            "Earth Mass",
            step=1e-7,
            fmt="{:.1e}",
        ),
        Slider(
            slider_x,
            slider_y + slider_gap * 8,
            slider_w,
            1e-4,
            2e-3,
            M_JUPITER,
            "Jupiter Mass",
            step=1e-5,
            fmt="{:.1e}",
        ),
        Slider(
            slider_x,
            slider_y + slider_gap * 9,
            slider_w,
            -2.0,
            2.0,
            ASTEROID_BASE_POS[0],
            "Ast Base Pos X",
            step=0.01,
        ),
        Slider(
            slider_x,
            slider_y + slider_gap * 10,
            slider_w,
            -2.0,
            2.0,
            ASTEROID_BASE_POS[1],
            "Ast Base Pos Y",
            step=0.01,
        ),
        Slider(
            slider_x,
            slider_y + slider_gap * 11,
            slider_w,
            -0.05,
            0.05,
            ASTEROID_BASE_VEL[0],
            "Ast Base Vel X",
            step=0.001,
        ),
        Slider(
            slider_x,
            slider_y + slider_gap * 12,
            slider_w,
            -0.05,
            0.05,
            ASTEROID_BASE_VEL[1],
            "Ast Base Vel Y",
            step=0.001,
        ),
        Slider(
            slider_x,
            slider_y + slider_gap * 13,
            slider_w,
            0.1,
            10.0,
            dt,
            "dt (days/frame)",
            step=0.01,
        ),
    ]
    # --- Window Control Buttons ---
    BUTTON_SIZE = 32
    BUTTON_PADDING = 8
    btn_close_rect = pygame.Rect(
        WIDTH - BUTTON_SIZE - BUTTON_PADDING, BUTTON_PADDING, BUTTON_SIZE, BUTTON_SIZE
    )
    btn_min_rect = pygame.Rect(
        WIDTH - 2 * BUTTON_SIZE - 2 * BUTTON_PADDING,
        BUTTON_PADDING,
        BUTTON_SIZE,
        BUTTON_SIZE,
    )
    btn_max_rect = pygame.Rect(
        WIDTH - 3 * BUTTON_SIZE - 3 * BUTTON_PADDING,
        BUTTON_PADDING,
        BUTTON_SIZE,
        BUTTON_SIZE,
    )

    def draw_window_buttons():
        # Close button (red)
        pygame.draw.rect(screen, (220, 60, 60), btn_close_rect, border_radius=8)
        pygame.draw.line(
            screen,
            (255, 255, 255),
            btn_close_rect.topleft,
            btn_close_rect.bottomright,
            3,
        )
        pygame.draw.line(
            screen,
            (255, 255, 255),
            btn_close_rect.topright,
            btn_close_rect.bottomleft,
            3,
        )
        # Minimize button (yellow)
        pygame.draw.rect(screen, (230, 200, 40), btn_min_rect, border_radius=8)
        pygame.draw.line(
            screen,
            (80, 80, 80),
            (btn_min_rect.left + 8, btn_min_rect.centery),
            (btn_min_rect.right - 8, btn_min_rect.centery),
            3,
        )
        # Maximize button (green)
        pygame.draw.rect(screen, (60, 200, 80), btn_max_rect, border_radius=8)
        pygame.draw.rect(screen, (255, 255, 255), btn_max_rect.inflate(-12, -12), 2)

    while running:
        for event in pygame.event.get():
            # Sliders event handling
            slider_changed = False
            for s in sliders:
                if s.handle_event(event):
                    slider_changed = True
            if slider_changed:
                laser_thrust = sliders[0].value
                laser_duration = int(sliders[1].value)
                ASTEROID_UNC_POS = sliders[2].value
                ASTEROID_UNC_VEL = sliders[3].value
                NUM_ASTEROIDS = int(sliders[4].value)
                EARTH_ORBIT_RADIUS = sliders[5].value
                EARTH_ORBITAL_VELOCITY = np.sqrt(G * M_SUN / EARTH_ORBIT_RADIUS)
                JUPITER_ORBIT_RADIUS = sliders[6].value
                JUPITER_ORBITAL_VELOCITY = np.sqrt(G * M_SUN / JUPITER_ORBIT_RADIUS)
                M_EARTH = sliders[7].value
                M_JUPITER = sliders[8].value
                ASTEROID_BASE_POS[0] = sliders[9].value
                ASTEROID_BASE_POS[1] = sliders[10].value
                ASTEROID_BASE_VEL[0] = sliders[11].value
                ASTEROID_BASE_VEL[1] = sliders[12].value
                dt = sliders[13].value
                # Update planet objects
                earth.mass = M_EARTH
                earth.orbit_radius = EARTH_ORBIT_RADIUS
                earth.orbital_velocity = EARTH_ORBITAL_VELOCITY
                jupiter.mass = M_JUPITER
                jupiter.orbit_radius = JUPITER_ORBIT_RADIUS
                jupiter.orbital_velocity = JUPITER_ORBITAL_VELOCITY
                asteroids = generate_asteroids()
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos
                if btn_close_rect.collidepoint(mouse_pos):
                    running = False
                elif btn_min_rect.collidepoint(mouse_pos):
                    # Minimize window (simulate by iconifying)
                    pygame.display.iconify()
                elif btn_max_rect.collidepoint(mouse_pos):
                    # Maximize/restore window (simulate by toggling fullscreen)
                    if not pygame.display.get_surface().get_flags() & pygame.FULLSCREEN:
                        pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
                    else:
                        pygame.display.set_mode((WIDTH, HEIGHT))
            # --- User Controls ---
            if event.type == pygame.KEYDOWN:
                # Pause/resume (SPACE)
                if event.key == pygame.K_SPACE:
                    paused = not paused
                # Toggle trail (TAB)
                if event.key == pygame.K_TAB:
                    show_trail = not show_trail
                # Reset (ESCAPE)
                if event.key == pygame.K_ESCAPE:
                    t = 0
                    asteroids = generate_asteroids()
                    trajectories = [[] for _ in range(NUM_ASTEROIDS)]
        # --- Physics Update ---
        if not paused:
            # Combine all bodies for mutual gravity
            all_bodies = planets + asteroids
            # Update asteroids
            for asteroid in asteroids:
                asteroid.update(
                    dt, t, all_bodies, laser_thrust, laser_start_time, laser_duration
                )
            # Update planets (except sun)
            for planet in planets:
                planet.update(dt, t, all_bodies)
            t += dt
        # --- Drawing ---
        # Starry background (use fixed star positions)
        screen.fill((10, 10, 30))
        for x, y in star_positions:
            pygame.draw.circle(screen, (255, 255, 255), (x, y), 1)
        # Draw left UI border
        border_x = slider_x + slider_w + 30
        pygame.draw.line(screen, (200, 200, 200), (border_x, 0), (border_x, HEIGHT), 3)
        # Draw window control buttons
        draw_window_buttons()
        # Draw sliders
        for s in sliders:
            s.draw(screen)
        # Draw simulation area (everything right of border)
        sim_offset_x = border_x
        # Draw Sun and planets
        sim_center = (int((WIDTH + border_x) // 2), HEIGHT // 2)
        for planet in planets:
            if planet.name != "Sun":
                pygame.draw.circle(
                    screen,
                    (200, 200, 200),
                    sim_center,
                    int(planet.orbit_radius * SCALE),
                    1,
                )
            planet_pos = planet.get_position(t)
            planet_screen = (
                int(sim_center[0] + planet_pos[0] * SCALE),
                int(sim_center[1] + planet_pos[1] * SCALE),
            )
            if planet.name == "Sun":
                pygame.draw.circle(screen, planet.color, planet_screen, 15)
            else:
                pygame.draw.circle(
                    screen,
                    planet.color,
                    planet_screen,
                    10 if planet.name == "Earth" else 13,
                )
        # Draw Asteroids and Trajectories
        for i, asteroid in enumerate(asteroids):
            color = COLOR1 if i < NUM_ASTEROIDS // 2 else COLOR2
            asteroid.draw(screen, sim_center, SCALE, color, show_trail)
        # Draw Info (minimal, only simulation state and trail toggle)
        sim_state = font.render(
            f"Simulation: {'PAUSED' if paused else 'RUNNING'} (SPACE)",
            True,
            (255, 100, 100) if paused else (100, 255, 100),
        )
        info9 = font.render(
            f"Trail: {'ON' if show_trail else 'OFF'} (TAB)", True, (255, 255, 255)
        )
        info10 = font.render("Press ESC to reset", True, (255, 255, 0))
        screen.blit(sim_state, (slider_x, 15))
        screen.blit(info9, (slider_x, HEIGHT - 60))
        screen.blit(info10, (slider_x, HEIGHT - 30))
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
