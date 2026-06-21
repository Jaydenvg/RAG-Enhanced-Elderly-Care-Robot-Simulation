# RAG-Enhanced Elderly Care Robot Simulation

**A fully simulated intelligent elderly care robot system combining ROS2, Retrieval-Augmented Generation (RAG), and Natural Language Interface (NLI).**

## 🎯 Project Overview

BEng Robotics Final Year Project at Heriot-Watt University Dubai, supervised by Dr. Rula Sharqi.

## 🚀 Quick Start

```bash
cd ~/rag_elderly_care_robot_simulation
source venv/bin/activate
source /opt/ros/jazzy/setup.bash
cd ros2_ws && colcon build --symlink-install && source install/setup.bash
```

## 📊 Status: Phase 0 ✅ COMPLETE

- ✅ Project structure created
- ✅ 10 knowledge base documents (6,530 words)
- ✅ 4 YAML configuration files  
- ✅ Python virtual environment (all dependencies installed)
- ✅ ROS2 workspace initialized
- ✅ Git repository configured

## 🧠 Knowledge Base Created

**Medications (7 files, 4,000 words)**
- hypertension_meds.md, diabetes_meds.md, arthritis_meds.md
- dementia_meds.md, cardiac_meds.md, osteoporosis_meds.md, copd_meds.md

**Elderly Care (2 files, 1,500 words)**
- fall_prevention.md, medication_safety.md

**Total: 10 files, 6,530 words of elderly-friendly healthcare content**

## 📋 Next Steps (Phase 1)

Week 2-4: Implement RAG core components
- Document loader
- Vector database population  
- Semantic search retrieval

## 👤 Project Information

- **Student:** Jayden Varghese George
- **University:** Heriot-Watt University Dubai
- **Supervisor:** Dr. Rula Sharqi
- **Timeline:** June - September 2026
- **Version:** 1.0.0
