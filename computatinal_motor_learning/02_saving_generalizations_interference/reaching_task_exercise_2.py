import pandas as pd
import pygame
import sys
import random
import math
import numpy as np
import matplotlib.pyplot as plt
from pygame.draw import circle

# Game parameters
SCREEN_X, SCREEN_Y = 3840, 2160  # your screen resolution
WIDTH, HEIGHT = SCREEN_X // 1.5, SCREEN_Y // 1.5  # be aware of monitor scaling on windows (150%)
CIRCLE_SIZE = 20
TARGET_SIZE = CIRCLE_SIZE
TARGET_RADIUS = 300
MASK_RADIUS = 0.66 * TARGET_RADIUS
ATTEMPTS_LIMIT = 160
START_POSITION = (WIDTH // 2, HEIGHT // 2)
START_ANGLE = 0
PERTURBATION_ANGLE = 30
TIME_LIMIT = 1000  # time limit in ms

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Initialize Pygame
pygame.init()

# Set up the display
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Reaching Game")

# Initialize game metrics
score = 0
attempts = 0
new_target = None
start_time = 0

new_target = None
start_target = math.radians(START_ANGLE)
move_faster = False
clock = pygame.time.Clock()

# Initialize game modes
mask_mode = False
target_mode = 'fix'  # Mode for angular shift of target: random, fix, dynamic
perturbation_mode = True
perturbation_type = 'gradual'  # Mode for angular shift of controll: random, gradual or sudden
prev_gradual_attempts = 0
perturbation_angle = math.radians(PERTURBATION_ANGLE)  # Angle between mouse_pos and circle_pos
perturbed_mouse_angle = 0
gradual_step = 0
gradual_attempts = 1
perturbation_rand = random.uniform(-math.pi / 4, +math.pi / 4)

error_angles = []  # List to store error angles

# Flag for showing mouse position and deltas
show_mouse_info = False


# Function to generate a new target position
def generate_target_position():
    if target_mode == 'random':
        angle = random.uniform(0, 2 * math.pi)

    elif target_mode == 'fix':
        angle = start_target;

    new_target_x = WIDTH // 2 + TARGET_RADIUS * math.sin(angle)
    new_target_y = HEIGHT // 2 + TARGET_RADIUS * -math.cos(angle)  # zero-angle at the top
    return [new_target_x, new_target_y]


# Function to check if the current target is reached0
def check_target_reached():
    if new_target:
        distance = math.hypot(circle_pos[0] - new_target[0], circle_pos[1] - new_target[1])
        return distance <= CIRCLE_SIZE
    return False


# Function to check if player is at starting position and generate new target
def at_start_position_and_generate_target(mouse_pos):
    distance = math.hypot(mouse_pos[0] - START_POSITION[0], mouse_pos[1] - START_POSITION[1])
    if distance <= CIRCLE_SIZE:
        return True
    return False


def compute_error_angle(start_position,
                        target,
                        circle_pos):
    s = np.array(start_position)
    t = np.array(target)
    c = np.array(circle_pos)

    A = t - s
    B = c - s
    dot_product = np.dot(A, B)
    magnitude_A = np.linalg.norm(A)
    magnitude_B = np.linalg.norm(B)
    # Compute the cosine of the angle
    cos_theta = dot_product / (magnitude_A * magnitude_B)

    # Compute the angle in radians and degrees
    angle_radians = np.arccos(cos_theta)
    angle_degrees = np.degrees(angle_radians)
    # Equivalent to A_x * B_y - A_y * B_x
    det = A[0] * B[1] - A[1] * B[0]

    # Compute the signed angle using atan2(det, dot_product)
    signed_angle_radians = np.arctan2(det, dot_product)
    signed_angle_degrees = np.degrees(signed_angle_radians)

    assert np.isclose(angle_degrees, np.abs(
        signed_angle_degrees)), "The angle in degrees should equal the magnitude of the signed angle."
    # assuming clock wise error is negative.
    return signed_angle_degrees


# Main game loop
running = True
while running:
    screen.fill(BLACK)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:  # Press 'esc' to close the experiment
                running = False
            elif event.key == pygame.K_4:  # Press '4' to test pertubation_mode
                perturbation_mode = True
            elif event.key == pygame.K_5:  # Press '5' to end pertubation_mode
                perturbation_mode = False
            elif event.key == pygame.K_h:  # Press 'h' to toggle mouse info display
                show_mouse_info = not show_mouse_info

    # Design experiment
    if attempts == 1:
        perturbation_mode = False
    elif attempts == 20:
        perturbation_mode = True
        perturbation_type = 'sudden'
    elif attempts == 60:
        perturbation_mode = False
    elif attempts == 80:
        perturbation_mode = True
        perturbation_type = 'sudden'
    elif attempts == 140:
        perturbation_mode = False
    elif attempts >= ATTEMPTS_LIMIT:
        running = False

    # Hide the mouse cursor
    pygame.mouse.set_visible(False)
    # Get mouse position
    mouse_pos = pygame.mouse.get_pos()

    # Calculate distance from START_POSITION to mouse_pos
    deltax = mouse_pos[0] - START_POSITION[0]
    deltay = mouse_pos[1] - START_POSITION[1]
    distance = math.hypot(deltax, deltay)
    mouse_angle = math.atan2(deltay, deltax)

    # TASK1: CALCULATE perturbed_mouse_pos
    # PRESS 'h' in game for a hint
    if perturbation_mode:
        if perturbation_type == 'sudden':
            # sudden clockwise perturbation of perturbation_angle
            perturbed_mouse_angle = mouse_angle + perturbation_angle  # Add perturbation angle
            perturbed_mouse_pos = [
                START_POSITION[0] + distance * math.cos(perturbed_mouse_angle),
                START_POSITION[1] + distance * math.sin(perturbed_mouse_angle)
            ]

            assert len(perturbed_mouse_pos) == 2
        elif perturbation_type == 'gradual':
            # gradual counterclockwise perturbation of perturbation_angle in 10 steps, with perturbation_angle/10, each step lasts 3 attempts
            delta_angle = perturbation_angle / 10

            perturbed_mouse_angle = mouse_angle - gradual_step * (perturbation_angle / 10)

            # Each step lasts 3 attempts, We increase gradual_step only if gradual_attempts has changed.
            if gradual_attempts % 3 == 0 and not prev_gradual_attempts == gradual_attempts:  # Attempts then increase it.
                gradual_step += 1

            if gradual_step >= 10:
                # Resets after 10 steps for cyclic perturbation
                gradual_attempts = 0

            perturbed_mouse_pos = [
                START_POSITION[0] + distance * math.cos(perturbed_mouse_angle),
                START_POSITION[1] + distance * math.sin(perturbed_mouse_angle)
            ]

        circle_pos = perturbed_mouse_pos
    else:
        circle_pos = pygame.mouse.get_pos()

    # Check if target is hit or missed
    # hit if circle touches target's center
    if check_target_reached():
        score += 1
        attempts += 1

        # CALCULATE AND SAVE ERRORS between target and circle end position for a hit
        error_angle = compute_error_angle(start_position=START_POSITION,
                                          target=new_target,
                                          circle_pos=circle_pos)
        error_angles.append(error_angle)

        new_target = None  # Set target to None to indicate hit
        start_time = 0  # Reset start_time after hitting the target
        if perturbation_type == 'gradual' and perturbation_mode:
            gradual_attempts += 1

    # miss if player leaves the target_radius + 1% tolerance
    elif new_target and math.hypot(circle_pos[0] - START_POSITION[0],
                                   circle_pos[1] - START_POSITION[1]) > TARGET_RADIUS * 1.01:
        attempts += 1

        # CALCULATE AND SAVE ERRORS between target and circle end position for a miss
        error_angle = compute_error_angle(start_position=START_POSITION,
                                          target=new_target,
                                          circle_pos=circle_pos)
        error_angles.append(error_angle)

        new_target = None  # Set target to None to indicate miss
        start_time = 0  # Reset start_time after missing the target

        if perturbation_type == 'gradual' and perturbation_mode:
            gradual_attempts += 1

    # Check if player moved to the center and generate new target
    if not new_target and at_start_position_and_generate_target(mouse_pos):
        new_target = generate_target_position()
        move_faster = False
        start_time = pygame.time.get_ticks()  # Start the timer for the attempt

    # Check if time limit for the attempt is reached
    current_time = pygame.time.get_ticks()
    if start_time != 0 and (current_time - start_time) > TIME_LIMIT:
        move_faster = True
        start_time = 0  # Reset start_time

    # Show 'MOVE FASTER!'
    if move_faster:
        font = pygame.font.Font(None, 36)
        text = font.render('MOVE FASTER!', True, RED)
        text_rect = text.get_rect(center=(START_POSITION))
        screen.blit(text, text_rect)
        # Exclude attempts
        if len(error_angles) > 0:
            error_angles.pop()  # Remove the most recent one
            error_angles.append(np.nan)

    # Generate playing field
    # Draw current target
    if new_target:
        pygame.draw.circle(screen, BLUE, new_target, TARGET_SIZE // 2)

    # Draw circle cursor
    if mask_mode:
        if distance < MASK_RADIUS:
            pygame.draw.circle(screen, WHITE, circle_pos, CIRCLE_SIZE // 2)
    else:
        pygame.draw.circle(screen, WHITE, circle_pos, CIRCLE_SIZE // 2)

    # Draw start position
    pygame.draw.circle(screen, WHITE, START_POSITION, 5)

    # Show score
    font = pygame.font.Font(None, 36)
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (10, 10))

    # Show attempts
    font = pygame.font.Font(None, 36)
    score_text = font.render(f"Attempts: {attempts}", True, WHITE)
    screen.blit(score_text, (10, 30))

    if show_mouse_info:
        mouse_info_text = font.render(f"Mouse: x={mouse_pos[0]}, y={mouse_pos[1]}", True, WHITE)
        delta_info_text = font.render(f"Delta: Δx={deltax}, Δy={deltay}", True, WHITE)
        mouse_angle_text = font.render(f"Mouse_Ang: {np.rint(np.degrees(mouse_angle))}", True, WHITE)
        screen.blit(mouse_info_text, (10, 60))
        screen.blit(delta_info_text, (10, 90))
        screen.blit(mouse_angle_text, (10, 120))

    # Update display
    pygame.display.flip()
    clock.tick(60)

# Quit Pygame
pygame.quit()

## TASK 2, CALCULATE, PLOT AND SAVE (e.g. export as .csv) ERRORS from error_angles
df = pd.DataFrame(error_angles, columns=['error_angles'])
df.to_csv('error_angles_random_increased_target_radius.csv', index=False)

df = pd.read_csv('error_angles_savings.csv')


