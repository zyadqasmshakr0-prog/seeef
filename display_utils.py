"""Present the fixed logical game canvas without Android letterboxing."""
import pygame


def present(surface):
    target = pygame.display.get_surface()
    if target is not None:
        if target is not surface:
            pygame.transform.scale(surface, target.get_size(), target)
    pygame.display.flip()
