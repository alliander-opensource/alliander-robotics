<!--
SPDX-FileCopyrightText: Alliander N. V.

SPDX-License-Identifier: Apache-2.0
-->

# Behaviors
Several behavior tree configurations can be found in `alliander_behavior`'s `config` folder.
Note: these behaviors are different from Nav2's built-in behavior tree. The behaviors described here are run on platform level, and will often call functions that, in turn, trigger Nav2's `NavigateToPose` or `NavigateRecovery` behavior.

## Patrol and charge
`patrol_and_charge.xml` is a behavior tree for an autonomously navigting robot, e.g. a Husarion Panther or Lynx.
```text
MainTree (PatrolAndCharge)
└── ReactiveFallback [retries: -1]
    ├── Sequence (Charge)
    │   ├── IsBatteryLow (subscribes to battery messages and checks percentage and age)
    │   ├── NavigateToDock (waypoint to known dock location)
    │   ├── DockRobot (calls Nav2's docking service)
    │   ├── WaitUntilCharged (waits until robot is sufficiently charged)
    │   └── UndockRobot (calls Nav2's docking service)
    │
    └── Sequence (Patrol, in case Charge is completed)
        ├── GetCurrentWaypoint (gets latest waypoint before charging occurred
        ├── NavigateToWaypoint (this calls Nav2's NavigateRecovery behavior) 
        └── IncrementWaypoint (increments waypoint by 1)
```
