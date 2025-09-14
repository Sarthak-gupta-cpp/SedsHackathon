import pygame
import numpy as np
from physics import Planet, Asteroid, G
from ui import Slider, draw_window_buttons

# --- Simulation Parameters ---
M_SUN = 1.0
M_EARTH = 3.003e-6
M_JUPITER = 9.548e-4
EARTH_ORBIT_RADIUS = 1.0
JUPITER_ORBIT_RADIUS = 5.2
EARTH_ORBITAL_VELOCITY = np.sqrt(G * M_SUN / EARTH_ORBIT_RADIUS)
JUPITER_ORBITAL_VELOCITY = np.sqrt(G * M_SUN / JUPITER_ORBIT_RADIUS)

ASTEROID_BASE_POS = np.array([-1.1, 0.3])
ASTEROID_BASE_VEL = np.array([-0.005, -0.015])
ASTEROID_MASS = 1e-12
ASTEROID_UNC_POS = 0.03
ASTEROID_UNC_VEL = 0.003
NUM_ASTEROIDS = 7

laser_thrust = 5e-9
laser_duration = 20
laser_start_time = 100
dt = 0.5
show_trail = True

pygame.init()
INFO = pygame.display.Info()
WIDTH, HEIGHT = INFO.current_w, INFO.current_h
SCALE = min(WIDTH, HEIGHT) // 3
FPS = 60
COLOR1 = (200, 200, 200)
COLOR2 = (255, 80, 80)

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Asteroid Deflection Game")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 20)

NUM_STARS = 80
star_positions = [
    (np.random.randint(0, WIDTH), np.random.randint(0, HEIGHT))
    for _ in range(NUM_STARS)
]


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


def main():
    global laser_thrust, laser_duration, laser_start_time
    global \
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
    asteroids = generate_asteroids()
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
    paused = False
    while running:
        for event in pygame.event.get():
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
                    pygame.display.iconify()
                elif btn_max_rect.collidepoint(mouse_pos):
                    if not pygame.display.get_surface().get_flags() & pygame.FULLSCREEN:
                        pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
                    else:
                        pygame.display.set_mode((WIDTH, HEIGHT))
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                if event.key == pygame.K_TAB:
                    show_trail = not show_trail
                if event.key == pygame.K_ESCAPE:
                    t = 0
                    asteroids = generate_asteroids()
        if not paused:
            all_bodies = planets + asteroids
            for asteroid in asteroids:
                asteroid.update(
                    dt, t, all_bodies, laser_thrust, laser_start_time, laser_duration
                )
            for planet in planets:
                planet.update(dt, t, all_bodies)
            t += dt
        screen.fill((10, 10, 30))
        for x, y in star_positions:
            pygame.draw.circle(screen, (255, 255, 255), (x, y), 1)
        border_x = slider_x + slider_w + 30
        pygame.draw.line(screen, (200, 200, 200), (border_x, 0), (border_x, HEIGHT), 3)
        draw_window_buttons(screen, btn_close_rect, btn_min_rect, btn_max_rect)
        for s in sliders:
            s.draw(screen, font)
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
        for i, asteroid in enumerate(asteroids):
            color = COLOR1 if i < NUM_ASTEROIDS // 2 else COLOR2
            asteroid_screen = (
                int(sim_center[0] + asteroid.pos[0] * SCALE),
                int(sim_center[1] + asteroid.pos[1] * SCALE),
            )
            if show_trail and len(asteroid.trail) > 1:
                points = [
                    (
                        int(sim_center[0] + p[0] * SCALE),
                        int(sim_center[1] + p[1] * SCALE),
                    )
                    for p in asteroid.trail
                ]
                pygame.draw.lines(screen, (180, 180, 180), False, points, 2)
            pygame.draw.circle(screen, color, asteroid_screen, 4)
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
    import sys

    sys.exit()


if __name__ == "__main__":
    main()
