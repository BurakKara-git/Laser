# RANGES(mm)
X_MIN = 0.0
X_MAX = 40.0
Y_MIN = 1.0
Y_MAX = 50.0
Z_MIN = 18.0
Z_MAX = 40.0
X_CENTER = 21.08  # Not Precise
Y_CENTER = 13.14  # Not Precise

# VELOCITIES (mm/s)
MIN_X_VEL = 1e-3
MAX_X_VEL = 150.0
MIN_Y_VEL = 1e-3
MAX_Y_VEL = 150.0
MIN_Z_VEL = 1e-3
MAX_Z_VEL = 150.0
MAX_ROT_VEL = 30  # (Radians/s)
Z_TEST_VELOCITY = 0.1
MATRIX_VELOCITY = 50.0

# PLACEHOLDERS
INITIAL_X = 0.0
INITIAL_Y = 3.0
INITIAL_Z = 22.75
INITIAL_ROT = 29333.0
INITIAL_INCREMENT = 0.3
INITIAL_DIAMETER = 12.0
INITIAL_VELOCITY = 1.0
DEGREES = (20, 25, 30, 35, 40, 45, 50, 52, 54, 56, 58, 60)
ENERGIES = {
    20: 1.500,
    25: 1.465,
    30: 1.395,
    35: 1.200,
    40: 0.995,
    45: 0.715,
    50: 0.475,
    52: -52,
    54: -54,
    56: -56,
    58: -58,
    60: 0.105,
}
GCODE_PLACEHOLDER = ";The first line should be the initial positions\n"

# GUI
PROGRESS_BAR_LENGTH = 200

# RUN.PY
log_head = [
    "N",
    "Energy(µJ)",
    "X_Position(mm-Rel)",
    "X_Velocity(mm/s)",
    "Y_Position(mm-Rel)",
    "Y_Velocity(mm/s)",
    "Avg_X_Velocity(mm/s)",
    "Initial_X(mm)",
    "Initial_Y(mm)",
    "Initial_Z(mm)",
    "Initial_Rot(native)",
]
IMAGE_PATH = "sag.png"
Z_TEST_STEP = 0.01

# TEST.PY
TEST_ID = "ae28609e-18a4-4b28-8d89-30c567001c23"
TEST_TOKEN = "VJ_GV-w4_fYUQiI8zrSpz2F6Bh2ZLpCF"
