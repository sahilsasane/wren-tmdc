# WrenAI Service Development Setup with UV - Complete Guide

This guide provides step-by-step instructions for setting up the WrenAI service for development using UV instead of Poetry.

## ✅ What We've Accomplished

We successfully:
- ✅ Resolved grpcio compilation issues using Python 3.12 and pre-compiled wheels
- ✅ Set up a working Python 3.12 environment with UV
- ✅ Installed all core dependencies including qdrant-haystack, FastAPI, and more
- ✅ Created automated setup scripts
- ✅ Verified the installation works correctly

## 🚀 Quick Start (Recommended)

### Option 1: Automated Setup
```bash
# Run the simple setup script
./setup_uv_simple.sh

# Or run the full setup script
./setup_uv.sh
```

### Option 2: Manual Setup

1. **Install UV** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   source $HOME/.local/share/../bin/env
   ```

2. **Create Python 3.12 environment**:
   ```bash
   uv venv --python 3.12
   source .venv/bin/activate
   ```

3. **Install grpcio first** (prevents compilation issues):
   ```bash
   uv pip install --only-binary=grpcio grpcio grpcio-tools
   ```

4. **Install core dependencies**:
   ```bash
   uv pip install fastapi "uvicorn[standard]" langfuse psycopg2-binary sqlglot sqlparse streamlit
   ```

5. **Install qdrant and haystack**:
   ```bash
   uv pip install "qdrant-haystack>=9.0.0"
   ```

## 🔧 Key Solutions for Common Issues

### GRPCIO Compilation Issues
**Problem**: GRPCIO fails to compile with Python 3.13 due to API changes.

**Solution**: 
- Use Python 3.12 instead of 3.13
- Install grpcio with pre-compiled wheels: `uv pip install --only-binary=grpcio grpcio`

### Qdrant-Haystack Import Issues
**Problem**: `from qdrant_haystack import ...` doesn't work.

**Solution**: Use the new import path:
```python
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore
from haystack_integrations.components.retrievers.qdrant import QdrantEmbeddingRetriever
```

### Version Conflicts
**Problem**: Requirements.txt has incompatible versions.

**Solution**: Updated versions that work together:
- `qdrant-haystack==9.2.0`
- `qdrant-client==1.15.1`
- `haystack-ai==2.16.1`

## 📁 Generated Files

The setup creates these files:
- `UV_SETUP_GUIDE.md` - Detailed setup guide
- `setup_uv.sh` - Full automated setup script
- `setup_uv_simple.sh` - Simple automated setup script
- `GRPCIO_TROUBLESHOOTING.md` - GRPCIO-specific troubleshooting

## ✅ Verification Commands

Test your installation:

```bash
# Activate environment
source .venv/bin/activate

# Test core components
python -c "import grpc; print(f'GRPC version: {grpc.__version__}')"
python -c "import fastapi; print(f'FastAPI version: {fastapi.__version__}')"
python -c "from haystack_integrations.document_stores.qdrant import QdrantDocumentStore; print('✅ Qdrant Haystack works!')"
python -c "import src; print('✅ Main application imports work!')"
```

## 🎯 Next Steps

1. **Configure Environment**:
   ```bash
   # Copy example configurations
   cp tools/config/config.example.yaml config.yaml
   cp tools/config/.env.dev.example .env.dev
   
   # Edit configurations
   nano .env.dev
   nano config.yaml
   ```

2. **Install Just** (optional but recommended):
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to /usr/local/bin
   ```

3. **Start Development Services**:
   ```bash
   # If you have Just installed
   just up
   just start
   
   # Or manually
   python -m src.__main__
   ```

## 🔄 Alternative: Using the Existing Poetry Setup

If you prefer to keep using Poetry but want to avoid grpcio issues:

```bash
# Use Python 3.12
pyenv install 3.12.11
pyenv local 3.12.11

# Install grpcio first
pip install --only-binary=grpcio grpcio grpcio-tools

# Then install with Poetry
poetry install
```

## 🎉 Benefits of Using UV

1. **Speed**: UV is 10-100x faster than pip and Poetry
2. **Reliability**: Better dependency resolution
3. **Simplicity**: No need to learn Poetry-specific commands
4. **Compatibility**: Works with existing requirements.txt files
5. **Modern**: Built in Rust with modern Python packaging standards

## 📊 Performance Comparison

| Tool   | Initial Install | Subsequent Installs | Resolution Speed |
|--------|----------------|---------------------|------------------|
| Poetry | ~5-10 minutes  | ~2-5 minutes        | Slow             |
| pip    | ~3-8 minutes   | ~1-3 minutes        | Medium           |
| UV     | ~1-3 minutes   | ~30-60 seconds      | Very Fast        |

## 🛠️ Troubleshooting

### Issue: Command not found
```bash
# Make sure UV is in your PATH
source $HOME/.local/share/../bin/env
# Or restart your shell
```

### Issue: Permission denied
```bash
# Make scripts executable
chmod +x setup_uv.sh setup_uv_simple.sh
```

### Issue: Python version mismatch
```bash
# Force Python 3.12
uv venv --python 3.12 --force
```

## 📚 Additional Resources

- [UV Documentation](https://docs.astral.sh/uv/)
- [WrenAI Documentation](https://docs.getwren.ai/)
- [Haystack Integration Guide](https://haystack.deepset.ai/integrations/qdrant-document-store)

---

**🎯 Summary**: We've successfully set up WrenAI service with UV, resolved grpcio compilation issues, and created automated setup scripts for future use. The environment is ready for development!
