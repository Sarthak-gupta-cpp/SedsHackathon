import pygame
import numpy as np
import sys

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
WIDTH, HEIGHT = 900, 900
CENTER = (WIDTH // 2, HEIGHT // 2)
SCALE = 300  # AU to pixels
FPS = 60

# --- Asteroid Colors ---
COLOR1 = (200, 200, 200)  # Light gray
COLOR2 = (255, 80, 80)  # Red

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
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


def generate_asteroids():
    asteroids = []
    for _ in range(NUM_ASTEROIDS):
        pos = ASTEROID_BASE_POS + np.random.uniform(
            -ASTEROID_UNC_POS, ASTEROID_UNC_POS, 2
        )
        vel = ASTEROID_BASE_VEL + np.random.uniform(
            -ASTEROID_UNC_VEL, ASTEROID_UNC_VEL, 2
        )
        asteroids.append(np.concatenate([pos, vel]))
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


# --- Physics Functions ---
def get_planet_state(time_days):
    # Circular orbits, starting at +x axis
    angle_earth = (EARTH_ORBITAL_VELOCITY / EARTH_ORBIT_RADIUS) * time_days
    pos_earth = np.array(
        [
            EARTH_ORBIT_RADIUS * np.cos(angle_earth),
            EARTH_ORBIT_RADIUS * np.sin(angle_earth),
        ]
    )
    angle_jupiter = (JUPITER_ORBITAL_VELOCITY / JUPITER_ORBIT_RADIUS) * time_days
    pos_jupiter = np.array(
        [
            JUPITER_ORBIT_RADIUS * np.cos(angle_jupiter),
            JUPITER_ORBIT_RADIUS * np.sin(angle_jupiter),
        ]
    )
    return pos_earth, pos_jupiter


def asteroid_accel(pos, vel, t):
    pos_earth, pos_jupiter = get_planet_state(t)
    pos_sun = np.array([0, 0])
    # Gravitational forces
    r_sun = pos - pos_sun
    r_earth = pos - pos_earth
    r_jupiter = pos - pos_jupiter
    accel_sun = -G * M_SUN * r_sun / np.linalg.norm(r_sun) ** 3
    accel_earth = -G * M_EARTH * r_earth / np.linalg.norm(r_earth) ** 3
    accel_jupiter = -G * M_JUPITER * r_jupiter / np.linalg.norm(r_jupiter) ** 3
    total_accel = accel_sun + accel_earth + accel_jupiter
    # Laser thrust
    if laser_start_time <= t < laser_start_time + laser_duration:
        thrust_direction = -vel / np.linalg.norm(vel)
        total_accel += laser_thrust * thrust_direction
    return total_accel


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
    trajectories = [[] for _ in range(NUM_ASTEROIDS)]
    paused = False
    sliders = [
        Slider(
            650,
            60,
            200,
            1e-9,
            1e-7,
            laser_thrust,
            "Laser Thrust",
            step=1e-10,
            fmt="{:.1e}",
        ),
        Slider(
            650,
            100,
            200,
            1,
            100,
            laser_duration,
            "Laser Duration",
            step=1,
            fmt="{:.0f}",
        ),
        Slider(650, 140, 200, 0.01, 0.2, ASTEROID_UNC_POS, "Ast Unc Pos", step=0.01),
        Slider(650, 180, 200, 0.001, 0.01, ASTEROID_UNC_VEL, "Ast Unc Vel", step=0.001),
        Slider(
            650, 220, 200, 1, 2000, NUM_ASTEROIDS, "Num Asteroids", step=1, fmt="{:.0f}"
        ),
        Slider(650, 260, 200, 0.5, 2.0, EARTH_ORBIT_RADIUS, "Earth Radius", step=0.01),
        Slider(
            650, 300, 200, 1.0, 7.0, JUPITER_ORBIT_RADIUS, "Jupiter Radius", step=0.01
        ),
        Slider(
            650, 340, 200, 1e-6, 1e-5, M_EARTH, "Earth Mass", step=1e-7, fmt="{:.1e}"
        ),
        Slider(
            650,
            380,
            200,
            1e-4,
            2e-3,
            M_JUPITER,
            "Jupiter Mass",
            step=1e-5,
            fmt="{:.1e}",
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
                asteroids = generate_asteroids()
                trajectories = [[] for _ in range(NUM_ASTEROIDS)]
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
                # Laser controls (L/I/O/P)
                if event.key == pygame.K_l:
                    laser_thrust *= 1.2
                if event.key == pygame.K_i:
                    laser_thrust /= 1.2
                if event.key == pygame.K_o:
                    laser_duration += 5
                if event.key == pygame.K_p:
                    laser_duration = max(0, laser_duration - 5)
                # Asteroid uncertainty controls (T/G for pos, Y/H for vel, U/J for number)
                if event.key == pygame.K_t:
                    ASTEROID_UNC_POS += 0.01
                if event.key == pygame.K_g:
                    ASTEROID_UNC_POS = max(0, ASTEROID_UNC_POS - 0.01)
                if event.key == pygame.K_y:
                    ASTEROID_UNC_VEL += 0.001
                if event.key == pygame.K_h:
                    ASTEROID_UNC_VEL = max(0, ASTEROID_UNC_VEL - 0.001)
                if event.key == pygame.K_u:
                    NUM_ASTEROIDS = min(2000, NUM_ASTEROIDS + 1)
                if event.key == pygame.K_j:
                    NUM_ASTEROIDS = max(1, NUM_ASTEROIDS - 1)
                # Regenerate asteroids with new uncertainty/number
                if event.key in [
                    pygame.K_t,
                    pygame.K_g,
                    pygame.K_y,
                    pygame.K_h,
                    pygame.K_u,
                    pygame.K_j,
                ]:
                    asteroids = generate_asteroids()
                    trajectories = [[] for _ in range(NUM_ASTEROIDS)]
                # Asteroid base controls (move all, WASD replaced with F/V/B/N for vel, R/F/C/X for pos)
                if event.key == pygame.K_f:
                    ASTEROID_BASE_VEL[1] += 0.001
                    asteroids = generate_asteroids()
                if event.key == pygame.K_v:
                    ASTEROID_BASE_VEL[1] -= 0.001
                    asteroids = generate_asteroids()
                if event.key == pygame.K_b:
                    ASTEROID_BASE_VEL[0] -= 0.001
                    asteroids = generate_asteroids()
                if event.key == pygame.K_n:
                    ASTEROID_BASE_VEL[0] += 0.001
                    asteroids = generate_asteroids()
                if event.key == pygame.K_r:
                    ASTEROID_BASE_POS[1] += 0.05
                    asteroids = generate_asteroids()
                if event.key == pygame.K_f:
                    ASTEROID_BASE_POS[1] -= 0.05
                    asteroids = generate_asteroids()
                if event.key == pygame.K_c:
                    ASTEROID_BASE_POS[0] -= 0.05
                    asteroids = generate_asteroids()
                if event.key == pygame.K_x:
                    ASTEROID_BASE_POS[0] += 0.05
                    asteroids = generate_asteroids()
                # Earth controls (Q/E)
                if event.key == pygame.K_q:
                    EARTH_ORBIT_RADIUS += 0.1
                    EARTH_ORBITAL_VELOCITY = np.sqrt(G * M_SUN / EARTH_ORBIT_RADIUS)
                if event.key == pygame.K_e:
                    EARTH_ORBIT_RADIUS = max(0.5, EARTH_ORBIT_RADIUS - 0.1)
                    EARTH_ORBITAL_VELOCITY = np.sqrt(G * M_SUN / EARTH_ORBIT_RADIUS)
                # Jupiter controls (Z/X)
                if event.key == pygame.K_z:
                    JUPITER_ORBIT_RADIUS += 0.2
                    JUPITER_ORBITAL_VELOCITY = np.sqrt(G * M_SUN / JUPITER_ORBIT_RADIUS)
                if event.key == pygame.K_x:
                    JUPITER_ORBIT_RADIUS = max(1.0, JUPITER_ORBIT_RADIUS - 0.2)
                    JUPITER_ORBITAL_VELOCITY = np.sqrt(G * M_SUN / JUPITER_ORBIT_RADIUS)
                # Sun mass (S/D)
                if event.key == pygame.K_s:
                    M_SUN *= 1.05
                    EARTH_ORBITAL_VELOCITY = np.sqrt(G * M_SUN / EARTH_ORBIT_RADIUS)
                    JUPITER_ORBITAL_VELOCITY = np.sqrt(G * M_SUN / JUPITER_ORBIT_RADIUS)
                if event.key == pygame.K_d:
                    M_SUN /= 1.05
                    EARTH_ORBITAL_VELOCITY = np.sqrt(G * M_SUN / EARTH_ORBIT_RADIUS)
                    JUPITER_ORBITAL_VELOCITY = np.sqrt(G * M_SUN / JUPITER_ORBIT_RADIUS)
                # Simulation speed (A/W)
                if event.key == pygame.K_a:
                    dt *= 1.2
                if event.key == pygame.K_w:
                    dt = max(0.1, dt / 1.2)
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
            for i in range(NUM_ASTEROIDS):
                pos = asteroids[i][:2]
                vel = asteroids[i][2:]
                accel = asteroid_accel(pos, vel, t)
                vel += accel * dt
                pos += vel * dt
                asteroids[i] = np.concatenate([pos, vel])
                trajectories[i].append(pos.copy())
            t += dt
        # --- Drawing ---
        # Starry background (use fixed star positions)
        screen.fill((10, 10, 30))
        for x, y in star_positions:
            pygame.draw.circle(screen, (255, 255, 255), (x, y), 1)
        # Draw window control buttons
        draw_window_buttons()
        # Draw Sun
        pygame.draw.circle(screen, (255, 215, 0), CENTER, 15)
        # Draw Earth orbit
        pygame.draw.circle(
            screen, (0, 80, 200), CENTER, int(EARTH_ORBIT_RADIUS * SCALE), 1
        )
        # Draw Jupiter orbit
        pygame.draw.circle(
            screen, (200, 120, 0), CENTER, int(JUPITER_ORBIT_RADIUS * SCALE), 1
        )
        # Draw Earth
        pos_earth, pos_jupiter = get_planet_state(t)
        earth_screen = (
            int(CENTER[0] + pos_earth[0] * SCALE),
            int(CENTER[1] + pos_earth[1] * SCALE),
        )
        pygame.draw.circle(screen, (0, 100, 255), earth_screen, 10)
        # Draw Jupiter
        jupiter_screen = (
            int(CENTER[0] + pos_jupiter[0] * SCALE),
            int(CENTER[1] + pos_jupiter[1] * SCALE),
        )
        pygame.draw.circle(screen, (255, 140, 0), jupiter_screen, 13)
        # Draw Asteroids and Trajectories
        for i in range(NUM_ASTEROIDS):
            pos = asteroids[i][:2]
            asteroid_screen = (
                int(CENTER[0] + pos[0] * SCALE),
                int(CENTER[1] + pos[1] * SCALE),
            )
            # Draw original trail (single polyline, no fading)
            if show_trail and len(trajectories[i]) > 1:
                points = [
                    (int(CENTER[0] + p[0] * SCALE), int(CENTER[1] + p[1] * SCALE))
                    for p in trajectories[i]
                ]
                pygame.draw.lines(screen, (180, 180, 180), False, points, 2)
            # Alternate asteroid color
            color = COLOR1 if i < NUM_ASTEROIDS // 2 else COLOR2
            pygame.draw.circle(screen, color, asteroid_screen, 4)
        # Draw Info
        sim_state = font.render(
            f"Simulation: {'PAUSED' if paused else 'RUNNING'} (SPACE)",
            True,
            (255, 100, 100) if paused else (100, 255, 100),
        )
        info1 = font.render(
            f"Laser Thrust: {laser_thrust:.1e} AU/day^2 (L/I)",
            True,
            (255, 255, 255),
        )
        info2 = font.render(
            f"Laser Duration: {laser_duration} days (O/P)", True, (255, 255, 255)
        )
        info3 = font.render(
            f"Asteroid Base Pos: [{ASTEROID_BASE_POS[0]:.2f}, {ASTEROID_BASE_POS[1]:.2f}] (R/F/C/X)",
            True,
            (200, 200, 255),
        )
        info4 = font.render(
            f"Asteroid Base Vel: [{ASTEROID_BASE_VEL[0]:.3f}, {ASTEROID_BASE_VEL[1]:.3f}] (F/V/B/N)",
            True,
            (200, 200, 255),
        )
        info11 = font.render(
            f"Uncertainty Pos: ±{ASTEROID_UNC_POS:.3f} (T/G)", True, (255, 180, 180)
        )
        info12 = font.render(
            f"Uncertainty Vel: ±{ASTEROID_UNC_VEL:.4f} (Y/H)", True, (255, 180, 180)
        )
        info13 = font.render(
            f"Num Asteroids: {NUM_ASTEROIDS} (U/J)", True, (255, 180, 180)
        )
        info5 = font.render(
            f"Earth Radius: {EARTH_ORBIT_RADIUS:.2f} AU (Q/E)", True, (0, 255, 255)
        )
        info6 = font.render(
            f"Jupiter Radius: {JUPITER_ORBIT_RADIUS:.2f} AU (Z/X)", True, (255, 200, 0)
        )
        info7 = font.render(f"Sun Mass: {M_SUN:.2f} (S/D)", True, (255, 255, 0))
        info8 = font.render(f"dt: {dt:.2f} days/frame (A/W)", True, (255, 255, 255))
        info9 = font.render(
            f"Trail: {'ON' if show_trail else 'OFF'} (TAB)", True, (255, 255, 255)
        )
        info10 = font.render("Press ESC to reset", True, (255, 255, 0))
        screen.blit(info1, (20, 20))
        screen.blit(sim_state, (650, 20))
        screen.blit(info2, (20, 50))
        screen.blit(info3, (20, 80))
        screen.blit(info4, (20, 110))
        screen.blit(info5, (20, 140))
        screen.blit(info6, (20, 170))
        screen.blit(info7, (20, 200))
        screen.blit(info8, (20, 230))
        screen.blit(info9, (20, 260))
        screen.blit(info10, (20, 290))
        screen.blit(info11, (20, 320))
        screen.blit(info12, (20, 350))
        screen.blit(info13, (20, 380))
        # Draw sliders
        for s in sliders:
            s.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
