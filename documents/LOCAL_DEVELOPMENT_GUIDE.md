# Running WrenAI Without Docker - Complete Setup Guide

This guide shows you how to run all WrenAI components locally without Docker. You'll need to set up each service individually.

## 🔧 Prerequisites

### System Requirements
- **Python 3.11** or **Python 3.12** (for AI Service and Ibis Server)
- **Node.js 18+** (for Wren UI)
- **Java 21** (for Wren Engine Legacy)
- **Rust** (for Wren Core)
- **PostgreSQL** (optional, for Wren UI database)

### Development Tools
```bash
# Install Just (command runner)
curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to ~/.local/bin

# Install Poetry (Python package manager)
curl -sSL https://install.python-poetry.org | python3 - --version 1.8.3

# Install Rust (for Wren Core)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install pyenv (Python version manager)
curl https://pyenv.run | bash
```

## 🗄️ Step 1: Start Vector Database (Qdrant)

Qdrant is required for the AI Service. You can run it via Docker or install locally:

### Option A: Run Qdrant via Docker (Recommended)
```bash
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant:v1.11.0
```

### Option B: Install Qdrant Locally
```bash
# Download and install Qdrant
wget https://github.com/qdrant/qdrant/releases/download/v1.11.0/qdrant-x86_64-unknown-linux-gnu.tar.gz
tar -xzf qdrant-x86_64-unknown-linux-gnu.tar.gz
./qdrant
```

## 🔧 Step 2: Setup Wren Engine (Java - Legacy)

The Java engine provides fallback support for complex queries.

```bash
# Navigate to the Wren Engine directory
cd wren-engine/wren-core-legacy

# Build the executable JAR
./mvnw clean install -DskipTests -P exec-jar

# Create configuration directory
mkdir -p docker/etc
echo "node.environment=production" > docker/etc/config.properties
echo "wren.experimental-enable-dynamic-fields=true" >> docker/etc/config.properties

# Start the Java engine
java -Dconfig=docker/etc/config.properties \
     --add-opens=java.base/java.nio=ALL-UNNAMED \
     -jar wren-server/target/wren-server-*-executable.jar
```

The Java engine will run on **http://localhost:8080**

## ⚙️ Step 3: Setup Ibis Server (Python)

Ibis Server is the main data access layer that connects to your databases.

```bash
# Navigate to Ibis Server directory
cd wren-engine/ibis-server

# Install dependencies
just install

# Create environment configuration
cat > .env << EOF
WREN_ENGINE_ENDPOINT=http://localhost:8080
LOG_LEVEL=DEBUG
EOF

# Start Ibis Server
just run
```

The Ibis Server will run on **http://localhost:8000**

## 🤖 Step 4: Setup Wren AI Service (Python)

The AI Service handles natural language to SQL conversion.

```bash
# Navigate to AI Service directory
cd wren-ai-service

# Install dependencies
poetry install

# Initialize configuration files
just init

# Edit the generated .env.dev file
cat > .env.dev << EOF
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Vector Database
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Engine Configuration
WREN_IBIS_ENDPOINT=http://localhost:8000
WREN_ENGINE_ENDPOINT=http://localhost:8080

# Service Configuration
WREN_AI_SERVICE_HOST=localhost
WREN_AI_SERVICE_PORT=5555

# UI Configuration
WREN_UI_ENDPOINT=http://localhost:3000
EOF

# Edit config.yaml for your LLM provider (if not using OpenAI)
# See: docs/configuration.md for custom LLM setup

# Start required containers (just Qdrant if you didn't install it locally)
just up

# Start the AI Service
just start
```

The AI Service will run on **http://localhost:5555**

## 🖥️ Step 5: Setup Wren UI (Node.js)

The UI provides the web interface for WrenAI.

```bash
# Navigate to UI directory
cd wren-ui

# Install dependencies
yarn install

# Setup database (SQLite by default)
yarn migrate

# For PostgreSQL instead of SQLite (optional):
# export DB_TYPE=pg
# export PG_URL=postgres://user:password@localhost:5432/dbname
# yarn migrate

# Configure environment for local development
export OTHER_SERVICE_USING_DOCKER=false
export EXPERIMENTAL_ENGINE_RUST_VERSION=false

# Set service endpoints
export WREN_ENGINE_ENDPOINT=http://localhost:8080
export IBIS_SERVER_ENDPOINT=http://localhost:8000
export WREN_AI_SERVICE_ENDPOINT=http://localhost:5555

# Start the development server
yarn dev
```

The UI will run on **http://localhost:3000**

## 🚀 Step 6: Verification & Testing

### Check Service Health
```bash
# Check Java Engine
curl http://localhost:8080/v2/health

# Check Ibis Server
curl http://localhost:8000/health

# Check AI Service
curl http://localhost:5555/health

# Check Qdrant
curl http://localhost:6333/health

# Check UI
curl http://localhost:3000/api/health
```

### Test Data Source Connection
1. Open **http://localhost:3000** in your browser
2. Go through the setup wizard
3. Configure a data source connection
4. Test with a simple query

## 📁 Directory Structure & Ports

```
WrenAI/
├── wren-engine/
│   ├── wren-core-legacy/     # Java Engine (Port 8080)
│   └── ibis-server/          # Data Access Layer (Port 8000)
├── wren-ai-service/          # AI Service (Port 5555)
├── wren-ui/                  # Web UI (Port 3000)
└── docker/                   # Docker configs (for reference)

External Services:
├── Qdrant Vector DB          # Port 6333/6334
└── Your Databases            # Various ports
```

## 🔧 Environment Variables Reference

### Wren UI (.env or environment)
```bash
# Database
DB_TYPE=sqlite  # or 'pg' for PostgreSQL
SQLITE_FILE=./db.sqlite3  # for SQLite
PG_URL=postgres://user:pass@localhost:5432/dbname  # for PostgreSQL

# Service Endpoints
WREN_ENGINE_ENDPOINT=http://localhost:8080
IBIS_SERVER_ENDPOINT=http://localhost:8000
WREN_AI_SERVICE_ENDPOINT=http://localhost:5555

# Development
OTHER_SERVICE_USING_DOCKER=false
EXPERIMENTAL_ENGINE_RUST_VERSION=false
```

### AI Service (.env.dev)
```bash
# LLM Provider
OPENAI_API_KEY=your_api_key_here
GENERATION_MODEL=gpt-4o-mini

# Vector Database
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Services
WREN_IBIS_ENDPOINT=http://localhost:8000
WREN_ENGINE_ENDPOINT=http://localhost:8080
WREN_UI_ENDPOINT=http://localhost:3000

# AI Service
WREN_AI_SERVICE_HOST=localhost
WREN_AI_SERVICE_PORT=5555
```

### Ibis Server (.env)
```bash
WREN_ENGINE_ENDPOINT=http://localhost:8080
LOG_LEVEL=DEBUG
```

## 🛠️ Development Workflow

### Starting All Services
```bash
# Terminal 1 - Java Engine
cd wren-engine/wren-core-legacy
java -Dconfig=docker/etc/config.properties --add-opens=java.base/java.nio=ALL-UNNAMED -jar wren-server/target/wren-server-*-executable.jar

# Terminal 2 - Ibis Server  
cd wren-engine/ibis-server
just run

# Terminal 3 - AI Service
cd wren-ai-service
just start

# Terminal 4 - UI
cd wren-ui
yarn dev

# Terminal 5 - Qdrant (if not using Docker)
./qdrant
```

### Stopping Services
- Use `Ctrl+C` in each terminal
- Or use `just down` in the AI Service directory to stop containers

## 🔍 Troubleshooting

### Common Issues

#### 1. Port Conflicts
```bash
# Check what's using a port
lsof -i :8080
lsof -i :3000

# Kill processes if needed
kill -9 <PID>
```

#### 2. Python Version Issues
```bash
# Use pyenv to manage Python versions
pyenv install 3.12
pyenv local 3.12
poetry env use $(pyenv which python)
```

#### 3. Java Engine Build Issues
```bash
# Clean and rebuild
cd wren-engine/wren-core-legacy
./mvnw clean
./mvnw clean install -DskipTests -P exec-jar
```

#### 4. Node.js Version Issues
```bash
# Use nvm to manage Node.js versions
nvm install 18
nvm use 18
```

#### 5. Database Connection Issues
```bash
# For PostgreSQL setup
createdb wrenai
export PG_URL=postgres://postgres:password@localhost:5432/wrenai

# For SQLite (default)
rm -f db.sqlite3  # Reset database
yarn migrate      # Recreate tables
```

### Service Dependencies

The services must be started in this order:
1. **Qdrant** (vector database)
2. **Java Engine** (semantic processing)
3. **Ibis Server** (data access)
4. **AI Service** (natural language processing)
5. **UI** (web interface)

### Logs & Debugging

```bash
# AI Service logs
cd wren-ai-service
tail -f logs/wren-ai-service.log

# Ibis Server logs  
cd wren-engine/ibis-server
just run  # Logs appear in terminal

# Java Engine logs
# Check terminal output where Java engine is running

# UI logs
cd wren-ui
yarn dev  # Logs appear in terminal
```

## 🌟 Benefits of Non-Docker Setup

1. **Faster Development**: Direct code changes without rebuilds
2. **Better Debugging**: Native IDE integration and debugging
3. **Resource Efficiency**: No Docker overhead
4. **Easier Testing**: Direct access to all services
5. **Custom Configuration**: Full control over all settings

## 📚 Additional Resources

- [Wren AI Documentation](https://docs.getwren.ai/)
- [AI Service Configuration](wren-ai-service/docs/configuration.md)
- [Engine Development Guide](wren-engine/ibis-server/docs/development.md)
- [UI Development Guide](wren-ui/README.md)

This setup gives you full control over the WrenAI stack for development and customization!
