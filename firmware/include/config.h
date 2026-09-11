#ifndef CONFIG_H
#define CONFIG_H

#include <stdint.h>

#define CONTROL_HZ           1000
#define NUM_AXES             3

#define AXIS_YAW             0
#define AXIS_PITCH           1
#define AXIS_EXT             2

/* Soft limits (milli-deg or mm) */
#define YAW_MIN_MDEG         (-70000)
#define YAW_MAX_MDEG         (70000)
#define PITCH_MIN_MDEG       (-15000)
#define PITCH_MAX_MDEG       (70000)
#define EXT_MIN_MM           0
#define EXT_MAX_MM           500

/* Unqualified commissioning envelope; never a validated performance rating. */
#define YAW_VEL_CAP_MDEG_S   20000
#define PITCH_VEL_CAP_MDEG_S 20000
#define EXT_VEL_CAP_MM_S     150

#define WATCHDOG_MS          2
#define FRAME_TIMEOUT_MS      20
#define SETPOINT_TIMEOUT_MS   50
#define HOST_TIMEOUT_MS      200

#define PIN_ESTOP_SENSE      2
#define PIN_EXT_HOME         3
#define PIN_EXT_MAX          4
#define PIN_CATCH_SENSOR     5
#define PIN_LATCH_SERVO      6

#endif
