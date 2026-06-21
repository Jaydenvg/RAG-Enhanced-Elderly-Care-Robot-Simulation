# Phase 2 Completion Summary
**NLI + LLM Integration Architecture**

**Date Completed:** June 22, 2026  
**Student:** Jayden Varghese George  
**Supervisor:** Dr. Rula Sharqi  
**Project:** RAG-Enhanced Elderly Care Robot Simulation

---

## ✅ PHASE 2 STATUS: ARCHITECTURE COMPLETE

### Weeks 4-5: NLI Processor & LLM Interface Implementation

**NLI Processor Package:**
- Implemented `intent_classifier.py` (175 lines) - 7 intent types with keyword matching
- Implemented `entity_extractor.py` (260 lines) - Medication, condition, dosage, time extraction
- Implemented `nli_node.py` (160 lines) - ROS2 node with pub/sub
- Implemented `__init__.py` - Package exports
- **Result:** Intent classification + entity extraction working end-to-end

**LLM Interface Package:**
- Implemented `model_loader.py` (210 lines) - Phi-2 GGUF loading via llama-cpp-python
- Implemented `prompt_builder.py` (380 lines) - 5 prompt templates (medication info, health Q&A, reminders, side effects, emergency)
- Implemented `llm_node.py` (410 lines) - ROS2 orchestration node (NLI + RAG → LLM)
- Implemented `__init__.py` - Package exports
- **Result:** Architecture complete and ready (model loading issue to debug)

---

## 📦 TECH STACK (Phase 2)

**Core Libraries:**
- llama-cpp-python (Phi-2 GGUF model inference)
- ROS2 Jazzy with pub/sub messaging
- Python 3.12 with detailed logging

**Models:**
- Phi-2-Q4 GGUF (1.67GB, quantized for CPU inference)
- Sentence-Transformers (all-MiniLM-L6-v2, 384-dim from Phase 1)

**ROS2 Infrastructure:**
- nli_processor node
- llm_interface node
- rag_server node (from Phase 1)

---

## 🏗️ ARCHITECTURE

### Data Flow Pipeline

Patient Query

	↓

/patient_query topic

	↓

NLI Processor Node
├─ IntentClassifier: Classify intent (7 types)
├─ EntityExtractor: Extract medications, conditions, times, dosages
└─ Publish to /nli_result (JSON)

	↓

/nli_result topic

	↓

RAG Server Node (Phase 1)
├─ Semantic search with query
├─ Retrieve top-3 relevant documents
└─ Publish to /rag_results (JSON)

	↓

/rag_results + /nli_result

	↓

LLM Inference Node
├─ Wait for both NLI and RAG data
├─ Build intent-specific prompt
├─ Generate response via Phi-2
└─ Publish to /llm_response (JSON)

	↓

Final Response to Patient

### ROS2 Topics

**Inputs:**
- `/patient_query` (std_msgs/String) - Patient natural language query
- `/rag_results` (std_msgs/String) - Retrieved documents from RAG

**Outputs:**
- `/nli_result` (std_msgs/String) - Intent, confidence, entities
- `/rag_results` (std_msgs/String) - Retrieved documents with similarity scores
- `/llm_response` (std_msgs/String) - Generated response with metadata

---

## 📂 KEY FILES (Phase 2)

### NLI Processor Package

ros2_ws/src/nli_processor/
├── nli_processor/
│   ├── intent_classifier.py      # 7 intent types, keyword matching
│   ├── entity_extractor.py       # Extract medical entities
│   ├── nli_node.py               # ROS2 node
│   └── init.py               # Package exports
├── package.xml                   # ROS2 metadata
├── setup.py                      # Entry point: nli_processor_node
└── test/                         # Unit tests


### LLM Interface Package

ros2_ws/src/llm_interface/
├── llm_interface/
│   ├── model_loader.py           # Phi-2 GGUF loading
│   ├── prompt_builder.py         # 5 prompt templates
│   ├── llm_node.py               # ROS2 orchestration
│   └── init.py               # Package exports
├── package.xml                   # ROS2 metadata
├── setup.py                      # Entry point: llm_inference_node
└── test/                         # Unit tests


---

## 🎯 INTENT CLASSIFICATION

**7 Intent Types:**

1. **ask_medication** - "What is lisinopril?"
2. **ask_side_effects** - "What are side effects?"
3. **ask_dosage** - "How much should I take?"
4. **medication_reminder** - "Time to take medicine"
5. **health_question** - "Why do I have hypertension?"
6. **request_help** - "Can you help me?"
7. **emergency_alert** - "I fell! Help!"

**Confidence Scoring:** 0.0-1.0 based on keyword matches

**Example Results:**
```json
{
  "query": "What are the side effects of lisinopril?",
  "intent": "ask_side_effects",
  "confidence": 0.85,
  "entities": {
    "medications": ["lisinopril"],
    "conditions": [],
    "dosages": [],
    "times": []
  }
}
```

---

## 🧠 ENTITY EXTRACTION

**Recognized Entities:**

| Category | Examples |
|----------|----------|
| Medications | lisinopril, metformin, ibuprofen, aspirin, insulin, etc. |
| Conditions | hypertension, diabetes, arthritis, dementia, heart disease, etc. |
| Dosages | "10 mg", "500 ml", "2 tablets", etc. (regex-based) |
| Times | morning, afternoon, evening, bedtime, before meals, etc. |

**Example Extraction:**


Query: "I need to take my lisinopril 10mg in the morning"
Extracted:

medications: ["lisinopril"]
dosages: ["10 mg"]
times: ["morning"]
conditions: []


---

## 📊 PROMPT TEMPLATES

**5 Different Prompt Types:**

1. **Medication Info Prompt**
   - Purpose: Explain medication to patient
   - Includes: Drug purpose, how to take, side effects, when to contact doctor

2. **Health Question Prompt**
   - Purpose: Answer general health questions
   - Includes: Condition info, self-care tips, when to see doctor

3. **Medication Reminder Prompt**
   - Purpose: Friendly medication reminder
   - Includes: Medication name, dosage, purpose, instructions

4. **Side Effects Assessment Prompt**
   - Purpose: Help patient understand if symptom is a side effect
   - Includes: Known side effects, severity, management tips

5. **Emergency Assessment Prompt**
   - Purpose: Assess if situation requires emergency services
   - Includes: Critical symptom checking, recommendations

---

## 🚀 RUNNING THE SYSTEM (Phase 2)

### Terminal 1: RAG Server
```bash
cd ~/rag_elderly_care_robot_simulation/ros2_ws
source install/setup.bash
ros2 run rag_server rag_server_node \
  --ros-args \
  -p kb_path:=/home/jayden/rag_elderly_care_robot_simulation/knowledge_base \
  -p db_path:=/home/jayden/rag_elderly_care_robot_simulation/data/chroma_db
```

### Terminal 2: NLI Processor
```bash
cd ~/rag_elderly_care_robot_simulation/ros2_ws
source install/setup.bash
ros2 run nli_processor nli_processor_node
```

### Terminal 3: LLM Inference (when model issue fixed)
```bash
cd ~/rag_elderly_care_robot_simulation/ros2_ws
source install/setup.bash
ros2 run llm_interface llm_inference_node
```

### Terminal 4: Test Query
```bash
ros2 topic pub /patient_query std_msgs/String "data: 'What are side effects of lisinopril?'" --once
```

---

## ✅ VERIFIED WORKING

**NLI Processor:**
- ✅ Intent classification working (7 intent types)
- ✅ Entity extraction working (medications, conditions, dosages, times)
- ✅ ROS2 node builds and runs
- ✅ Pub/sub working
- ✅ JSON serialization working

**RAG Server (Phase 1):**
- ✅ Semantic search working (top-3 results)
- ✅ Similarity scores calculated correctly
- ✅ 18 documents indexed
- ✅ ChromaDB persistent storage

**LLM Interface:**
- ✅ All files implemented and syntactically correct
- ✅ Package builds with colcon
- ✅ ROS2 nodes initialize properly
- ✅ Subscribers and publishers created
- ✅ Prompt builder working with 5 templates

**Known Issues:**
- ⚠️ Phi-2 model loading: llama-cpp-python AssertionError
  - File verified: 1.67GB GGUF format
  - Error: `assert self.model is not None` fails during initialization
  - Workaround: Use alternative GGUF format or debug llama-cpp-python compatibility

---

## 📊 STATISTICS

**NLI Processor:**
- 7 intent types defined
- 30+ keywords per intent category
- 20+ medication names recognized
- 15+ medical conditions recognized
- Regex patterns for dosage extraction

**LLM Interface:**
- 5 prompt templates
- 380 lines of prompt engineering
- Context window: 2048 tokens
- Inference parameters configurable

**Phase 2 Code:**
- NLI Processor: 600+ lines
- LLM Interface: 1000+ lines
- Total Phase 2: 1600+ lines

---

## 🔧 CONFIGURATION

**NLI Config (inferred):**
```yaml
intent_labels:
  - ask_medication
  - ask_side_effects
  - ask_dosage
  - medication_reminder
  - health_question
  - request_help
  - emergency_alert

confidence_threshold: 0.5
```

**LLM Config (rag_config.yaml):**
```yaml
llm_inference:
  model: phi-2-q4.gguf
  model_path: ./llm_models/phi-2-q4.gguf
  max_tokens: 256
  temperature: 0.7
  top_p: 0.95
  cpu_threads: 4
  context_window: 2048
```

---

## 🧪 TESTING STATUS

**Component Testing:**
- ✅ NLI Processor: Intent classification tested
- ✅ RAG Server: Semantic search tested
- ⏳ LLM Inference: Architecture complete, model loading needs fix

**Integration Testing:**
- ✅ NLI → RAG topic flow (verified in isolation)
- ⏳ NLI → RAG → LLM full pipeline (blocked by model loading)

**Next Tests Needed:**
- End-to-end pipeline test once model issue resolved
- Performance benchmarking (inference time per component)
- Multi-query stress testing
- Intent classification accuracy assessment

---

## 📝 GIT HISTORY

**Phase 2 Commits:**
1. Phase 2: NLI + LLM Integration Architecture
   - All NLI and LLM files
   - ChromaDB data from Phase 1
   - Comprehensive commit message

---

## 🎯 PHASE 2 PREREQUISITES MET

Phase 2 (NLI + LLM Integration) built on Phase 1:
- ✅ Document loading working (18 chunks)
- ✅ Vector database working (ChromaDB)
- ✅ Semantic search working (top-3 results)
- ✅ ROS2 node infrastructure ready

Phase 2 delivered:
- ✅ Intent classification (7 intent types)
- ✅ Entity extraction (medications, conditions, dosages, times)
- ✅ LLM inference architecture (Phi-2 GGUF support)
- ✅ Context augmentation (RAG + prompt builder)

---

## ⚠️ KNOWN ISSUES & DEBUGGING

### Phi-2 Model Loading Issue

**Problem:**
AssertionError in llama-cpp-python during Llama() initialization
assert self.model is not None

**Diagnosis:**
- Model file: 1.67GB GGUF format (verified)
- llama-cpp-python: Installed correctly
- Error: Silent assertion failure suggests GGUF parsing issue

**Potential Causes:**
1. GGUF format version mismatch
2. Corrupted model file (despite correct size)
3. Missing system libraries for GGUF support
4. llama-cpp-python version compatibility

**Investigation Steps:**
1. Try alternative GGUF quantization (Q5_K_M instead of Q4_K_M)
2. Verify GGUF file with `file` command (shows as "data")
3. Test with different model (e.g., mistral-7b-v0.1.Q4_K_M.gguf)
4. Check llama-cpp-python version and update if needed
5. Inspect llama-cpp library logs with verbose=True

**Workarounds:**
- Continue Phase 2 development with RAG + NLI (no LLM inference)
- Mock LLM responses for testing
- Use API-based LLM (e.g., Ollama server) instead of local GGUF

---

## 💡 KEY LEARNINGS (Phase 2)

1. **ROS2 Syntax:** Use `qos_profile` parameter correctly in `create_subscription/create_publisher`
2. **Intent Classification:** Keyword-based approach works for medical domain with good coverage
3. **Entity Extraction:** Regex patterns + predefined lists effective for medical entities
4. **Prompt Engineering:** Different intents need different prompt structures (5 templates)
5. **GGUF Model Loading:** llama-cpp-python compatibility requires careful version management

---

## 📚 FILES FOR REFERENCE

**Project Files (in /mnt/project/):**
- PHASE0_CODE_TEMPLATES.md
- FYP_IMPLEMENTATION_ROADMAP.md
- PROJECT_KICKOFF_SUMMARY.md
- PHASE1_SESSION_SUMMARY.md

**This Completion Summary:**
- PHASE2_SESSION_SUMMARY.md (this file)

---

## ✨ NEXT STEPS (Phase 3)

When ready for Phase 3, address:

1. **Resolve Phi-2 Model Loading**
   - Debug GGUF compatibility
   - Test alternative models/quantizations
   - Or switch to API-based LLM

2. **Full Pipeline Integration**
   - Connect NLI → RAG → LLM message flow
   - Implement state management between nodes
   - Add response caching

3. **Patient Context Management** (Phase 3 focus)
   - Patient profile management (JSON-based)
   - Interaction history logging
   - Personalized responses based on patient history
   - Multi-turn dialogue support

4. **Testing & Evaluation**
   - End-to-end pipeline tests
   - Performance benchmarking
   - Intent classification accuracy
   - Response generation quality assessment

---

**Phase 2 Complete!** 🎉  
**Architecture Ready!** 🏗️  
**Model Issue Under Investigation** ⚠️  
**Total Lines of Code (Phase 2):** 1,600+  
**Git Commits:** 1 (comprehensive)

---

**Ready to proceed to Phase 3: Context Management & Patient Profiles?**

Reference this file when starting Phase 3.
