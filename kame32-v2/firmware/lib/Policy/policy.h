#ifndef policy_h
#define policy_h

// Neural-network gait policy for kame32 (no-IMU variant).
//
// Replaces the sinusoidal oscillator gait with a trained reinforcement-learning policy.
// The network weights live in policy_weights.h (generated on the PC by export_policy.py).
//
// The policy is BLIND: its only inputs are the velocity command (from the joystick) and the
// history of its own past actions. It runs at 50 Hz. Each call:
//   - takes the current command (lin_vel_x, lin_vel_y=0, ang_vel_z),
//   - builds the 55-value observation (5-step history of [command(3), last_action(8)]),
//   - runs the MLP,
//   - maps the 8 raw outputs to the 8 servo angles in degrees.
//
// See policy.cpp for the exact observation layout, the servo mapping and the sign array that
// must be calibrated on the real robot.

class Policy {
public:
    void begin();                             // reset history buffers to zero
    bool selfTest();                          // check inference matches the embedded test case

    // Run one 50 Hz control step. Inputs are the velocity command; outputs are 8 servo angles
    // in degrees (physical servo order 0..7), ready for Kame::setServo.
    void step(float lin_vel_x, float lin_vel_y, float ang_vel_z, float servo_deg_out[8]);

    // Raw MLP forward pass (normalization + 4 ELU layers). obs[55] -> act[8]. Exposed for the
    // self-test. Does not touch history.
    void forward(const float obs[55], float act[8]);

private:
    // rolling history of the last 5 (command, action) pairs, newest at index _head
    float _cmd_hist[5][3];
    float _act_hist[5][8];
    int _head;                 // index of the newest entry
    bool _primed;              // whether the buffers have been filled once
    float _last_action[8];     // raw network output of the previous step

    void buildObs(const float cmd[3], float obs[55]);
};

#endif
