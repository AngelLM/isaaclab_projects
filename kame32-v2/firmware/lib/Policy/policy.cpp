#include "policy.h"
#include "policy_weights.h"
#include <math.h>

// ---------------------------------------------------------------------------------------------
// Robot-specific mapping (fixed for this robot; NOT part of the exported weights)
// ---------------------------------------------------------------------------------------------
//
// Simulation joint order (0..7): [Body_BLB, Body_BRB, Body_BLF, Body_BRF, BLB_LLB, BRB_LRB,
// BLF_LLF, BRF_LRF] = 4 yaw joints then 4 lift joints.
//
// Physical servo order (0..7), from the Kame firmware: 0 FL-yaw, 1 FR-yaw, 2 FL-lift, 3 FR-lift,
// 4 BL-yaw, 5 BR-yaw, 6 BL-lift, 7 BR-lift.
//
// So each simulation joint maps to a physical servo like this:
static const int SIM_TO_SERVO[8] = {4, 5, 0, 1, 6, 7, 2, 3};

// The resting pose in servo degrees (this is exactly Kame::home()). The policy outputs
// deviations from the resting pose, so a servo angle is home + direction * deviation.
static const float HOME_DEG[8] = {110, 70, 55, 125, 70, 110, 125, 55};

// Mounting direction of each PHYSICAL servo: +1 or -1. This is the ONE thing that must be
// calibrated on the real robot: if a leg moves the wrong way, flip the sign of that servo.
// Indexed by physical servo (0..7). Start all +1 and calibrate (see the docs).
static const float SERVO_DIR[8] = {1, 1, 1, 1, 1, 1, 1, 1};

// Action scale from training (JointPositionActionCfg.scale). target_rad = home_rad + SCALE*action.
static const float ACTION_SCALE = 0.5f;
static const float RAD2DEG = 57.29577951308232f;

// ---------------------------------------------------------------------------------------------

static inline float eluf(float x) { return x > 0.0f ? x : (expf(x) - 1.0f); }
static inline float clampf(float x, float lo, float hi) { return x < lo ? lo : (x > hi ? hi : x); }

void Policy::begin() {
    for (int i = 0; i < 5; i++) {
        for (int k = 0; k < 3; k++) _cmd_hist[i][k] = 0.0f;
        for (int k = 0; k < 8; k++) _act_hist[i][k] = 0.0f;
    }
    for (int k = 0; k < 8; k++) _last_action[k] = 0.0f;
    _head = 0;
    _primed = false;
}

// Build the 55-value observation exactly as Isaac Lab does: the history is per-term and ordered
// oldest -> newest. First the five commands (5 x 3 = 15), then the five actions (5 x 8 = 40).
void Policy::buildObs(const float cmd[3], float obs[55]) {
    // write the current entry into the newest slot
    for (int k = 0; k < 3; k++) _cmd_hist[_head][k] = cmd[k];
    for (int k = 0; k < 8; k++) _act_hist[_head][k] = _last_action[k];

    // oldest slot is the one just after the newest (it will be overwritten next)
    int oldest = (_head + 1) % 5;
    int idx = 0;
    // 5 commands, oldest -> newest
    for (int s = 0; s < 5; s++) {
        int slot = (oldest + s) % 5;
        for (int k = 0; k < 3; k++) obs[idx++] = _cmd_hist[slot][k];
    }
    // 5 actions, oldest -> newest
    for (int s = 0; s < 5; s++) {
        int slot = (oldest + s) % 5;
        for (int k = 0; k < 8; k++) obs[idx++] = _act_hist[slot][k];
    }
}

void Policy::forward(const float obs[55], float act[8]) {
    // normalize: clip((obs - mean) * inv_std, -CLIP, +CLIP)  (matches skrl RunningStandardScaler)
    float x0[POLICY_OBS_DIM];
    for (int i = 0; i < POLICY_OBS_DIM; i++)
        x0[i] = clampf((obs[i] - POLICY_OBS_MEAN[i]) * POLICY_OBS_INV_STD[i], -POLICY_CLIP, POLICY_CLIP);

    float h1[POLICY_HIDDEN], h2[POLICY_HIDDEN], h3[POLICY_HIDDEN];
    // layer 0: 55 -> 128, ELU
    for (int o = 0; o < POLICY_HIDDEN; o++) {
        float acc = POLICY_B0[o];
        const float *w = &POLICY_W0[o * POLICY_OBS_DIM];
        for (int i = 0; i < POLICY_OBS_DIM; i++) acc += w[i] * x0[i];
        h1[o] = eluf(acc);
    }
    // layer 2: 128 -> 128, ELU
    for (int o = 0; o < POLICY_HIDDEN; o++) {
        float acc = POLICY_B2[o];
        const float *w = &POLICY_W2[o * POLICY_HIDDEN];
        for (int i = 0; i < POLICY_HIDDEN; i++) acc += w[i] * h1[i];
        h2[o] = eluf(acc);
    }
    // layer 4: 128 -> 128, ELU
    for (int o = 0; o < POLICY_HIDDEN; o++) {
        float acc = POLICY_B4[o];
        const float *w = &POLICY_W4[o * POLICY_HIDDEN];
        for (int i = 0; i < POLICY_HIDDEN; i++) acc += w[i] * h2[i];
        h3[o] = eluf(acc);
    }
    // output layer: 128 -> 8, linear (this is the Gaussian mean, used directly at inference)
    for (int o = 0; o < POLICY_ACT_DIM; o++) {
        float acc = POLICY_BOUT[o];
        const float *w = &POLICY_WOUT[o * POLICY_HIDDEN];
        for (int i = 0; i < POLICY_HIDDEN; i++) acc += w[i] * h3[i];
        act[o] = acc;
    }
}

void Policy::step(float lin_vel_x, float lin_vel_y, float ang_vel_z, float servo_deg_out[8]) {
    float cmd[3] = {lin_vel_x, lin_vel_y, ang_vel_z};
    float obs[55];
    float act[8];

    buildObs(cmd, obs);
    forward(obs, act);
    for (int k = 0; k < 8; k++) _last_action[k] = act[k];
    _head = (_head + 1) % 5;   // advance so the next step writes the next slot

    // map the 8 sim actions to the 8 physical servo angles (degrees)
    for (int j = 0; j < 8; j++) {
        int servo = SIM_TO_SERVO[j];
        float deviation_deg = RAD2DEG * ACTION_SCALE * act[j];  // deg away from resting pose
        servo_deg_out[servo] = HOME_DEG[servo] + SERVO_DIR[servo] * deviation_deg;
    }
}

bool Policy::selfTest() {
    float act[8];
    forward(POLICY_TEST_OBS, act);
    float max_err = 0.0f;
    for (int k = 0; k < 8; k++) {
        float e = fabsf(act[k] - POLICY_TEST_ACT[k]);
        if (e > max_err) max_err = e;
    }
    return max_err < 1e-2f;
}
