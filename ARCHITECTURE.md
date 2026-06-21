# System Architecture

## Overview

Four-layer architecture with all components communicating via ROS2 topics on localhost.

## Architecture Layers

Layer 4: USER INTERFACES
• patient_interface.py (chat)
• caregiver_dashboard.py (monitoring)

       ↓ ROS2 Topics ↓

Layer 3: RAG + NLI INTEGRATION (NEW)

• nli_processor_node (intent classification)
• rag_server_node (semantic search)
• llm_interface_node (Phi-2 inference)
• context_manager_node (patient data)

       ↓ ROS2 Topics ↓

Layer 2: ROS2 CONTROL NODES (EXISTING)
• decision_maker_node (task orchestration)
• navigation_node (Nav2 path planning)
• robot_controller_node (movement execution)
• manipulation_node (MoveIt arm control)
• gazebo_bridge_node (simulation sync)

       ↓ Physics/Simulation ↓

Layer 1: SIMULATION
• Gazebo (physics engine: Bullet)
• RViz (visualization)
• TurtleBot3 Waffle robot model
• Elderly home environment


## Component Details

### Layer 1: Simulation (Gazebo + RViz)

Files:
- simulation/worlds/elderly_home.world
- simulation/models/rag_robot/
- simulation/models/medication_table/

Named Locations:
- home_position: (0.0, 0.0, 0.0)
- patient_area: (2.0, 0.0, 0.0)
- medication_table: (3.0, -1.0, 0.0)
- pickup_table: (3.0, 1.0, 0.0)

Physics: Bullet engine, 0.001s timestep, real-time

### Layer 2: ROS2 Control Nodes (EXISTING - DO NOT MODIFY)

decision_maker_node
- Subscribes: /patient_query, /rag_context, /nli_result, /llm_response
- Publishes: /nav_goal, /cmd_vel, /gripper_command
- Role: Task orchestration

navigation_node (Nav2)
- Subscribes: /nav_goal
- Publishes: /cmd_vel
- Role: Path planning, obstacle avoidance

robot_controller_node
- Subscribes: /cmd_vel
- Publishes: /odom
- Role: Movement execution

manipulation_node (MoveIt)
- Role: Arm motion planning

gazebo_bridge_node
- Role: Gazebo ↔ ROS2 synchronization

### Layer 3: RAG + NLI Integration (NEW)

#### nli_processor_node

Purpose: Parse queries and extract intent/entities

Intent Labels:
- ask_medication: "What is Lisinopril?"
- ask_side_effects: "What are the side effects?"
- ask_dosage: "How much should I take?"
- request_help: "Can you help me?"
- health_question: "Why do I get dizzy?"
- medication_reminder: System reminder
- emergency_alert: "I fell!"

Entity Types:
- medications (drug names)
- conditions (medical terms)
- dosages (amounts: "10mg")
- times (morning, evening, etc.)

Files:
- ros2_ws/src/nli_processor/nli_processor/nli_node.py
- ros2_ws/src/nli_processor/nli_processor/intent_classifier.py
- ros2_ws/src/nli_processor/nli_processor/entity_extractor.py

#### rag_server_node

Purpose: Retrieve healthcare knowledge from vector database

Knowledge Base (10 files, 6,530 words):

Medications (7 files, 4,000 words):
- hypertension_meds.md, diabetes_meds.md, arthritis_meds.md
- dementia_meds.md, cardiac_meds.md, osteoporosis_meds.md, copd_meds.md

Elderly Care (2 files, 1,500 words):
- fall_prevention.md, medication_safety.md

Vector Database:
- Type: ChromaDB
- Path: ./data/chroma_db/
- Embedding Model: sentence-transformers/all-MiniLM-L6-v2
- Embedding Dimension: 384
- Retrieval: Top-3 most similar documents (cosine similarity)
- Threshold: 0.6

Files:
- ros2_ws/src/rag_server/rag_server/rag_server_node.py
- ros2_ws/src/rag_server/rag_server/retriever.py
- ros2_ws/src/rag_server/rag_server/vector_db.py
- ros2_ws/src/rag_server/rag_server/embeddings.py

#### llm_interface_node

Purpose: Generate natural language responses using LLM

LLM Model:
- Model: Phi-2 (2.7B parameters)
- Format: GGUF quantized (Q4_K_M)
- File: ./llm_models/phi-2-q4_k_m.gguf (~2.3GB)
- Inference Time: 5-10 seconds per query
- Device: CPU (no GPU needed)
- Max Tokens: 256
- Temperature: 0.7 (balanced)

Files:
- ros2_ws/src/llm_interface/llm_interface/llm_node.py
- ros2_ws/src/llm_interface/llm_interface/model_loader.py
- ros2_ws/src/llm_interface/llm_interface/prompt_builder.py

#### context_manager_node

Purpose: Manage patient data and interaction state

Patient Profile (JSON):
- patient_id, name, age
- conditions, medications, allergies
- mobility, cognitive status, fall_risk

Interaction History:
- Stores all interactions with timestamps
- Records query, intent, response, confidence
- Tracks medication adherence
- Logs performance metrics

Files:
- ros2_ws/src/context_manager/context_manager/context_node.py
- ros2_ws/src/context_manager/context_manager/patient_profile.py
- ros2_ws/src/context_manager/context_manager/interaction_history.py

### Layer 4: User Interfaces

patient_interface.py
- Chat interface for elderly patients
- Medication reminder notifications
- Simple, large buttons
- Located: ui/patient_interface.py

caregiver_dashboard.py
- Monitoring dashboard for caregivers
- Health status, medication adherence
- Interaction history, robot status
- Emergency controls
- Located: ui/caregiver_dashboard.py

robot_status_monitor.py
- Real-time robot visualization
- Current task, navigation path, status
- Located: ui/robot_status_monitor.py

## ROS2 Topics

Input:
- /patient_query: Raw text from patient
- /medication_reminder: Scheduled medication events
- /fall_detected: Fall sensor triggers

Internal:
- /nli_result: Intent + entities
- /rag_context: Retrieved documents
- /patient_context: Patient profile
- /llm_response: Generated response

Output:
- /odom: Robot odometry
- /interaction_log: Logged interactions
- /system_status: System health

## Data Flow Example: Medication Reminder

1. decision_maker_node detects medication time
2. patient_interface displays reminder
3. Patient queries via /patient_query
4. nli_processor classifies intent
5. rag_server retrieves relevant documents
6. context_manager loads patient profile
7. llm_interface generates response (Phi-2)
8. decision_maker triggers robot action
9. navigation_node plans path
10. robot_controller executes movement
11. context_manager logs interaction
12. caregiver_dashboard displays result

## Performance

| Component | Latency | Throughput |
|-----------|---------|-----------|
| NLI Processing | <100ms | 1000 queries/min |
| RAG Retrieval | <500ms | 100 queries/min |
| LLM Inference | 5-10s | 6-12 responses/min |
| Navigation | 2-5s/meter | Varies |
| End-to-End | 6-15s | 4-10 interactions/min |

## Configuration

RAG Config (config/rag_config.yaml):
- embedding_model: sentence-transformers/all-MiniLM-L6-v2
- chunk_size: 500 words
- top_k_retrieval: 3
- similarity_threshold: 0.6

LLM Config (config/llm_config.yaml):
- model_name: phi-2
- max_tokens: 256
- temperature: 0.7
- device: cpu
- n_threads: 4

NLI Config (config/nli_config.yaml):
- 7 intent labels
- confidence_threshold: 0.7
- 4 entity types

Robot Config (config/robot_config.yaml):
- robot_model: turtlebot3_waffle
- nav2_enabled: true
- movegroup_enabled: true
- use_gazebo: true

## Version Information

- Architecture Version: 1.0.0
- Last Updated: June 21, 2026
- Phase: 0 (Foundation) - Complete ✅
- Next Phase: 1 (RAG Core) - Week 2-4
