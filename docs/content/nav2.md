<!--
SPDX-FileCopyrightText: Alliander N. V.

SPDX-License-Identifier: Apache-2.0
-->

# Nav2

According to the official [website](https://docs.nav2.org/):

"*Nav2 is the professionally-supported successor of the ROS Navigation Stack deploying the same kinds of technology powering Autonomous Vehicles brought down, optimized, and reworked for mobile and surface robotics.*"

This documentation shows Nav2 components that are used in this repository, sometimes with some additional explanation about implementation choices.

## Planner
We choose to implement, for our Husarion platforms, the `SmacPlanner2D` planner. This because it is a standard planner in Nav2, and does not need a minimum turning radius. The `SmacPlannerHybrid` needs a minimum turning radius as large as the costmap resolution, a constraint that the Husarion platforms do not have. Using the Hybrid-A* planner sometimes results in no path being found, even though the Husarion robot is able to physically move to the goal pose. Using the classic 2D A* planner resolves this.

## Controller
With a relatively simple planner, we choose MPPI as the Husarion robots` controller. This because it is good for dynamic obstacle avoidance, produces smooth commands, and supports GPU acceleration.


## Behaviour Tree
We implement a behaviour tree that was originally inspired by Nav2's `navigate_to_pose_w_replanning_and_recovery.xml`. See below our tree written out:

```text
MainTree
└── RecoveryNode (NavigateRecovery) [retries: 6]
    ├── PipelineSequence (NavigateWithReplanning)
    │   ├── ControllerSelector
    │   ├── PlannerSelector
    │   ├── RateController (4 Hz)
    │   │   └── RecoveryNode (ComputePathToPose) [retries: 20]
    │   │       ├── ComputePathToPose
    │   │       └── Wait (2s)
    │   └── RecoveryNode (FollowPath) [retries: 1]
    │       ├── ReactiveSequence (FollowPathWithGpsCheck)
    |       |   ├── IsSystemHealthy (custom ConditionNode)
    │       |   └── FollowPath
    │       └── Sequence (Contextual Recovery, in case FollowPath fails)
    │           ├── WouldAControllerRecoveryHelp?
    │           └── ClearEntireCostmap (Local)
    │
    └── Sequence (Global Recovery Branch, in case PipelineSequence a.k.a. navigation fails)
        ├── Fallback (If either says yes, proceed to ReactiveFallback)
        │   ├── WouldAControllerRecoveryHelp?
        │   └── WouldAPlannerRecoveryHelp?
        │
        └── ReactiveFallback (RecoveryFallback)
            ├── GoalUpdated? (If yes, then exit recovery, else proceed to RoundRobin)
            └── RoundRobin (RecoveryActions)
                ├── Sequence (ClearingActions)
                │   ├── ClearEntireCostmap (Local)
                │   └── ClearEntireCostmap (Global)
                ├── Spin (1.57 rad ≈ 90°)
                ├── Wait (5s)
                └── BackUp (0.30m @ 0.15 m/s)
```

In short, this behaviour tree performs autonomous navigation with constant replanning and recovery back-ups. Initially it tries to plan and follow a path, pausing navigation when the GPS signal is not sufficient enough. If either planning or path following fails, there are some local recovery sequences installed (e.g., clearing the local costmap). If navigation still fails, it moves on to a global recovery sequence, that can clear costmaps, spin the vehicle, wait for a period, or move the vehicle back a bit before retrying navigation.
