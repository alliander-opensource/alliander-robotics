<!--
SPDX-FileCopyrightText: Alliander N. V.

SPDX-License-Identifier: Apache-2.0
-->

# Behavior trees

Several behavior tree configurations can be found in `alliander_behavior`'s `behavior_trees` folder.
Note: these behaviors are different from Nav2's built-in behavior tree. The behaviors described here are run on platform level, and will often call functions that, in turn, trigger Nav2's `NavigateToPose` or `NavigateRecovery` behavior.

## Trees

Below is a list of the trees that are currently available. These trees will incorporate re-usable behaviors, which are detailed in a later section.

### Patrol and charge

`patrol_and_charge.xml` is a behavior tree for an autonomously navigting robot, e.g. a Husarion Panther or Lynx.

```text
BehaviorTree PatrolAndCharge
└── ReactiveFallback
    ├── SubTree Charge
    ├── Sequence StopCurrentRoute (if a Stop command comes in)
    │   ├── StopRequested (Service listening on ~/stop)
    │   ├── Script (route_size := 0)
    │   └── PublishStatus ("Navigation stopped")
    ├── Sequence ApplyNewRoute (if a new route is received)
    │   ├── ReceiveRoute (subscription to gps_waypoints)
    │   ├── Script (re-initializes route blackboard values) 
    │   └── PublishStatus ("New route received")
    ├── Sequence PatrolIfRoute
    │   ├── ScriptCondition (route_size > 0)
    │   └── SubTree Patrol
    └── Sequence Idle
        ├── PublishStatus ("Idle: waiting for route")
        └── Sleep (msec = 5000)
```

The nodes in the `ReactiveFallback` are ticked in order. If charging is necessary (battery level is low), then `Charge` willexecute. If not, it checks if a `Stop` command is given and if `StopCurrentRoute` needs to execute. If not, it checks if a new route is available and if it should run `ApplyNewRoute`. If that's not the case, the vehicle will `Patrol`, but only if it has a route. If all else fails, the robot will `Idle`, publishing a status that it is waiting for a route.

## Subtrees

### Charge

```text
BehaviorTree Charge
└──Sequence 
    ├── IsBatteryBelow (subscribes to battery messages, SUCCESS if below threshold or stale)
    ├── Fallback DockWithAlert
    │   ├── RetryUntilSuccessful (num_attempts := 5)
    │   │   └── CallTriggerAction DockRobot (calls dock_robot action server)
    │   └── Sequence
    │      ├── PublishStatus ("ALERT: Failed to dock after 5 attempts") 
    │      ├── Sleep (dock_retry_delay_ms)
    │      └── AlwaysFailure 
    ├── SubTree WaitUntilCharged 
    │   ├── Timeout (charge_timeout_ms)
    │   └── Inverter (turns it into "is battery above") 
    │       └── KeepRunningUntilFailure
    │          └── IsBatteryBelow
    └── UndockRobot (calls undock_robot action server) 
``` 

This subtree starts when `IsBatteryBelow` returns `SUCCESS`. Then it tries to dock the robot a few times, logging when it fails. If docking is successful, the robot will wait for a while until charged. Then it undocks and the subtree completes.

### Patrol

```text
BehaviorTree Patrol 
└──Sequence 
    ├── SubTree GetCurrentWaypoint (subscribes to battery messages, SUCCESS if below threshold or stale)
    │   ├── SelectWaypoint (selects next waypoint from route in blackboard, with wrapping)
    │   ├── FromLL (turns GPS waypoint into local map frame point)
    │   └── MakePose (turns map_point into PoseStamped)
    ├── Fallback 
    │   ├── Sequence (navigates to current waypoint)
    │   │   ├── NavigateToPose (calls Nav2's BT for navigation with recovery)
    │   │   └── Script (navigation_failures := 0) 
    │   └── Sequence NavigationFailed (skips to next waypoint)
    │       ├── Script (navigation_failures += 1) 
    │       ├── PublishStatus ("Navigation to waypoint failed, skipping it")
    │       └── Sleep (navigation_retry_delay_ms) 
    ├── Fallback (if all waypoints failed, abandon route) 
    │   ├── ScriptCondition (navigation_failures >= route_size) 
    │   └── Sequence AbandonRoute 
    │       ├── PublishStatus ("ALERT: navigation failed for every waypoint, abandoning route") 
    │       └── Script (route_size := 0) 
    └── Script IncrementWaypoint (waypoint_index = (waypoint_index) + 1 % route_size) 
```
This subtree selects the current waypoint from the blackboard's `route` entry, then turns the GPS coordinates into an (x, y)-pair in map frame. Then it calls Nav2's `NavigateToPose` service, which handles re-planning, costmap clearing, and other recovery behaviors. If that fails, it skips to the next waypoint. Continuing like this, if all waypoints fail, it abandons route and completes the tree. If navigation succeeds, the `waypoint_index` is incremented and navigation starts towards the next waypoint in the list.
