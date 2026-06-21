# Environment Setup Guide

## Prerequisites

- OS: Ubuntu 24.04 LTS
- ROS2: Jazzy Jalisco (already installed)
- Python: 3.12+ (already installed)
- RAM: 16GB+ (for LLM model inference)

## Step 1: Virtual Environment

Your venv is already created and activated:

```bash
cd ~/rag_elderly_care_robot_simulation
source venv/bin/activate
```

## Step 2: Python Dependencies

All packages are already installed via:

```bash
pip install -r requirements.txt
```

Verify:
```bash
python3 -c "import langchain, chromadb, sentence_transformers, torch; print('✓ All packages OK')"
```

## Step 3: ROS2 Setup

Source ROS2:
```bash
source /opt/ros/jazzy/setup.bash
```

Build workspace:
```bash
cd ~/rag_elderly_care_robot_simulation/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

Verify:
```bash
ros2 node list
```

## Step 4: Knowledge Base

10 healthcare documents created in knowledge_base/:

**Medications (7 files, 4,000 words)**
- hypertension_meds.md (1,165 words)
- diabetes_meds.md (528 words)
- arthritis_meds.md (562 words)
- dementia_meds.md (359 words)
- cardiac_meds.md (407 words)
- osteoporosis_meds.md (587 words)
- copd_meds.md (645 words)

**Elderly Care (2 files, 1,500 words)**
- fall_prevention.md (741 words)
- medication_safety.md (759 words)

## Step 5: Configuration Files

Four YAML files created in config/:
- rag_config.yaml
- llm_config.yaml
- nli_config.yaml
- robot_config.yaml

## Step 6: Download LLM Model (Optional)

```bash
cd ~/rag_elderly_care_robot_simulation/llm_models
wget https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2-q4_k_m.gguf
```

File size: ~2.3GB

## Step 7: Launch System

Terminal 1: Gazebo
```bash
source /opt/ros/jazzy/setup.bash
cd ~/rag_elderly_care_robot_simulation/ros2_ws
source install/setup.bash
ros2 launch gazebo gazebo.launch.py
```

Terminal 2: RViz
```bash
source /opt/ros/jazzy/setup.bash
cd ~/rag_elderly_care_robot_simulation/ros2_ws
source install/setup.bash
ros2 launch rviz rviz.launch.py
```

Terminal 3: ROS2 Nodes
```bash
source /opt/ros/jazzy/setup.bash
cd ~/rag_elderly_care_robot_simulation/ros2_ws
source install/setup.bash
ros2 launch complete_system complete_system.launch.py
```

Terminal 4: Patient Interface
```bash
cd ~/rag_elderly_care_robot_simulation
source venv/bin/activate
python3 ui/patient_interface.py
```

## Troubleshooting

ROS2 build fails:
```bash
cd ros2_ws
rm -rf build install log
colcon build --symlink-install
```

Package import errors:
```bash
python3 -c "import [package_name]; print('OK')"
pip install --force-reinstall [package_name]
```

## Status

- ✅ Virtual environment ready
- ✅ All Python dependencies installed
- ✅ ROS2 workspace built
- ✅ Knowledge base populated
- ✅ Configuration files ready
- ⏳ Ready for Phase 1 (RAG implementation)

**Version:** 1.0.0 | **Updated:** June 21, 2026

