SDK → API → Orchestrator
       │
       ├──► CostLab
       │       ├── Router (choose model)
       │       └── Cache (check hit)
       │
       ├──► MonitorLab
       │       ├── Logger (store call)
       │       ├── ImmutableSink (append-only mirror)
       │       └── ALRI (score)
       │
       └──► GovernLab
               ├── Alerts (rule engine)
               └── Redactor (privacy filters)
