import pygame


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

    def draw(self, surf, font):
        pygame.draw.rect(surf, (80, 80, 80), self.rect, border_radius=6)
        fillw = int((self.value - self.minv) / (self.maxv - self.minv) * self.rect.w)
        pygame.draw.rect(
            surf,
            (180, 180, 255),
            (self.rect.x, self.rect.y, fillw, self.rect.h),
            border_radius=6,
        )
        handlex = self.rect.x + fillw
        pygame.draw.circle(surf, (40, 40, 200), (handlex, self.rect.centery), 9)
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


def draw_window_buttons(screen, btn_close_rect, btn_min_rect, btn_max_rect):
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
    pygame.draw.rect(screen, (230, 200, 40), btn_min_rect, border_radius=8)
    pygame.draw.line(
        screen,
        (80, 80, 80),
        (btn_min_rect.left + 8, btn_min_rect.centery),
        (btn_min_rect.right - 8, btn_min_rect.centery),
        3,
    )
    pygame.draw.rect(screen, (60, 200, 80), btn_max_rect, border_radius=8)
    pygame.draw.rect(screen, (255, 255, 255), btn_max_rect.inflate(-12, -12), 2)
