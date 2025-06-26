# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is the Rasa Pro 3.11 source code extracted from site-packages. Rasa is a conversational AI framework for building contextual AI assistants and chatbots. The codebase is structured as a comprehensive Python package with CLI interface, core dialogue management, NLU (Natural Language Understanding), and advanced dialogue understanding capabilities.

## Common Development Commands

Since this is extracted source code from site-packages, typical development commands are not available. The codebase is primarily for analysis and understanding rather than development. However, the main entry points are:

- **Main CLI Interface**: `python -m rasa` (via `__main__.py`)
- **Training Models**: `python -m rasa train` 
- **Testing Models**: `python -m rasa test`
- **Running Server**: `python -m rasa run`
- **Interactive Learning**: `python -m rasa interactive`
- **Shell Interface**: `python -m rasa shell`

## Architecture Overview

### Core Components

1. **CLI Layer** (`cli/`): Command-line interface with subcommands for training, testing, running, and other operations
2. **Core Engine** (`core/`): Dialogue management, policy framework, and conversation handling
3. **NLU Pipeline** (`nlu/`): Natural language understanding components including tokenizers, featurizers, classifiers, and extractors
4. **Dialogue Understanding** (`dialogue_understanding/`): Advanced LLM-based dialogue understanding with command generation and flow management
5. **Shared Components** (`shared/`): Common utilities, domain management, and data structures

### Key Architecture Patterns

- **Plugin Architecture**: Extensive use of plugin system with hooks for extensibility
- **Pipeline-based Processing**: Both NLU and dialogue processing use configurable pipelines
- **Event-driven Architecture**: Dialogue state managed through events and trackers
- **Provider Pattern**: LLM and embedding providers abstracted through client interfaces
- **Recipe-based Configuration**: Component registration and configuration through recipes

### Data Flow

1. **Input Processing**: User messages processed through NLU pipeline
2. **Dialogue Understanding**: LLM-based command generation for flow control
3. **Policy Framework**: Multiple policies predict next actions
4. **Action Execution**: Actions executed through various executors
5. **Response Generation**: NLG generates appropriate responses
6. **State Management**: Tracker stores maintain conversation state

### Key Directories

- `core/`: Dialogue management, policies, actions, and conversation processing
- `nlu/`: Natural language understanding components and pipelines  
- `dialogue_understanding/`: LLM-based dialogue understanding and command generation
- `shared/`: Common utilities, domain definitions, and data structures
- `cli/`: Command-line interface and argument parsing
- `engine/`: Training engine, graph execution, and model management
- `graph_components/`: Reusable components for training and inference graphs

### Important Classes

- `Agent` (`core/agent.py`): Main interface for loading and running Rasa models
- `Domain` (`shared/core/domain.py`): Defines assistant capabilities, intents, entities, slots, and responses
- `MessageProcessor` (`core/processor.py`): Processes incoming messages through the full pipeline
- `DialogueStateTracker` (`shared/core/trackers.py`): Maintains conversation state and history
- `SingleStepLLMCommandGenerator` (`dialogue_understanding/`): Generates commands using LLM for dialogue flow control

### Configuration

- Configuration is YAML-based with schema validation
- Training pipelines defined through recipes and component graphs
- Domain files define assistant capabilities and conversation scope
- Multiple deployment options including server mode and various channels