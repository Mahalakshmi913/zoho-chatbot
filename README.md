# Zoho ChatBot

An intelligent, multi-agent chatbot built with LangGraph, FastAPI, and React that connects directly to your Zoho Projects portal. This assistant can answer questions about your projects and perform actions (create, update, delete tasks) on your behalf using natural language.

---

## Section 1: Setup Steps

### Prerequisites
Before you begin, ensure you have the following installed:
* Python 3.11
* Node.js 18+
* A Zoho Account with access to Zoho Projects

### Step-by-Step Installation
1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd zoho-chatbot
   ```

2. **Configure Environment Variables:**
   ```bash
   cp .env.example .env
   ```
   Open the `.env` file and fill in your specific values. See **Section 2** for details on finding your Zoho API credentials. 

3. **Install Backend Dependencies and Run:**
   ```bash
   # Install python dependencies
   pip install -r requirements.txt
   
   # Start the FastAPI server
   py -m uvicorn backend.main:app --reload
   ```

4. **Install Frontend Dependencies and Run:**
   Open a new terminal window:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

---

## 🔐 Section 2: OAuth Configuration Guide

To allow the AI to interact with your Zoho Projects, you must create an OAuth application in the Zoho Developer Console.

### 1. Create an App in Zoho API Console
*   Go to the Zoho API Console.
*   Click Add Client and choose Server-based Applications.
*   Name your application (e.g., "Zoho Chatbot").
*   Set the Homepage URL to `http://localhost:3000` (or your frontend URL).
*   Set the Authorized Redirect URIs to `http://localhost:3000/callback`.
*   Click Create.

### 2. Configure Scopes
When authorizing the application, the chatbot relies on specific scopes. Ensure the authorization request includes:
*   `ZohoProjects.portals.READ`
*   `ZohoProjects.projects.ALL`
*   `ZohoProjects.tasks.ALL`
*   `ZohoProjects.users.READ`

### 3. Add Client ID and Secret
*   In the Zoho API Console, open your newly created application.
*   Go to the **Client Secret** tab.
*   Copy the **Client ID** and **Client Secret**.
*   Paste them into your `.env` file under `ZOHO_CLIENT_ID` and `ZOHO_CLIENT_SECRET`.

### 4. Find Your Portal Name
Your Zoho Portal Name/ID is required to make API requests. You can find it by:
*   **Checking the URL:** When logged into Zoho Projects, look at your browser URL (e.g., `https://projects.zoho.com/portal/YOUR_PORTAL_NAME`).
*   **API Verification:** Alternatively, call the `/portals/` endpoint with a valid access token to see the `id_string` of your available portals.

---

## 🏗️ Section 3: Architecture Overview

The system is built on a modern, decoupled architecture designed for extensibility and performance.

*   **Frontend (React/Vite):** A lightweight, responsive chat interface that handles user input and OAuth callback flows. It communicates exclusively with the backend via REST endpoints.
*   **Backend (FastAPI):** Serves as the orchestration layer, handling API routing, secure token management, and WebSocket/HTTP connections. It bridges the gap between the frontend UI and the LangGraph agents.
*   **LangGraph (Stateful AI Routing):** The brain of the application. It routes user requests, maintains conversation state, and orchestrates the execution of LLMs and external tools.
*   **ZohoClient (API Wrapper):** A dedicated, asynchronous HTTP client that manages authenticated communication with the Zoho Projects API v3 endpoints, complete with token refresh logic.

### The Two-Agent System
To maximize efficiency and accuracy, the AI is split into two specialized agents:
1.  **Query Agent:** Optimized for fetching, reading, and summarizing data (e.g., listing tasks, checking team utilization).
2.  **Action Agent:** Strictly permissioned for executing modifying operations (creating, updating, deleting). 

Separating these concerns prevents accidental data modification during casual queries and allows us to provide different system prompts and safety guardrails (like Human-in-the-Loop confirmations) for write operations.

### Memory Layers
The chatbot utilizes a dual-memory approach:
*   **Short-Term Conversation State:** Managed by LangGraph state and FastAPI sessions to maintain context during a single chat interaction.
*   **Long-Term Memory:** An SQLite database securely persists OAuth tokens and user preferences across server restarts, preventing the need to log in repeatedly.

---

## Section 4: Known Limitations

This architecture has a few intentional constraints to remain lightweight:
*   **Single portal only:** The application logic is currently designed to operate within a single Zoho portal. Multi-portal Zoho accounts are not fully supported out-of-the-box.
*   **No concurrent user handling:** The session management is designed primarily for a single-user demo environment. Handling multiple unique users simultaneously requires implementing strict session segregation.
