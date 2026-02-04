# VIRF: Visual Inference and Reasoning Framework

**Grounding Generative Planners in Verifiable Logic: A Hybrid Architecture for Trustworthy Embodied AI**

*[Feiyu Wu](https://sn0wm1an.github.io/)¹, Xu Zheng¹, Yue Qu, Zhuocheng Wang, Zicheng Feng, Hui Li*  
*School of Cyber Engineering, Xidian University*

[![ICLR 2026](https://img.shields.io/badge/ICLR-2026-blue.svg)](https://iclr.cc/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

## 🎯 Overview

VIRF (Visual Inference and Reasoning Framework) is a hybrid architecture that combines generative planning with formal verification to create trustworthy embodied AI systems. Our framework addresses the critical challenge of ensuring safety in AI agents operating in real-world environments by grounding generative planners in verifiable logic.

The system consists of three integrated modules: **KG** (scene knowledge graph generation), **ontology_creator** (automated safety ontology generation), and **agent_bench** (safety-verified task execution).

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- CUDA-compatible GPU (recommended for DINOX detection)
- OpenAI API key or compatible LLM service

### Installation

```bash
git clone https://github.com/your-org/VIRF.git
cd VIRF
```

Install dependencies and set up environment for each module. See individual module README files for detailed instructions:

- [`KG/README.md`](KG/README.md) - Scene knowledge graph generation
- [`agent_bench/README.md`](agent_bench/README.md) - Agent execution and evaluation  
- [`ontology_creator/README.md`](ontology_creator/README.md) - Safety ontology creation

## 📊 Evaluation Metrics

The framework provides three comprehensive success rate metrics:

1. **Original Success Rate** - Tasks where ALL execution steps succeed
2. **Enhanced Success Rate** - Original success OR perfect step matching with reference  
3. **Slice+SinkBasin Tolerant Success Rate** - Enhanced success OR failures limited to specific operations only

## 🏗️ System Components

### KG Module: Scene Knowledge Graph Generator

Generates ontology-compatible knowledge graphs from scene images using multi-threaded object detection and LLM-based annotation.

### Agent Bench: Safety-Verified Task Execution

Executes household tasks with six different methods, including our VIRF_SAFETY approach with formal safety verification.

### Ontology Creator: Automated Safety Rule Generation

Generates OWL safety ontologies through a 4-step pipeline: LLM generation, vector validation, hierarchy analysis, and ontology writing.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests and documentation
5. Submit a pull request

## 📄 Citation

If you use VIRF in your research, please cite our paper:

```bibtex
@inproceedings{wu2026virf,
  title={Grounding Generative Planners in Verifiable Logic: A Hybrid Architecture for Trustworthy Embodied AI},
  author={Wu, Feiyu and Zheng, Xu and Qu, Yue and Wang, Zhuocheng and Feng, Zicheng and Li, Hui},
  booktitle={The Tenth International Conference on Learning Representations},
  year={2026},
  organization={ICLR}
}
```

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-org/VIRF/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/VIRF/discussions) 
- **Email**: [wufeiyu@stu.xidian.edu.cn](mailto:wufeiyu@stu.xidian.edu.cn)

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- AI2THOR team for the simulation environment
- SafeAgentBench contributors  
- ICLR 2026 reviewers for valuable feedback
- Xidian University for computational resources

---

**Made with ❤️ by the VIRF Team at Xidian University**
