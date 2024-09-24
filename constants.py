# RANGES(mm)
X_MIN = 0.0
X_MAX = 40.0
Y_MIN = 1.0
Y_MAX = 50.0
Z_MIN = 20.0
Z_MAX = 40.0
X_CENTER = 21  # Not Precise
Y_CENTER = 16.5  # Not Precise
RADIUS_LIST = [
    [0, 420],
    [742, 957],
    [1133, 1284],
    [1420, 1543],
    [1600, 1765],
    [1866, 1961],
    [2053, 2140],
    [2222, 2305],
    [2384, 2459],
    [2533, 2603],
    [2674, 2741],
    [2808, 2871],
    [2935, 2996],
]  # [Inner, Outer] um

# VELOCITIES (mm/s)
MIN_X_VEL = 1e-3
MAX_X_VEL = 150.0
MIN_Y_VEL = 1e-3
MAX_Y_VEL = 150.0
MIN_Z_VEL = 1e-3
MAX_Z_VEL = 150.0
MAX_ROT_VEL = 50  # (Radians/s)
Z_TEST_VELOCITY = 0.1
MATRIX_VELOCITY = 50.0

# PLACEHOLDERS
INITIAL_X = 0.0
INITIAL_Y = 3.0
INITIAL_Z = 25.84
INITIAL_ROT = 29333.0
INITIAL_INCREMENT = 0.3
INITIAL_DIAMETER = 12.0
INITIAL_VELOCITY = 1.0
DEGREES = (20, 25, 30, 35, 40, 45, 50, 52, 54, 56, 58, 60, 62, 64)
ENERGIES = {
    20: 1.85,
    30: 1.395,
    35: 1.200,
    40: 0.995,
    45: 0.715,
    50: 0.825,
    52: 0.850,
    54: 0.700,
    56: 0.540,
    58: 0.435,
    60: 0.301,
    62: 0.200,
    64: 0.117,
}
GCODE_PLACEHOLDER = ";The first line should be the initial positions\n"

# GUI
PROGRESS_BAR_LENGTH = 200

# RUN.PY
log_head = [
    "N",
    "Power(Watt)",
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
HEIGHT_PATH = "./Data/profile.csv"
Z_TEST_STEP = 0.01

# TEST.PY
TEST_ID = "ae28609e-18a4-4b28-8d89-30c567001c23"
TEST_TOKEN = "VJ_GV-w4_fYUQiI8zrSpz2F6Bh2ZLpCF"
